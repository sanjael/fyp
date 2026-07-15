import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, ForeignKey, 
    Numeric, BigInt, Date, SmallInteger, JSON, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='user')
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    profile = relationship("Profile", back_populates="user", uselist=False)
    collections = relationship("Collection", back_populates="user")
    experiments = relationship("Experiment", back_populates="user")
    settings = relationship("Setting", back_populates="user", uselist=False)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(Text)
    ip_address = Column(INET)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_name = Column(String(255))
    organization = Column(String(255))
    department = Column(String(255))
    research_area = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")

class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    chroma_collection_name = Column(String(255), nullable=False, unique=True)
    
    trri_weight_tf = Column(Numeric(4,3), nullable=False, default=0.350)
    trri_weight_sc = Column(Numeric(4,3), nullable=False, default=0.250)
    trri_weight_src = Column(Numeric(4,3), nullable=False, default=0.200)
    trri_weight_cc = Column(Numeric(4,3), nullable=False, default=0.200)
    trri_threshold_high = Column(Numeric(4,3), nullable=False, default=0.700)
    trri_threshold_medium = Column(Numeric(4,3), nullable=False, default=0.450)
    
    default_top_k = Column(SmallInteger, nullable=False, default=10)
    chunk_size = Column(SmallInteger, nullable=False, default=512)
    chunk_overlap = Column(SmallInteger, nullable=False, default=64)
    half_life_days = Column(Numeric(6,1), nullable=False, default=180.0)
    
    document_count = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)
    total_size_bytes = Column(BigInt, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    original_filename = Column(String(512), nullable=False)
    stored_filename = Column(String(512), nullable=False)
    file_size_bytes = Column(BigInt, nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False)
    
    title = Column(Text)
    author = Column(Text)
    document_type = Column(String(50), nullable=False, default='unknown')
    document_date = Column(Date)
    doi = Column(String(128))
    isbn = Column(String(32))
    source_url = Column(Text)
    language = Column(String(10), default='en')
    
    status = Column(String(50), nullable=False, default='pending')
    page_count = Column(Integer)
    chunk_count = Column(Integer)
    error_message = Column(Text)
    
    celery_task_id = Column(String(255))
    ingestion_started_at = Column(DateTime(timezone=True))
    ingestion_completed_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    page_number = Column(Integer)
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    chroma_chunk_id = Column(String(255), nullable=False, unique=True)
    embedding_model = Column(String(128), nullable=False)
    embedding_dim = Column(SmallInteger, nullable=False)
    
    document_date = Column(Date)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    age_at_ingestion_days = Column(Integer)
    
    estimated_credibility = Column(Numeric(4,3))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="chunks")

class Setting(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    generation_model = Column(String(128), nullable=False, default='llama3.1:8b-instruct-q4_K_M')
    embedding_model = Column(String(128), nullable=False, default='nomic-embed-text')
    temperature = Column(Numeric(3,2), nullable=False, default=0.10)
    max_tokens = Column(Integer, nullable=False, default=2048)
    
    theme = Column(String(16), nullable=False, default='dark')
    default_top_k = Column(SmallInteger, nullable=False, default=10)
    show_trri_details = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="settings")

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    experiment_key = Column(String(64), nullable=False)
    config = Column(JSONB, nullable=False, server_default='{}')
    status = Column(String(50), nullable=False, default='created')
    celery_task_id = Column(String(255))
    progress_pct = Column(Numeric(5,2), default=0.0)
    current_step = Column(Text)
    error_message = Column(Text)
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="experiments")

# More tables like evaluations, benchmark_runs, chat_sessions can be added similarly.
