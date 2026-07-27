"""
Validation suite for the 5 critical IEEE evaluation fixes.

Run with:
    cd e:/fyp/backend
    pytest tests/test_eval_fixes.py -v

Each test class maps to one fix. All tests must pass before running benchmarks.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(content: str = "text", **meta) -> Document:
    return Document(page_content=content, metadata=meta)


# ===========================================================================
# Fix 1 — CQS removed from QueryResponse
# ===========================================================================

class TestFix1_CQSRemoved:

    def test_query_response_has_no_cqs_field(self):
        """QueryResponse must not contain a cqs field."""
        from app.api.query import QueryResponse
        assert not hasattr(QueryResponse.model_fields, "cqs"), (
            "cqs field still present in QueryResponse. "
            "CQS = TRRI + 0.05 is mathematically dependent and must be removed."
        )

    def test_query_response_has_trri_field(self):
        """TRRI must still be present as the primary reliability score."""
        from app.api.query import QueryResponse
        assert "trri" in QueryResponse.model_fields

    def test_query_py_source_has_no_cqs_assignment(self):
        """Verify no cqs = ... assignment remains in query.py source."""
        import inspect
        import app.api.query as query_module
        source = inspect.getsource(query_module)
        assert "cqs = " not in source, (
            "cqs assignment still found in query.py source code."
        )


# ===========================================================================
# Fix 2 — No silent predictor fallback
# ===========================================================================

class TestFix2_NoSilentPredictorFallback:

    def test_model_not_trained_error_exists(self):
        """ModelNotTrainedError must be importable."""
        from app.services.predictor.inference import ModelNotTrainedError
        assert issubclass(ModelNotTrainedError, RuntimeError)

    def test_predict_raises_when_no_model(self):
        """predict() must raise ModelNotTrainedError when no model file exists."""
        from app.services.predictor.inference import PredictorEngine, ModelNotTrainedError
        engine = PredictorEngine()
        # Patch loader to simulate missing model
        engine.loader.load_model = MagicMock(
            side_effect=FileNotFoundError("No models found in registry.")
        )
        with pytest.raises(ModelNotTrainedError) as exc_info:
            engine.predict({"temporal_freshness": 0.8, "temporal_availability": 1.0,
                            "source_credibility": 0.9, "evidence_consistency": 0.7,
                            "evidence_sufficiency": 0.85})
        assert "train" in str(exc_info.value).lower(), (
            "Error message must instruct the user to train the model."
        )

    def test_predict_does_not_return_05_on_failure(self):
        """predict() must never silently return 0.5 when the model is missing."""
        from app.services.predictor.inference import PredictorEngine, ModelNotTrainedError
        engine = PredictorEngine()
        engine.loader.load_model = MagicMock(
            side_effect=FileNotFoundError("No models found.")
        )
        with pytest.raises(ModelNotTrainedError):
            engine.predict({"temporal_freshness": 0.5, "temporal_availability": 0.5,
                            "source_credibility": 0.5, "evidence_consistency": 0.5,
                            "evidence_sufficiency": 0.5})

    def test_inference_source_has_no_mean_fallback(self):
        """Verify np.mean fallback is not present in inference.py source."""
        import inspect
        import app.services.predictor.inference as mod
        source = inspect.getsource(mod)
        assert "np.mean(features_array)" not in source, (
            "np.mean fallback still present in inference.py."
        )

    def test_inference_source_has_no_05_fallback(self):
        """Verify safe_trri = 0.5 fallback is not present in inference.py source."""
        import inspect
        import app.services.predictor.inference as mod
        source = inspect.getsource(mod)
        assert "safe_trri = 0.5" not in source, (
            "safe_trri = 0.5 fallback still present in inference.py."
        )


# ===========================================================================
# Fix 3 — ChromaDB isolation in evaluation runners
# ===========================================================================

class TestFix3_ChromaDBIsolation:

    def test_ragguard_runner_uses_isolated_collection(self):
        """RAGGuardTRRunner must use a per-sample collection, not ragguard_docs."""
        from evaluation.runners.ragguard_tr_runner import _collection_name
        name = _collection_name("sample_abc_123")
        assert name.startswith("eval_rg_"), (
            f"Collection name '{name}' does not use eval_rg_ prefix."
        )
        assert "ragguard_docs" not in name

    def test_baseline_runner_uses_isolated_collection(self):
        """BaselineRAGRunner must use a per-sample collection, not ragguard_docs."""
        from evaluation.runners.baseline_runner import _collection_name
        name = _collection_name("sample_abc_123")
        assert name.startswith("eval_bl_"), (
            f"Collection name '{name}' does not use eval_bl_ prefix."
        )
        assert "ragguard_docs" not in name

    def test_collection_names_are_different_per_sample(self):
        """Different sample IDs must produce different collection names."""
        from evaluation.runners.ragguard_tr_runner import _collection_name
        assert _collection_name("sample_001") != _collection_name("sample_002")

    def test_collection_name_max_length(self):
        """Collection names must not exceed ChromaDB's 63-character limit."""
        from evaluation.runners.ragguard_tr_runner import _collection_name
        long_id = "a" * 200
        assert len(_collection_name(long_id)) <= 63

    def test_rg_and_bl_collections_are_different(self):
        """RAGGuard-TR and Baseline must use different collection names for same sample."""
        from evaluation.runners.ragguard_tr_runner import _collection_name as rg_name
        from evaluation.runners.baseline_runner import _collection_name as bl_name
        sid = "sample_xyz"
        assert rg_name(sid) != bl_name(sid), (
            "RAGGuard-TR and Baseline share the same collection name — "
            "they would contaminate each other."
        )

    def test_runner_has_delete_collection_method(self):
        """Both runners must implement _delete_collection for cleanup."""
        from evaluation.runners.ragguard_tr_runner import RAGGuardTRRunner
        from evaluation.runners.baseline_runner import BaselineRAGRunner
        assert hasattr(RAGGuardTRRunner, "_delete_collection")
        assert hasattr(BaselineRAGRunner, "_delete_collection")

    def test_runner_source_uses_finally_for_cleanup(self):
        """Collection deletion must be in a finally block to run even on failure."""
        import inspect
        from evaluation.runners import ragguard_tr_runner, baseline_runner
        for mod in (ragguard_tr_runner, baseline_runner):
            source = inspect.getsource(mod)
            assert "finally:" in source, (
                f"{mod.__name__} does not use finally: for collection cleanup."
            )


