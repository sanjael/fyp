import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from ..services.vector_store import search_documents
from ..services.llm_service import generate_answer
from ..services.rrfe.engine import rrfe_engine
from ..services.dataset_generator.engine import dataset_engine
from ..services.predictor.inference import predictor_engine
from ..core.query_store import record_query_execution

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class Source(BaseModel):
    filename: str
    trri: Optional[float] = None


class FeatureExplanation(BaseModel):
    """Explainability card for a single RRFE feature."""
    feature_name: str
    score: Optional[float]   # None when extractor could not produce a valid score
    confidence: float
    reason: str
    evidence_source: str


class PredictorMetadataResponse(BaseModel):
    model_version: str
    prediction_latency_ms: float
    drift_flags: List[str]


class QueryResponse(BaseModel):
    answer: str
    risk_level: str
    # NOTE: CQS removed — it was mathematically dependent on TRRI
    # (trri + 0.05) and therefore scientifically invalid as an independent metric.
    trri: Optional[float] = None
    sources: List[Source]
    rrfe_features: Dict[str, Optional[float]]
    # Full per-feature explainability cards
    rrfe_explanations: List[FeatureExplanation]
    execution_metadata: Dict[str, Any]
    predictor_metadata: PredictorMetadataResponse
    shap_values: Optional[Dict[str, float]] = None


def run_dataset_generation_task(query: str, docs: list, rrfe_result) -> None:
    try:
        sample = dataset_engine.process_session(query, docs, rrfe_result.features)
        dataset_engine.export([sample], "dataset_ragguard_tr.csv")
    except Exception as exc:
        print(f"Dataset generation failed: {exc}")


@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    t_start = time.perf_counter()

    # 1. Retrieve chunks
    t0 = time.perf_counter()
    results = search_documents(request.query, k=3)
    t_retrieval_ms = round((time.perf_counter() - t0) * 1000, 2)
    docs = [doc for doc, _ in results]

    context_text = ""
    sources_data: List[Source] = []
    for doc, _ in results:
        context_text += doc.page_content + "\n\n"
        sources_data.append(Source(
            filename=doc.metadata.get("filename", "Unknown"),
            trri=None,
        ))

    # 2. Extract RRFE features + explanations
    t0 = time.perf_counter()
    rrfe_result = rrfe_engine.extract_features(request.query, docs)
    t_rrfe_ms = round((time.perf_counter() - t0) * 1000, 2)

    # 3. Build explainability cards
    explanations: List[FeatureExplanation] = [
        FeatureExplanation(
            feature_name=name,
            score=feat.score,
            confidence=feat.confidence,
            reason=feat.reason,
            evidence_source=feat.evidence_source,
        )
        for name, feat in rrfe_result.explanations.items()
    ]

    # 4. Predict TRRI
    t0 = time.perf_counter()
    inference_response = predictor_engine.predict(rrfe_result.features.model_dump())
    t_pred_ms = round((time.perf_counter() - t0) * 1000, 2)
    trri = inference_response.trri

    if trri is None:
        risk_level = "unavailable"
    elif trri < 0.5:
        risk_level = "high"
    elif trri < 0.8:
        risk_level = "medium"
    else:
        risk_level = "low"

    # 5. Generate answer
    t0 = time.perf_counter()
    answer = generate_answer(request.query, context_text)
    t_gen_ms = round((time.perf_counter() - t0) * 1000, 2)

    t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)

    exec_metadata = dict(rrfe_result.execution_metadata)
    exec_metadata["profiler"] = {
        "retrieval_ms": t_retrieval_ms,
        "rrfe_ms": t_rrfe_ms,
        "predictor_ms": t_pred_ms,
        "generation_ms": t_gen_ms,
        "total_ms": t_total_ms,
    }

    # 6. Record query telemetry
    record_query_execution(
        query=request.query,
        trri=trri,
        risk_level=risk_level,
        rrfe_features=rrfe_result.features.model_dump(),
    )

    # 7. Background dataset accumulation
    background_tasks.add_task(
        run_dataset_generation_task, request.query, docs, rrfe_result
    )

    return QueryResponse(
        answer=answer,
        risk_level=risk_level,
        trri=trri,
        sources=sources_data,
        rrfe_features=rrfe_result.features.model_dump(),
        rrfe_explanations=explanations,
        execution_metadata=exec_metadata,
        predictor_metadata=PredictorMetadataResponse(
            model_version=inference_response.metadata.model_version,
            prediction_latency_ms=inference_response.metadata.prediction_latency_ms,
            drift_flags=inference_response.metadata.drift_flags,
        ),
        shap_values=inference_response.shap_values,
    )
