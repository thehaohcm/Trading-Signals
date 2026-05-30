-- Phase 1: Update symbols_watchlist check constraint
ALTER TABLE public.symbols_watchlist
    DROP CONSTRAINT IF EXISTS symbols_watchlist_signal_type_check;

UPDATE public.symbols_watchlist
SET signal_type = 'ema9_above_ema21'
WHERE signal_type = 'ma9_above_ema21';

ALTER TABLE public.symbols_watchlist
    ADD CONSTRAINT symbols_watchlist_signal_type_check
    CHECK (signal_type IN ('near_52w_ath', 'ema9_above_ema21', 'top_growth_20d'));


-- Phase 2: Update cryptos_watchlist check constraint
ALTER TABLE public.cryptos_watchlist
    DROP CONSTRAINT IF EXISTS cryptos_watchlist_signal_type_check;

UPDATE public.cryptos_watchlist
SET signal_type = 'ema9_above_ema21'
WHERE signal_type = 'ma9_above_ema21';

ALTER TABLE public.cryptos_watchlist
    ADD CONSTRAINT cryptos_watchlist_signal_type_check
    CHECK (signal_type IN ('near_52w_ath', 'near_ath', 'ema9_above_ema21'));
