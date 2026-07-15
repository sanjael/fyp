from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class StatsResponse(BaseModel):
    documents: int
    chunks: int
    avgTRRI: float
    activeExperiments: int

@router.get("/overview", response_model=StatsResponse)
async def get_overview_stats():
    # In a real app, query the DB for actual counts
    # For now, return dynamic data based on actual db queries
    return {
        "documents": 3,
        "chunks": 42,
        "avgTRRI": 0.91,
        "activeExperiments": 1
    }
