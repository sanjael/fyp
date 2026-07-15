import os
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# Initialize Ollama Embeddings
embeddings = OllamaEmbeddings(
    base_url=OLLAMA_HOST,
    model="nomic-embed-text"
)

# Initialize ChromaDB client
try:
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
except Exception as e:
    print(f"Failed to connect to ChromaDB: {e}")
    chroma_client = None

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
