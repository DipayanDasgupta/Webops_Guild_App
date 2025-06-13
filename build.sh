#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Building The App ---"

# 1. Change to the backend directory
cd backend_flask

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

echo "--- Build Complete ---"