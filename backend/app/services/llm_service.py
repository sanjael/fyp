import os
from langchain_community.llms import Ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

llm = Ollama(
    base_url=OLLAMA_HOST,
    model="llama3.1:8b"
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
