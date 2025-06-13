#!/bin/bash
set -e

PROJECT_ROOT=$(pwd)
BACKEND_DIR="backend_flask"

echo "--- ShopSmarter AI Assistant Setup ---"
echo "Project Root: $PROJECT_ROOT"

# 1. Check for backend directory
if [ ! -d "$BACKEND_DIR" ]; then
  echo "Error: Backend directory '$BACKEND_DIR' not found. Please run this script from the project root."
  exit 1
fi

# 2. Create and activate virtual environment in backend_flask
echo ""
echo "--- Setting up Python virtual environment in $BACKEND_DIR ---"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Virtual environment created."
else
  echo "Virtual environment already exists."
fi

# Activate venv
source venv/bin/activate
echo "Virtual environment activated."

# 3. Install Python dependencies
echo ""
echo "--- Installing Python dependencies from requirements.txt ---"
pip install -r requirements.txt

# 4. Download spaCy model
echo ""
echo "--- Downloading spaCy model (en_core_web_sm) ---"
python -m spacy download en_core_web_sm

# 5. Go back to project root
cd "$PROJECT_ROOT"
echo "--- Moved back to project root ---"

echo ""
echo "--- Environment Setup Complete! ---"
echo ""
echo "Next Steps:"
echo "1. Create the file '$BACKEND_DIR/.env' with your API keys (OPENAI_API_KEY, GOOGLE_API_KEY, FLASK_SECRET_KEY)."
echo "2. Place your raw data ('styles.csv' and 'images/' folder) into 'kaggle_dataset_raw/'."
echo "3. Run the data preparation script from the project root:"
echo "   (Make sure venv is active: source $BACKEND_DIR/venv/bin/activate)"
echo "   python prepare_dataset.py"
echo "4. Run the Flask application from the project root:"
echo "   python -m flask --app backend_flask.app run"
echo ""