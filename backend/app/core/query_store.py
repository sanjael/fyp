"""
Query Store & System Telemetry Manager.
Stores real-time query execution logs, TRRI predictions, and RRFE features.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

QUERY_LOGS: List[Dict[str, Any]] = []

def record_query_execution(
    query: str,
    trri: Optional[float],
    risk_level: str,
    rrfe_features: Dict[str, Optional[float]]
) -> None:
    QUERY_LOGS.append({
        "query": query,
        "trri": trri,
        "risk_level": risk_level,
        "rrfe_features": rrfe_features,
        "timestamp": datetime.utcnow().isoformat(),
    })

def get_avg_trri() -> float:
    valid_scores = [q["trri"] for q in QUERY_LOGS if q.get("trri") is not None]
    if not valid_scores:
        return 0.0
    return round(sum(valid_scores) / len(valid_scores), 3)

def get_latest_rrfe() -> Optional[Dict[str, Optional[float]]]:
    if not QUERY_LOGS:
        return None
    return QUERY_LOGS[-1].get("rrfe_features")

def has_executed_queries() -> bool:
    return len(QUERY_LOGS) > 0
