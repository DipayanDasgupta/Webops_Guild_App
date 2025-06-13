import os
import json # New import
from flask import Flask, jsonify, render_template # render_template is new
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')

# Add UPLOAD_FOLDER config and ensure the directory exists
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)


@app.route('/')
def index_route():
    # Now rendering the actual HTML template from the /templates folder
    # We pass an empty list as a JSON string for the 'initial_recommendations' variable in the template
    return render_template('index.html', initial_recommendations=json.dumps([]))

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # use_reloader=False is good practice when loading AI models to prevent them from reloading on every code change.
    app.run(debug=True, use_reloader=False)