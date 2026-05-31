CREATE TABLE IF NOT EXISTS public.futures_watchlist (
    symbol varchar NOT NULL,
    signal_type varchar(50) DEFAULT 'near_52w_high' NOT NULL,
    highest_price numeric(20, 8) NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT futures_watchlist_pkey PRIMARY KEY (symbol, signal_type),
    CONSTRAINT futures_watchlist_signal_type_check CHECK (signal_type IN ('near_52w_high', 'ema9_above_ema21'))
);
