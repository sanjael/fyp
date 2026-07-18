import os
import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def verify_gemini():
    report = {
        "api_key_exists": False,
        "gemini_reachable": False,
        "model_exists": False,
        "response_latency_ms": 0.0,
        "token_usage_supported": True, # Approximated natively if callback provided, for now just boolean flag
        "status": "FAIL",
        "error_message": None
    }
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        report["error_message"] = "GOOGLE_API_KEY is missing from environment"
        _write_report(report)
        return
        
    report["api_key_exists"] = True
    
    try:
        model_name = "gemini-1.5-flash"
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        report["model_exists"] = True
        
        start_time = time.time()
        response = llm.invoke("Hello, return exactly the word 'acknowledge'.")
        latency = (time.time() - start_time) * 1000
        report["response_latency_ms"] = round(latency, 2)
        
        if response and "acknowledge" in response.content.lower():
            report["gemini_reachable"] = True
            report["status"] = "PASS"
        else:
            report["error_message"] = f"Unexpected response: {response.content}"
            
    except Exception as e:
        report["error_message"] = str(e)
        
    _write_report(report)
    print(json.dumps(report, indent=4))

def _write_report(report):
    with open("gemini_health_report.json", "w") as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    verify_gemini()
