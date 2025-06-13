# backend_flask/ai_core/product_catalog.py
import json
import os
from flask import current_app
from .vision_models import extract_vit_features

# The name of the JSON file located in the backend_flask directory
DB_METADATA_FILE = "curated_product_catalog.json"
# This will be our in-memory "database" holding products with their embeddings
AI_PRODUCT_CATALOG = []

def load_and_preprocess_catalog():
    """
    Loads product data from a JSON file and computes ViT embeddings for their images.
    This should be called once on app startup within the Flask app context.
    """
    global AI_PRODUCT_CATALOG
    # Avoid reprocessing if already loaded
    if AI_PRODUCT_CATALOG:
        current_app.logger.info("Product catalog already loaded and preprocessed.")
        return

    # The ViT model must be loaded first (this is handled in app.py)
    catalog_file_path = os.path.join(current_app.root_path, DB_METADATA_FILE)
    current_app.logger.info(f"Attempting to load product catalog from: {catalog_file_path}")

    try:
        with open(catalog_file_path, 'r') as f:
            raw_products = json.load(f)
        current_app.logger.info(f"Loaded {len(raw_products)} raw products from {DB_METADATA_FILE}")
    except FileNotFoundError:
        current_app.logger.error(f"FATAL: {DB_METADATA_FILE} not found. Cannot populate product catalog.")
        return
    except json.JSONDecodeError:
        current_app.logger.error(f"FATAL: Error decoding JSON from {DB_METADATA_FILE}.")
        return

    processed_count = 0
    # Process each product to generate its embedding
    for product_data in raw_products:
        # Create a copy to work with
        product = product_data.copy()
        
        # The 'image_path_for_ai' is relative to the backend_flask folder, e.g., "static/product_images_db/1163.jpg"
        rel_image_path = product.get('image_path_for_ai')
        
        if rel_image_path:
            # Create the absolute path for the AI model to read the file
            abs_image_path_for_ai = os.path.join(current_app.root_path, rel_image_path)
            
            if os.path.exists(abs_image_path_for_ai):
                # This function call does the actual AI processing
                embedding = extract_vit_features(abs_image_path_for_ai)
                if embedding is not None:
                    product["embedding"] = embedding
                    processed_count += 1
                else:
                    product["embedding"] = None
                    current_app.logger.warning(f"Failed to get ViT embedding for {product.get('name', 'Unknown')}")
            else:
                product["embedding"] = None
                current_app.logger.warning(f"Image for ViT not found at path: {abs_image_path_for_ai}")
        else:
            product["embedding"] = None

        # Standardize the image URL for the frontend
        # The 'images' array should contain web-accessible paths like "/static/product_images_db/1163.jpg"
        product["imageUrl"] = product["images"][0] if product.get("images") else "/static/placeholder.png"
        
        AI_PRODUCT_CATALOG.append(product)
    
    current_app.logger.info(f"Finished catalog preprocessing. {processed_count}/{len(AI_PRODUCT_CATALOG)} products now have ViT embeddings.")
    if processed_count == 0 and len(AI_PRODUCT_CATALOG) > 0:
        current_app.logger.warning("WARNING: No products were successfully embedded with ViT. Check image paths and ViT model loading.")

def get_catalog_products():
    """Returns the processed product catalog with embeddings."""
    return AI_PRODUCT_CATALOG