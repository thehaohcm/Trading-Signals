-- Migration 024: Update default stop loss to 2%
ALTER TABLE public.breakout_watchlist 
ALTER COLUMN sl_pct SET DEFAULT 2.00;

UPDATE public.breakout_watchlist
SET sl_pct = 2.00
WHERE sl_pct = 3.00 OR sl_pct = 5.00;
