-- Migration 013: Create triggered_alerts table for real-time web alerts
CREATE TABLE IF NOT EXISTS public.triggered_alerts (
    id SERIAL PRIMARY KEY,
    asset_type varchar(20) NOT NULL,
    symbol varchar(50) NOT NULL,
    price numeric(20, 8) NOT NULL,
    message text NOT NULL,
    is_read bool DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_triggered_alerts_unread ON public.triggered_alerts(is_read);
