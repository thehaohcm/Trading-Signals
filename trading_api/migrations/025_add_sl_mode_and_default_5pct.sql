-- 1. Add sl_mode to breakout_watchlist and set default sl_pct to 5.00
ALTER TABLE public.breakout_watchlist 
    ALTER COLUMN sl_pct SET DEFAULT 5.00;

ALTER TABLE public.breakout_watchlist 
    ADD COLUMN IF NOT EXISTS sl_mode VARCHAR(30) DEFAULT 'TRAILING_PEAK' NOT NULL;

-- 2. Update existing watchlist items to default 5.00% if they were at 2.00% or 3.00%
UPDATE public.breakout_watchlist
SET sl_pct = 5.00
WHERE sl_pct IN (2.00, 3.00);

-- 3. Add sl_mode to paper_positions
ALTER TABLE public.paper_positions 
    ADD COLUMN IF NOT EXISTS sl_mode VARCHAR(30) DEFAULT 'TRAILING_PEAK' NOT NULL;
