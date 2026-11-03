-- AI buy/avoid status per asset group, produced by the Platform Intelligence (thesis) run.
--   ai_status     : 'buy' (nên) | 'avoid' (không nên) - written by osint_ai_worker on every thesis run
--   admin_status  : NULL = follow the AI; 'buy' / 'avoid' = manual override set by a signed-in admin
-- Effective status used by scripts/alert.py = COALESCE(admin_status, ai_status).
-- The admin override is never touched by the AI worker, so it survives new AI runs until reset to "follow AI".
-- Seeded as 'buy' with ai_updated_at NULL, so behaviour is unchanged until the first AI run writes a verdict.

CREATE TABLE IF NOT EXISTS public.ai_asset_signals (
    asset_key        VARCHAR(20)  PRIMARY KEY,
    asset_label      VARCHAR(50)  NOT NULL,
    sort_order       INT          NOT NULL DEFAULT 0,
    ai_status        VARCHAR(10)  NOT NULL DEFAULT 'buy' CHECK (ai_status IN ('buy', 'avoid')),
    ai_reason        TEXT         NOT NULL DEFAULT '',
    ai_confidence    NUMERIC(4,3),
    ai_updated_at    TIMESTAMPTZ,
    admin_status     VARCHAR(10)  CHECK (admin_status IN ('buy', 'avoid')),
    admin_updated_by VARCHAR(255),
    admin_updated_at TIMESTAMPTZ
);

INSERT INTO public.ai_asset_signals (asset_key, asset_label, sort_order) VALUES
    ('gold',     'Vàng',          1),
    ('silver',   'Bạc',           2),
    ('oil',      'Dầu',           3),
    ('bitcoin',  'Bitcoin',       4),
    ('crypto',   'Crypto',        5),
    ('altcoin',  'Altcoin',       6),
    ('us_stock', 'Cổ phiếu Mỹ',   7),
    ('vn_stock', 'Cổ phiếu VN',   8)
ON CONFLICT (asset_key) DO NOTHING;
