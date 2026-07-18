import os
from langchain_community.llms import Ollama
from app.core.config import global_config

llm = Ollama(
    base_url=global_config.OLLAMA_HOST,
    model=global_config.GENERATOR_LLM_MODEL
)

def generate_answer(query: str, context: str) -> str:
    prompt = f"""You are RAGGuard-TR, a highly intelligent and reliable AI assistant.
Answer the user's question based strictly on the provided context. If the context does not contain the answer, say "I cannot answer this based on the available context."

Context:
{context}

Question:
{query}

Answer:"""
    
    response = llm.invoke(prompt)
    return response
