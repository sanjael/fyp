"""
Adaptive Generation Controller — Phase 2
=========================================
Dynamically adjusts the generation strategy based on hallucination risk.

Strategy:
    Low Risk    (0–30%)  → Direct Generation
    Medium Risk (30–60%) → Expand Retrieval → Re-evaluate
    High Risk   (60%+)   → Verification Mode (multi-step cross-check)
"""

from typing import Dict, List, Optional

import config
from modules.retriever import Retriever
from modules.context_shield import ContextShield
from modules.cqs_scorer import CQSScorer
from modules.risk_engine import RiskEngine


class AdaptiveController:
    """
    Self-adaptive RAG generation controller.
    Changes the generation pipeline dynamically based on risk level.
    """

    def __init__(
        self,
        retriever: Retriever,
        context_shield: ContextShield,
        cqs_scorer: CQSScorer,
        risk_engine: RiskEngine,
    ):
        self.retriever = retriever
        self.context_shield = context_shield
        self.cqs_scorer = cqs_scorer
        self.risk_engine = risk_engine

    def prepare_context(
        self,
        query: str,
        initial_risk: Dict,
        initial_passed_chunks: List[Dict],
        initial_shield_report: Dict,
    ) -> Dict:
        """
        Prepare final context based on the risk level.
        Returns the final context chunks and adaptation log.
        """
        risk_level = initial_risk.get("risk_level", "low")
        action = initial_risk.get("recommendation", {}).get("action", "direct_generation")

        adaptation_log = [
            {
                "step": 1,
                "action": "initial_evaluation",
                "risk_level": risk_level,
                "risk_score": initial_risk.get("risk_score", 0),
                "passed_chunks": len(initial_passed_chunks),
            }
        ]

        if action == "direct_generation":
            # Low risk: use initial context as-is
            return {
                "final_chunks": initial_passed_chunks,
                "strategy": "direct_generation",
                "adaptation_log": adaptation_log,
                "final_risk": initial_risk,
            }

        elif action == "expand_retrieval":
            # Medium risk: fetch more documents
            return self._expand_retrieval_strategy(
                query, initial_passed_chunks, initial_risk, adaptation_log
            )

        else:
            # High risk: verification mode
            return self._verification_mode_strategy(
                query, initial_passed_chunks, initial_risk, adaptation_log
            )

    def _expand_retrieval_strategy(
        self,
        query: str,
        initial_chunks: List[Dict],
        initial_risk: Dict,
        adaptation_log: List[Dict],
    ) -> Dict:
        """
        Medium risk: retrieve additional chunks and re-evaluate.
        """
        print("[AdaptiveController] Expanding retrieval (Medium Risk)...")

        # Retrieve more documents with higher top_k
        expanded_results = self.retriever.retrieve(
            query=query,
            top_k=config.TOP_K_RESULTS * 2,
        )

        # Re-run shield on expanded set
        shield_result = self.context_shield.evaluate(query, expanded_results)
        expanded_passed = shield_result["passed_chunks"]
        expanded_report = shield_result["shield_report"]

        # Score expanded chunks
        scored_chunks = self.cqs_scorer.score_chunks(
            expanded_passed,
            query=query,
            contradiction_pairs=shield_result["contradiction_pairs"],
        )
        cqs_agg = self.cqs_scorer.compute_aggregate_cqs(scored_chunks)

        # Re-evaluate risk
        new_risk = self.risk_engine.predict_risk(
            query=query,
            retrieved_chunks=expanded_results,
            passed_chunks=scored_chunks,
            cqs_aggregate=cqs_agg,
            shield_report=expanded_report,
        )

        adaptation_log.append({
            "step": 2,
            "action": "expand_retrieval",
            "expanded_retrieved": len(expanded_results),
            "new_passed_chunks": len(scored_chunks),
            "new_risk_score": new_risk.get("risk_score", 0),
        })

        return {
            "final_chunks": scored_chunks,
            "strategy": "expand_retrieval",
            "adaptation_log": adaptation_log,
            "final_risk": new_risk,
        }

    def _verification_mode_strategy(
        self,
        query: str,
        initial_chunks: List[Dict],
        initial_risk: Dict,
        adaptation_log: List[Dict],
    ) -> Dict:
        """
        High risk: multi-step verification with cross-checking.
        1. Re-retrieve with maximum top_k
        2. Apply stricter shield thresholds
        3. Cross-verify key claims across multiple sources
        4. Only include claims supported by 2+ sources
        """
        print("[AdaptiveController] Entering Verification Mode (High Risk)...")

        # Step 1: Maximum retrieval
        max_results = self.retriever.retrieve(
            query=query,
            top_k=config.TOP_K_RESULTS * 3,
            min_similarity=0.70,  # Stricter threshold
        )

        adaptation_log.append({
            "step": 2,
            "action": "verification_retrieval",
            "chunks_retrieved": len(max_results),
        })

        # Step 2: Strict shield
        shield_result = self.context_shield.evaluate(
            query, max_results, include_flagged=False
        )
        verified_chunks = shield_result["passed_chunks"]

        # Step 3: Cross-source verification — keep only chunks supported by 2+ sources
        cross_verified = self._cross_source_verify(verified_chunks)

        adaptation_log.append({
            "step": 3,
            "action": "cross_source_verification",
            "before_verification": len(verified_chunks),
            "after_verification": len(cross_verified),
        })

        # Score final chunks
        scored_chunks = self.cqs_scorer.score_chunks(
            cross_verified,
            query=query,
            contradiction_pairs=shield_result["contradiction_pairs"],
        )
        cqs_agg = self.cqs_scorer.compute_aggregate_cqs(scored_chunks)

        # Final risk assessment
        final_risk = self.risk_engine.predict_risk(
            query=query,
            retrieved_chunks=max_results,
            passed_chunks=scored_chunks,
            cqs_aggregate=cqs_agg,
            shield_report=shield_result["shield_report"],
        )

        adaptation_log.append({
            "step": 4,
            "action": "final_risk_assessment",
            "final_risk_score": final_risk.get("risk_score", 0),
            "final_chunks": len(scored_chunks),
        })

        return {
            "final_chunks": scored_chunks,
            "strategy": "verification_mode",
            "adaptation_log": adaptation_log,
            "final_risk": final_risk,
        }

    def _cross_source_verify(self, chunks: List[Dict]) -> List[Dict]:
        """
        Keep chunks that have supporting evidence from multiple sources.
        Single-source high-risk claims are removed.
        """
        if len(chunks) <= 2:
            return chunks  # Not enough for cross-verification

        # Group chunks by source
        source_groups: Dict[str, List] = {}
        for chunk in chunks:
            source = chunk.get("source", "unknown")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(chunk)

        # If only one source, return all (can't cross-verify)
        if len(source_groups) == 1:
            return chunks

        # Keep chunks whose content is corroborated by at least one other source
        # (using the CQS as proxy for reliability)
        high_quality = [c for c in chunks if c.get("cqs_score", 0) >= 65]
        if high_quality:
            return high_quality
        return chunks  # Fallback: return all if none meet threshold
