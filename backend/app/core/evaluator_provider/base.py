import time
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional, Dict
from diskcache import Cache
from tenacity import retry, wait_exponential, stop_after_attempt
from pydantic import BaseModel
import contextvars

current_sample_id = contextvars.ContextVar("current_sample_id", default="Unknown")

def classify_prompt(prompt: str) -> Tuple[str, str, str]:
    p = prompt.lower()
    if "extract one or more statements" in p or "extract statements" in p or "sentences" in p and "statements" in p:
        return "RAGAS", "Faithfulness", "Statement Generation"
    if "determine whether they are supported" in p or "supported by the information" in p or "verdict" in p and "statement" in p:
        return "RAGAS", "Faithfulness", "Statement Verification"
    if "generate a question" in p or "question for the given answer" in p:
        return "RAGAS", "Answer Relevancy", "Question Generation"
    if "useful in answering the question" in p or "was the context useful" in p or "context is useful" in p:
        return "RAGAS", "Context Precision", "Context Judgement"
    
    # DeepEval fallbacks
    if "actual output" in p and "retrieval context" in p and "faithfulness" in p:
        return "DeepEval", "Faithfulness", "Faithfulness Judge"
    if "relevancy" in p and "actual output" in p:
        return "DeepEval", "Answer Relevancy", "Answer Judge"
    if "contextual precision" in p or "contextual" in p and "node" in p:
        return "DeepEval", "Context Precision", "Context Judge"
        
    return "Unknown", "Unknown", "Unknown"

cache = Cache(".eval_cache")

class EvaluationMetrics(BaseModel):
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    unique_requests: int = 0
    http_429_count: int = 0
    retry_count: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    cache_lookup_time_ms: float = 0.0
    rate_limit_wait_time_ms: float = 0.0

import asyncio
import threading
from collections import deque

class RateLimiter:
    def __init__(self, rpm_limit: int = 30, tpm_limit: int = 6000):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.requests_window = deque()
        self.tokens_window = deque()
        self.lock = threading.Lock()
        
    def _get_wait_time(self, estimated_tokens: int) -> float:
        now = time.time()
        
        while self.requests_window and now - self.requests_window[0] > 60:
            self.requests_window.popleft()
        while self.tokens_window and now - self.tokens_window[0][0] > 60:
            self.tokens_window.popleft()
            
        current_rpm = len(self.requests_window)
        current_tpm = sum(t for _, t in self.tokens_window)
        
        wait_time = 0.0
        
        if current_rpm >= self.rpm_limit:
            wait_time = max(wait_time, 60.0 - (now - self.requests_window[0]))
            
        if current_tpm + estimated_tokens > self.tpm_limit:
            needed_tokens = (current_tpm + estimated_tokens) - self.tpm_limit
            freed = 0
            for ts, t in self.tokens_window:
                freed += t
                if freed >= needed_tokens:
                    wait_time = max(wait_time, 60.0 - (now - ts))
                    break
                    
        return wait_time

    def _record_usage(self, estimated_tokens: int):
        now = time.time()
        self.requests_window.append(now)
        self.tokens_window.append((now, estimated_tokens))

    def wait(self, estimated_tokens: int) -> float:
        total_wait = 0.0
        while True:
            with self.lock:
                wait_time = self._get_wait_time(estimated_tokens)
                if wait_time <= 0:
                    self._record_usage(estimated_tokens)
                    return total_wait
            time.sleep(wait_time)
            total_wait += wait_time
            
    async def await_wait(self, estimated_tokens: int) -> float:
        total_wait = 0.0
        while True:
            with self.lock:
                wait_time = self._get_wait_time(estimated_tokens)
                if wait_time <= 0:
                    self._record_usage(estimated_tokens)
                    return total_wait
            await asyncio.sleep(wait_time)
            total_wait += wait_time
            
    def update_actual_tokens(self, estimated_tokens: int, actual_tokens: int):
        with self.lock:
            for i in range(len(self.tokens_window)-1, -1, -1):
                if self.tokens_window[i][1] == estimated_tokens:
                    self.tokens_window[i] = (self.tokens_window[i][0], actual_tokens)
                    break

