from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from .ollama_client import OllamaHTTPClient
from .groq_client import GroqHTTPClient

from app.core.json_repair import clean_json_text

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
        return "\n".join([m.content for m in messages if hasattr(m, 'content')])

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._format_messages(messages)
        is_json = "json" in prompt.lower()
        if is_json:
            kwargs["format"] = "json"

        response_text = self.client.generate(model=self.model_name, prompt=prompt, **kwargs)
        if is_json:
            response_text = clean_json_text(response_text)
            response_text = normalize_ragas_json(response_text)
        
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
        is_json = "json" in prompt.lower()
        if is_json:
            kwargs["format"] = "json"

        response_text = await self.client.agenerate(model=self.model_name, prompt=prompt, **kwargs)
        if is_json:
            response_text = clean_json_text(response_text)
            response_text = normalize_ragas_json(response_text)
        
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "custom_ollama_adapter"


def normalize_ragas_json(response_text: str) -> str:
    """
    Normalizes JSON responses from evaluator LLMs (Groq / Ollama) to satisfy RAGAS 0.1.x Pydantic schema validation:
    1. Preserves statement generation output: {'statements': ['A', 'B']}
    2. Renames statement_1, statement_2, etc. keys to 'statement'
    3. Normalizes verdict fields to integers (1, 0, -1)
    4. Preserves noncommittal and custom object schemas
    5. Normalizes root dicts/lists into lists for verification RootModels
    6. Logs ORIGINAL JSON and NORMALIZED JSON to groq_debug.log if modified
    """
    import json
    import re

    try:
        data = json.loads(response_text)
        original_data = json.dumps(data)

        # Helper 1: Rename statement_X -> statement and normalize verdicts recursively
        def process_item(item):
            if isinstance(item, dict):
                new_dict = {}
                for k, v in item.items():
                    # Rename statement_1, statement_2, etc. to 'statement'
                    new_key = "statement" if re.match(r"^statement_\d+$", k, re.IGNORECASE) else k

                    if isinstance(v, (dict, list)):
                        processed_v = process_item(v)
                    elif new_key.lower() in ("verdict", "faithful", "answer_is_correct", "is_relevant"):
                        s_val = str(v).strip().lower()
                        if s_val in ("1", "yes", "true"):
                            processed_v = 1
                        elif s_val in ("0", "no", "false"):
                            processed_v = 0
                        elif s_val in ("-1", "-1.0", "null", "nil", "none"):
                            processed_v = -1
                        elif isinstance(v, (int, float)):
                            processed_v = int(v)
                        else:
                            processed_v = v
                    else:
                        processed_v = v

                    new_dict[new_key] = processed_v
                return new_dict
            elif isinstance(item, list):
                return [process_item(elem) for elem in item]
            return item

        processed = process_item(data)

        # Helper 2: Handle root JSON structure
        if isinstance(processed, dict):
            # Preserve statement generation output: {'statements': ['A', 'B']}
            if "statements" in processed and isinstance(processed["statements"], list):
                if not processed["statements"] or isinstance(processed["statements"][0], str):
                    data_to_return = processed
                else:
                    # If 'statements' contains dict items, unwrap to list
                    data_to_return = processed["statements"]
            # Preserve question / noncommittal output: {'question': '...', 'noncommittal': 1}
            elif "question" in processed and "noncommittal" in processed:
                data_to_return = processed
            # Unwrap dict containing single list of dicts: {'verifications': [{...}], ...}
            elif len(processed) == 1 and isinstance(list(processed.values())[0], list):
                val_list = list(processed.values())[0]
                if val_list and isinstance(val_list[0], dict):
                    data_to_return = val_list
                else:
                    data_to_return = processed
            # Wrap single verification object into list: {'statement': '...', 'reason': '...', 'verdict': 0}
            elif ("reason" in processed and "verdict" in processed) or ("statement" in processed and "verdict" in processed):
                data_to_return = [processed]
            else:
                data_to_return = processed
        else:
            data_to_return = processed

        normalized_str = json.dumps(data_to_return)

        # Log original and normalized JSON if modified
        if normalized_str != response_text and original_data != normalized_str:
            try:
                with open("groq_debug.log", "a", encoding="utf-8") as f:
                    f.write(
                        f"\n[NORMALIZER MODIFIED OUTPUT]\n"
                        f"ORIGINAL JSON:\n{response_text}\n"
                        f"NORMALIZED JSON:\n{normalized_str}\n"
                        f"{'='*50}\n"
                    )
            except Exception:
                pass

        return normalized_str
    except json.JSONDecodeError:
        pass

    return response_text


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
    def _normalize_json_response(self, response_text: str) -> str:
        return normalize_ragas_json(response_text)






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
                response_text = normalize_ragas_json(response_text)
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
                response_text = normalize_ragas_json(response_text)
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
