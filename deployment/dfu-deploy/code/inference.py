import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import boto3
from io import BytesIO
import os

s3 = boto3.client("s3")


# =========================
# MODEL CLASS
# =========================
class VGG19VAE(nn.Module):
    def __init__(self, latent_dim=256):
        super(VGG19VAE, self).__init__()

        # Load pretrained VGG19 model
        vgg19 = models.vgg19(pretrained=True)

        # Freeze VGG19 encoder weights
        for param in vgg19.features.parameters():
            param.requires_grad = False

        # Use only the convolutional layers from VGG19
        self.encoder = nn.Sequential(*list(vgg19.features.children()))

        # Calculate the flattened size
        self.encoder_output_size = 512 * 7 * 7

        # Fully connected layers for latent space
        self.fc1 = nn.Linear(self.encoder_output_size, 1024)
        self.fc21 = nn.Linear(1024, latent_dim)  # Mean
        self.fc22 = nn.Linear(1024, latent_dim)  # Log-variance

        # Decoder
        self.fc3 = nn.Linear(latent_dim, 1024)
        self.fc4 = nn.Linear(1024, 512 * 7 * 7)

        # Deconvolutional layers
        self.deconv1 = nn.ConvTranspose2d(512, 256, 4, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(256)
        self.deconv2 = nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.deconv3 = nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.deconv4 = nn.ConvTranspose2d(64, 3, 4, stride=1, padding=1)

    def encode(self, x):
        x = self.encoder(x)
        x = x.view(-1, self.encoder_output_size)
        x = torch.relu(self.fc1(x))
        mean = self.fc21(x)
        log_var = self.fc22(x)
        return mean, log_var

    def reparameterize(self, mu, log_var):
        std = torch.exp(0.5 * log_var)
        epsilon = torch.randn_like(std)
        return mu + epsilon * std

    def decode(self, z):
        z = torch.relu(self.fc3(z))
        z = torch.relu(self.fc4(z))
        z = z.view(-1, 512, 7, 7)
        z = torch.relu(self.bn1(self.deconv1(z)))
        z = torch.relu(self.bn2(self.deconv2(z)))
        z = torch.relu(self.bn3(self.deconv3(z)))
        z = torch.sigmoid(self.deconv4(z))

        # Resize to 224x224
        if z.shape[-1] != 224:
            z = nn.functional.interpolate(z, size=(224, 224), mode='bilinear', align_corners=False)

        return z

    def forward(self, x):
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        x_hat = self.decode(z)
        return x_hat, mu, log_var

    def get_latent_representation(self, x):
        """Get latent representation (mu) of input"""
        mu, log_var = self.encode(x)
        return mu, log_var

    def get_reconstruction_error(self, x):
        """Calculate reconstruction error (MSE)"""
        recon, _, _ = self.forward(x)
        mse = torch.mean((x - recon) ** 2, dim=[1, 2, 3])
        return mse

class PrototypicalNetworks(nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone

    def forward(self, support_images, support_labels, query_images):
        z_support = self.backbone(support_images)
        z_query = self.backbone(query_images)

        n_way = len(torch.unique(support_labels))

        z_proto = torch.stack([
            z_support[support_labels == c].mean(dim=0)
            for c in range(n_way)
        ])

        dists = torch.cdist(z_query, z_proto)
        return -dists


# =========================
# LOAD IMAGE FROM S3
# =========================
def load_image_from_s3(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    img_bytes = response["Body"].read()
    return Image.open(BytesIO(img_bytes)).convert("RGB")


# =========================
# LOAD SUPPORT SET (USED ONCE)
# =========================
def load_support_from_s3(bucket, prefix):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])

    support_images = []
    support_labels = []
    class_to_idx = {}

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]

            if key.endswith("/"):
                continue

            cls = key.split("/")[-2]

            if cls not in class_to_idx:
                class_to_idx[cls] = len(class_to_idx)

            img = load_image_from_s3(bucket, key)
            support_images.append(transform(img))
            support_labels.append(class_to_idx[cls])

    print(f" Loaded {len(support_images)} support images")
    return torch.stack(support_images), torch.tensor(support_labels), class_to_idx


