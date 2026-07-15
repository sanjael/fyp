"""
Hallucination Risk Prediction Engine — Phase 2 Research Contribution
=====================================================================
Predicts the probability of hallucination BEFORE answer generation.
This is a key research novelty of RAGShield.

Risk Levels:
    Low    (0–30%)   → Direct generation
    Medium (30–60%)  → Retrieve more documents
    High   (60–100%) → Verification Mode

Features used:
    - Average CQS score
    - Average similarity score
    - Contradiction count
    - Pass rate (% of chunks that passed the shield)
    - Source reliability variance
    - Min CQS (weakest chunk)
"""

import math
import os
import pickle
from typing import Dict, List, Optional
from pathlib import Path

import numpy as np

import config


class RiskEngine:
    """
    Hallucination Risk Prediction Engine.

    Uses a rule-based heuristic model for immediate functionality,
    with XGBoost model support when training data is available.
    """

    def __init__(self):
        self.model = None
        self.model_path = Path(config.BASE_DIR) / "models" / "risk_predictor.pkl"
        self._load_model()

    def _load_model(self):
        """Load XGBoost model if available."""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                print("[RiskEngine] Loaded trained XGBoost risk model.")
            except Exception as e:
                print(f"[RiskEngine] Could not load model: {e}. Using heuristic mode.")
        else:
            print("[RiskEngine] No trained model found. Using heuristic risk estimation.")

    def predict_risk(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        passed_chunks: List[Dict],
        cqs_aggregate: Dict,
        shield_report: Dict,
    ) -> Dict:
        """
        Predict hallucination risk before generation.

        Args:
            query: User's query
            retrieved_chunks: All retrieved chunks (pre-shield)
            passed_chunks: Chunks that passed the shield
            cqs_aggregate: Aggregate CQS statistics
            shield_report: Context Shield analysis report

        Returns:
            Dict with risk_score, risk_level, risk_factors, recommendation
        """
        features = self._extract_features(
            query, retrieved_chunks, passed_chunks, cqs_aggregate, shield_report
        )

        if self.model is not None:
            risk_score = self._predict_with_model(features)
        else:
            risk_score = self._heuristic_risk(features)

        risk_level = self._get_risk_level(risk_score)
        risk_factors = self._explain_risk_factors(features, risk_score)
        recommendation = self._get_recommendation(risk_level, features)

        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_percentage": round(risk_score, 1),
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "features": {k: round(v, 3) if isinstance(v, float) else v
                        for k, v in features.items()},
        }

    def _extract_features(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        passed_chunks: List[Dict],
        cqs_aggregate: Dict,
        shield_report: Dict,
    ) -> Dict:
        """Extract numerical features for risk prediction."""

        total_retrieved = shield_report.get("total_retrieved", 0)
        total_passed = shield_report.get("total_passed", 0)
        pass_rate = total_passed / max(1, total_retrieved)

        avg_cqs = cqs_aggregate.get("avg_cqs", 0.0)
        min_cqs = cqs_aggregate.get("min_cqs", 0.0)
        std_cqs = cqs_aggregate.get("std_cqs", 0.0)

        avg_similarity = (
            sum(c.get("similarity_score", 0) for c in passed_chunks) / max(1, len(passed_chunks))
            if passed_chunks else 0.0
        )

        contradiction_count = shield_report.get("contradictions_found", 0)
        duplicates_removed = shield_report.get("duplicates_removed", 0)
        irrelevant_removed = shield_report.get("irrelevant_removed", 0)

        source_scores = [c.get("source_reliability_score", 50) for c in passed_chunks]
        avg_source_reliability = sum(source_scores) / max(1, len(source_scores)) if source_scores else 50.0
        source_variance = self._variance(source_scores)

        freshness_scores = [c.get("freshness_score", 50) for c in passed_chunks]
        avg_freshness = sum(freshness_scores) / max(1, len(freshness_scores)) if freshness_scores else 50.0

        # Query complexity (longer, multi-part queries are harder)
        query_words = len(query.split())
        has_question_words = any(w in query.lower() for w in ["what", "why", "how", "when", "where", "who"])

        return {
            "avg_cqs": avg_cqs,
            "min_cqs": min_cqs,
            "std_cqs": std_cqs,
            "avg_similarity": avg_similarity * 100,  # Scale to 0-100
            "pass_rate": pass_rate * 100,
            "contradiction_count": contradiction_count,
            "duplicates_removed": duplicates_removed,
            "irrelevant_removed": irrelevant_removed,
            "avg_source_reliability": avg_source_reliability,
            "source_variance": source_variance,
            "avg_freshness": avg_freshness,
            "num_passed_chunks": total_passed,
            "num_retrieved": total_retrieved,
            "query_length": query_words,
            "is_complex_query": int(has_question_words and query_words > 8),
        }

    def _heuristic_risk(self, features: Dict) -> float:
        """
        Rule-based hallucination risk estimation.
        Used when no trained model is available.

        Higher risk when:
        - Low CQS scores
        - Many contradictions
        - Low pass rate
        - Low source reliability
        """
        risk = 0.0

        # CQS-based risk (40% weight)
        avg_cqs = features.get("avg_cqs", 50)
        cqs_risk = max(0, (70 - avg_cqs) / 70) * 100
        risk += 0.40 * cqs_risk

        # Contradiction risk (25% weight)
        contradiction_count = features.get("contradiction_count", 0)
        contradiction_risk = min(100, contradiction_count * 25)
        risk += 0.25 * contradiction_risk

        # Pass rate risk (20% weight)
        pass_rate = features.get("pass_rate", 100)
        pass_risk = max(0, (60 - pass_rate) / 60) * 100
        risk += 0.20 * pass_risk

        # Source reliability risk (10% weight)
        avg_reliability = features.get("avg_source_reliability", 70)
        reliability_risk = max(0, (70 - avg_reliability) / 70) * 100
        risk += 0.10 * reliability_risk

        # Freshness risk (5% weight)
        avg_freshness = features.get("avg_freshness", 70)
        freshness_risk = max(0, (60 - avg_freshness) / 60) * 100
        risk += 0.05 * freshness_risk

        # No context passed → maximum risk
        if features.get("num_passed_chunks", 0) == 0:
            risk = 95.0

        return min(100.0, max(0.0, risk))

    def _predict_with_model(self, features: Dict) -> float:
        """Use trained XGBoost model for risk prediction."""
        try:
            feature_vector = np.array([[
                features["avg_cqs"],
                features["min_cqs"],
                features["std_cqs"],
                features["avg_similarity"],
                features["pass_rate"],
                features["contradiction_count"],
                features["avg_source_reliability"],
                features["avg_freshness"],
                features["num_passed_chunks"],
                features["query_length"],
            ]])
            prob = self.model.predict_proba(feature_vector)[0][1]  # Probability of hallucination
            return float(prob * 100)
        except Exception as e:
            print(f"[RiskEngine] Model prediction failed: {e}. Falling back to heuristic.")
            return self._heuristic_risk(features)

    def _get_risk_level(self, risk_score: float) -> str:
        """Classify risk into Low / Medium / High."""
        if risk_score < config.RISK_LOW_THRESHOLD:
            return "low"
        elif risk_score < config.RISK_HIGH_THRESHOLD:
            return "medium"
        else:
            return "high"

    def _explain_risk_factors(self, features: Dict, risk_score: float) -> List[Dict]:
        """Generate human-readable risk factor explanations."""
        factors = []

        if features.get("avg_cqs", 100) < 60:
            factors.append({
                "factor": "Low Context Quality",
                "severity": "high",
                "detail": f"Average CQS: {features['avg_cqs']:.1f}/100 — context may be unreliable",
            })

        if features.get("contradiction_count", 0) > 0:
            factors.append({
                "factor": "Contradictory Evidence",
                "severity": "high",
                "detail": f"{features['contradiction_count']} contradiction(s) found across sources",
            })

        if features.get("pass_rate", 100) < 50:
            factors.append({
                "factor": "Low Retrieval Quality",
                "severity": "medium",
                "detail": f"Only {features['pass_rate']:.0f}% of retrieved chunks passed the shield",
            })

        if features.get("avg_source_reliability", 100) < 60:
            factors.append({
                "factor": "Unreliable Sources",
                "severity": "medium",
                "detail": f"Average source reliability: {features['avg_source_reliability']:.0f}/100",
            })

        if features.get("avg_freshness", 100) < 50:
            factors.append({
                "factor": "Outdated Information",
                "severity": "low",
                "detail": f"Average freshness score: {features['avg_freshness']:.0f}/100",
            })

        if features.get("num_passed_chunks", 1) == 0:
            factors.append({
                "factor": "No Reliable Context",
                "severity": "critical",
                "detail": "No chunks passed the Context Shield. Answer will be unreliable.",
            })

        if not factors:
            factors.append({
                "factor": "Strong Context Quality",
                "severity": "low",
                "detail": "Retrieved context appears reliable and consistent",
            })

        return factors

    def _get_recommendation(self, risk_level: str, features: Dict) -> Dict:
        """Get adaptive generation recommendation based on risk level."""
        if risk_level == "low":
            return {
                "action": "direct_generation",
                "label": "Direct Generation",
                "description": "Context quality is high. Generate answer directly.",
                "icon": "✅",
            }
        elif risk_level == "medium":
            return {
                "action": "expand_retrieval",
                "label": "Expand Retrieval",
                "description": "Retrieve additional documents to strengthen context before generating.",
                "icon": "🔄",
            }
        else:
            return {
                "action": "verification_mode",
                "label": "Verification Mode",
                "description": "High hallucination risk. Re-retrieve, cross-check, and verify before answering.",
                "icon": "🔍",
            }

    def _variance(self, values: List[float]) -> float:
        """Compute variance of a list of values."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    def save_model(self, model) -> bool:
        """Save a trained XGBoost model."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, "wb") as f:
                pickle.dump(model, f)
            self.model = model
            print(f"[RiskEngine] Model saved to {self.model_path}")
            return True
        except Exception as e:
            print(f"[RiskEngine] Save failed: {e}")
            return False