class EvaluatorProvider(ABC):
    def __init__(
        self,
        model_name: str,
        rpm_limit: int = 30,
        tpm_limit: int = 5000,
        max_concurrency: int = 1,
        max_retries: int = 3,
        max_wait: float = 30.0,
        timeout: float = 120.0,
    ):
        self.model_name = model_name
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self.max_wait = max_wait
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rpm_limit, tpm_limit)
        # Shared metrics state across calls (simple approach)
        self.total_metrics = EvaluationMetrics()

    def get_ragas_run_config(self) -> Any:
        """Returns a provider-aware RAGAS RunConfig object."""
        try:
            from ragas.run_config import RunConfig
            return RunConfig(
                max_workers=self.max_concurrency,
                max_retries=self.max_retries,
                max_wait=int(self.max_wait),
                timeout=int(self.timeout),
            )
        except Exception:
            return None

    @abstractmethod
    def get_langchain_model(self) -> Any:
        """Returns the native Langchain model (for RAGAS)."""
        pass
        
    @abstractmethod
    def get_deepeval_model(self) -> Any:
        """Returns the DeepEval model wrapper (for DeepEval)."""
        pass
        
    @abstractmethod
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the cost in USD for the given tokens."""
        pass
        
    def get_and_reset_metrics(self) -> EvaluationMetrics:
        metrics = self.total_metrics.model_copy()
        self.total_metrics = EvaluationMetrics()
        return metrics


    def record_trace(self, prompt: str, latency: float, p_tokens: int, c_tokens: int, 
                     status: int, cache_status: str, retries: int):
        framework, metric, prompt_type = classify_prompt(prompt)
        # Using a global array to hold traces for profiling
        from app.services.dataset_construction.pipeline import REQUEST_TRACES
        seq = len(REQUEST_TRACES) + 1
        trace = {
            "Request Sequence": seq,
            "Sample ID": current_sample_id.get(),
            "Framework": framework,
            "Metric": metric,
            "Prompt Type": prompt_type,
            "Latency": latency / 1000.0,
            "Prompt Tokens": p_tokens,
            "Completion Tokens": c_tokens,
            "Total Tokens": p_tokens + c_tokens,
            "HTTP Status": status,
            "Cache Status": cache_status,
            "Retries": retries
        }
        REQUEST_TRACES.append(trace)

    def _get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(f"{self.model_name}_{prompt}".encode()).hexdigest()

    def execute_with_features(self, prompt: str, generate_func) -> str:
        """
        Executes a prompt with rate limiting, caching, retries, and metric logging.
        """
        cache_start = time.time()
        cache_key = self._get_cache_key(prompt)
        in_cache = cache_key in cache
        cache_time = (time.time() - cache_start) * 1000
        self.total_metrics.cache_lookup_time_ms += cache_time
        
        if in_cache:
            self.total_metrics.cache_hit_count += 1
            self.record_trace(prompt, cache_time, 0, 0, 200, "HIT", 0)
            return cache.get(cache_key)
        self.total_metrics.cache_miss_count += 1
        self.total_metrics.unique_requests += 1
        
        est_tokens = len(prompt) // 4 + 400
            
        @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
        def _call_with_retry():
            self.total_metrics.total_requests += 1
            wait_time = self.rate_limiter.wait(est_tokens)
            self.total_metrics.rate_limit_wait_time_ms += (wait_time * 1000.0)
            
            start_time = time.time()
            local_retries = self.total_metrics.retry_count
            http_status = 200
            try:
                response = generate_func(prompt)
            except Exception as e:
                self.total_metrics.retry_count += 1
                if "429" in str(e):
                    self.total_metrics.http_429_count += 1
                    http_status = 429
                else:
                    http_status = 500
                self.record_trace(prompt, (time.time() - start_time) * 1000, 0, 0, http_status, "MISS", 1)
                raise e
                
            latency = (time.time() - start_time) * 1000
            
            p_tokens = len(prompt) // 4
            c_tokens = len(response) // 4
            cost = self.calculate_cost(p_tokens, c_tokens)
            
            self.total_metrics.latency_ms += latency
            self.total_metrics.prompt_tokens += p_tokens
            self.total_metrics.completion_tokens += c_tokens
            self.total_metrics.total_cost += cost
            
            self.rate_limiter.update_actual_tokens(est_tokens, p_tokens + c_tokens)
            
            retries_for_this = self.total_metrics.retry_count - local_retries
            self.record_trace(prompt, latency, p_tokens, c_tokens, http_status, "STORE", retries_for_this)
            
            return response
            
        result = _call_with_retry()
        cache.set(cache_key, result, expire=86400) # cache for 1 day
        return result
        
    async def a_execute_with_features(self, prompt: str, agenerate_func) -> str:
        """Async version of execute_with_features."""
        cache_start = time.time()
        cache_key = self._get_cache_key(prompt)
        in_cache = cache_key in cache
        cache_time = (time.time() - cache_start) * 1000
        self.total_metrics.cache_lookup_time_ms += cache_time
        
        if in_cache:
            self.total_metrics.cache_hit_count += 1
            self.record_trace(prompt, cache_time, 0, 0, 200, "HIT", 0)
            return cache.get(cache_key)
        self.total_metrics.cache_miss_count += 1
        self.total_metrics.unique_requests += 1
        
        est_tokens = len(prompt) // 4 + 400
            
        @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
        async def _acall_with_retry():
            self.total_metrics.total_requests += 1
            wait_time = await self.rate_limiter.await_wait(est_tokens)
            self.total_metrics.rate_limit_wait_time_ms += (wait_time * 1000.0)
            
            start_time = time.time()
            local_retries = self.total_metrics.retry_count
            http_status = 200
            try:
                response = await agenerate_func(prompt)
            except Exception as e:
                self.total_metrics.retry_count += 1
                if "429" in str(e):
                    self.total_metrics.http_429_count += 1
                    http_status = 429
                else:
                    http_status = 500
                self.record_trace(prompt, (time.time() - start_time) * 1000, 0, 0, http_status, "MISS", 1)
                raise e
                
            latency = (time.time() - start_time) * 1000
            
            p_tokens = len(prompt) // 4
            c_tokens = len(response) // 4
            cost = self.calculate_cost(p_tokens, c_tokens)
            
            self.total_metrics.latency_ms += latency
            self.total_metrics.prompt_tokens += p_tokens
            self.total_metrics.completion_tokens += c_tokens
            self.total_metrics.total_cost += cost
            
            self.rate_limiter.update_actual_tokens(est_tokens, p_tokens + c_tokens)
            
            retries_for_this = self.total_metrics.retry_count - local_retries
            self.record_trace(prompt, latency, p_tokens, c_tokens, http_status, "STORE", retries_for_this)
            
            return response
            
        result = await _acall_with_retry()
        cache.set(cache_key, result, expire=86400)
        return result

# ==========================================
# Wrappers to Intercept API Calls
# ==========================================

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
try:
    from deepeval.models.base_model import DeepEvalBaseLLM
    DEEPEVAL_AVAILABLE = True
except Exception:
    DEEPEVAL_AVAILABLE = False
    class DeepEvalBaseLLM:
        pass

from app.core.json_repair import clean_json_text

class ProviderLangchainWrapper(BaseChatModel):
    provider: Any
    underlying: Any
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        prompt = messages[0].content if messages else ""
        def func(p):
            res = self.underlying.invoke(messages, stop=stop, **kwargs)
            return res.content
        content = self.provider.execute_with_features(prompt, func)
        cleaned_content = clean_json_text(content) if content and "```" in content else content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=cleaned_content))])
        
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        prompt = messages[0].content if messages else ""
        async def func(p):
            res = await self.underlying.ainvoke(messages, stop=stop, **kwargs)
            return res.content
        content = await self.provider.a_execute_with_features(prompt, func)
        cleaned_content = clean_json_text(content) if content and "```" in content else content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=cleaned_content))])
        
    @property
    def _llm_type(self) -> str:
        return "provider_wrapper"

class ProviderDeepEvalWrapper(DeepEvalBaseLLM):
    def __init__(self, provider: EvaluatorProvider):
        self.provider = provider
        
    def load_model(self):
        return self.provider.get_langchain_model()
        
    def generate(self, prompt: str) -> str:
        def func(p):
            return self.provider.get_langchain_model().invoke(p).content
        content = self.provider.execute_with_features(prompt, func)
        return clean_json_text(content) if content and ("{" in content or "```" in content) else content
        
    async def a_generate(self, prompt: str) -> str:
        async def func(p):
            res = await self.provider.get_langchain_model().ainvoke(p)
            return res.content
        content = await self.provider.a_execute_with_features(prompt, func)
        return clean_json_text(content) if content and ("{" in content or "```" in content) else content
        
    def get_model_name(self):
        return self.provider.model_name

