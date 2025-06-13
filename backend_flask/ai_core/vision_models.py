# backend_flask/ai_core/vision_models.py
import os
import base64
from PIL import Image
import torch
from transformers import ViTImageProcessor, ViTModel
import openai as openai_sdk
from flask import current_app

# --- Global variables for the ViT Model ---
# This ensures we only load the model into memory once.
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
VIT_MODEL_NAME = 'google/vit-base-patch16-224-in21k'
image_processor_vit = None
model_vit = None

def load_vit_model():
    """Loads the Vision Transformer model and processor into memory."""
    global image_processor_vit, model_vit
    if image_processor_vit is None or model_vit is None:
        try:
            current_app.logger.info(f"Loading ViT model: {VIT_MODEL_NAME} on device: {DEVICE}")
            image_processor_vit = ViTImageProcessor.from_pretrained(VIT_MODEL_NAME)
            model_vit = ViTModel.from_pretrained(VIT_MODEL_NAME).to(DEVICE)
            model_vit.eval() # Set model to evaluation mode
            current_app.logger.info(f"Successfully loaded ViT model: {VIT_MODEL_NAME}")
        except Exception as e:
            current_app.logger.error(f"Error loading ViT model ({VIT_MODEL_NAME}): {e}. Visual search will not work.")
            image_processor_vit = None
            model_vit = None

def extract_vit_features(image_path_or_pil):
    """Extracts features (embedding) from a given image using the loaded ViT model."""
    # Ensure models are loaded
    if image_processor_vit is None or model_vit is None:
        current_app.logger.error("ViT model or processor not available for feature extraction.")
        return None
    try:
        # Open image from file path or use provided PIL image object
        if isinstance(image_path_or_pil, str):
            img = Image.open(image_path_or_pil).convert("RGB")
        else: # Assumes it's a PIL Image
            img = image_path_or_pil.convert("RGB")

        # Process the image and move tensors to the correct device (CPU/GPU)
        inputs = image_processor_vit(images=img, return_tensors="pt").to(DEVICE)
        
        # Get model output without calculating gradients
        with torch.no_grad():
            outputs = model_vit(**inputs)
        
        # The CLS token embedding is a good representation of the entire image
        features = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return features.flatten()
    except Exception as e:
        current_app.logger.error(f"Error extracting ViT features: {e}")
        return None

def get_image_description_openai(image_path, openai_client):
    """Gets a detailed text description of an image using OpenAI's GPT-4o model."""
    if not openai_client:
        current_app.logger.warning("OpenAI client not available. Skipping OpenAI Vision call.")
        return "Image description not available (OpenAI client not configured)."
    try:
        # Read the image file and encode it in base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image focusing on apparel, accessories, style, colors, patterns, and material. Provide a concise but detailed summary useful for e-commerce search."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                    ],
                }
            ],
            max_tokens=300
        )
        description = response.choices[0].message.content
        current_app.logger.info(f"OpenAI Vision Description generated.")
        return description
    except openai_sdk.APIError as e:
        current_app.logger.error(f"OpenAI API Error in vision_models: {e.message}")
        return f"Error from OpenAI API: {e.message}"
    except Exception as e:
        current_app.logger.error(f"General error with OpenAI Vision API call: {e}")
        return f"Error getting image description: {str(e)}"