import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load just the API key
load_dotenv(dotenv_path=".env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # try loading from ../.env if running from backend
    load_dotenv(dotenv_path="../.env")
    api_key = os.getenv("GEMINI_API_KEY")

print(f"Using API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("❌ No API Key found! Check .env")
    exit(1)

genai.configure(api_key=api_key)

print("\n--- Available Models (via google-generativeai) ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"❌ Error listing models: {e}")
