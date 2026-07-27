from langchain_community.llms import Ollama
from app.core.config import global_config

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = Ollama(
            base_url=global_config.OLLAMA_HOST,
            model=global_config.GENERATOR_LLM_MODEL
        )
    return _llm

def generate_answer(query: str, context: str) -> str:
    prompt = f"""You are RAGGuard-TR, a highly intelligent and reliable AI assistant.
Answer the user's question based strictly on the provided context. If the context does not contain the answer, say "I cannot answer this based on the available context."

Context:
{context}

Question:
{query}

Answer:"""
    return _get_llm().invoke(prompt)
