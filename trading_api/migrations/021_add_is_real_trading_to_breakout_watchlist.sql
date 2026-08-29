-- Migration 021: Add is_real_trading toggle to breakout_watchlist

ALTER TABLE public.breakout_watchlist 
ADD COLUMN IF NOT EXISTS is_real_trading BOOLEAN DEFAULT FALSE NOT NULL;
