-- Migration 038: Giao dịch thật song song nhiều sàn (Binance + OKX + Bybit)
--
-- Mỗi mã trong breakout_watchlist chọn MỘT sàn để giao dịch thật (mặc định 'binance' để
-- không ảnh hưởng dữ liệu cũ). Khác với trước đây (chỉ có 1 cấu hình 'crypto_exchange'
-- toàn cục không thực sự được code dùng), từ nay mỗi mã độc lập — cho phép trade đồng thời
-- 2-3 tài khoản khác sàn như người dùng yêu cầu.
--
-- Đóng lệnh thủ công trên OKX/Bybit từ UI KHÔNG thực hiện trực tiếp trong trading_api (container
-- Go không có Python/ccxt) — chỉ đánh dấu "đã yêu cầu đóng", vòng quét vị thế (scripts/alert.py,
-- Python, có ccxt) sẽ thực hiện lệnh bán thật trong vòng chu kỳ quét kế tiếp.

ALTER TABLE public.breakout_watchlist
    ADD COLUMN IF NOT EXISTS exchange TEXT NOT NULL DEFAULT 'binance';

ALTER TABLE public.breakout_watchlist
    DROP CONSTRAINT IF EXISTS breakout_watchlist_exchange_check;
ALTER TABLE public.breakout_watchlist
    ADD CONSTRAINT breakout_watchlist_exchange_check CHECK (exchange IN ('binance', 'okx', 'bybit'));

ALTER TABLE public.paper_positions
    ADD COLUMN IF NOT EXISTS manual_close_requested_at TIMESTAMPTZ NULL;
ALTER TABLE public.paper_positions
    ADD COLUMN IF NOT EXISTS manual_close_reason TEXT NULL;
