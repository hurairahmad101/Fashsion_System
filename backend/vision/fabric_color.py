import cv2
import numpy as np

def analyze_fabric(image_bytes):
    img_np = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    avg_color = img.mean(axis=(0,1))
    dominant_color = f"RGB{tuple(avg_color.astype(int))}"

    return {
        "fabric_type": "Cotton",
        "dominant_color": dominant_color,
        "suggested_use": "Summer Wear"
    }