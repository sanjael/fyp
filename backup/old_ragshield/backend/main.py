"""
RAGShield — FastAPI Main Application
=====================================
Entry point for the RAGShield backend API.

Endpoints:
    POST /api/upload          — Upload and index a PDF
    POST /api/query           — Ask a question (full RAGShield pipeline)
    GET  /api/documents       — List all indexed documents
    DELETE /api/documents/{f} — Delete a document
    GET  /api/stats           — System statistics
    POST /api/poison-test     — Run poisoning benchmark
    GET  /api/health          — Health check
"""

import os
import time
import shutil
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config
from modules.document_processor import DocumentProcessor
from modules.embedding_engine import EmbeddingEngine
from modules.vector_store import VectorStore
from modules.retriever import Retriever
from modules.context_shield import ContextShield
from modules.cqs_scorer import CQSScorer
from modules.risk_engine import RiskEngine
from modules.adaptive_controller import AdaptiveController
from modules.poisoning_simulator import PoisoningSimulator
from modules.llm_engine import LLMEngine

# ─── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="RAGShield API",
    description="Risk-Aware and Self-Adaptive Framework for Hallucination Prevention in RAG Systems",
    version=config.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Dependency Initialization ────────────────────────────────────────────────

print("[RAGShield] Initializing components...")

embedding_engine = EmbeddingEngine()
vector_store = VectorStore()
document_processor = DocumentProcessor()
retriever = Retriever(vector_store)
context_shield = ContextShield()
cqs_scorer = CQSScorer()
risk_engine = RiskEngine()
adaptive_controller = AdaptiveController(
    retriever, context_shield, cqs_scorer, risk_engine
)
poisoning_simulator = PoisoningSimulator()

# LLM is optional (requires API key)
llm_engine = None
try:
    llm_engine = LLMEngine()
except ValueError as e:
    print(f"[RAGShield] LLM not available: {e}")

print("[RAGShield] All components initialized. Server ready.")


# ─── Request / Response Models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    source_filter: Optional[str] = None
    enable_adaptive: Optional[bool] = True


class PoisonTestRequest(BaseModel):
    query: str
    poison_ratio: Optional[float] = 0.3
    poison_types: Optional[List[str]] = None


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "llm_available": llm_engine is not None,
        "total_chunks": vector_store.get_total_chunks(),
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_model": config.LLM_MODEL,
    }


# ─── Upload Document ──────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Upload a PDF document, extract text, chunk, embed, and store in ChromaDB."""
    start_time = time.time()

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save uploaded file
    upload_path = Path(config.PDF_UPLOAD_PATH) / file.filename
    try:
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Process document
    try:
        chunks, metadata = document_processor.process_pdf(str(upload_path))
        chunks_added = vector_store.add_chunks(chunks)

        processing_time = round(time.time() - start_time, 2)

        return {
            "status": "success",
            "filename": file.filename,
            "title": metadata.get("title", file.filename),
            "author": metadata.get("author", "Unknown"),
            "year": metadata.get("year", "Unknown"),
            "source_type": metadata.get("source_type", "unknown"),
            "num_pages": metadata.get("num_pages", 0),
            "total_chunks": len(chunks),
            "new_chunks_added": chunks_added,
            "processing_time_seconds": processing_time,
            "message": f"Successfully indexed {chunks_added} new chunks from {file.filename}",
        }
    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ─── Query (Full RAGShield Pipeline) ─────────────────────────────────────────

