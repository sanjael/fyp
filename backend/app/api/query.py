from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from ..services.vector_store import search_documents
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
    trri: float
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
    # 1. Retrieve chunks
    results = search_documents(request.query, k=3)
    docs = [doc for doc, _ in results]

    context_text = ""
    sources_data: List[Source] = []
    for doc, _ in results:
        context_text += doc.page_content + "\n\n"
        sources_data.append(Source(
            filename=doc.metadata.get("filename", "Unknown"),
            trri=0.85,
        ))

    # 2. Extract RRFE features + explanations
    rrfe_result = rrfe_engine.extract_features(request.query, docs)

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
    inference_response = predictor_engine.predict(rrfe_result.features.model_dump())
    trri = inference_response.trri

    if trri < 0.5:
        risk_level = "high"
    elif trri < 0.8:
        risk_level = "medium"
    else:
        risk_level = "low"

    # 5. Generate answer
    answer = generate_answer(request.query, context_text)

    # 6. Background dataset accumulation
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
        execution_metadata=rrfe_result.execution_metadata,
        predictor_metadata=PredictorMetadataResponse(
            model_version=inference_response.metadata.model_version,
            prediction_latency_ms=inference_response.metadata.prediction_latency_ms,
            drift_flags=inference_response.metadata.drift_flags,
        ),
        shap_values=inference_response.shap_values,
    )
