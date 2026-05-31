-- Add market_cap column to futures_watchlist table
ALTER TABLE public.futures_watchlist ADD COLUMN IF NOT EXISTS market_cap numeric(20, 8) DEFAULT 0 NULL;
