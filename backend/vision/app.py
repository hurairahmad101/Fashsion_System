# app.py
'''import gradio as gr
from inference import run_vton
from model.vton_model import VTONGenerator  # replace with your IDM-VTON import

# Load pretrained generator
generator_model = VTONGenerator().to("cuda")
generator_model.load_state_dict(torch.load("models/vton_ckpt.pth"))

def vton_web(person_img, cloth_img):
    # Save uploaded images temporarily
    person_path = "images/person_tmp.jpg"
    cloth_path = "images/cloth_tmp.png"
    person_img.save(person_path)
    cloth_img.save(cloth_path)

    # Run inference
    output = run_vton(person_path, cloth_path, generator_model)
    return output

# Launch Gradio Interface
iface = gr.Interface(
    fn=vton_web,
    inputs=[gr.Image(type="pil"), gr.Image(type="pil")],
    outputs=gr.Image(type="pil"),
    title="Next-Level Virtual Try-On",
    description="Upload a person image and a clothing item to see the try-on result"
)
iface.launch()
'''