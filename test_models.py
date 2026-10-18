from config import GEMINI_API_KEY
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

print("--- DOSTĘPNE MODELE ---")
for model in client.models.list():
    if "flash" in model.name:
        print(model.name)