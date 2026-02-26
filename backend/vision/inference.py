'''# inference.py
import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np

# Load VTON GAN model (pretrained)
from model.vton_model import VTONGenerator  # replace with your IDM-VTON model import

device = "cuda" if torch.cuda.is_available() else "cpu"

# Preprocessing transforms
transform = T.Compose([
    T.Resize((512, 512)),
    T.ToTensor(),
])

def load_image(path):
    img = Image.open(path).convert("RGB")
    return transform(img).unsqueeze(0).to(device)

def run_vton(person_path, cloth_path, generator_model):
    # Load images
    person = load_image(person_path)
    cloth = load_image(cloth_path)

    # Forward pass through GAN generator
    with torch.no_grad():
        tryon_image = generator_model(person, cloth)  # Returns warped and blended cloth

    # Convert tensor to image
    img_np = (tryon_image.squeeze().cpu().permute(1,2,0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(img_np)
'''