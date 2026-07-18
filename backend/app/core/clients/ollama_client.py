import httpx
from typing import Optional

class OllamaHTTPClient:
    """
    A lightweight HTTP client for interacting with the Ollama API directly,
    bypassing the need for heavy LangChain wrappers like langchain-ollama.
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"

    def generate(self, model: str, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
            
        # Merge in any additional model kwargs like temperature, etc.
        if kwargs:
            payload["options"] = kwargs

        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.generate_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")

    async def agenerate(self, model: str, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
            
        if kwargs:
            payload["options"] = kwargs

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.generate_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
