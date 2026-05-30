-- Migration 012: Add highest_price to cryptos_watchlist and symbols_watchlist
-- Use NUMERIC for cryptos to support small decimal prices (e.g., meme coins)

ALTER TABLE public.cryptos_watchlist
    ADD COLUMN IF NOT EXISTS highest_price NUMERIC;

ALTER TABLE public.symbols_watchlist
    ADD COLUMN IF NOT EXISTS highest_price int8;
