from typing import Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from .documents import UPLOADED_DOCS
from ..services.vector_store import get_chroma_client
from ..core.query_store import get_avg_trri, get_latest_rrfe, has_executed_queries

router = APIRouter()

class StatsResponse(BaseModel):
    documents: int
    chunks: int
    avgTRRI: float
    activeExperiments: int
    latest_rrfe: Optional[Dict[str, Optional[float]]] = None
    has_executed_query: bool = False

@router.get("/overview", response_model=StatsResponse)
async def get_overview_stats():
    # 1. Dynamic document count from uploaded documents registry
    doc_count = len(UPLOADED_DOCS)
    
    # 2. Dynamic chunk count calculated from ChromaDB + uploaded document registry
    uploaded_chunks_sum = sum(d.get("chunks", 0) for d in UPLOADED_DOCS if isinstance(d.get("chunks"), int))
    chroma_chunks_count = 0
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection("ragguard_docs")
        chroma_chunks_count = collection.count()
    except Exception:
        pass
    
    total_chunks = max(uploaded_chunks_sum, chroma_chunks_count)
    
    # 3. Dynamic average TRRI score from query execution store
    avg_trri = get_avg_trri()
    
    # 4. Latest RRFE scores & query status
    latest_rrfe = get_latest_rrfe()
    query_status = has_executed_queries()

    return StatsResponse(
        documents=doc_count,
        chunks=total_chunks,
        avgTRRI=avg_trri,
        activeExperiments=1 if doc_count > 0 else 0,
        latest_rrfe=latest_rrfe,
        has_executed_query=query_status,
    )
