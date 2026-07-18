from pydantic_settings import BaseSettings

class RRFEConfig(BaseSettings):
    DEFAULT_TEMPORAL_SCORE: float = 0.5
    DEFAULT_CREDIBILITY_SCORE: float = 0.5
    DEFAULT_CONSISTENCY_SCORE: float = 0.5
    DEFAULT_SUFFICIENCY_SCORE: float = 0.5
    
    # Embedding based thresholds or constants if needed
    EMBEDDING_BATCH_SIZE: int = 32

config = RRFEConfig()
