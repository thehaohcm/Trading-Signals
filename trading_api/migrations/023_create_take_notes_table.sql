-- Create take_notes table for homepage Take Notes & Reminders
CREATE TABLE IF NOT EXISTS take_notes (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_take_notes_user_id ON take_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_take_notes_created_at ON take_notes(created_at DESC);
