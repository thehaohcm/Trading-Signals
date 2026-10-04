-- Migration 029: Create economic_calendar and highest_bank_interest_rate tables
CREATE TABLE IF NOT EXISTS public.highest_bank_interest_rate (
    id SERIAL PRIMARY KEY,
    bank VARCHAR(255) NOT NULL,
    rate NUMERIC(5, 2) NOT NULL,
    term VARCHAR(100),
    channel VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS public.economic_calendar (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    country VARCHAR(20),
    event_time TIMESTAMPTZ,
    impact VARCHAR(20),
    forecast VARCHAR(50),
    previous VARCHAR(50),
    actual VARCHAR(50),
    surprise VARCHAR(50),
    status VARCHAR(20),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE IF EXISTS public.system_settings ALTER COLUMN value TYPE TEXT;
