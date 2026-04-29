ALTER TABLE public.symbols_watchlist
    DROP CONSTRAINT IF EXISTS symbols_watchlist_signal_type_check;

ALTER TABLE public.symbols_watchlist
    ADD CONSTRAINT symbols_watchlist_signal_type_check
    CHECK (signal_type IN ('near_52w_ath', 'ma9_above_ema21', 'top_growth_20d'));
