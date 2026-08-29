-- Migration 020: Update default stop loss to 3% and add trading settings keys

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
