from pydantic_settings import BaseSettings


class RRFEConfig(BaseSettings):
    # Temporal Freshness
    FRESHNESS_HALF_LIFE_DAYS: float = 180.0

    # Source Credibility defaults by document type
    EMBEDDING_BATCH_SIZE: int = 32

    # Consistency
    CONSISTENCY_VARIANCE_PENALTY_THRESHOLD: float = 0.3

    # Sufficiency weights
    SUFFICIENCY_MAX_WEIGHT: float = 0.6
    SUFFICIENCY_MEAN_WEIGHT: float = 0.4


config = RRFEConfig()
