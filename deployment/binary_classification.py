import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score,recall_score, f1_score
import plotly.graph_objects as go
from PIL import Image
import os

# # # # # # # # # # # # # #
# 0 - 0.5 -> Abnormal DFU
# > 0.5 -> Normal
# # # # # # # # # # # # # #

def loadModel():
    # Load trained model
    model = models.vgg19(weights=models.VGG19_Weights.DEFAULT)
    model.classifier = torch.nn.Sequential(
        torch.nn.Linear(25088, 512),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.5),
        torch.nn.Linear(512, 1)
    )
    save_path = "./vgg19_model.pth"
    model.load_state_dict(torch.load( save_path , map_location='cpu'))
    return model

def testModel( model ):
    label_map = {
        0: "DFU",
        1: "Normal"
    }
    # Transform
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
    ])

    # -----------------------------
    # Folder paths
    # -----------------------------
    file_path = "C:/Users/saifu/Desktop/DFU/Testing/12.jpg"
    img = Image.open(file_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0)
    model.eval()
    with torch.no_grad():
        prediction_value = torch.sigmoid(model(img_tensor)).item()

    predicted_class = 1 if prediction_value > 0.5 else 0
    predicted_label = label_map[predicted_class]
    return predicted_label

model = loadModel()
result = testModel( model )

print(result)
