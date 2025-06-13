import os
import uuid
import json
import sqlite3
from datetime import datetime
from flask import (
    Flask, request, jsonify, render_template, url_for,
    current_app, send_from_directory, session
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Flask extensions
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Custom Modules
from . import db
from .models import User
from .ai_core.vision_models import load_vit_model, extract_vit_features, get_image_description_openai
from .ai_core.language_models import load_spacy_model, extract_keywords_spacy, get_refined_search_gemini
from .ai_core.product_catalog import load_and_preprocess_catalog, get_catalog_products

# Load environment variables from .env file
load_dotenv()

# --- Initialize AI API Clients ---
# OpenAI SDK
import openai
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Generative AI
import google.generativeai as genai
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Flask App Initialization & Configuration ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key_change_this_123!')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

db.init_app(app)

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id_str):
    return User.get_by_id(user_id_str)

# --- Initialize AI Models and Data Catalog on Startup ---
with app.app_context():
    # Ensure the upload folder exists
    upload_folder_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder_path, exist_ok=True)
    
    app.logger.info("Initializing AI models and services...")
    load_vit_model()
    load_spacy_model()
    load_and_preprocess_catalog()
    app.logger.info("AI services initialization complete.")

# --- Helper Function ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Core Recommendation Logic ---
def generate_final_recommendations(query_image_path=None, text_prompt="", top_k=12):
    current_catalog_with_embeddings = get_catalog_products()
    if not current_catalog_with_embeddings:
        app.logger.error("Product catalog is empty. Cannot generate recommendations.")
        return [], "Error: Product catalog unavailable.", {}

    openai_description = "N/A"
    gemini_refinement = {}
    visual_recommendations = []

    # 1. Visual Search (if an image is provided)
    if query_image_path:
        if openai_client:
            openai_description = get_image_description_openai(query_image_path, openai_client)
        
        query_embedding = extract_vit_features(query_image_path)
        if query_embedding is not None:
            # Prepare catalog embeddings for comparison
            products_with_embeddings = [p for p in current_catalog_with_embeddings if p.get("embedding") is not None]
            if products_with_embeddings:
                db_embeddings = np.array([p["embedding"] for p in products_with_embeddings])
                similarities = cosine_similarity(query_embedding.reshape(1, -1), db_embeddings)[0]
                
                # Get top N visually similar items
                sorted_indices = np.argsort(similarities)[::-1]
                for i in sorted_indices[:top_k * 2]: # Get more initial candidates
                    product = products_with_embeddings[i].copy()
                    product["visual_score"] = float(similarities[i])
                    visual_recommendations.append(product)
    
    # 2. Text and Language Model Processing
    spacy_keywords = extract_keywords_spacy(text_prompt) if text_prompt else []
    
    if text_prompt or openai_description != "N/A":
        gemini_refinement = get_refined_search_gemini(openai_description, text_prompt)

    # 3. Combine and Score all products
    # Start with visual recommendations if they exist, otherwise use the whole catalog
    candidate_products = visual_recommendations if visual_recommendations else [p.copy() for p in current_catalog_with_embeddings]
    
    all_search_keywords = set(spacy_keywords)
    if isinstance(gemini_refinement, dict):
        all_search_keywords.update(gemini_refinement.get("key_attributes", []))
        all_search_keywords.update(gemini_refinement.get("refined_search_query", "").lower().split())

    scored_recommendations = []
    for product in candidate_products:
        score = product.get("visual_score", 0.0) * 10.0 # Weight visual similarity highly
        
        # Combine product metadata into a searchable text block
        product_text_corpus = (f"{product.get('name','')} {product.get('description','')} {product.get('type','')} "
                               f"{product.get('category','')} {' '.join(product.get('color_tags',[]))}").lower()
        
        # Add points for each matching keyword
        text_match_count = sum(1 for kw in all_search_keywords if kw in product_text_corpus)
        score += text_match_count * 2.0

        product["final_score"] = score
        scored_recommendations.append(product)

    # Sort by the final combined score
    scored_recommendations.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    final_recs_list = scored_recommendations[:top_k]
    
    # Clean up final list for JSON response
    for rec in final_recs_list:
        if "embedding" in rec: del rec["embedding"]
        if "visual_score" in rec: del rec["visual_score"]

    return final_recs_list, openai_description, gemini_refinement

# --- Main Application Routes ---
@app.route('/')
def index_route():
    recs, _, _ = generate_final_recommendations(text_prompt="popular trending fashion", top_k=8)
    return render_template('index.html', initial_recommendations=json.dumps(recs))

@app.route('/upload_image', methods=['POST'])
def upload_image_route():
    if 'imageFile' not in request.files:
        return jsonify({"error": "No image file part"}), 400
    file = request.files['imageFile']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "No selected file or file type not allowed"}), 400

    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    # --- Corrected Code ---
