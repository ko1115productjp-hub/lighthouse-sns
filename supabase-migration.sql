-- =============================================================================
-- Lighthouse Database Migration for Supabase
-- =============================================================================
-- このSQLをSupabase SQL Editorで実行してください
-- =============================================================================

-- Enable pgvector extension (already done in UI, but just in case)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create ENUM types first
DO $$ BEGIN
    CREATE TYPE visibility AS ENUM ('public', 'private', 'followers_only');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE citation_type AS ENUM ('agree', 'criticize', 'develop', 'reference');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_review_status AS ENUM ('pending', 'approved', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM (
        'citation',
        'follow',
        'ai_review_rejected',
        'protocol_update'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE referenced_entity_type AS ENUM (
        'place',
        'book',
        'movie',
        'experience'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- Table: users
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    full_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    oauth_provider VARCHAR(50),
    oauth_provider_id VARCHAR(255),
    protocol_agreed_at TIMESTAMP,
    protocol_version INTEGER DEFAULT 1,
    UNIQUE(oauth_provider, oauth_provider_id)
);

-- =============================================================================
-- Table: outputs
-- =============================================================================
CREATE TABLE IF NOT EXISTS outputs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    hash VARCHAR(64) NOT NULL UNIQUE,
    previous_hash VARCHAR(64),
    visibility visibility DEFAULT 'public',
    novelty_score INTEGER,
    ai_review_status ai_review_status DEFAULT 'pending',
    ai_review_flagged_categories VARCHAR(50)[],
    ai_review_feedback TEXT,
    originality_score INTEGER,
    originality_reasoning TEXT,
    suspected_source VARCHAR(500),
    embedding vector(1536),
    referenced_entity_type referenced_entity_type,
    referenced_entity_id VARCHAR(255),
    referenced_entity_name VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for outputs
CREATE INDEX IF NOT EXISTS idx_outputs_user_id ON outputs(user_id);
CREATE INDEX IF NOT EXISTS idx_outputs_visibility ON outputs(visibility);
CREATE INDEX IF NOT EXISTS idx_outputs_created_at ON outputs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outputs_content_hash ON outputs(content_hash);
CREATE INDEX IF NOT EXISTS idx_outputs_previous_hash ON outputs(previous_hash);
CREATE INDEX IF NOT EXISTS idx_outputs_ai_review_status ON outputs(ai_review_status);
CREATE INDEX IF NOT EXISTS idx_outputs_referenced_entity ON outputs(referenced_entity_type, referenced_entity_id);
CREATE INDEX IF NOT EXISTS idx_outputs_embedding_vector ON outputs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Fulltext search index
CREATE INDEX IF NOT EXISTS idx_outputs_content_fts ON outputs USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_outputs_title_fts ON outputs USING gin(to_tsvector('english', COALESCE(title, '')));

-- =============================================================================
-- Table: citations
-- =============================================================================
CREATE TABLE IF NOT EXISTS citations (
    id SERIAL PRIMARY KEY,
    source_output_id INTEGER NOT NULL REFERENCES outputs(id) ON DELETE CASCADE,
    cited_output_id INTEGER NOT NULL REFERENCES outputs(id) ON DELETE CASCADE,
    citation_type citation_type NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_output_id, cited_output_id)
);

CREATE INDEX IF NOT EXISTS idx_citations_source ON citations(source_output_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_output_id);

-- =============================================================================
-- Table: follows
-- =============================================================================
CREATE TABLE IF NOT EXISTS follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followed_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(follower_id, followed_id),
    CHECK (follower_id != followed_id)
);

CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_followed ON follows(followed_id);

-- =============================================================================
-- Table: output_follows
-- =============================================================================
CREATE TABLE IF NOT EXISTS output_follows (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    output_id INTEGER NOT NULL REFERENCES outputs(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, output_id)
);

CREATE INDEX IF NOT EXISTS idx_output_follows_user ON output_follows(user_id);
CREATE INDEX IF NOT EXISTS idx_output_follows_output ON output_follows(output_id);

-- =============================================================================
-- Table: notifications
-- =============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    related_output_id INTEGER REFERENCES outputs(id) ON DELETE CASCADE,
    related_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- =============================================================================
-- Table: alembic_version (for migration tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(64) NOT NULL PRIMARY KEY
);

-- Insert the latest migration version
INSERT INTO alembic_version (version_num) VALUES ('20260327_0700_add_title_to_outputs')
ON CONFLICT (version_num) DO NOTHING;

-- =============================================================================
-- Migration Complete!
-- =============================================================================
