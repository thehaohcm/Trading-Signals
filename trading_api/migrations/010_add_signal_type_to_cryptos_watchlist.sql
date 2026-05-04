-- Add signal_type column to cryptos_watchlist (similar to symbols_watchlist)
-- This allows multiple signal types per crypto (e.g. near_52w_ath, ma9_above_ema21)

-- Step 1: Drop the old primary key
ALTER TABLE public.cryptos_watchlist DROP CONSTRAINT IF EXISTS cryptos_watchlist_pkey;

-- Step 2: Add signal_type column with default for backward compatibility
ALTER TABLE public.cryptos_watchlist
    ADD COLUMN IF NOT EXISTS signal_type varchar(50) DEFAULT 'near_52w_ath' NOT NULL;

-- Step 3: Migrate existing data - set signal_type based on is_ath
-- ATH coins get 'near_ath' signal, others keep 'near_52w_ath'
UPDATE public.cryptos_watchlist
SET signal_type = 'near_ath'
WHERE is_ath = true;

-- Step 4: Create new composite primary key
ALTER TABLE public.cryptos_watchlist
    ADD CONSTRAINT cryptos_watchlist_pkey PRIMARY KEY (crypto, signal_type);

-- Step 5: Add CHECK constraint for allowed signal types
ALTER TABLE public.cryptos_watchlist
    ADD CONSTRAINT cryptos_watchlist_signal_type_check
    CHECK (signal_type IN ('near_52w_ath', 'near_ath', 'ma9_above_ema21'));
