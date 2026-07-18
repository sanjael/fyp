import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found.")
    exit(1)
    
os.environ["GEMINI_API_KEY"] = api_key.strip()

print(f"Testing with raw genai SDK. Key starts with: {api_key[:5]}")

try:
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents='What is 2+2?'
    )
    print("Success! Response:", response.text)
except Exception as e:
    print("FAILED with Exception:", str(e))
