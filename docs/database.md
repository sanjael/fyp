# RAGGuard-TR: Database Design Document

**Document Version:** 1.0.0  
**Status:** Approved  
**Authors:** Capstone Research Team  
**Last Updated:** 2026-06-16  
**Classification:** Internal Technical Reference  

---

## Table of Contents

1. [Database Overview](#1-database-overview)
2. [PostgreSQL Schema — Production DDL](#2-postgresql-schema--production-ddl)
3. [Index Strategy](#3-index-strategy)
4. [Constraint Summary](#4-constraint-summary)
5. [Optimization Recommendations](#5-optimization-recommendations)
6. [ChromaDB Collection Design](#6-chromadb-collection-design)
7. [Metadata Schemas (JSON)](#7-metadata-schemas-json)
8. [Sample Data Examples](#8-sample-data-examples)

---

## 1. Database Overview

RAGGuard-TR uses two database systems:

| System | Role | Engine |
|--------|------|--------|
| **PostgreSQL 15** | All relational data: users, sessions, documents, experiments, evaluations, audit | `asyncpg` driver via SQLAlchemy 2.0 async |
| **ChromaDB** | Vector embeddings + chunk metadata for semantic search | Python client (persistent mode) |

### Entity Relationship Summary

```
users ──< profiles
users ──< collections ──< documents ──< document_chunks
users ──< chat_sessions ──< chat_messages
users ──< settings
users ──< experiments ──< evaluations
                       ──< benchmark_runs
                       ──< ablation_results
users ──< audit_logs
collections ──< reliability_scores
```

---

## 2. PostgreSQL Schema — Production DDL

```sql
-- ============================================================
-- RAGGUARD-TR: Production PostgreSQL DDL
-- PostgreSQL 15
-- Generated: 2026-06-16
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================
-- ENUMERATIONS
-- ============================================================

CREATE TYPE user_role AS ENUM ('admin', 'researcher', 'user');
CREATE TYPE document_status AS ENUM (
    'pending',
    'processing',
    'chunking',
    'embedding',
    'completed',
    'failed'
);
CREATE TYPE document_type AS ENUM (
    'academic_paper',
    'official_report',
    'technical_documentation',
    'news_article',
    'blog_post',
    'social_media',
    'unknown'
);
CREATE TYPE adaptive_decision AS ENUM (
    'PROCEED',
    'EXPAND_RETRIEVAL',
    'REJECT'
);
CREATE TYPE experiment_status AS ENUM (
    'created',
    'running',
    'completed',
    'failed',
    'aborted'
);
CREATE TYPE benchmark_dataset AS ENUM (
    'hotpotqa',
    'natural_questions',
    'triviaqa',
    'timeqa',
    'chronoqa'
);
CREATE TYPE retrieval_strategy AS ENUM (
    'naive_rag',
    'self_rag',
    'crag',
    'adaptive_rag',
    'ragguard_tr'
);
CREATE TYPE ablation_factor AS ENUM (
    'temporal_freshness',
    'semantic_coherence',
    'source_credibility',
    'contextual_completeness',
    'full_trri',
    'no_trri'
);
CREATE TYPE audit_action AS ENUM (
    'user_registered',
    'user_login',
    'user_logout',
    'collection_created',
    'collection_deleted',
    'document_uploaded',
    'document_deleted',
    'experiment_created',
    'experiment_run',
    'benchmark_run',
    'settings_changed'
);

-- ============================================================
-- TABLE: users
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE users IS 'Core user accounts. Soft-delete via deleted_at.';
COMMENT ON COLUMN users.password_hash IS 'bcrypt hash with cost factor 12. Never store plaintext.';

-- ============================================================
-- TABLE: refresh_tokens
-- ============================================================

CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(128) NOT NULL,  -- SHA-256 of raw token
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_agent      TEXT,
    ip_address      INET,

    CONSTRAINT refresh_tokens_hash_unique UNIQUE (token_hash)
);

COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens. Only token_hash stored — raw token sent to client only once.';

-- ============================================================
-- TABLE: profiles
-- ============================================================

CREATE TABLE profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255),
    organization    VARCHAR(255),
    department      VARCHAR(255),
    research_area   VARCHAR(255),
    bio             TEXT,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT profiles_user_unique UNIQUE (user_id)
);

-- ============================================================
-- TABLE: collections
-- ============================================================

CREATE TABLE collections (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                    VARCHAR(128) NOT NULL,
    description             TEXT,
    chroma_collection_name  VARCHAR(255) NOT NULL,  -- ChromaDB collection identifier
    
    -- TRRI Configuration
    trri_weight_tf          NUMERIC(4,3) NOT NULL DEFAULT 0.350,
    trri_weight_sc          NUMERIC(4,3) NOT NULL DEFAULT 0.250,
    trri_weight_src         NUMERIC(4,3) NOT NULL DEFAULT 0.200,
    trri_weight_cc          NUMERIC(4,3) NOT NULL DEFAULT 0.200,
    trri_threshold_high     NUMERIC(4,3) NOT NULL DEFAULT 0.700,
    trri_threshold_medium   NUMERIC(4,3) NOT NULL DEFAULT 0.450,
    
    -- Retrieval Configuration
    default_top_k           SMALLINT NOT NULL DEFAULT 10,
    chunk_size              SMALLINT NOT NULL DEFAULT 512,
    chunk_overlap           SMALLINT NOT NULL DEFAULT 64,
    half_life_days          NUMERIC(6,1) NOT NULL DEFAULT 180.0,
    
    -- Stats (denormalized for performance)
    document_count          INTEGER NOT NULL DEFAULT 0,
    chunk_count             INTEGER NOT NULL DEFAULT 0,
    total_size_bytes        BIGINT NOT NULL DEFAULT 0,
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ,

    CONSTRAINT collections_user_name_unique UNIQUE (user_id, name),
    CONSTRAINT collections_chroma_name_unique UNIQUE (chroma_collection_name),
    CONSTRAINT collections_weights_valid CHECK (
        ABS((trri_weight_tf + trri_weight_sc + trri_weight_src + trri_weight_cc) - 1.0) < 0.001
    ),
    CONSTRAINT collections_thresholds_valid CHECK (
        trri_threshold_high > trri_threshold_medium
        AND trri_threshold_high BETWEEN 0 AND 1
        AND trri_threshold_medium BETWEEN 0 AND 1
    ),
    CONSTRAINT collections_top_k_valid CHECK (default_top_k BETWEEN 1 AND 100),
    CONSTRAINT collections_chunk_size_valid CHECK (chunk_size BETWEEN 128 AND 4096)
);

COMMENT ON TABLE collections IS 'Document collections. Each maps to one ChromaDB collection.';
COMMENT ON COLUMN collections.chroma_collection_name IS 'Format: collection_{uuid}. Must match ChromaDB collection name exactly.';

-- ============================================================
-- TABLE: documents
-- ============================================================

CREATE TABLE documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id       UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id),
    
    -- File Info
    original_filename   VARCHAR(512) NOT NULL,
    stored_filename     VARCHAR(512) NOT NULL,  -- S3 key or local path
    file_size_bytes     BIGINT NOT NULL,
    mime_type           VARCHAR(128) NOT NULL,
    file_hash_sha256    VARCHAR(64) NOT NULL,
    
    -- Document Metadata
    title               TEXT,
    author              TEXT,
    document_type       document_type NOT NULL DEFAULT 'unknown',
    document_date       DATE,                  -- Publication or last-modified date
    doi                 VARCHAR(128),
    isbn                VARCHAR(32),
    source_url          TEXT,
    language            VARCHAR(10) DEFAULT 'en',
    
    -- Processing Status
    status              document_status NOT NULL DEFAULT 'pending',
    page_count          INTEGER,
    chunk_count         INTEGER,
    error_message       TEXT,
    
    -- Ingestion Tracking
    celery_task_id      VARCHAR(255),
    ingestion_started_at TIMESTAMPTZ,
    ingestion_completed_at TIMESTAMPTZ,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT documents_hash_collection_unique UNIQUE (file_hash_sha256, collection_id),
    CONSTRAINT documents_file_size_valid CHECK (file_size_bytes > 0 AND file_size_bytes <= 52428800),
    CONSTRAINT documents_page_count_valid CHECK (page_count IS NULL OR page_count > 0)
);

COMMENT ON TABLE documents IS 'Uploaded source documents. Tracks ingestion status through the async pipeline.';
COMMENT ON COLUMN documents.document_date IS 'The date the document was published or last authoritatively modified. Critical for TRRI temporal freshness computation.';
COMMENT ON COLUMN documents.file_hash_sha256 IS 'SHA-256 of raw file bytes. Prevents duplicate ingestion within same collection.';

-- ============================================================
-- TABLE: document_chunks
-- ============================================================

CREATE TABLE document_chunks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    collection_id       UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    
    -- Chunk Content
    content             TEXT NOT NULL,
    content_hash        VARCHAR(64) NOT NULL,  -- SHA-256 of content
    chunk_index         INTEGER NOT NULL,      -- Position within document
    
    -- Location Metadata
    page_number         INTEGER,
    start_char          INTEGER,
    end_char            INTEGER,
    
    -- Embedding Reference
    chroma_chunk_id     VARCHAR(255) NOT NULL,  -- ID within ChromaDB collection
    embedding_model     VARCHAR(128) NOT NULL,  -- e.g., "nomic-embed-text"
    embedding_dim       SMALLINT NOT NULL,
    
    -- Temporal Metadata
    document_date       DATE,                  -- Inherited from parent document
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    age_at_ingestion_days INTEGER,
    
    -- TRRI Pre-computed Metadata
    estimated_credibility NUMERIC(4,3),        -- Pre-computed SrC component
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT document_chunks_chroma_unique UNIQUE (chroma_chunk_id),
    CONSTRAINT document_chunks_index_unique UNIQUE (document_id, chunk_index),
    CONSTRAINT document_chunks_credibility_range CHECK (
        estimated_credibility IS NULL
        OR estimated_credibility BETWEEN 0 AND 1
    )
);

COMMENT ON TABLE document_chunks IS 'Individual text chunks produced during document ingestion. Mirrors ChromaDB entries for relational queries.';
COMMENT ON COLUMN document_chunks.chroma_chunk_id IS 'Must exactly match the ID used when inserting into ChromaDB. Format: chunk_{uuid}.';

-- ============================================================
-- TABLE: chat_sessions
-- ============================================================

CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    collection_id   UUID REFERENCES collections(id) ON DELETE SET NULL,
    title           VARCHAR(255),
    message_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- ============================================================
-- TABLE: chat_messages
-- ============================================================

CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    role            VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    
    -- Retrieval context (assistant messages only)
    chunk_ids       UUID[],                    -- IDs of document_chunks used
    trri_score      NUMERIC(5,4),              -- Overall TRRI [0,1]
    trri_tf         NUMERIC(5,4),
    trri_sc         NUMERIC(5,4),
    trri_src        NUMERIC(5,4),
    trri_cc         NUMERIC(5,4),
    adaptive_decision adaptive_decision,
    retrieval_rounds SMALLINT DEFAULT 1,
    
    -- Generation metadata
    model           VARCHAR(128),
    tokens_generated INTEGER,
    generation_ms   INTEGER,
    trri_computation_ms INTEGER,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chat_messages_trri_range CHECK (
        trri_score IS NULL OR trri_score BETWEEN 0 AND 1
    )
);

COMMENT ON TABLE chat_messages IS 'Individual messages in chat sessions. TRRI fields populated only for assistant messages.';

-- ============================================================
-- TABLE: settings
-- ============================================================

CREATE TABLE settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- LLM Settings
    generation_model    VARCHAR(128) NOT NULL DEFAULT 'llama3.1:8b-instruct-q4_K_M',
    embedding_model     VARCHAR(128) NOT NULL DEFAULT 'nomic-embed-text',
    temperature         NUMERIC(3,2) NOT NULL DEFAULT 0.10,
    max_tokens          INTEGER NOT NULL DEFAULT 2048,
    
    -- UI Settings
    theme               VARCHAR(16) NOT NULL DEFAULT 'dark',
    default_top_k       SMALLINT NOT NULL DEFAULT 10,
    show_trri_details   BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT settings_user_unique UNIQUE (user_id),
    CONSTRAINT settings_temperature_valid CHECK (temperature BETWEEN 0 AND 2),
    CONSTRAINT settings_max_tokens_valid CHECK (max_tokens BETWEEN 64 AND 8192)
);

-- ============================================================
-- TABLE: experiments
-- ============================================================

CREATE TABLE experiments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    
    -- Identification
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    experiment_key      VARCHAR(64) NOT NULL,  -- Short slug for referencing in paper

    -- Configuration (stored as JSONB for full reproducibility)
    config              JSONB NOT NULL DEFAULT '{}',
    /*
    config schema:
    {
        "retrieval_strategy": "ragguard_tr",
        "dataset": "hotpotqa",
        "split": "test",
        "sample_size": 500,
        "random_seed": 42,
        "top_k": 10,
        "generation_model": "llama3.1:8b-instruct-q4_K_M",
        "embedding_model": "nomic-embed-text",
        "trri_weights": {
            "temporal_freshness": 0.35,
            "semantic_coherence": 0.25,
            "source_credibility": 0.20,
            "contextual_completeness": 0.20
        },
        "trri_thresholds": {
            "high": 0.70,
            "medium": 0.45
        },
        "half_life_days": 180.0,
        "dataset_version": "v1.1",
        "collection_id": "uuid-here"
    }
    */
    
    -- Execution State
    status              experiment_status NOT NULL DEFAULT 'created',
    celery_task_id      VARCHAR(255),
    progress_pct        NUMERIC(5,2) DEFAULT 0.0,
    current_step        TEXT,
    error_message       TEXT,
    
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    duration_seconds    INTEGER,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT experiments_key_user_unique UNIQUE (experiment_key, user_id)
);

COMMENT ON TABLE experiments IS 'Research experiments. config JSONB captures full reproducibility state.';
COMMENT ON COLUMN experiments.experiment_key IS 'Short human-readable key for referencing in papers (e.g., "exp-hotpot-ragguard-v1").';

-- ============================================================
-- TABLE: evaluations
-- ============================================================

CREATE TABLE evaluations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id       UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- RAGAS Metrics
    faithfulness            NUMERIC(6,4),
    answer_relevancy        NUMERIC(6,4),
    context_precision       NUMERIC(6,4),
    context_recall          NUMERIC(6,4),
    
    -- DeepEval Metrics
    hallucination_score     NUMERIC(6,4),   -- DeepEval hallucination metric
    answer_correctness      NUMERIC(6,4),
    
    -- TRRI Calibration Metrics
    ece                     NUMERIC(8,6),   -- Expected Calibration Error
    mce                     NUMERIC(8,6),   -- Maximum Calibration Error
    auc_roc                 NUMERIC(6,4),   -- AUC-ROC of TRRI as hallucination predictor
    brier_score             NUMERIC(8,6),   -- Brier score
    
    -- Reliability Statistics
    mean_trri_score         NUMERIC(5,4),
    median_trri_score       NUMERIC(5,4),
    std_trri_score          NUMERIC(5,4),
    trri_score_distribution JSONB,          -- Histogram data {bins, counts}
    
    -- Adaptive Retrieval Statistics
    proceed_pct             NUMERIC(5,2),
    expand_pct              NUMERIC(5,2),
    reject_pct              NUMERIC(5,2),
    
    -- Sample Information
    n_samples               INTEGER NOT NULL,
    n_hallucinated          INTEGER,        -- If hallucination labels available
    
    -- Calibration Diagram Data
    calibration_diagram     JSONB,          -- {bins: [{lower, upper, confidence, accuracy, count}]}
    
    evaluated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evaluation_duration_s   INTEGER,

    CONSTRAINT evaluations_experiment_unique UNIQUE (experiment_id),
    CONSTRAINT evaluations_faithfulness_range CHECK (
        faithfulness IS NULL OR faithfulness BETWEEN 0 AND 1
    ),
    CONSTRAINT evaluations_ece_range CHECK (
        ece IS NULL OR ece BETWEEN 0 AND 1
    )
);

COMMENT ON TABLE evaluations IS 'Evaluation results for each completed experiment. One row per experiment.';

-- ============================================================
-- TABLE: benchmark_runs
-- ============================================================

CREATE TABLE benchmark_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id       UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Dataset Configuration
    dataset             benchmark_dataset NOT NULL,
    split               VARCHAR(32) NOT NULL DEFAULT 'test',
    sample_size         INTEGER NOT NULL,
    dataset_version     VARCHAR(32),
    
    -- Retrieval Strategy
    strategy            retrieval_strategy NOT NULL,
    
    -- Per-question Results (JSONB array for large result sets)
    results             JSONB,
    /*
    results schema (array):
    [
        {
            "question_id": "hotpot_dev_001",
            "question": "...",
            "gold_answer": "...",
            "generated_answer": "...",
            "retrieved_chunk_ids": ["uuid1", "uuid2"],
            "trri_score": 0.789,
            "trri_tf": 0.820,
            "trri_sc": 0.740,
            "trri_src": 0.880,
            "trri_cc": 0.690,
            "adaptive_decision": "PROCEED",
            "faithfulness": 0.91,
            "answer_relevancy": 0.87,
            "is_hallucinated": false,
            "generation_ms": 1240
        },
        ...
    ]
    */
    
    -- Aggregate Statistics
    total_questions     INTEGER NOT NULL,
    completed_questions INTEGER NOT NULL DEFAULT 0,
    failed_questions    INTEGER NOT NULL DEFAULT 0,
    
    -- Status
    status              experiment_status NOT NULL DEFAULT 'created',
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    duration_seconds    INTEGER,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE benchmark_runs IS 'Individual benchmark dataset runs. Results stored as JSONB for flexibility.';

-- ============================================================
-- TABLE: reliability_scores
-- ============================================================

CREATE TABLE reliability_scores (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id           UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    session_id              UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    experiment_id           UUID REFERENCES experiments(id) ON DELETE SET NULL,
    
    -- Query Context
    query_text              TEXT NOT NULL,
    query_hash              VARCHAR(64) NOT NULL,  -- SHA-256 of normalized query
    
    -- Retrieved Chunks
    retrieved_chunk_ids     UUID[] NOT NULL,
    top_k_requested         SMALLINT NOT NULL,
    retrieval_rounds        SMALLINT NOT NULL DEFAULT 1,
    
    -- TRRI Scores
    trri_score              NUMERIC(5,4) NOT NULL,
    trri_tf                 NUMERIC(5,4) NOT NULL,
    trri_sc                 NUMERIC(5,4) NOT NULL,
    trri_src                NUMERIC(5,4) NOT NULL,
    trri_cc                 NUMERIC(5,4) NOT NULL,
    
    -- Applied Configuration
    applied_weights         JSONB NOT NULL,  -- {tf, sc, src, cc} at time of computation
    applied_thresholds      JSONB NOT NULL,  -- {high, medium}
    adaptive_decision       adaptive_decision NOT NULL,
    
    -- Per-Chunk Scores (for analysis)
    chunk_trri_breakdown    JSONB,
    /*
    chunk_trri_breakdown schema:
    [
        {
            "chunk_id": "uuid",
            "tf_score": 0.82,
            "src_score": 0.90,
            "document_date": "2025-01-15",
            "age_days": 517,
            "similarity": 0.87
        }
    ]
    */
    
    -- Outcome (populated post-evaluation if known)
    is_hallucinated         BOOLEAN,    -- Ground truth label
    faithfulness_score      NUMERIC(5,4),
    
    -- Latency
    computation_ms          INTEGER NOT NULL,
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT reliability_scores_trri_range CHECK (
        trri_score BETWEEN 0 AND 1
        AND trri_tf BETWEEN 0 AND 1
        AND trri_sc BETWEEN 0 AND 1
        AND trri_src BETWEEN 0 AND 1
        AND trri_cc BETWEEN 0 AND 1
    )
);

COMMENT ON TABLE reliability_scores IS 'Per-query TRRI computation results. Core data for calibration analysis and hallucination prediction experiments.';

-- ============================================================
-- TABLE: ablation_results
-- ============================================================

CREATE TABLE ablation_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id       UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Ablation Configuration
    ablated_factor      ablation_factor NOT NULL,
    ablation_config     JSONB NOT NULL,
    /*
    When ablated_factor = 'temporal_freshness', weights become:
    {
        "temporal_freshness": 0.00,  -- factor disabled
        "semantic_coherence": 0.333,
        "source_credibility": 0.333,
        "contextual_completeness": 0.334
    }
    */
    
    -- Results (same schema as evaluations)
    faithfulness            NUMERIC(6,4),
    answer_relevancy        NUMERIC(6,4),
    context_recall          NUMERIC(6,4),
    ece                     NUMERIC(8,6),
    auc_roc                 NUMERIC(6,4),
    mean_trri_score         NUMERIC(5,4),
    n_samples               INTEGER NOT NULL,
    
    -- Comparison to Full TRRI
    delta_faithfulness      NUMERIC(6,4),  -- Δ vs full TRRI run
    delta_auc_roc           NUMERIC(6,4),
    
    -- Statistical Significance vs Full TRRI
    wilcoxon_p_value        NUMERIC(10,8),
    is_significant          BOOLEAN,
    effect_size             NUMERIC(6,4),
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ablation_results IS 'Ablation study results. Each row is one factor-disabled run compared against full TRRI baseline.';

-- ============================================================
-- TABLE: audit_logs
-- ============================================================

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    
    action          audit_action NOT NULL,
    resource_type   VARCHAR(64),     -- e.g., 'collection', 'document', 'experiment'
    resource_id     UUID,
    
    metadata        JSONB DEFAULT '{}',
    
    ip_address      INET,
    user_agent      TEXT,
    request_id      VARCHAR(64),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE audit_logs IS 'Immutable audit trail. Never updated or deleted. Used for security and experiment reproducibility auditing.';
```

---

## 3. Index Strategy

```sql
-- ============================================================
-- INDEXES
-- ============================================================

-- users
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- refresh_tokens
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash) WHERE revoked = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE revoked = FALSE;

-- collections
CREATE INDEX idx_collections_user_id ON collections(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_collections_created_at ON collections(created_at DESC);
CREATE INDEX idx_collections_name_trgm ON collections USING GIN (name gin_trgm_ops);

-- documents
CREATE INDEX idx_documents_collection_id ON documents(collection_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_document_date ON documents(document_date);
CREATE INDEX idx_documents_celery_task ON documents(celery_task_id) WHERE celery_task_id IS NOT NULL;
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);

-- document_chunks
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_collection_id ON document_chunks(collection_id);
CREATE INDEX idx_chunks_chroma_id ON document_chunks(chroma_chunk_id);
CREATE INDEX idx_chunks_document_date ON document_chunks(document_date) WHERE document_date IS NOT NULL;

-- chat_sessions
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_collection_id ON chat_sessions(collection_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- chat_messages
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(session_id, created_at ASC);
CREATE INDEX idx_chat_messages_trri ON chat_messages(trri_score) WHERE trri_score IS NOT NULL;

-- experiments
CREATE INDEX idx_experiments_user_id ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_key ON experiments(experiment_key);
CREATE INDEX idx_experiments_config ON experiments USING GIN (config jsonb_path_ops);
CREATE INDEX idx_experiments_created_at ON experiments(created_at DESC);

-- evaluations
CREATE INDEX idx_evaluations_experiment_id ON evaluations(experiment_id);
CREATE INDEX idx_evaluations_faithfulness ON evaluations(faithfulness DESC) WHERE faithfulness IS NOT NULL;
CREATE INDEX idx_evaluations_auc_roc ON evaluations(auc_roc DESC) WHERE auc_roc IS NOT NULL;

-- benchmark_runs
CREATE INDEX idx_benchmark_runs_experiment_id ON benchmark_runs(experiment_id);
CREATE INDEX idx_benchmark_runs_dataset ON benchmark_runs(dataset);
CREATE INDEX idx_benchmark_runs_strategy ON benchmark_runs(strategy);
CREATE INDEX idx_benchmark_runs_status ON benchmark_runs(status);

-- reliability_scores (high-volume — optimized for analytics queries)
CREATE INDEX idx_reliability_collection_id ON reliability_scores(collection_id);
CREATE INDEX idx_reliability_experiment_id ON reliability_scores(experiment_id) WHERE experiment_id IS NOT NULL;
CREATE INDEX idx_reliability_trri_score ON reliability_scores(trri_score);
CREATE INDEX idx_reliability_adaptive_decision ON reliability_scores(adaptive_decision);
CREATE INDEX idx_reliability_created_at ON reliability_scores(created_at DESC);
CREATE INDEX idx_reliability_collection_date ON reliability_scores(collection_id, created_at DESC);
-- Partial index for hallucination analysis (labeled samples only)
CREATE INDEX idx_reliability_hallucination ON reliability_scores(trri_score, is_hallucinated)
    WHERE is_hallucinated IS NOT NULL;

-- ablation_results
CREATE INDEX idx_ablation_experiment_id ON ablation_results(experiment_id);
CREATE INDEX idx_ablation_factor ON ablation_results(ablated_factor);

-- audit_logs
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
```

---

## 4. Constraint Summary

| Table | Constraint | Type | Description |
|-------|-----------|------|-------------|
| `users` | `email_format` | CHECK | RFC-compliant email pattern |
| `users` | `email_unique` | UNIQUE | No duplicate accounts |
| `collections` | `weights_valid` | CHECK | TRRI weights must sum to 1.0 (±0.001) |
| `collections` | `thresholds_valid` | CHECK | high threshold > medium threshold |
| `collections` | `user_name_unique` | UNIQUE | No duplicate collection names per user |
| `documents` | `hash_collection_unique` | UNIQUE | No duplicate files per collection |
| `documents` | `file_size_valid` | CHECK | 0 < size ≤ 50 MB |
| `document_chunks` | `chroma_unique` | UNIQUE | ChromaDB ID uniqueness |
| `document_chunks` | `index_unique` | UNIQUE | Chunk ordering per document |
| `chat_messages` | `role_valid` | CHECK | Role in {user, assistant, system} |
| `chat_messages` | `trri_range` | CHECK | TRRI score ∈ [0, 1] |
| `reliability_scores` | `trri_range` | CHECK | All TRRI factors ∈ [0, 1] |
| `evaluations` | `experiment_unique` | UNIQUE | One evaluation row per experiment |
| `evaluations` | `faithfulness_range` | CHECK | Faithfulness ∈ [0, 1] |

---

## 5. Optimization Recommendations

### 5.1 Partitioning

For deployments with > 1M `reliability_scores` rows, partition by month:

```sql
CREATE TABLE reliability_scores (
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE reliability_scores_2026_01
    PARTITION OF reliability_scores
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE reliability_scores_2026_02
    PARTITION OF reliability_scores
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- etc.
```

### 5.2 `benchmark_runs.results` Handling

For benchmarks with > 10,000 questions, JSONB column becomes unwieldy. Split into a dedicated `benchmark_qa_results` table:

```sql
-- Optional: materialized for large benchmark runs
CREATE TABLE benchmark_qa_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_run_id    UUID NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    question_id         VARCHAR(128) NOT NULL,
    question            TEXT NOT NULL,
    gold_answer         TEXT,
    generated_answer    TEXT,
    trri_score          NUMERIC(5,4),
    faithfulness        NUMERIC(5,4),
    is_hallucinated     BOOLEAN,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT benchmark_qa_unique UNIQUE (benchmark_run_id, question_id)
);
CREATE INDEX idx_bench_qa_run_id ON benchmark_qa_results(benchmark_run_id);
CREATE INDEX idx_bench_qa_trri ON benchmark_qa_results(trri_score);
```

### 5.3 Connection Pool Sizing

```
Pool size = (number of API workers × 2) + (number of Celery workers × 1)
= (3 API replicas × 2) + (4 workers × 1) = 10 connections
Max overflow = 20
```

### 5.4 Vacuum and Analyze

Enable autovacuum tuning for high-write tables:
```sql
ALTER TABLE reliability_scores SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE audit_logs SET (
    autovacuum_vacuum_scale_factor = 0.10
);
```

---

## 6. ChromaDB Collection Design

### 6.1 Collection Naming Convention

```
collection_{collection_uuid_without_dashes}
Example: collection_6ba7b8109dad11d180b400c04fd430c8
```

### 6.2 Document (Chunk) Schema

Each document in ChromaDB represents one text chunk:

```python
# ChromaDB upsert call structure
collection.upsert(
    ids=["chunk_6ba7b810..."],                   # chunk UUID
    documents=["Full chunk text content here..."], # The text
    embeddings=[[0.023, -0.441, ...]],            # 768-dim nomic-embed-text vector
    metadatas=[{...}],                             # See metadata schema below
)
```

### 6.3 ChromaDB Metadata Schema

All metadata fields are stored alongside each vector for filtered retrieval:

```json
{
    "chunk_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "document_id": "a4e12fc0-1b2c-4d5e-8f90-123456789abc",
    "collection_id": "c1d2e3f4-0000-1111-2222-333344445555",
    "chunk_index": 7,
    "page_number": 3,
    "start_char": 1452,
    "end_char": 1964,
    "content_preview": "First 100 chars of chunk for debug...",
    "document_filename": "temporal_rag_survey_2025.pdf",
    "document_title": "A Survey of Temporal Reasoning in RAG Systems",
    "document_author": "Chen, Liu, Patel",
    "document_type": "academic_paper",
    "document_date": "2025-03-15",
    "document_date_ts": 1742000000,
    "ingested_at": "2026-06-16T06:00:00Z",
    "ingested_at_ts": 1750060800,
    "age_at_ingestion_days": 457,
    "doi": "10.1145/3626772.3657861",
    "source_url": "https://arxiv.org/abs/2503.12345",
    "language": "en",
    "embedding_model": "nomic-embed-text",
    "embedding_dim": 768,
    "estimated_credibility": 0.95
}
```

### 6.4 Temporal Metadata Field Definitions

| Field | Type | Description | TRRI Usage |
|-------|------|-------------|------------|
| `document_date` | `string (ISO date)` | Publication or last-modified date of source document | Primary input to TF calculator |
| `document_date_ts` | `integer (Unix timestamp)` | Numeric form for ChromaDB range filtering | Metadata filtering |
| `ingested_at` | `string (ISO 8601)` | When chunk was added to ChromaDB | Audit |
| `ingested_at_ts` | `integer` | Numeric form of `ingested_at` | Metadata filtering |
| `age_at_ingestion_days` | `integer` | `(ingested_at - document_date).days` | Precomputed for analytics |
| `estimated_credibility` | `float [0,1]` | Source credibility precomputed at ingestion | SrC calculator warm-start |

### 6.5 Reliability Metadata Schema (TRRI Result — Attached to Query, not Chunk)

When a query is issued and TRRI is computed, the result is logged to PostgreSQL `reliability_scores`. The ChromaDB metadata is read-only and not modified per query.

---

## 7. Metadata Schemas (JSON)

### 7.1 Experiment Configuration JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ExperimentConfig",
    "type": "object",
    "required": [
        "retrieval_strategy",
        "dataset",
        "split",
        "sample_size",
        "random_seed",
        "top_k",
        "generation_model",
        "embedding_model"
    ],
    "properties": {
        "retrieval_strategy": {
            "type": "string",
            "enum": ["naive_rag", "self_rag", "crag", "adaptive_rag", "ragguard_tr"]
        },
        "dataset": {
            "type": "string",
            "enum": ["hotpotqa", "natural_questions", "triviaqa", "timeqa", "chronoqa"]
        },
        "split": {
            "type": "string",
            "enum": ["train", "dev", "test"],
            "default": "test"
        },
        "sample_size": {
            "type": "integer",
            "minimum": 10,
            "maximum": 10000
        },
        "random_seed": {
            "type": "integer",
            "default": 42
        },
        "top_k": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        },
        "generation_model": {
            "type": "string",
            "example": "llama3.1:8b-instruct-q4_K_M"
        },
        "embedding_model": {
            "type": "string",
            "example": "nomic-embed-text"
        },
        "trri_weights": {
            "type": "object",
            "properties": {
                "temporal_freshness": {"type": "number", "minimum": 0, "maximum": 1},
                "semantic_coherence": {"type": "number", "minimum": 0, "maximum": 1},
                "source_credibility": {"type": "number", "minimum": 0, "maximum": 1},
                "contextual_completeness": {"type": "number", "minimum": 0, "maximum": 1}
            }
        },
        "trri_thresholds": {
            "type": "object",
            "properties": {
                "high": {"type": "number", "minimum": 0, "maximum": 1},
                "medium": {"type": "number", "minimum": 0, "maximum": 1}
            }
        },
        "half_life_days": {
            "type": "number",
            "minimum": 1,
            "maximum": 3650,
            "default": 180.0
        },
        "dataset_version": {"type": "string"},
        "collection_id": {"type": "string", "format": "uuid"}
    }
}
```

### 7.2 TRRI Result JSON (Returned in SSE + Stored in reliability_scores)

```json
{
    "query": "What is the current policy on remote work for government employees?",
    "query_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
    "collection_id": "c1d2e3f4-0000-1111-2222-333344445555",
    "trri_score": 0.7231,
    "factors": {
        "temporal_freshness": {
            "score": 0.8201,
            "weight": 0.35,
            "weighted_contribution": 0.2870
        },
        "semantic_coherence": {
            "score": 0.6854,
            "weight": 0.25,
            "weighted_contribution": 0.1714
        },
        "source_credibility": {
            "score": 0.8750,
            "weight": 0.20,
            "weighted_contribution": 0.1750
        },
        "contextual_completeness": {
            "score": 0.4487,
            "weight": 0.20,
            "weighted_contribution": 0.0897
        }
    },
    "adaptive_decision": "PROCEED",
    "retrieval_rounds": 1,
    "applied_weights": {
        "temporal_freshness": 0.35,
        "semantic_coherence": 0.25,
        "source_credibility": 0.20,
        "contextual_completeness": 0.20
    },
    "applied_thresholds": {
        "high": 0.70,
        "medium": 0.45
    },
    "chunk_breakdown": [
        {
            "chunk_id": "b3c4d5e6-...",
            "content_preview": "As of January 2026, federal agencies are required to...",
            "similarity": 0.921,
            "tf_score": 0.951,
            "src_score": 0.900,
            "document_date": "2026-01-15",
            "age_days": 152
        },
        {
            "chunk_id": "f7a8b9c0-...",
            "content_preview": "Remote work guidelines were updated in the 2025 omnibus...",
            "similarity": 0.887,
            "tf_score": 0.723,
            "src_score": 0.900,
            "document_date": "2025-03-01",
            "age_days": 472
        }
    ],
    "computation_ms": 127
}
```

### 7.3 Calibration Diagram JSON (stored in evaluations.calibration_diagram)

```json
{
    "n_bins": 10,
    "n_samples": 500,
    "ece": 0.0412,
    "mce": 0.0891,
    "bins": [
        {
            "bin_lower": 0.0,
            "bin_upper": 0.1,
            "mean_confidence": 0.052,
            "mean_accuracy": 0.071,
            "count": 14
        },
        {
            "bin_lower": 0.1,
            "bin_upper": 0.2,
            "mean_confidence": 0.148,
            "mean_accuracy": 0.133,
            "count": 30
        },
        {
            "bin_lower": 0.2,
            "bin_upper": 0.3,
            "mean_confidence": 0.251,
            "mean_accuracy": 0.278,
            "count": 36
        },
        {
            "bin_lower": 0.7,
            "bin_upper": 0.8,
            "mean_confidence": 0.748,
            "mean_accuracy": 0.737,
            "count": 89
        },
        {
            "bin_lower": 0.8,
            "bin_upper": 0.9,
            "mean_confidence": 0.847,
            "mean_accuracy": 0.854,
            "count": 112
        },
        {
            "bin_lower": 0.9,
            "bin_upper": 1.0,
            "mean_confidence": 0.932,
            "mean_accuracy": 0.921,
            "count": 67
        }
    ]
}
```

---

## 8. Sample Data Examples

### 8.1 Sample Experiment Record

```json
{
    "id": "exp-1a2b3c4d-...",
    "user_id": "usr-9f8e7d6c-...",
    "name": "RAGGuard-TR vs Self-RAG on HotpotQA",
    "experiment_key": "exp-hotpot-ragguard-v1",
    "config": {
        "retrieval_strategy": "ragguard_tr",
        "dataset": "hotpotqa",
        "split": "test",
        "sample_size": 500,
        "random_seed": 42,
        "top_k": 10,
        "generation_model": "llama3.1:8b-instruct-q4_K_M",
        "embedding_model": "nomic-embed-text",
        "trri_weights": {
            "temporal_freshness": 0.35,
            "semantic_coherence": 0.25,
            "source_credibility": 0.20,
            "contextual_completeness": 0.20
        },
        "trri_thresholds": { "high": 0.70, "medium": 0.45 },
        "half_life_days": 180.0,
        "dataset_version": "v1.1"
    },
    "status": "completed",
    "progress_pct": 100.0,
    "started_at": "2026-06-16T08:00:00Z",
    "completed_at": "2026-06-16T09:47:23Z",
    "duration_seconds": 6443,
    "created_at": "2026-06-16T07:55:00Z"
}
```

### 8.2 Sample Evaluation Record

```json
{
    "id": "eval-5e6f7g8h-...",
    "experiment_id": "exp-1a2b3c4d-...",
    "faithfulness": 0.8724,
    "answer_relevancy": 0.8341,
    "context_precision": 0.7893,
    "context_recall": 0.8156,
    "hallucination_score": 0.1276,
    "ece": 0.0412,
    "mce": 0.0891,
    "auc_roc": 0.8134,
    "brier_score": 0.1023,
    "mean_trri_score": 0.6847,
    "median_trri_score": 0.7102,
    "std_trri_score": 0.1423,
    "proceed_pct": 71.4,
    "expand_pct": 21.6,
    "reject_pct": 7.0,
    "n_samples": 500,
    "n_hallucinated": 64,
    "evaluated_at": "2026-06-16T09:50:00Z",
    "evaluation_duration_s": 157
}
```

---

*End of Database Design Document — RAGGuard-TR v1.0.0*