# ===========================================================================
# Fix 4 — None propagation for failed RRFE extractors
# ===========================================================================

class TestFix4_NullFeaturePropagation:

    def test_feature_result_score_can_be_none(self):
        """FeatureResult must accept score=None."""
        from app.services.rrfe.models import FeatureResult
        fr = FeatureResult(
            score=None,
            confidence=0.0,
            reason="Feature extraction failed",
            evidence_source="Unavailable",
        )
        assert fr.score is None

    def test_registry_fallback_uses_none_not_05(self):
        """Registry _FALLBACK must have score=None, not 0.5."""
        from app.services.rrfe.registry import _FALLBACK
        assert _FALLBACK.score is None, (
            f"_FALLBACK.score={_FALLBACK.score}. Must be None, not 0.5."
        )

    def test_registry_exception_fallback_uses_none(self):
        """When an extractor raises, the registry must store score=None."""
        from app.services.rrfe.registry import FeatureRegistry
        from app.services.rrfe.core.base_extractor import BaseFeatureExtractor
        from app.services.rrfe.models import FeatureResult

        class BrokenExtractor(BaseFeatureExtractor):
            @property
            def feature_name(self): return "temporal_freshness"
            def extract(self, query, docs): raise RuntimeError("simulated failure")

        registry = FeatureRegistry()
        # Replace first extractor with broken one
        registry._extractors[0] = BrokenExtractor()
        result = registry.execute_all("test query", [_doc("some text")])
        assert result.explanations["temporal_freshness"].score is None, (
            "Failed extractor must produce score=None, not 0.5."
        )

    def test_missing_features_logged_in_metadata(self):
        """Execution metadata must list features with score=None."""
        from app.services.rrfe.registry import FeatureRegistry
        from app.services.rrfe.core.base_extractor import BaseFeatureExtractor

        class NullExtractor(BaseFeatureExtractor):
            @property
            def feature_name(self): return "source_credibility"
            def extract(self, query, docs): raise RuntimeError("forced null")

        registry = FeatureRegistry()
        registry._extractors[2] = NullExtractor()
        result = registry.execute_all("q", [_doc("text")])
        assert "missing_feature_scores" in result.execution_metadata
        assert "source_credibility" in result.execution_metadata["missing_feature_scores"]

    def test_preprocessor_raises_on_none_feature(self):
        """FeaturePreprocessor must raise MissingFeatureError when any score is None."""
        from app.services.predictor.feature_preprocessor import (
            FeaturePreprocessor, MissingFeatureError
        )
        preprocessor = FeaturePreprocessor()
        features_with_none = {
            "temporal_freshness": None,   # missing
            "temporal_availability": 1.0,
            "source_credibility": 0.9,
            "evidence_consistency": 0.7,
            "evidence_sufficiency": 0.8,
        }
        with pytest.raises(MissingFeatureError) as exc_info:
            preprocessor.transform(features_with_none)
        assert "temporal_freshness" in str(exc_info.value)

    def test_preprocessor_does_not_substitute_05(self):
        """FeaturePreprocessor source must not contain .get(name, 0.5)."""
        import inspect
        from app.services.predictor import feature_preprocessor as mod
        source = inspect.getsource(mod)
        assert "0.5)" not in source, (
            "FeaturePreprocessor still contains a 0.5 default substitution."
        )