@app.post("/api/query")
async def query(request: QueryRequest):
    """
    Full RAGShield pipeline:
    Query → Retrieve → Context Shield → CQS Score → Risk Predict → Adaptive → LLM → Answer
    """
    start_time = time.time()
    query_text = request.query.strip()

    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if vector_store.get_total_chunks() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed. Please upload PDF documents first."
        )

    # ── Step 1: Retrieve ──────────────────────────────────────────────────────
    retrieved_chunks = retriever.retrieve(
        query=query_text,
        top_k=request.top_k,
        source_filter=request.source_filter,
    )

    if not retrieved_chunks:
        return {
            "query": query_text,
            "answer": "No relevant documents found. Please upload more relevant PDFs.",
            "retrieved_count": 0,
            "passed_count": 0,
            "risk": {"risk_level": "high", "risk_score": 95},
            "pipeline_stages": {},
            "processing_time": round(time.time() - start_time, 2),
        }

    # ── Step 2: Context Shield ────────────────────────────────────────────────
    shield_result = context_shield.evaluate(query_text, retrieved_chunks)
    passed_chunks = shield_result["passed_chunks"]
    filtered_chunks = shield_result["filtered_chunks"]
    shield_report = shield_result["shield_report"]

    # ── Step 3: CQS Scoring ───────────────────────────────────────────────────
    scored_chunks = cqs_scorer.score_chunks(
        passed_chunks,
        query=query_text,
        contradiction_pairs=shield_result.get("contradiction_pairs", []),
    )
    cqs_aggregate = cqs_scorer.compute_aggregate_cqs(scored_chunks)

    # ── Step 4: Risk Prediction ───────────────────────────────────────────────
    risk = risk_engine.predict_risk(
        query=query_text,
        retrieved_chunks=retrieved_chunks,
        passed_chunks=scored_chunks,
        cqs_aggregate=cqs_aggregate,
        shield_report=shield_report,
    )

    # ── Step 5: Adaptive Controller ───────────────────────────────────────────
    final_context = {"final_chunks": scored_chunks, "strategy": "direct_generation",
                     "adaptation_log": [], "final_risk": risk}

    if request.enable_adaptive and risk["risk_level"] != "low":
        try:
            final_context = adaptive_controller.prepare_context(
                query=query_text,
                initial_risk=risk,
                initial_passed_chunks=scored_chunks,
                initial_shield_report=shield_report,
            )
        except Exception as e:
            print(f"[API] Adaptive controller error: {e}")

    final_chunks = final_context["final_chunks"]
    strategy = final_context["strategy"]
    final_risk = final_context.get("final_risk", risk)

    # ── Step 6: LLM Generation ────────────────────────────────────────────────
    if llm_engine and final_chunks:
        llm_response = llm_engine.generate(
            query=query_text,
            context_chunks=final_chunks,
            risk_level=final_risk.get("risk_level", "low"),
            strategy=strategy,
        )
    else:
        # Demo mode without LLM
        llm_response = _demo_response(query_text, final_chunks, final_risk)

    processing_time = round(time.time() - start_time, 2)

    return {
        "query": query_text,
        "answer": llm_response["answer"],
        "sources": llm_response.get("sources", []),
        "confidence": llm_response.get("confidence", "unknown"),
        "strategy": strategy,
        "risk": {
            "risk_score": final_risk.get("risk_score", 0),
            "risk_level": final_risk.get("risk_level", "unknown"),
            "risk_factors": final_risk.get("risk_factors", []),
            "recommendation": final_risk.get("recommendation", {}),
        },
        "retrieved_count": len(retrieved_chunks),
        "passed_count": len(final_chunks),
        "filtered_count": len(filtered_chunks),
        "cqs_stats": cqs_aggregate,
        "shield_report": shield_report,
        "scored_chunks": [
            {
                "chunk_id": c.get("chunk_id"),
                "text": c.get("text", "")[:300] + ("..." if len(c.get("text","")) > 300 else ""),
                "source": c.get("source"),
                "year": c.get("year"),
                "similarity_score": c.get("similarity_score"),
                "cqs_score": c.get("cqs_score"),
                "quality_level": c.get("quality_level"),
                "component_scores": c.get("component_scores", {}),
                "shield_verdict": c.get("shield_verdict"),
            }
            for c in final_chunks
        ],
        "filtered_chunks": [
            {
                "chunk_id": c.get("chunk_id"),
                "text": c.get("text", "")[:200] + "...",
                "source": c.get("source"),
                "shield_verdict": c.get("shield_verdict"),
                "filter_reason": c.get("filter_reason"),
                "similarity_score": c.get("similarity_score"),
            }
            for c in filtered_chunks[:10]
        ],
        "adaptation_log": final_context.get("adaptation_log", []),
        "processing_time_seconds": processing_time,
        "model": config.LLM_MODEL,
    }


