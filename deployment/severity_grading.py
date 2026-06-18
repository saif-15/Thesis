import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import transforms, datasets
from torchvision import models
from tqdm import tqdm

from easyfsl.samplers import TaskSampler
from easyfsl.utils import plot_images
from sklearn.model_selection import train_test_split

import random
from PIL import Image
import os


label_map = {
    1 : 'A superficial, partial- or full-thickness ulcer of the skin.',
    2 : 'A deep ulcer that extends to ligaments, tendons, joint capsules, or bone.',
    3 : 'A deep ulcer with an abscess, osteomyelitis (bone infection), or joint sepsis',
    4 : 'Localized gangrene',
    5 : 'Globalized gangrene'
}

support_path = "C:/***/DFU/Severity"

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

support_images = []
support_labels = []

class_to_idx = {cls: i for i, cls in enumerate(sorted(os.listdir(support_path)))}

for cls in class_to_idx.keys():
    class_dir = os.path.join(support_path, cls)

    for filename in os.listdir(class_dir):
        img_path = os.path.join(class_dir, filename)
        img = Image.open(img_path).convert("RGB")
        support_images.append(transform(img))
        support_labels.append(class_to_idx[cls])

support_images = torch.stack(support_images)
support_labels = torch.tensor(support_labels)

print("Loaded support set.")


class PrototypicalNetworks(nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone

    def forward(self, support_images, support_labels, query_images):
        z_support = self.backbone(support_images)
        z_query   = self.backbone(query_images)

        n_way = len(torch.unique(support_labels))

        z_proto = torch.stack([
            z_support[support_labels == c].mean(dim=0)
            for c in range(n_way)
        ])

        dists = torch.cdist(z_query, z_proto)
        return -dists

load_path = "./vit_prototype_model.pth"
backbone = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
backbone.heads = nn.Flatten()
model = PrototypicalNetworks(backbone)
checkpoint = torch.load(load_path, map_location=torch.device('cpu'))
model.load_state_dict(checkpoint["model_state_dict"])
print('Model loaded successfully!')

img_path = "C:/***/DFU/Testing/12.jpg"

query_imgs = []
map = {}

img = Image.open(img_path).convert("RGB")
img_tensor = transform(img).unsqueeze(0)

model.eval()
with torch.no_grad():
    scores = model(support_images, support_labels, img_tensor)
    prediction = scores.argmax(dim=1).item()

idx_to_class = {v: k for k, v in class_to_idx.items()}
predicted_label = int(idx_to_class[prediction])

print("Predicted label:", label_map[predicted_label])
