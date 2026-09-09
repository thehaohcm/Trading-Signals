-- Migration 027: Update default sl_pct to 2.00%
ALTER TABLE IF EXISTS public.breakout_watchlist ALTER COLUMN sl_pct SET DEFAULT 2.00;

-- Update existing items with 5% or 3% to 2%
UPDATE public.breakout_watchlist 
SET sl_pct = 2.00, updated_at = CURRENT_TIMESTAMP 
WHERE sl_pct IN (5.00, 3.00) OR sl_pct IS NULL;

-- Also update existing OPEN positions at layer 1 whose stop loss was set with 5% SL
UPDATE public.paper_positions
SET stop_loss_price = avg_entry_price * (1.0 - 0.02), updated_at = CURRENT_TIMESTAMP
WHERE status = 'OPEN' AND current_layer = 1 AND (stop_loss_price <= (avg_entry_price * 0.955) OR stop_loss_price = 0);
