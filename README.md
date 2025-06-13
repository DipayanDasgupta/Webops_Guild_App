# ShopSmarter: AI-Powered Personal Shopping Assistant

ShopSmarter is an advanced AI-powered personal shopping assistant designed to revolutionize the e-commerce experience. Users can upload images of items they like or use natural language text prompts for product discovery. The assistant leverages a suite of AI models to provide intelligent, personalized recommendations.

This project was built for the Software Dev Guild Member Application.

## Live Demo & Video

*   **Video Demo:** [**Watch the Demo on Google Drive**](https://drive.google.com/file/d/1Anu8OEmjdkVM5-eCe3E0GKZhuz_wpqG0/view?usp=sharing)
*   **Live Demo:** While the application is architected for production, deployment to free-tier cloud services like Render failed due to the platform's 512MB RAM limit, which is insufficient for the large AI models used. A detailed explanation is provided in the "Deployment Strategy" section below.

## Core Features

*   **Multi-Modal Search:**
    *   **Image-based Search:** Upload an image to find visually similar products from a curated local catalog using a Vision Transformer (ViT).
    *   **Text-based Search:** Use natural language prompts (e.g., "blue summer shirt") for discovery.
*   **Advanced AI Integration:**
    *   **AI Image Description (OpenAI GPT-4o):** Get detailed, human-like descriptions of uploaded images to understand context.
    *   **NLP Keyword Extraction (spaCy):** Intelligently extracts key nouns and adjectives from text prompts.
    *   **LLM-Powered Query Refinement (Google Gemini):** Analyzes all inputs to suggest optimized search queries and key product attributes.
*   **Intelligent Product Recommendations:**
    *   Combines visual similarity (ViT), AI-generated descriptions, and keyword matching to score and rank products.
*   **Full User Authentication & Personalization:**
    *   Secure user registration and login system with password hashing (Bcrypt).
    *   Persistent user-specific wishlists and shopping carts saved across sessions in an SQLite database.
    *   A mock checkout process to simulate a complete e-commerce flow.
*   **Interactive User Experience:**
    *   Clean, modern, and responsive UI with a user-toggleable dark mode.
    *   Modal pop-ups for detailed product views and real-time feedback with loading indicators.

## Tech Stack

*   **Backend:** Python (Flask), Gunicorn
*   **Database:** SQLite
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3
*   **Core AI/ML Models:**
    *   **Visual Similarity:** Hugging Face `transformers` with `google/vit-base-patch16-224-in21k`.
    *   **Image Description:** OpenAI API (`gpt-4o`).
    *   **Language Refinement:** Google Generative AI API (`gemini-1.5-flash-latest`).
    *   **NLP Preprocessing:** spaCy (`en_core_web_sm`).
*   **Deployment:** Prepared for Render deployment.

## Deployment Strategy & Hosting Challenge

The application was fully prepared for production deployment on **Render**.
*   **Production Server:** Uses `gunicorn` instead of the Flask development server.
*   **Automated Builds:** A `build.sh` script automates the installation of all dependencies and AI models on the remote server.
*   **Optimized Startup:** The `gunicorn` start command is configured with a long timeout (`-t 120`) to accommodate the time required to load large ML models.

**Hosting Outcome:** The deployment attempt on Render's free tier was unsuccessful due to a hard technical constraint: **memory limitations**. The free tier's **512MB RAM** is insufficient for the project's dependencies, particularly PyTorch and the Transformer models, which require significantly more memory. This caused the instance to crash during the model loading phase. A successful deployment would require a paid plan with higher memory (2GB+), which was outside the scope of this hackathon's free-tier bonus suggestion. This process demonstrates a practical understanding of production deployment challenges for memory-intensive AI applications.

## Data Source: Strategic Curation & Scraping Proof-of-Concept

A key challenge in this project was acquiring a clean and consistent dataset. I addressed the problem statement's requirement for live scraping with a strategic, two-part approach.

**1. Primary Method: Curated Product Catalog**
To ensure a high-quality and stable user experience for the demo, a foundational dataset was curated from the Kaggle **[Fashion Product Images (Small)](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small)** collection. A custom Python script (`prepare_dataset.py`) processes this raw data to create a clean, 2000-item catalog that serves as the application's reliable data backbone. This is not "dummy data" but a structured, production-like dataset.

**2. Proof-of-Concept: Real-Time Scraper**
To demonstrate the ability to meet the live scraping requirement, a sophisticated web scraper was developed using **Python, Playwright, and Playwright-Stealth**. The code (`backend_flask/scraper/`) is included in the repository as a proof-of-concept of this advanced skill. Due to the unreliability of scraping live e-commerce sites for a demo, the final application uses the curated dataset for stability and performance.

## How to Run Locally

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/DipayanDasgupta/Webops_Guild_App.git
    cd Webops_Guild_App
    ```

2.  **Set up Backend Environment (using the provided script):**
    ```bash
    # Make the script executable
    chmod +x setup.sh
    # Run the setup script
    ./setup.sh
    ```

3.  **Set up API Keys:**
    *   Create a file named `.env` inside the `backend_flask/` directory.
    *   Add your keys to this file:
        ```env
        OPENAI_API_KEY="your_openai_api_key_here"
        GOOGLE_API_KEY="your_google_api_key_here"
        FLASK_SECRET_KEY="generate_a_strong_random_secret_key"
        ```

4.  **Prepare Product Data:**
    *   Download the dataset from the Kaggle link above.
    *   Create a `kaggle_dataset_raw` folder in the project root.
    *   Place `styles.csv` inside it and all product images inside `kaggle_dataset_raw/images/`.
    *   Run the preparation script from the project root (ensure your venv is active):
        ```bash
        source backend_flask/venv/bin/activate
        python prepare_dataset.py
        ```

5.  **Run the Application:**
    *   Ensure your virtual environment is activated.
    *   Run the Flask application from the project root:
        ```bash
        python -m flask --app backend_flask.app run
        ```
    *   Open your web browser and navigate to `http://127.0.0.1:5000`.