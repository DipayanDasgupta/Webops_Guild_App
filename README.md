# ShopSmarter: AI-Powered Personal Shopping Assistant

ShopSmarter is an advanced AI-powered personal shopping assistant designed to revolutionize the e-commerce experience. Users can upload images of items they like or use natural language text prompts for product discovery. The assistant leverages a suite of AI models to provide intelligent, personalized recommendations.

This project was built for the Software Dev Guild Member Application.

## Live Demo & Video

*   **Video Demo:** [Link to your video demo in the README of your GitHub repo]

## Core Features

*   **Multi-Modal Search:**
    *   **Image-based Search:** Upload an image to find visually similar products from a curated local catalog using a Vision Transformer (ViT).
    *   **Text-based Search:** Use natural language prompts (e.g., "blue summer shirt") for discovery.
*   **Advanced AI Integration:**
    *   **AI Image Description (OpenAI GPT-4o):** Get detailed, human-like descriptions of uploaded images.
    *   **NLP Keyword Extraction (spaCy):** Intelligently extracts key nouns, adjectives, and concepts from text prompts.
    *   **LLM-Powered Query Refinement (Google Gemini):** Analyzes all inputs to suggest optimized search queries and key product attributes.
*   **Intelligent Product Recommendations:**
    *   Combines visual similarity (ViT), AI-generated descriptions, and keyword matching to score and rank products.
    *   The "Why Recommended" feature gives users insight into the AI's decision-making process.
*   **Full User Authentication & Personalization:**
    *   Secure user registration and login system with password hashing (Bcrypt).
    *   Persistent user-specific wishlists and shopping carts that are saved across sessions in an SQLite database.
    *   A mock checkout process to simulate a complete e-commerce flow.
*   **Interactive User Experience:**
    *   Clean, modern, and responsive UI with a user-toggleable dark mode.
    *   Modal pop-ups for detailed product views.
    *   Real-time feedback with loading indicators and insightful messages.

## Tech Stack

*   **Backend:** Python (Flask)
    *   **Authentication:** Flask-Login, Flask-Bcrypt
*   **Database:** SQLite
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3
*   **Core AI/ML Models:**
    *   **Visual Similarity:** Hugging Face `transformers` with Vision Transformer (`google/vit-base-patch16-224-in21k`).
    *   **Image Description:** OpenAI API (`gpt-4o`).
    *   **Language Refinement:** Google Generative AI API (`gemini-1.5-flash-latest`).
    *   **NLP Preprocessing:** spaCy (`en_core_web_sm`).
*   **Data Source & Preparation:**
    *   **Dataset:** Kaggle "Fashion Product Images (Small)".
    *   **Processing:** A custom Python script (`prepare_dataset.py`) processes the raw data, curates a 2000-item catalog, and copies images.

## Project Structure
Webops_Guild_App/
├── backend_flask/
│ ├── ai_core/ # AI-specific logic modules
│ │ ├── init.py
│ │ ├── vision_models.py # ViT, OpenAI Vision
│ │ ├── language_models.py # Gemini, spaCy
│ │ └── product_catalog.py # Manages product data & embeddings
│ ├── static/
│ │ ├── css/style.css
│ │ ├── js/main.js
│ │ └── product_images_db/ # Curated product images
│ ├── templates/
│ │ └── index.html
│ ├── uploads/ # Temporary user uploads (gitignored)
│ ├── app.py # Main Flask application, routes, logic
│ ├── db.py # Database connection and initialization
│ ├── models.py # User model definition for SQLite
│ ├── schema.sql # SQL schema for database tables
│ ├── curated_product_catalog.json # Curated product metadata
│ └── requirements.txt
├── .env.example # Example environment file
├── .gitignore
├── prepare_dataset.py # Script to process raw Kaggle data
└── README.md