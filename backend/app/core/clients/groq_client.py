import asyncio
import logging
import random
import time
import httpx
from typing import Optional
from ..config import global_config

logger = logging.getLogger("groq_client")

# Provider-aware semaphore: concurrency limit default 1 for Groq to prevent 429/409 rate limit errors
_GROQ_SEMAPHORE = asyncio.Semaphore(global_config.EVALUATOR_CONCURRENCY)

class GroqHTTPClient:
    """
    A robust HTTP client for interacting with the Groq API directly.
    Includes capped exponential backoff with jitter and concurrency control (default 1 worker)
    to serialize evaluation requests and prevent HTTP 409/429 rate limit errors.
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
        self.max_retries = global_config.EVALUATOR_MAX_RETRIES
        self.max_wait = global_config.EVALUATOR_MAX_WAIT

    def generate(self, model: str, prompt: str, system: Optional[str] = None, max_retries: Optional[int] = None, **kwargs) -> str:
        num_retries = max_retries if max_retries is not None else self.max_retries
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if prompt:
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        payload.update(kwargs)

        backoff = 2.0
        with httpx.Client(timeout=global_config.EVALUATOR_TIMEOUT) as client:
            for attempt in range(num_retries):
                try:
                    response = client.post(self.generate_url, headers=self.headers, json=payload)
                    if response.status_code in (409, 429, 500, 502, 503, 504):
                        jitter = random.uniform(0.1, 0.5)
                        header_wait = response.headers.get("retry-after")
                        if header_wait:
                            try:
                                wait_time = min(self.max_wait, float(header_wait) + jitter)
                            except ValueError:
                                wait_time = min(self.max_wait, backoff + jitter)
                        else:
                            wait_time = min(self.max_wait, backoff + jitter)

                        logger.warning(
                            f"Groq API returned HTTP {response.status_code} [model={model}, attempt={attempt+1}/{num_retries}]. "
                            f"Retrying in {wait_time:.2f}s (jitter={jitter:.2f}s, max_wait={self.max_wait}s)..."
                        )
                        time.sleep(wait_time)
                        backoff = min(self.max_wait, backoff * 2.0)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    return ""
                except (httpx.HTTPStatusError, httpx.RequestError) as err:
                    if attempt == num_retries - 1:
                        logger.error(f"Groq API request failed after {num_retries} attempts [model={model}]: {err}")
                        raise err
                    jitter = random.uniform(0.1, 0.5)
                    wait_time = min(self.max_wait, backoff + jitter)
                    logger.warning(f"Groq request exception '{err}' [model={model}, attempt={attempt+1}/{num_retries}]. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    backoff = min(self.max_wait, backoff * 2.0)
        return ""

    async def agenerate(self, model: str, prompt: str, system: Optional[str] = None, max_retries: Optional[int] = None, **kwargs) -> str:
        num_retries = max_retries if max_retries is not None else self.max_retries
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if prompt:
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        payload.update(kwargs)

        backoff = 2.0
        async with _GROQ_SEMAPHORE:
            # Serializing / pacing async Groq evaluation requests
            await asyncio.sleep(0.2)
            async with httpx.AsyncClient(timeout=global_config.EVALUATOR_TIMEOUT) as client:
                for attempt in range(num_retries):
                    try:
                        response = await client.post(self.generate_url, headers=self.headers, json=payload)
                        if response.status_code in (409, 429, 500, 502, 503, 504):
                            jitter = random.uniform(0.1, 0.5)
                            header_wait = response.headers.get("retry-after")
                            if header_wait:
                                try:
                                    wait_time = min(self.max_wait, float(header_wait) + jitter)
                                except ValueError:
                                    wait_time = min(self.max_wait, backoff + jitter)
                            else:
                                wait_time = min(self.max_wait, backoff + jitter)

                            logger.warning(
                                f"Groq API async returned HTTP {response.status_code} [model={model}, attempt={attempt+1}/{num_retries}]. "
                                f"Retrying in {wait_time:.2f}s (concurrency limit={global_config.EVALUATOR_CONCURRENCY})..."
                            )
                            await asyncio.sleep(wait_time)
                            backoff = min(self.max_wait, backoff * 2.0)
                            continue
                        
                        response.raise_for_status()
                        data = response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        return ""
                    except (httpx.HTTPStatusError, httpx.RequestError) as err:
                        if attempt == num_retries - 1:
                            logger.error(f"Groq API async request failed after {num_retries} attempts [model={model}]: {err}")
                            raise err
                        jitter = random.uniform(0.1, 0.5)
                        wait_time = min(self.max_wait, backoff + jitter)
                        logger.warning(f"Groq async request exception '{err}' [model={model}, attempt={attempt+1}/{num_retries}]. Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        backoff = min(self.max_wait, backoff * 2.0)
        return ""


