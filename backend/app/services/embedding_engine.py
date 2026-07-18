import os
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import global_config

# Initialize Ollama Embeddings
embeddings = OllamaEmbeddings(
    base_url=global_config.OLLAMA_HOST,
    model=global_config.EMBEDDING_MODEL
)

# Initialize ChromaDB client
try:
    chroma_client = chromadb.HttpClient(host=global_config.CHROMA_HOST, port=global_config.CHROMA_PORT)
    chroma_client.heartbeat()
except Exception as e:
    print(f"Failed to connect to ChromaDB via HTTP: {e}. Falling back to PersistentClient...")
    chroma_client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "..", "..", "chroma"))

def get_vector_store(collection_name: str = "ragguard_docs"):
    if not chroma_client:
        raise Exception("ChromaDB client is not initialized")
    
    return Chroma(
        client=chroma_client,
        collection_name=collection_name,
        embedding_function=embeddings
    )

def add_documents_to_chroma(chunks, collection_name: str = "ragguard_docs"):
    vector_store = get_vector_store(collection_name)
    ids = vector_store.add_documents(chunks)
    return ids

def search_documents(query: str, k: int = 5, collection_name: str = "ragguard_docs"):
    vector_store = get_vector_store(collection_name)
    results = vector_store.similarity_search_with_score(query, k=k)
    return results
