-- Migration 020: Update default stop loss to 3% and add trading settings keys

-- 0. Ensure breakout tables exist
CREATE TABLE IF NOT EXISTS public.breakout_watchlist (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    ath_price NUMERIC(20, 8) NOT NULL,
    initial_budget NUMERIC(20, 2) DEFAULT 1000.00 NOT NULL,
    step_pct NUMERIC(5, 2) DEFAULT 1.00 NOT NULL,
    pyramid_ratio NUMERIC(5, 2) DEFAULT 0.67 NOT NULL,
    sl_pct NUMERIC(5, 2) DEFAULT 2.00 NOT NULL,
    max_pyramids INT DEFAULT 3 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    current_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_breakout_symbol_asset UNIQUE(symbol, asset_type)
);

CREATE TABLE IF NOT EXISTS public.paper_positions (
    id SERIAL PRIMARY KEY,
    watchlist_id INT REFERENCES public.breakout_watchlist(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    current_layer INT DEFAULT 1 NOT NULL,
    total_invested NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    total_units NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    avg_entry_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    last_buy_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    highest_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    current_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    stop_loss_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    next_pyramid_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    unrealized_pnl NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    unrealized_roi_pct NUMERIC(10, 2) DEFAULT 0 NOT NULL,
    realized_pnl NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_at TIMESTAMPTZ,
    close_reason VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS public.paper_orders (
    id SERIAL PRIMARY KEY,
    position_id INT REFERENCES public.paper_positions(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    layer INT NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    amount_usd NUMERIC(20, 2) NOT NULL,
    units NUMERIC(20, 8) NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 1. Update breakout_watchlist table default sl_pct to 3.00
ALTER TABLE public.breakout_watchlist 
ALTER COLUMN sl_pct SET DEFAULT 3.00;

-- 2. Update existing items that still have default 5.00% sl_pct to 3.00%
UPDATE public.breakout_watchlist
SET sl_pct = 3.00
WHERE sl_pct = 5.00;

-- 3. Seed trading settings keys into system_settings table
INSERT INTO public.system_settings (key, value) VALUES 
('trading_mode', 'demo'),
('binance_api_key', ''),
('binance_api_secret', ''),
('binance_testnet', 'false'),
('binance_trade_amount_usdt', '20.0'),
('mt5_account', ''),
('mt5_password', ''),
('mt5_server', ''),
('mt5_path', ''),
('mt5_lot_size', '0.01')
ON CONFLICT (key) DO NOTHING;