filepath = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    prompt_text = request.form.get('prompt', '')
    
    recs, openai_desc, gemini_refine = generate_final_recommendations(
        query_image_path=filepath, text_prompt=prompt_text
    )
    
    image_url_for_preview = url_for('send_uploaded_file', filename=filename)
    
    return jsonify({
        "message": "Image processed successfully",
        "image_preview_url": image_url_for_preview,
        "recommendations": recs,
        "openai_description": openai_desc,
        "gemini_refinement": gemini_refine
    })

@app.route(f"/{app.config['UPLOAD_FOLDER']}/<path:filename>")
def send_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations_route():
    data = request.json
    prompt_text = data.get('prompt', '')
    recs, _, gemini_refine = generate_final_recommendations(text_prompt=prompt_text)
    return jsonify({"recommendations": recs, "gemini_refinement": gemini_refine})

# --- Authentication Routes ---
@app.route('/api/signup', methods=['POST'])
def signup_api_route():
    if current_user.is_authenticated:
        return jsonify({"error": "You are already logged in"}), 400
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if User.get_by_username(username):
        return jsonify({"error": "Username already exists"}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    database = db.get_db()
    try:
        cursor = database.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO user_preferences (user_id, preferences_json) VALUES (?, ?)", (user_id, json.dumps({})))
        database.commit()
        new_user = User.get_by_id(user_id)
        login_user(new_user, remember=True)
        return jsonify({"message": "Signup successful!", "user": {"username": new_user.username, "id": new_user.id}}), 201
    except sqlite3.Error as e:
        app.logger.error(f"Database error during signup: {e}")
        return jsonify({"error": "A database error occurred"}), 500

@app.route('/api/login', methods=['POST'])
def login_api_route():
    if current_user.is_authenticated:
        return jsonify({"error": "You are already logged in"}), 400
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.get_by_username(username)
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        return jsonify({"message": "Login successful", "user": {"username": user.username, "id": user.id}}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout_api_route():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/current_user_status')
def current_user_status_api_route():
    if current_user.is_authenticated:
        # We now need full product details for cart/wishlist to display them
        all_catalog = get_catalog_products()
        
        wishlist_ids = current_user.get_wishlist_ids()
        wishlist_details = [p for p in all_catalog if str(p.get('id')) in wishlist_ids]

        cart_items_raw = current_user.get_cart_items()
        cart_details = []
        for item_raw in cart_items_raw:
            product = next((p.copy() for p in all_catalog if str(p.get('id')) == str(item_raw['product_id'])), None)
            if product:
                product['quantity'] = item_raw['quantity']
                cart_details.append(product)

        return jsonify({
            "logged_in": True,
            "user": {
                "id": current_user.id, "username": current_user.username,
                "wishlist_details": wishlist_details,
                "cart_details": cart_details
            }
        })
    return jsonify({"logged_in": False})

# --- User Data API Routes (Wishlist, Cart) ---
@app.route('/api/wishlist', methods=['POST', 'DELETE'])
@login_required
def wishlist_api_route():
    data = request.json
    product_id = str(data.get('productId'))
    if not product_id: return jsonify({"error": "productId required"}), 400

    if request.method == 'POST':
        current_user.add_to_wishlist_db(product_id)
        return jsonify({"message": "Added to wishlist", "wishlist_ids": current_user.get_wishlist_ids()}), 200
    elif request.method == 'DELETE':
        current_user.remove_from_wishlist_db(product_id)
        return jsonify({"message": "Removed from wishlist", "wishlist_ids": current_user.get_wishlist_ids()}), 200
    return jsonify({"error": "Invalid method"}), 405

@app.route('/api/cart', methods=['POST', 'DELETE'])
@login_required
def cart_api_route():
    data = request.json
    product_id = str(data.get('productId'))
    if not product_id: return jsonify({"error": "productId required"}), 400

    if request.method == 'POST':
        # This simple model just adds one item. The JS handles the logic of not adding duplicates.
        current_user.add_to_cart_db(product_id, 1)
        return jsonify({"message": "Added to cart", "cart_items_data": current_user.get_cart_items()}), 200
    elif request.method == 'DELETE':
        current_user.remove_from_cart_db(product_id)
        return jsonify({"message": "Removed from cart", "cart_items_data": current_user.get_cart_items()}), 200
    return jsonify({"error": "Invalid method"}), 405

@app.route('/api/mock_checkout_process', methods=['POST'])
@login_required
def mock_checkout_process_route():
    cart_items = current_user.get_cart_items()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    order_id = str(uuid.uuid4())
    # In a real app, you would save this order to the database.
    app.logger.info(f"Mock Order {order_id} created for user {current_user.id} with items: {cart_items}")
    
    current_user.clear_cart_db()
    return jsonify({"message": f"Mock checkout successful! Your order ID is {order_id}.", "orderId": order_id}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)