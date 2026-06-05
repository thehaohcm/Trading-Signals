-- 019_create_osint_tables.sql

CREATE TABLE IF NOT EXISTS osint_signals (
    id VARCHAR(255) PRIMARY KEY,
    source_news_id INTEGER NOT NULL REFERENCES news_items(id) ON DELETE CASCADE,
    category VARCHAR(255) NOT NULL,
    signal TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS osint_theses (
    id VARCHAR(255) PRIMARY KEY,
    thesis TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    supporting_evidence TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS osint_world_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS osint_proposed_changes (
    id VARCHAR(255) PRIMARY KEY,
    target_entity VARCHAR(255) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
