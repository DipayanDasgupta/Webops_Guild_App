import os
import uuid
import json
import sqlite3
from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv

# Flask extensions - NEW
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Custom Modules - NEW
from . import db
from .models import User

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

# NEW: Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
# If a user tries to access a page that requires login, Flask-Login will not redirect,
# but our frontend will handle the "401 Unauthorized" error.
# login_manager.login_view = 'login_api_route' # We can set this, but it's more for server-side rendering.

db.init_app(app)

# NEW: User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id_str):
    return User.get_by_id(user_id_str)

# --- Main Routes ---
@app.route('/')
def index_route():
    return render_template('index.html', initial_recommendations=json.dumps([]))

# --- Authentication Routes - ALL NEW ---
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
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )
        user_id = cursor.lastrowid
        # Initialize preferences for the new user
        cursor.execute(
            "INSERT INTO user_preferences (user_id, preferences_json) VALUES (?, ?)",
            (user_id, json.dumps({}))
        )
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

@app.route('/api/logout', methods=['POST']) # Use POST for actions that change state
@login_required
def logout_api_route():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/current_user_status')
def current_user_status_api_route():
    if current_user.is_authenticated:
        # Fetch fresh data for wishlist and cart
        wishlist_ids = current_user.get_wishlist_ids()
        cart_items = current_user.get_cart_items()
        
        return jsonify({
            "logged_in": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                # Send IDs for wishlist and full item data for cart
                "wishlist_ids": wishlist_ids,
                "cart_items_data": cart_items
            }
        })
    else:
        return jsonify({"logged_in": False})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)