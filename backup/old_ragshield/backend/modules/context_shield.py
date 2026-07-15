"""
Context Shield Layer — RAGShield's Core Innovation
=================================================
Evaluates and filters retrieved context BEFORE it reaches the LLM.
This pre-generation validation is the primary research contribution of RAGShield.

Shield Functions:
1. Duplicate Detection      — removes semantically identical chunks
2. Relevance Validation     — removes off-topic chunks
3. Contradiction Analysis   — detects conflicting information
4. Source Reliability Check — scores trustworthiness of sources
5. Noise Filtering          — removes low-quality, incoherent content
"""

import re
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np

import config
from modules.embedding_engine import EmbeddingEngine


class ShieldVerdict:
    """Verdict for a single chunk after Context Shield evaluation."""
    PASSED = "passed"
    FILTERED_DUPLICATE = "filtered_duplicate"
    FILTERED_IRRELEVANT = "filtered_irrelevant"
    FILTERED_NOISE = "filtered_noise"
    FLAGGED_CONTRADICTION = "flagged_contradiction"
    FLAGGED_LOW_QUALITY = "flagged_low_quality"


class ContextShield:
    """
    RAGShield's Context Shield Layer.

    Acts as a security guard between the Retriever and the LLM.
    Evaluates each retrieved chunk and only allows trusted, high-quality
    context to pass through to the language model.
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.current_year = datetime.now().year

    def evaluate(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        include_flagged: bool = False,
    ) -> Dict:
        """
        Main entry point: evaluate all retrieved chunks through the shield.

        Args:
            query: Original user query
            retrieved_chunks: Chunks from the retriever
            include_flagged: If True, include contradiction-flagged chunks with warnings

        Returns:
            Dict with passed_chunks, filtered_chunks, shield_report
        """
        if not retrieved_chunks:
            return {
                "passed_chunks": [],
                "filtered_chunks": [],
                "contradiction_pairs": [],
                "shield_report": self._empty_report(),
            }

        print(f"[ContextShield] Evaluating {len(retrieved_chunks)} chunks...")

        # Generate embeddings for all chunks (for similarity comparisons)
        texts = [c["text"] for c in retrieved_chunks]
        chunk_embeddings = self.embedding_engine.embed_documents(texts)
        query_embedding = self.embedding_engine.embed_query(query)

        # Run all shield modules
        dedup_results = self._duplicate_detection(retrieved_chunks, chunk_embeddings)
        relevance_results = self._relevance_validation(
            retrieved_chunks, chunk_embeddings, query_embedding
        )
        noise_results = self._noise_filtering(retrieved_chunks)
        contradiction_pairs = self._contradiction_analysis(
            retrieved_chunks, chunk_embeddings
        )
        source_scores = self._source_reliability_scoring(retrieved_chunks)
        freshness_scores = self._freshness_scoring(retrieved_chunks)

        # Combine evaluations and classify each chunk
        passed_chunks = []
        filtered_chunks = []
        contradiction_chunk_ids = set(
            cid for pair in contradiction_pairs for cid in pair["chunk_ids"]
        )

        for i, chunk in enumerate(retrieved_chunks):
            chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            verdict = ShieldVerdict.PASSED
            filter_reason = ""

            # Check duplicate
            if dedup_results.get(chunk_id) == "duplicate":
                verdict = ShieldVerdict.FILTERED_DUPLICATE
                filter_reason = "Semantically identical to another chunk"

            # Check relevance
            elif relevance_results.get(chunk_id, 1.0) < config.RELEVANCE_THRESHOLD:
                verdict = ShieldVerdict.FILTERED_IRRELEVANT
                filter_reason = f"Low relevance score: {relevance_results.get(chunk_id, 0):.2f}"

            # Check noise
            elif noise_results.get(chunk_id, False):
                verdict = ShieldVerdict.FILTERED_NOISE
                filter_reason = "Detected as noisy/incoherent content"

            # Check contradiction (flag but may still pass)
            elif chunk_id in contradiction_chunk_ids:
                verdict = ShieldVerdict.FLAGGED_CONTRADICTION
                filter_reason = "Contains information contradicting other retrieved chunks"

            # Enrich chunk with shield data
            enriched_chunk = {
                **chunk,
                "shield_verdict": verdict,
                "filter_reason": filter_reason,
                "relevance_score": round(relevance_results.get(chunk_id, chunk.get("similarity_score", 0)), 4),
                "source_reliability_score": source_scores.get(chunk_id, 50),
                "freshness_score": freshness_scores.get(chunk_id, 50),
                "is_contradicted": chunk_id in contradiction_chunk_ids,
            }

            if verdict == ShieldVerdict.PASSED:
                passed_chunks.append(enriched_chunk)
            elif verdict == ShieldVerdict.FLAGGED_CONTRADICTION and include_flagged:
                # Include with warning
                enriched_chunk["warning"] = "Contradictory information detected"
                passed_chunks.append(enriched_chunk)
            else:
                filtered_chunks.append(enriched_chunk)

        # Sort passed chunks by relevance score
        passed_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit to max context chunks
        final_passed = passed_chunks[:config.MAX_CONTEXT_CHUNKS]
        overflow_chunks = passed_chunks[config.MAX_CONTEXT_CHUNKS:]
        filtered_chunks.extend(overflow_chunks)

        shield_report = self._generate_shield_report(
            query=query,
            total_retrieved=len(retrieved_chunks),
            passed_chunks=final_passed,
            filtered_chunks=filtered_chunks,
            contradiction_pairs=contradiction_pairs,
            dedup_results=dedup_results,
            relevance_results=relevance_results,
        )

        print(f"[ContextShield] Passed: {len(final_passed)} | Filtered: {len(filtered_chunks)}")

        return {
            "passed_chunks": final_passed,
            "filtered_chunks": filtered_chunks,
            "contradiction_pairs": contradiction_pairs,
            "shield_report": shield_report,
        }

    # ─── Module 1: Duplicate Detection ───────────────────────────────────────

    def _duplicate_detection(
        self, chunks: List[Dict], embeddings: np.ndarray
    ) -> Dict[str, str]:
        """
        Detect semantically duplicate chunks using cosine similarity.
        Keeps only the highest-similarity chunk from each duplicate group.
        """
        n = len(chunks)
        verdicts = {}
        seen_ids = set()

        for i in range(n):
            chunk_id_i = chunks[i].get("chunk_id", f"chunk_{i}")
            if chunk_id_i in seen_ids:
                continue
            verdicts[chunk_id_i] = "unique"

            for j in range(i + 1, n):
                chunk_id_j = chunks[j].get("chunk_id", f"chunk_{j}")
                if chunk_id_j in seen_ids:
                    continue

                # Compute cosine similarity
                sim = float(np.dot(embeddings[i], embeddings[j]))

                if sim >= config.DUPLICATE_THRESHOLD:
                    # Mark the lower-relevance chunk as duplicate
                    score_i = chunks[i].get("similarity_score", 0)
                    score_j = chunks[j].get("similarity_score", 0)

                    if score_i >= score_j:
                        verdicts[chunk_id_j] = "duplicate"
                        seen_ids.add(chunk_id_j)
                    else:
                        verdicts[chunk_id_i] = "duplicate"
                        seen_ids.add(chunk_id_i)
                        break  # chunk_i is marked, stop checking it

        return verdicts

    # ─── Module 2: Relevance Validation ──────────────────────────────────────

    def _relevance_validation(
        self,
        chunks: List[Dict],
        chunk_embeddings: np.ndarray,
        query_embedding: np.ndarray,
    ) -> Dict[str, float]:
        """
        Compute relevance score for each chunk vs the query.
        Uses cosine similarity between chunk embedding and query embedding.
        """
        relevance_scores = {}
        similarities = self.embedding_engine.batch_cosine_similarity(
            query_embedding, chunk_embeddings
        )

        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            # Use max of ChromaDB score and recomputed score
            chroma_score = chunk.get("similarity_score", 0)
            computed_score = float(max(0, similarities[i]))
            relevance_scores[chunk_id] = max(chroma_score, computed_score)

        return relevance_scores

    # ─── Module 3: Noise Filtering ────────────────────────────────────────────

    def _noise_filtering(self, chunks: List[Dict]) -> Dict[str, bool]:
        """
        Detect noisy, incoherent, or low-information chunks.
        Checks: text length, symbol ratio, coherence heuristics.
        """
        noise_verdicts = {}

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", f"chunk_0")
            text = chunk.get("text", "")
            is_noise = False

            # Too short
            if len(text.strip()) < 80:
                is_noise = True

            # High symbol/number ratio (scanned text artifact)
            elif self._symbol_ratio(text) > 0.4:
                is_noise = True

            # Mostly numbers (tables, page numbers extracted incorrectly)
            elif self._number_ratio(text) > 0.6:
                is_noise = True

            # Repetitive content
            elif self._is_repetitive(text):
                is_noise = True

            noise_verdicts[chunk_id] = is_noise

        return noise_verdicts

    def _symbol_ratio(self, text: str) -> float:
        """Ratio of non-alphanumeric, non-space characters."""
        if not text:
            return 1.0
        symbol_count = len(re.findall(r"[^a-zA-Z0-9\s.,;:!?'\"-]", text))
        return symbol_count / len(text)

    def _number_ratio(self, text: str) -> float:
        """Ratio of digit characters."""
        if not text:
            return 1.0
        digit_count = sum(1 for c in text if c.isdigit())
        return digit_count / len(text)

    def _is_repetitive(self, text: str) -> bool:
        """Check if text has excessive repetition."""
        words = text.lower().split()
        if len(words) < 10:
            return False
        unique_ratio = len(set(words)) / len(words)
        return unique_ratio < 0.3  # Less than 30% unique words

    # ─── Module 4: Contradiction Analysis ────────────────────────────────────

    def _contradiction_analysis(
        self, chunks: List[Dict], embeddings: np.ndarray
    ) -> List[Dict]:
        """
        Detect potentially contradictory chunks.
        Chunks that are semantically similar (same topic) but have
        high textual divergence may contain contradictions.
        """
        contradiction_pairs = []
        n = len(chunks)

        for i in range(n):
            for j in range(i + 1, n):
                # Chunks must be from different sources to contradict
                if chunks[i].get("source") == chunks[j].get("source"):
                    continue

                # Semantic similarity (same topic?)
                semantic_sim = float(np.dot(embeddings[i], embeddings[j]))

                # High semantic similarity (same topic) but different content
                if 0.60 <= semantic_sim <= 0.88:
                    # Check for explicit numerical contradictions
                    has_num_conflict = self._detect_numerical_conflict(
                        chunks[i]["text"], chunks[j]["text"]
                    )

                    # Check for negation patterns
                    has_negation = self._detect_negation_conflict(
                        chunks[i]["text"], chunks[j]["text"]
                    )

                    if has_num_conflict or has_negation:
                        chunk_id_i = chunks[i].get("chunk_id", f"chunk_{i}")
                        chunk_id_j = chunks[j].get("chunk_id", f"chunk_{j}")
                        contradiction_pairs.append({
                            "chunk_ids": [chunk_id_i, chunk_id_j],
                            "similarity": round(semantic_sim, 3),
                            "type": "numerical" if has_num_conflict else "negation",
                            "sources": [
                                chunks[i].get("source", "unknown"),
                                chunks[j].get("source", "unknown"),
                            ],
                        })

        return contradiction_pairs

    def _detect_numerical_conflict(self, text1: str, text2: str) -> bool:
        """Check if two texts mention different numbers for similar contexts."""
        numbers1 = set(re.findall(r"\b\d+(?:\.\d+)?(?:%|million|billion|thousand)?\b", text1.lower()))
        numbers2 = set(re.findall(r"\b\d+(?:\.\d+)?(?:%|million|billion|thousand)?\b", text2.lower()))
        # Both have numbers but they differ significantly
        if numbers1 and numbers2 and not numbers1.intersection(numbers2):
            return len(numbers1) >= 1 and len(numbers2) >= 1
        return False

    def _detect_negation_conflict(self, text1: str, text2: str) -> bool:
        """Detect basic negation patterns suggesting contradiction."""
        negation_words = ["not", "never", "no", "cannot", "isn't", "aren't", "doesn't"]
        has_negation1 = any(f" {n} " in f" {text1.lower()} " for n in negation_words)
        has_negation2 = any(f" {n} " in f" {text2.lower()} " for n in negation_words)
        # One has negation, one doesn't — potential contradiction
        return has_negation1 != has_negation2

    # ─── Module 5: Source Reliability Scoring ────────────────────────────────

    def _source_reliability_scoring(self, chunks: List[Dict]) -> Dict[str, int]:
        """
        Score each chunk's source for reliability/credibility.
        Research papers > Textbooks > Wikipedia > Blogs.
        """
        scores = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            source_type = chunk.get("source_type", "unknown").lower()
            base_score = config.SOURCE_RELIABILITY_SCORES.get(
                source_type,
                config.SOURCE_RELIABILITY_SCORES["unknown"]
            )
            scores[chunk_id] = base_score
        return scores

    # ─── Module 6: Freshness Scoring ─────────────────────────────────────────

    def _freshness_scoring(self, chunks: List[Dict]) -> Dict[str, float]:
        """
        Score each chunk based on how recent the source document is.
        Older documents get penalized, especially for fast-evolving topics.
        """
        scores = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            year = int(chunk.get("year", self.current_year))
            age = self.current_year - year

            if age <= 0:
                score = 100.0
            elif age <= 1:
                score = 95.0
            elif age <= 2:
                score = 88.0
            elif age <= 3:
                score = 80.0
            elif age <= 5:
                score = 70.0
            elif age <= 8:
                score = 58.0
            elif age <= 10:
                score = 45.0
            else:
                score = max(20.0, 45.0 - (age - 10) * 2.5)

            scores[chunk_id] = round(score, 1)
        return scores

    # ─── Report Generation ────────────────────────────────────────────────────

    def _generate_shield_report(
        self,
        query: str,
        total_retrieved: int,
        passed_chunks: List[Dict],
        filtered_chunks: List[Dict],
        contradiction_pairs: List[Dict],
        dedup_results: Dict,
        relevance_results: Dict,
    ) -> Dict:
        """Generate a detailed report of the shield's decisions."""
        filter_reasons = {}
        for chunk in filtered_chunks:
            reason = chunk.get("shield_verdict", "unknown")
            filter_reasons[reason] = filter_reasons.get(reason, 0) + 1

        duplicates_removed = filter_reasons.get(ShieldVerdict.FILTERED_DUPLICATE, 0)
        irrelevant_removed = filter_reasons.get(ShieldVerdict.FILTERED_IRRELEVANT, 0)
        noise_removed = filter_reasons.get(ShieldVerdict.FILTERED_NOISE, 0)
        contradictions_found = len(contradiction_pairs)

        avg_relevance = (
            sum(c["relevance_score"] for c in passed_chunks) / len(passed_chunks)
            if passed_chunks else 0
        )

        return {
            "query": query,
            "total_retrieved": total_retrieved,
            "total_passed": len(passed_chunks),
            "total_filtered": len(filtered_chunks),
            "pass_rate": round(len(passed_chunks) / max(1, total_retrieved) * 100, 1),
            "duplicates_removed": duplicates_removed,
            "irrelevant_removed": irrelevant_removed,
            "noise_removed": noise_removed,
            "contradictions_found": contradictions_found,
            "contradiction_pairs": contradiction_pairs,
            "avg_relevance_score": round(avg_relevance, 4),
            "sources_passed": list(set(c.get("source", "?") for c in passed_chunks)),
            "sources_filtered": list(set(c.get("source", "?") for c in filtered_chunks)),
        }

    def _empty_report(self) -> Dict:
        return {
            "query": "",
            "total_retrieved": 0,
            "total_passed": 0,
            "total_filtered": 0,
            "pass_rate": 0,
            "duplicates_removed": 0,
            "irrelevant_removed": 0,
            "noise_removed": 0,
            "contradictions_found": 0,
            "contradiction_pairs": [],
            "avg_relevance_score": 0,
            "sources_passed": [],
            "sources_filtered": [],
        }