# =========================
# LOAD MODELS (RUNS ONCE)
# =========================
def model_fn(model_dir):

    # ------- VAE Model -----------
    vae_model = VGG19VAE(latent_dim=256).to("cpu")
    vae_model.load_state_dict(
        torch.load(os.path.join(model_dir, "vgg_vae.pth"), map_location="cpu") )
    vae_model.eval()

    # -------- Binary Model --------
    binary_model = models.vgg19(weights=None)
    binary_model.classifier = nn.Sequential(
        nn.Linear(25088, 512),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(512, 1)
    )
    binary_model.load_state_dict(
        torch.load(os.path.join(model_dir, "vgg19_model.pth"), map_location="cpu")
    )
    binary_model.eval()

    # -------- Severity Model --------
    backbone = models.vit_b_16(weights=None)
    backbone.heads = nn.Flatten()

    severity_model = PrototypicalNetworks(backbone)

    checkpoint = torch.load(
        os.path.join(model_dir, "vit_prototype_model.pth"),
        map_location="cpu"
    )
    severity_model.load_state_dict(checkpoint["model_state_dict"])
    severity_model.eval()

    # -------- LOAD SUPPORT SET ONCE (OPTIMIZED) --------
    bucket = os.environ.get("SUPPORT_BUCKET")
    prefix = os.environ.get("SUPPORT_PREFIX")

    support_images, support_labels, class_to_idx = load_support_from_s3(bucket, prefix)

    print("Support set cached successfully!")

    return {
        "vae" : vae_model,
        "binary": binary_model,
        "severity": severity_model,
        "support_images": support_images,
        "support_labels": support_labels,
        "class_to_idx": class_to_idx
    }


# =========================
# INPUT HANDLER
# =========================
def input_fn(request_body, content_type):
    import json
    return json.loads(request_body)


def calculate_reconstruction_error(model, image_tensor):
    """Calculate the reconstruction error for anomaly detection"""
    with torch.no_grad():
        recon_image, _, _ = model(image_tensor)
    mse = nn.MSELoss(reduction='mean')  # Use mean instead of sum to normalize the error
    reconstruction_error = mse(recon_image, image_tensor)
    return reconstruction_error.item()



# =========================
# PREDICTION
# =========================
def predict_fn(data, models_dict):

    bucket = data["bucket"]
    img_key = data["img_key"]

    vae_model = models_dict["vae"]
    binary_model = models_dict["binary"]
    severity_model = models_dict["severity"]

    # Cached support data
    support_images = models_dict["support_images"]
    support_labels = models_dict["support_labels"]
    class_to_idx = models_dict["class_to_idx"]
    label_map = {
        1 : 'A superficial, partial- or full-thickness ulcer of the skin.',
        2 : 'A deep ulcer that extends to ligaments, tendons, joint capsules, or bone.',
        3 : 'A deep ulcer with an abscess, osteomyelitis (bone infection), or joint sepsis',
        4 : 'Localized gangrene',
        5 : 'Globalized gangrene'
    }

    img = load_image_from_s3(bucket, img_key)


    # -------- VAE Transformation ------
    transform_vae = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    image_tensor = transform_vae(img).unsqueeze(0)
    # Calculate reconstruction error
    reconstruction_error = calculate_reconstruction_error(vae_model, image_tensor)

    # Threshould
    threshold = 0.05
    # Compare error with threshold
    if reconstruction_error > threshold:
        return {
            "prediction": "Anomaly Detected",
            "description" : "No DFU Detected. Please Upload Other image",
            "severity": None
        }
   
    # -------- Binary Transform --------
    transform_bin = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
    ])

    img_tensor = transform_bin(img).unsqueeze(0)

    # -------- Binary Prediction --------
    with torch.no_grad():
        pred_val = torch.sigmoid(binary_model(img_tensor)).item()

    if pred_val > 0.5:
        return {
            "prediction": "Normal",
            "description" : "No DFU Detected",
            "severity": None
        }

    # -------- Severity Transform --------
    transform_sev = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])

    query_tensor = transform_sev(img).unsqueeze(0)

    # -------- Severity Prediction --------
    with torch.no_grad():
        scores = severity_model(support_images, support_labels, query_tensor)
        pred = scores.argmax(dim=1).item()

    idx_to_class = {v: k for k, v in class_to_idx.items()}
    predicted_class = int(idx_to_class[pred])

    return {
        "prediction": "DFU",
        "description" : label_map[predicted_class],
        "severity": f"Grade {predicted_class}"
    }


# =========================
# OUTPUT HANDLER
# =========================
def output_fn(prediction, content_type):
    import json
    return json.dumps(prediction)