import os
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Flask App Initialization & Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')

# --- Main Application Routes ---
@app.route('/')
def index_route():
    # Later, this will render a template. For now, a simple message.
    return "<h1>Welcome to ShopSmarter AI!</h1><p>Flask server is running.</p>"

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)