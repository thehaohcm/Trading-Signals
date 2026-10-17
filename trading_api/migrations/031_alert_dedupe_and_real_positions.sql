-- Migration 031: các thay đổi schema do scripts/alert.py dùng
-- (alert.py cũng tự tạo khi khởi động; migration này giúp schema đồng bộ dù alert.py chưa chạy).
-- Tất cả đều idempotent (IF NOT EXISTS) nên chạy song song với alert.py không xung đột.

-- 1. Trạng thái chống báo trùng (đã báo tiệm cận / vượt đỉnh / chuẩn bị vào lệnh), giữ qua restart, hết hạn sau vài ngày
CREATE TABLE IF NOT EXISTS public.alert_dedupe_state (
    namespace VARCHAR(30) NOT NULL,
    key VARCHAR(120) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (namespace, key)
);

-- 2. Vị thế có lệnh thật trên sàn hay không (cố định lúc mở) + khối lượng thực khớp (để bán đúng khi cắt lỗ)
ALTER TABLE public.paper_positions
    ADD COLUMN IF NOT EXISTS is_real BOOLEAN DEFAULT FALSE NOT NULL,
    ADD COLUMN IF NOT EXISTS real_units NUMERIC(20, 8) DEFAULT 0 NOT NULL;

-- 3. Mỗi mã trong watchlist chỉ có tối đa 1 vị thế OPEN.
--    Nếu DB đang có vị thế OPEN bị trùng thì KHÔNG tạo index (tránh làm hỏng migration) và để lại NOTICE.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.paper_positions
        WHERE status = 'OPEN' AND watchlist_id IS NOT NULL
        GROUP BY watchlist_id HAVING COUNT(*) > 1
    ) THEN
        RAISE NOTICE 'Bỏ qua uq_paper_positions_one_open: đang có vị thế OPEN trùng watchlist_id — hãy đóng bớt rồi chạy lại';
    ELSE
        CREATE UNIQUE INDEX IF NOT EXISTS uq_paper_positions_one_open
            ON public.paper_positions(watchlist_id) WHERE status = 'OPEN';
    END IF;
END $$;
