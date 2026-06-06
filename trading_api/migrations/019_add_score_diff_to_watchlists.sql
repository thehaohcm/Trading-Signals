-- Migration 019: Add score_diff to cryptos_watchlist and symbols_watchlist
ALTER TABLE public.cryptos_watchlist ADD COLUMN IF NOT EXISTS score_diff NUMERIC(10, 2) DEFAULT 0.00;
ALTER TABLE public.symbols_watchlist ADD COLUMN IF NOT EXISTS score_diff NUMERIC(10, 2) DEFAULT 0.00;
