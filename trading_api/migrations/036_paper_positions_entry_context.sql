-- Ngữ cảnh lúc vào lệnh để phân tích/backtest sau này (alert.py cũng tự ALTER ... IF NOT EXISTS khi khởi động).
--   sl_pct_used      : SL% thực tế dùng cho vị thế (khác sl_pct của watchlist khi bật SL theo ATR)
--   entry_ai_state   : trạng thái AI/Admin của các nhóm tài sản liên quan lúc vào lệnh, vd "crypto=buy/ai; altcoin=buy/admin"
--   entry_filters    : JSON các bộ lọc breakout đã qua (thời gian giữ, khối lượng, chế độ BTC...)
ALTER TABLE public.paper_positions
    ADD COLUMN IF NOT EXISTS sl_pct_used NUMERIC(8, 4),
    ADD COLUMN IF NOT EXISTS entry_ai_state TEXT,
    ADD COLUMN IF NOT EXISTS entry_filters TEXT;
