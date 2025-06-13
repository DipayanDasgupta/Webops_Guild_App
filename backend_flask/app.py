import os
import json
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

# NEW: Import the db module
from . import db

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

# NEW: Initialize the database with the app
db.init_app(app)

@app.route('/')
def index_route():
    return render_template('index.html', initial_recommendations=json.dumps([]))

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)