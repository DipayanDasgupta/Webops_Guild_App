# backend_flask/ai_core/language_models.py
import os
import json
import google.generativeai as genai
import spacy
from flask import current_app

# --- Global variable for spaCy model ---
nlp_spacy = None

def load_spacy_model():
    """Loads the spaCy NLP model into memory."""
    global nlp_spacy
    if nlp_spacy is None:
        try:
            current_app.logger.info("Loading spaCy model (en_core_web_sm)...")
            nlp_spacy = spacy.load("en_core_web_sm")
            current_app.logger.info("spaCy model loaded successfully.")
        except OSError:
            current_app.logger.error("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
        except Exception as e:
            current_app.logger.error(f"Error loading spaCy model: {e}")

def extract_keywords_spacy(text):
    """Extracts relevant keywords from text using spaCy."""
    if not nlp_spacy or not text:
        return []
    
    doc = nlp_spacy(text.lower())
    # Extract nouns, proper nouns, and adjectives, avoiding stop words
    keywords = {token.lemma_ for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop}
    return list(keywords)

def get_refined_search_gemini(image_description, user_prompt):
    """Uses Google's Gemini to refine a search query based on image and text inputs."""
    # Check if the Gemini API key was configured on app startup
    if not os.getenv("GOOGLE_API_KEY"):
        current_app.logger.warning("GOOGLE_API_KEY not found. Skipping Gemini API call.")
        return {"error": "Gemini API key not configured."}

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        current_app.logger.info(f"Using Gemini model for search refinement.")
        
        prompt_template = f"""
        You are an intelligent e-commerce search assistant.
        Based on the following information, generate a structured JSON response to help find a product.
        
        - Image Description (from Vision AI): "{image_description}"
        - User's Text Query: "{user_prompt}"

        Your task is to provide a JSON object with ONLY the following keys:
        1. "refined_search_query": A single, optimized search query string (max 10 words) for an e-commerce site.
        2. "key_attributes": A list of 3-5 specific, searchable attributes (e.g., "red floral dress", "leather ankle boots").

        Example JSON output:
        {{
          "refined_search_query": "long sleeve vintage floral midi dress",
          "key_attributes": ["vintage floral print", "midi dress", "long sleeve", "bohemian style"]
        }}

        If the input is vague, make the attributes broader. Output ONLY the JSON object.
        """
        
        response = model.generate_content(prompt_template)
        
        # Clean up the response to ensure it's valid JSON
        cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        
        gemini_output = json.loads(cleaned_text)
        current_app.logger.info(f"Gemini Refinement Output (parsed): {gemini_output}")
        return gemini_output
        
    except json.JSONDecodeError:
        current_app.logger.warning(f"Gemini response was not valid JSON. Raw text: {response.text}")
        return {"raw_text": response.text, "error": "Gemini response was not valid JSON."}
    except Exception as e:
        current_app.logger.error(f"Error with Gemini API call: {e}")
        return {"error": f"Error interacting with Gemini: {str(e)}"}