from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from .ollama_client import OllamaHTTPClient
from .groq_client import GroqHTTPClient

class OllamaChatAdapter(BaseChatModel):
    """
    A lightweight adapter that bridges the official OllamaHTTPClient to LangChain's BaseChatModel interface.
    This satisfies RAGAS (which requires a BaseChatModel) without pulling in langchain-ollama.
    """
    model_name: str
    base_url: str = "http://localhost:11434"
    client: Optional[OllamaHTTPClient] = None
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name=model_name, base_url=base_url, **kwargs)
        self.client = OllamaHTTPClient(base_url=self.base_url)

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        # Simplified concatenation for evaluator prompts
        # RAGAS typically passes a single HumanMessage with the entire prompt
        return "\n".join([m.content for m in messages if hasattr(m, 'content')])

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._format_messages(messages)
        response_text = self.client.generate(model=self.model_name, prompt=prompt, **kwargs)
        
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._format_messages(messages)
        response_text = await self.client.agenerate(model=self.model_name, prompt=prompt, **kwargs)
        
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "custom_ollama_adapter"

class GroqChatAdapter(BaseChatModel):
    """
    A lightweight adapter that bridges the official GroqHTTPClient to LangChain's BaseChatModel interface.
    This satisfies RAGAS (which requires a BaseChatModel).
    """
    model_name: str
    api_key: str
    base_url: str = "https://api.groq.com/openai/v1"
    client: Optional[GroqHTTPClient] = None
    
    def __init__(self, model_name: str, api_key: str, base_url: str = "https://api.groq.com/openai/v1", **kwargs):
        super().__init__(model_name=model_name, api_key=api_key, base_url=base_url, **kwargs)
        self.client = GroqHTTPClient(api_key=self.api_key, base_url=self.base_url)

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        converted = []
        for m in messages:
            if m.type == "system":
                converted.append({"role": "system", "content": m.content})
            elif m.type in ["human", "user"]:
                converted.append({"role": "user", "content": m.content})
            elif m.type in ["ai", "assistant"]:
                converted.append({"role": "assistant", "content": m.content})
            else:
                converted.append({"role": "user", "content": m.content})
        return converted

    def _normalize_json_response(self, response_text: str) -> str:
        """
        Normalizes known binary verdict fields from integer (0/1) to string ("no"/"yes")
        to satisfy RAGAS schema expectations.
        """
        import json
        try:
            data = json.loads(response_text)
            modified = False
            
            def normalize_dict(d: dict):
                nonlocal modified
                for k, v in d.items():
                    if isinstance(v, dict):
                        normalize_dict(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                normalize_dict(item)
                    elif k.lower() in ["verdict", "faithful", "answer_is_correct", "is_relevant"]:
                        if v == 1 or v == "1":
                            d[k] = "yes"
                            modified = True
                        elif v == 0 or v == "0":
                            d[k] = "no"
                            modified = True
                            
            if isinstance(data, dict):
                normalize_dict(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        normalize_dict(item)
                        
            if modified:
                return json.dumps(data)
                
        except json.JSONDecodeError:
            pass
            
        return response_text

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import json
        converted_messages = self._convert_messages(messages)
        
        is_json = any("json" in m.get("content", "").lower() for m in converted_messages)
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}
            
        kwargs["messages"] = converted_messages
        response_text = self.client.generate(model=self.model_name, prompt="", **kwargs)
        
        with open("groq_debug.log", "a", encoding="utf-8") as f:
            f.write(f"=== SYNC GENERATE ===\nPROMPT:\n{converted_messages}\n\nRAW RESPONSE:\n{response_text}\n{'='*50}\n")
        
        if is_json:
            try:
                json.loads(response_text)
                response_text = self._normalize_json_response(response_text)
            except json.JSONDecodeError as e:
                raise Exception(
                    f"Invalid JSON response from Groq.\n"
                    f"Model: {self.model_name}\n"
                    f"Prompt type: JSON expected\n"
                    f"Raw response: {response_text}\n"
                    f"Error: {e}"
                )
        
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import json
        converted_messages = self._convert_messages(messages)
        
        is_json = any("json" in m.get("content", "").lower() for m in converted_messages)
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}
            
        kwargs["messages"] = converted_messages
        response_text = await self.client.agenerate(model=self.model_name, prompt="", **kwargs)
        
        with open("groq_debug.log", "a", encoding="utf-8") as f:
            f.write(f"=== ASYNC GENERATE ===\nPROMPT:\n{converted_messages}\n\nRAW RESPONSE:\n{response_text}\n{'='*50}\n")
        
        if is_json:
            try:
                json.loads(response_text)
                response_text = self._normalize_json_response(response_text)
            except json.JSONDecodeError as e:
                raise Exception(
                    f"Invalid JSON response from Groq.\n"
                    f"Model: {self.model_name}\n"
                    f"Prompt type: JSON expected\n"
                    f"Raw response: {response_text}\n"
                    f"Error: {e}"
                )
        
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "custom_groq_adapter"