# ─── Documents ────────────────────────────────────────────────────────────────

@app.get("/api/documents")
async def list_documents():
    """List all indexed documents."""
    docs = vector_store.list_documents()
    return {
        "documents": docs,
        "total_documents": len(docs),
        "total_chunks": vector_store.get_total_chunks(),
    }


@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from the vector store."""
    deleted = vector_store.delete_document(filename)

    # Also delete the PDF file
    pdf_path = Path(config.PDF_UPLOAD_PATH) / filename
    if pdf_path.exists():
        pdf_path.unlink()

    return {
        "status": "success",
        "filename": filename,
        "chunks_deleted": deleted,
    }


# ─── System Statistics ────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats():
    """System statistics for the dashboard."""
    docs = vector_store.list_documents()
    return {
        "total_documents": len(docs),
        "total_chunks": vector_store.get_total_chunks(),
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_model": config.LLM_MODEL,
        "llm_available": llm_engine is not None,
        "shield_thresholds": {
            "relevance": config.RELEVANCE_THRESHOLD,
            "duplicate": config.DUPLICATE_THRESHOLD,
        },
        "cqs_weights": {
            "relevance": config.CQS_WEIGHT_RELEVANCE,
            "credibility": config.CQS_WEIGHT_CREDIBILITY,
            "consistency": config.CQS_WEIGHT_CONSISTENCY,
            "freshness": config.CQS_WEIGHT_FRESHNESS,
        },
        "risk_thresholds": {
            "low": config.RISK_LOW_THRESHOLD,
            "high": config.RISK_HIGH_THRESHOLD,
        },
        "top_k": config.TOP_K_RESULTS,
        "max_context_chunks": config.MAX_CONTEXT_CHUNKS,
    }


# ─── Poisoning Test ───────────────────────────────────────────────────────────

@app.post("/api/poison-test")
async def run_poison_test(request: PoisonTestRequest):
    """Run a context poisoning benchmark test."""
    query_text = request.query.strip()

    retrieved = retriever.retrieve(query=query_text)
    if not retrieved:
        raise HTTPException(status_code=400, detail="No documents available for poison test.")

    # Run shield on clean chunks
    shield_result = context_shield.evaluate(query_text, retrieved)

    # Run benchmark
    benchmark = poisoning_simulator.benchmark(
        query=query_text,
        original_chunks=retrieved,
        shield_passed_chunks=shield_result["passed_chunks"],
        poison_ratio=request.poison_ratio,
    )

    return {
        "status": "success",
        "benchmark": benchmark,
        "message": f"RAGShield blocked {benchmark['detection_rate_percent']}% of poisoned chunks",
    }


# ─── Demo Helper (no API key mode) ───────────────────────────────────────────

def _demo_response(query: str, chunks: List[dict], risk: dict) -> dict:
    """Generate a demo response when LLM is not configured."""
    if not chunks:
        context_preview = "No context available."
    else:
        best_chunk = max(chunks, key=lambda c: c.get("cqs_score", 0))
        context_preview = best_chunk.get("text", "")[:500]

    answer = (
        f"[DEMO MODE — Add GEMINI_API_KEY to .env for real LLM responses]\n\n"
        f"Based on the retrieved context (Risk Level: {risk.get('risk_level','?').upper()}):\n\n"
        f"Top retrieved chunk preview:\n{context_preview}..."
    )

    return {
        "answer": answer,
        "sources": [{"filename": c.get("source", "?"), "cqs_score": c.get("cqs_score")} for c in chunks[:3]],
        "confidence": "demo",
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level="info",
    )
