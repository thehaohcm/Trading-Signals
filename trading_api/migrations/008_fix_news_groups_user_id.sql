-- Fix: Change user_id from INTEGER to VARCHAR to match the rest of the codebase
-- (journal_entries, community_posts, etc. all use VARCHAR for user_id)

-- Step 1: Drop the foreign key constraint if it exists
ALTER TABLE news_groups DROP CONSTRAINT IF EXISTS news_groups_user_id_fkey;

-- Step 2: Change user_id column type from INTEGER to VARCHAR(255)
ALTER TABLE news_groups ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::VARCHAR;

-- Step 3: Delete any orphaned groups with empty name or user_id='0' (from previous bugs)
DELETE FROM news_groups WHERE TRIM(name) = '' OR user_id = '0';

-- Step 4: Add an index for faster lookups by user_id
CREATE INDEX IF NOT EXISTS idx_news_groups_user_id ON news_groups(user_id);
