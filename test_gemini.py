import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("FAIL: GOOGLE_API_KEY is not set.")
        return
        
    try:
        print("Initializing Gemini (gemini-1.5-flash)...")
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        
        print("Sending test prompt: 'What is 2+2?'")
        response = llm.invoke("What is 2+2?")
        
        if response and response.content:
            print(f"Response received: {response.content.strip()}")
            if "4" in response.content or "four" in response.content.lower():
                print("PASS")
            else:
                print("FAIL: Unexpected response.")
        else:
            print("FAIL: Empty response.")
    except Exception as e:
        print(f"FAIL: Exception occurred: {e}")

if __name__ == "__main__":
    test_gemini()
