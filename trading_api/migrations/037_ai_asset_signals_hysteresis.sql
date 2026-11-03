-- Hysteresis cho trạng thái AI: chỉ đổi ai_status khi AI trả CÙNG một kết quả mới liên tiếp N lần chạy (mặc định 2).
--   ai_pending_status / ai_pending_count : kết quả đang chờ xác nhận và số lần liên tiếp đã thấy
--   follow_suggested_at                  : lần cuối đã nhắc "AI khuyến nghị NÊN lâu ngày, cân nhắc theo AI" (tránh nhắc lặp)
ALTER TABLE public.ai_asset_signals
    ADD COLUMN IF NOT EXISTS ai_pending_status VARCHAR(10) CHECK (ai_pending_status IN ('buy', 'avoid')),
    ADD COLUMN IF NOT EXISTS ai_pending_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS follow_suggested_at TIMESTAMPTZ;
