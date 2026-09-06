-- Migration 026: Update default step_pct to 1% and max_pyramids to 3
ALTER TABLE IF EXISTS public.breakout_watchlist ALTER COLUMN step_pct SET DEFAULT 1.0;
ALTER TABLE IF EXISTS public.breakout_watchlist ALTER COLUMN max_pyramids SET DEFAULT 3;

-- Update existing items with old 5% default to 1%
UPDATE public.breakout_watchlist 
SET step_pct = 1.0, updated_at = CURRENT_TIMESTAMP 
WHERE step_pct = 5.0 OR step_pct IS NULL;
