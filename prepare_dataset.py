# prepare_dataset.py
import pandas as pd
import json
import os
import shutil
from tqdm import tqdm # For progress bar, install with: pip install tqdm

# --- Configuration ---
# Paths relative to where this script is run from (project root)
KAGGLE_DATA_DIR = "kaggle_dataset_raw"
STYLES_CSV_FILE = os.path.join(KAGGLE_DATA_DIR, "styles.csv")
KAGGLE_IMAGES_DIR = os.path.join(KAGGLE_DATA_DIR, "images")

# Output paths
BACKEND_FLASK_DIR = "backend_flask"
CURATED_CATALOG_JSON_OUTPUT_PATH = os.path.join(BACKEND_FLASK_DIR, "curated_product_catalog.json")
# Define the destination for images relative to the 'static' folder inside the backend
CURATED_IMAGES_DB_DIR_RELATIVE_TO_STATIC = "product_images_db"
CURATED_IMAGES_DB_DIR_ABSOLUTE = os.path.join(BACKEND_FLASK_DIR, "static", CURATED_IMAGES_DB_DIR_RELATIVE_TO_STATIC)

MAX_PRODUCTS_TO_CURATE = 2000  # Adjust as needed for performance

# --- End Configuration ---

def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

def main():
    print("--- Starting Dataset Preparation ---")

    # 1. Ensure output directories exist
    ensure_dir_exists(CURATED_IMAGES_DB_DIR_ABSOLUTE)
    
    # 2. Check for and read styles.csv
    if not os.path.exists(STYLES_CSV_FILE):
        print(f"ERROR: {STYLES_CSV_FILE} not found. Please place it in {KAGGLE_DATA_DIR}/")
        return
    
    print(f"Reading {STYLES_CSV_FILE}...")
    try:
        # Use error_bad_lines=False for newer pandas versions if on_bad_lines is deprecated
        df = pd.read_csv(STYLES_CSV_FILE, on_bad_lines='skip')
        print(f"Successfully read {len(df)} rows from styles.csv.")
    except Exception as e:
        print(f"Error reading {STYLES_CSV_FILE}: {e}")
        return

    # 3. Curate products and copy their images
    print(f"Curating up to {MAX_PRODUCTS_TO_CURATE} products and copying images...")
    curated_products_list = []
    added_product_ids = set()

    # Use tqdm for a nice progress bar
    for _, row in tqdm(df.iterrows(), total=min(len(df), MAX_PRODUCTS_TO_CURATE), desc="Processing products"):
        if len(curated_products_list) >= MAX_PRODUCTS_TO_CURATE:
            break

        product_id_csv = str(row['id'])
        if product_id_csv in added_product_ids:
            continue

        original_image_filename = f"{product_id_csv}.jpg"
        path_to_original_image = os.path.join(KAGGLE_IMAGES_DIR, original_image_filename)

        if os.path.exists(path_to_original_image):
            # Copy image to the backend's static directory
            shutil.copy2(path_to_original_image, CURATED_IMAGES_DB_DIR_ABSOLUTE)

            # Define paths for the JSON catalog. These must be web-accessible.
            # Path for AI processing (relative to backend_flask root)
            image_path_for_ai = os.path.join("static", CURATED_IMAGES_DB_DIR_RELATIVE_TO_STATIC, original_image_filename).replace("\\", "/")
            # Path for frontend display (URL path)
            web_image_path = f"/{image_path_for_ai}"

            # Create a structured product entry
            product_entry = {
                "id": product_id_csv,
                "name": str(row.get('productDisplayName', f"Item {product_id_csv}")),
                # Generate a plausible-looking random price for the demo
                "price": f"${(abs(hash(product_id_csv)) % 180) + 19}.99",
                "description": f"A {row.get('gender', '')} {row.get('articleType', '')} in {row.get('baseColour', '')}. Suitable for {row.get('usage', 'casual wear')} during the {row.get('season', 'all seasons')}.",
                "type": str(row.get('articleType', 'Unknown')),
                "category": str(row.get('masterCategory', 'Unknown')),
                "style": str(row.get('usage', 'N/A')),
                "color_tags": [str(row.get('baseColour', '')).lower()] if pd.notna(row.get('baseColour')) else [],
                "image_path_for_ai": image_path_for_ai, # e.g., "static/product_images_db/1163.jpg"
                "images": [web_image_path], # e.g., ["/static/product_images_db/1163.jpg"]
                "embedding": None # Placeholder for ViT embedding
            }
            curated_products_list.append(product_entry)
            added_product_ids.add(product_id_csv)
            
    # 4. Save the curated catalog to a JSON file
    print(f"Saving {len(curated_products_list)} curated products to {CURATED_CATALOG_JSON_OUTPUT_PATH}...")
    try:
        with open(CURATED_CATALOG_JSON_OUTPUT_PATH, 'w') as f:
            json.dump(curated_products_list, f, indent=2)
        print("Curated product catalog saved successfully.")
    except Exception as e:
        print(f"Error saving curated catalog JSON: {e}")
        return
    
    print(f"--- Dataset Preparation Complete ---")

if __name__ == "__main__":
    main()