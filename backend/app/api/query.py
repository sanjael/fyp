from fastapi import APIRouter
from pydantic import BaseModel
from ..services.embedding_engine import search_documents
from ..services.llm_service import generate_answer
from ..services.trri_engine import calculate_trri

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class Source(BaseModel):
    filename: str
    trri: float

class QueryResponse(BaseModel):
    answer: str
    risk_level: str
    cqs: float
    sources: list[Source]

@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    # 1. Retrieve chunks
    results = search_documents(request.query, k=3)
    
    # Extract context and metadata
    context_text = ""
    sources_data = []
    
    for doc, score in results:
        context_text += doc.page_content + "\n\n"
        # Dummy TRRI for individual sources for now
        sources_data.append(Source(
            filename=doc.metadata.get("filename", "Unknown"),
            trri=0.85 
        ))
        
    # 2. Calculate TRRI and CQS
    metrics = calculate_trri(results)
    
    # 3. Generate Answer via Ollama
    answer = generate_answer(request.query, context_text)
    
    return QueryResponse(
        answer=answer,
        risk_level=metrics["risk_level"],
        cqs=metrics["cqs"],
        sources=sources_data
    )
