CREATE TABLE IF NOT EXISTS public.system_settings (
    key varchar(50) PRIMARY KEY,
    value varchar(255) NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Seed default active values
INSERT INTO public.system_settings (key, value) VALUES 
('scan_stock_vn', 'true'),
('scan_stock_us', 'true'),
('scan_crypto', 'true'),
('scan_futures', 'true')
ON CONFLICT (key) DO NOTHING;
