"""
Domain Exceptions for RAGGuard-TR System.
Provides a clear exception hierarchy for precise error handling across
services, extractors, predictors, evaluators, and API routes.
"""

class RAGGuardBaseException(Exception):
    """Base exception for all RAGGuard-TR domain errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(RAGGuardBaseException):
    """Raised when environment variables or settings are missing/invalid."""
    pass


class FeatureExtractionError(RAGGuardBaseException):
    """Raised when RRFE feature extraction fails due to invalid state or processing errors."""
    pass


class EvaluationError(RAGGuardBaseException):
    """Raised when RAGAS or DeepEval evaluation metrics execution fails."""
    pass


class RetrievalError(RAGGuardBaseException):
    """Raised when vector store or document retrieval fails."""
    pass


class LLMError(RAGGuardBaseException):
    """Raised when LLM invocation or JSON response parsing fails."""
    pass


class PredictionError(RAGGuardBaseException):
    """Raised when TRRI predictor inference or feature validation fails."""
    pass
