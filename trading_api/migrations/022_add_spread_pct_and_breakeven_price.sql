-- Migration 022: Add spread_pct and breakeven_price to breakout_watchlist and paper_positions

ALTER TABLE public.breakout_watchlist 
ADD COLUMN IF NOT EXISTS spread_pct NUMERIC(6, 4) DEFAULT 0.10 NOT NULL;

-- Set default spread_pct based on asset_type & symbol
UPDATE public.breakout_watchlist
SET spread_pct = CASE
    WHEN symbol IN ('XAUUSD', 'GOLD', 'XAGUSD', 'SILVER') OR asset_type = 'commodity' THEN 1.45
    WHEN asset_type = 'crypto' THEN 0.10
    WHEN asset_type = 'futures' THEN 0.08
    WHEN asset_type = 'stock_vn' THEN 0.25
    WHEN asset_type = 'stock_us' THEN 0.08
    WHEN asset_type = 'forex' THEN 0.05
    ELSE 0.10
END
WHERE spread_pct = 0.10 OR spread_pct IS NULL;

ALTER TABLE public.paper_positions 
ADD COLUMN IF NOT EXISTS spread_pct NUMERIC(6, 4) DEFAULT 0.10 NOT NULL,
ADD COLUMN IF NOT EXISTS breakeven_price NUMERIC(20, 8) DEFAULT 0 NOT NULL;

-- Backfill paper_positions spread_pct and breakeven_price from breakout_watchlist
UPDATE public.paper_positions p
SET spread_pct = COALESCE(w.spread_pct, 0.10),
    breakeven_price = p.avg_entry_price * (1.0 + COALESCE(w.spread_pct, 0.10) / 100.0)
FROM public.breakout_watchlist w
WHERE p.watchlist_id = w.id;
