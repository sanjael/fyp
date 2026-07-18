import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from urllib.request import Request, urlopen

def check_service(url, timeout=5):
    try:
        response = urlopen(url, timeout=timeout)
        return response.getcode() == 200
    except Exception:
        return False

def pull_ollama_model(base_url, model_name):
    print(f"Pulling {model_name} from {base_url} (this may take a while)...")
    url = f"{base_url}/api/pull"
    data = json.dumps({"name": model_name}).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urlopen(req)
        return response.getcode() == 200
    except Exception as e:
        print(f"Failed to pull {model_name}: {e}")
        return False

def check_ollama_models(base_url, required_models):
    url = f"{base_url}/api/tags"
    missing = []
    installed = []
    try:
        response = urlopen(url, timeout=5)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            for rm in required_models:
                found = False
                for m in models:
                    if rm in m:
                        found = True
                        break
                if found:
                    installed.append(rm)
                else:
                    missing.append(rm)
    except Exception as e:
        print(f"Failed to fetch ollama models: {e}")
        return installed, required_models

    return installed, missing

def main():
    report = {
        "status": "healthy",
        "services": {},
        "ollama_models": {
            "installed": [],
            "missing": [],
            "pull_failed": []
        }
    }
    
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = os.getenv("CHROMA_PORT", "8000")
    api_url = os.getenv("API_URL", "http://localhost:8080/health")
    
    generator_model = os.getenv("GENERATOR_LLM_MODEL", "qwen2.5:latest")
    evaluator_model = os.getenv("EVALUATOR_LLM_MODEL", "qwen2.5:latest")
    embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    required_models = list(set([generator_model, evaluator_model, embedding_model]))
    
    print("Checking ChromaDB...")
    chroma_url = f"http://{chroma_host}:{chroma_port}/api/v1/heartbeat"
    if check_service(chroma_url):
        report["services"]["chromadb"] = "online"
    else:
        report["services"]["chromadb"] = "offline"
        report["status"] = "unhealthy"

    print("Checking Ollama...")
    if check_service(f"{ollama_host}/api/tags"):
        report["services"]["ollama"] = "online"
        
        installed, missing = check_ollama_models(ollama_host, required_models)
        report["ollama_models"]["installed"] = installed
        report["ollama_models"]["missing"] = missing
        
        for m in missing:
            success = pull_ollama_model(ollama_host, m)
            if success:
                report["ollama_models"]["installed"].append(m)
                if m in report["ollama_models"]["missing"]:
                    report["ollama_models"]["missing"].remove(m)
            else:
                report["ollama_models"]["pull_failed"].append(m)
                report["status"] = "unhealthy"
    else:
        report["services"]["ollama"] = "offline"
        report["status"] = "unhealthy"

    print("Checking FastAPI...")
    if check_service(api_url):
        report["services"]["fastapi"] = "online"
    else:
        report["services"]["fastapi"] = "offline (or endpoint /health missing)"

    with open("health_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(f"\nHealth Check complete. Status: {report['status']}")
    print(f"Report saved to health_report.json")
    
    if report["status"] != "healthy":
        sys.exit(1)

if __name__ == "__main__":
    main()
