# core/ai_services.py

import google.generativeai as genai
from .config import settings # We already import our settings

# Configure the library once when the application starts
# This part is fine.
if settings.GEMINI_API_KEY != "API_KEY_NOT_FOUND":
    genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_narrative(prompt: str) -> str:
    # --- THIS IS THE CORRECTED LOGIC ---
    # Instead of checking 'genai.config', we check our own 'settings' object.
    # This is more reliable.
    if settings.GEMINI_API_KEY == "API_KEY_NOT_FOUND":
        return "AI narrative generation skipped. GEMINI_API_KEY is not configured in the .env file."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Add a helpful message for invalid API key errors
        if "API_KEY_INVALID" in str(e) or "PermissionDenied" in str(e):
            return "AI narrative could not be generated. The provided Gemini API key is invalid or expired."
        # Generic error for other issues
        return f"AI narrative could not be generated. Error: {e}"