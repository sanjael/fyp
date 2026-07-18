from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from ..services.embedding_engine import search_documents
from ..services.llm_service import generate_answer
from ..services.rrfe.engine import rrfe_engine
from ..services.dataset_generator.engine import dataset_engine
from ..services.predictor.inference import predictor_engine

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class Source(BaseModel):
    filename: str
    trri: float

class PredictorMetadataResponse(BaseModel):
    model_version: str
    prediction_latency_ms: float
    drift_flags: list[str]

class QueryResponse(BaseModel):
    answer: str
    risk_level: str
    cqs: float
    trri: float
    sources: list[Source]
    rrfe_features: Dict[str, float]
    execution_metadata: Dict[str, Any]
    predictor_metadata: PredictorMetadataResponse
    shap_values: Optional[Dict[str, float]] = None

def run_dataset_generation_task(query: str, docs: list, rrfe_result):
    """Background task to generate dataset samples asynchronously."""
    try:
        sample = dataset_engine.process_session(query, docs, rrfe_result.features)
        dataset_engine.export([sample], "dataset_ragguard_tr.csv")
    except Exception as e:
        print(f"Dataset generation failed: {e}")

@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    # 1. Retrieve chunks
    results = search_documents(request.query, k=3)
    
    # 2. Extract context and metadata
    context_text = ""
    sources_data = []
    
    # search_documents returns a list of tuples: (Document, score)
    docs = [doc for doc, score in results]
    
    for doc, score in results:
        context_text += doc.page_content + "\n\n"
        # Dummy TRRI for individual sources for now
        sources_data.append(Source(
            filename=doc.metadata.get("filename", "Unknown"),
            trri=0.85 
        ))
        
    # 3. Extract RRFE Features
    rrfe_result = rrfe_engine.extract_features(request.query, docs)
    
    # 4. Predict TRRI using XGBoost Regressor
    inference_response = predictor_engine.predict(rrfe_result.features.model_dump())
    trri = inference_response.trri
    
    # Calculate simple CQS and Risk Level for API backwards compatibility
    cqs = round(trri + 0.05, 2)  # Inverse of decay
    risk_level = "low"
    if trri < 0.5:
        risk_level = "high"
    elif trri < 0.8:
        risk_level = "medium"
    
    # 5. Generate Answer via Ollama
    answer = generate_answer(request.query, context_text)
    
    # 6. Kick off Dataset Generation in the background
    background_tasks.add_task(run_dataset_generation_task, request.query, docs, rrfe_result)
    
    return QueryResponse(
        answer=answer,
        risk_level=risk_level,
        cqs=cqs,
        trri=trri,
        sources=sources_data,
        rrfe_features=rrfe_result.features.model_dump(),
        execution_metadata=rrfe_result.execution_metadata,
        predictor_metadata=PredictorMetadataResponse(
            model_version=inference_response.metadata.model_version,
            prediction_latency_ms=inference_response.metadata.prediction_latency_ms,
            drift_flags=inference_response.metadata.drift_flags
        ),
        shap_values=inference_response.shap_values
    )
