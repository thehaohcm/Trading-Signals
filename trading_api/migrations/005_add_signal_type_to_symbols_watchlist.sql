ALTER TABLE public.symbols_watchlist
    ADD COLUMN IF NOT EXISTS signal_type VARCHAR(50) NOT NULL DEFAULT 'near_52w_ath';

ALTER TABLE public.symbols_watchlist
    DROP CONSTRAINT IF EXISTS symbols_watchlist_signal_type_check;

ALTER TABLE public.symbols_watchlist
    ADD CONSTRAINT symbols_watchlist_signal_type_check
    CHECK (signal_type IN ('near_52w_ath', 'ma9_above_ema21', 'top_growth_20d'));

ALTER TABLE public.symbols_watchlist
    DROP CONSTRAINT IF EXISTS symbols_watchlist_pkey;

ALTER TABLE public.symbols_watchlist
    ADD CONSTRAINT symbols_watchlist_pkey PRIMARY KEY (symbol, signal_type);ALTER TABLE public.symbols_watchlist
ADD COLUMN IF NOT EXISTS signal_type varchar(50) DEFAULT 'near_52w_ath' NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'symbols_watchlist_pkey'
          AND conrelid = 'public.symbols_watchlist'::regclass
    ) THEN
        ALTER TABLE public.symbols_watchlist
        DROP CONSTRAINT symbols_watchlist_pkey;
    END IF;
END $$;

ALTER TABLE public.symbols_watchlist
ADD CONSTRAINT symbols_watchlist_pkey PRIMARY KEY (symbol, signal_type);

CREATE INDEX IF NOT EXISTS idx_symbols_watchlist_signal_type
ON public.symbols_watchlist (signal_type);
