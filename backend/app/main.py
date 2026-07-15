from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth

app = FastAPI(
    title="RAGGuard-TR API",
    description="Temporal-aware Risk and Reliability Index for RAG Systems",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api import auth, documents, query, stats

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Stats"])
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RAGGuard-TR API"}
