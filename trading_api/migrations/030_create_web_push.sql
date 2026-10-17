-- Migration 030: Web Push notifications (Chrome / Edge / Firefox / Safari)

-- Cặp khoá VAPID dùng chung cho mọi instance API (tự sinh lần đầu nếu không đặt VAPID_* trong .env)
CREATE TABLE IF NOT EXISTS public.web_push_config (
    id INT PRIMARY KEY CHECK (id = 1),
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Mỗi trình duyệt đăng ký nhận thông báo là 1 dòng
CREATE TABLE IF NOT EXISTS public.push_subscriptions (
    id SERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent TEXT,
    notify_alerts BOOLEAN DEFAULT TRUE NOT NULL,
    notify_news BOOLEAN DEFAULT FALSE NOT NULL, -- Breaking News mặc định tắt
    failure_count INT DEFAULT 0 NOT NULL,
    last_success_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chống gửi trùng khi nhiều instance API (VPS + Fly.io) cùng chạy push worker
CREATE TABLE IF NOT EXISTS public.push_dispatch_log (
    event_key VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_push_dispatch_log_created ON public.push_dispatch_log(created_at);