# ===========================================================================
# Fix 5 — Ground truth weights are configurable and logged
# ===========================================================================

class TestFix5_GroundTruthWeights:

    def test_default_weights_are_documented(self):
        """DEFAULT_RRT_WEIGHTS must be importable and contain the two primary metrics."""
        from app.services.dataset_generator.ground_truth_builder import DEFAULT_RRT_WEIGHTS
        assert "ragas_context_precision" in DEFAULT_RRT_WEIGHTS
        assert "deepeval_faithfulness" in DEFAULT_RRT_WEIGHTS

    def test_weights_sum_to_one_excluding_manual(self):
        """Primary weights (excluding manual_expert_score) must sum to 1.0."""
        from app.services.dataset_generator.ground_truth_builder import DEFAULT_RRT_WEIGHTS
        primary = {k: v for k, v in DEFAULT_RRT_WEIGHTS.items() if k != "manual_expert_score"}
        total = sum(primary.values())
        assert abs(total - 1.0) < 1e-9, (
            f"Primary RRT weights sum to {total}, expected 1.0."
        )

    def test_custom_weights_accepted(self):
        """GroundTruthBuilder must accept custom weights via constructor."""
        from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
        custom = {"ragas_context_precision": 0.7, "deepeval_faithfulness": 0.3}
        builder = GroundTruthBuilder(weights=custom)
        assert builder.weights["ragas_context_precision"] == 0.7

    def test_rrt_computed_with_custom_weights(self):
        """RRT value must change when custom weights are provided."""
        from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
        metrics = {"ragas_context_precision": 0.8, "deepeval_faithfulness": 0.4}
        default_builder = GroundTruthBuilder()
        custom_builder = GroundTruthBuilder(
            weights={"ragas_context_precision": 0.9, "deepeval_faithfulness": 0.1}
        )
        r_default = default_builder.build_rrt(metrics)
        r_custom = custom_builder.build_rrt(metrics)
        assert r_default.rrt != r_custom.rrt, (
            "Custom weights had no effect on RRT computation."
        )

    def test_weights_logged_on_init(self, caplog):
        """GroundTruthBuilder must log weights at construction time."""
        import logging
        from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
        with caplog.at_level(logging.INFO, logger="ragguard.ground_truth"):
            GroundTruthBuilder()
        assert any("weights" in record.message for record in caplog.records), (
            "GroundTruthBuilder did not log weights at initialisation."
        )

    def test_rrt_debug_log_contains_weights(self, caplog):
        """build_rrt must log the weights used for each computation."""
        import logging
        from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
        builder = GroundTruthBuilder()
        with caplog.at_level(logging.DEBUG, logger="ragguard.ground_truth"):
            builder.build_rrt({"ragas_context_precision": 0.8, "deepeval_faithfulness": 0.6})
        assert any("weights" in record.message for record in caplog.records), (
            "build_rrt did not log the weights used."
        )

    def test_unknown_metrics_excluded_not_weighted_one(self):
        """Metrics not in the weights dict must be excluded (weight=0), not given weight=1."""
        from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
        builder = GroundTruthBuilder()
        # Include an unknown metric with a very high score
        metrics = {
            "ragas_context_precision": 0.5,
            "deepeval_faithfulness": 0.5,
            "some_unknown_metric": 1.0,   # must be excluded
        }
        result = builder.build_rrt(metrics)
        # RRT must equal 0.5 (both known metrics = 0.5, unknown excluded)
        assert result.rrt == pytest.approx(0.5, abs=0.001), (
            f"Unknown metric was not excluded. RRT={result.rrt}"
        )


# ===========================================================================
# Validation summary
# ===========================================================================

class TestValidationSummary:
    """Meta-test: confirms all fix modules are importable without errors."""

    def test_all_fix_modules_importable(self):
        import app.api.query
        import app.services.predictor.inference
        import app.services.predictor.feature_preprocessor
        import app.services.rrfe.models
        import app.services.rrfe.registry
        import app.services.dataset_generator.ground_truth_builder
        import evaluation.runners.ragguard_tr_runner
        import evaluation.runners.baseline_runner

    def test_no_cqs_anywhere_in_pipeline(self):
        """Confirm cqs does not appear as a computed value in any pipeline module."""
        import inspect
        import app.api.query as q
        import app.services.predictor.inference as inf
        for mod, name in [(q, "query.py"), (inf, "inference.py")]:
            src = inspect.getsource(mod)
            assert "cqs = " not in src, f"cqs assignment found in {name}"
