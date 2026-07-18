import httpx
from typing import Optional

class GroqHTTPClient:
    """
    A lightweight HTTP client for interacting with the Groq API directly,
    mimicking the OpenAI completion endpoint.
    """
    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1"):
        if not api_key:
            raise ValueError("GROQ_API_KEY must be provided")
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def generate(self, model: str, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        payload.update(kwargs)

        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.generate_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""

    async def agenerate(self, model: str, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.generate_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
