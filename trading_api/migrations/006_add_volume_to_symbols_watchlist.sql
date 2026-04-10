ALTER TABLE public.symbols_watchlist
    ADD COLUMN IF NOT EXISTS volume BIGINT NOT NULL DEFAULT 0;

UPDATE public.symbols_watchlist
SET volume = 0
WHERE volume IS NULL;

CREATE INDEX IF NOT EXISTS idx_symbols_watchlist_volume
ON public.symbols_watchlist (volume DESC);
