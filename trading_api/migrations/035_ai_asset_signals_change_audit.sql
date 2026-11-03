-- Audit trail for the admin status of ai_asset_signals: who changed it (user vs automatic logic) and why.
--   admin_source : 'user'  = a signed-in person pressed a button
--                  'logic' = an automatic rule changed it (admin_rule says which one)
--   admin_rule   : ai_follow_after_disagree | loss_streak_pause_7d   (NULL for user changes)
--   admin_note   : human-readable explanation of the latest change
-- Every change (user or logic) is also appended to ai_asset_signal_changes.
ALTER TABLE public.ai_asset_signals ADD COLUMN IF NOT EXISTS admin_source VARCHAR(10) CHECK (admin_source IN ('user', 'logic'));
ALTER TABLE public.ai_asset_signals ADD COLUMN IF NOT EXISTS admin_rule   VARCHAR(40);
ALTER TABLE public.ai_asset_signals ADD COLUMN IF NOT EXISTS admin_note   TEXT NOT NULL DEFAULT '';

-- Overrides that existed before this migration were set by people.
UPDATE public.ai_asset_signals SET admin_source = 'user' WHERE admin_status IS NOT NULL AND admin_source IS NULL;

CREATE TABLE IF NOT EXISTS public.ai_asset_signal_changes (
    id               BIGSERIAL PRIMARY KEY,
    asset_key        VARCHAR(20)  NOT NULL,
    changed_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_admin_status VARCHAR(10),
    new_admin_status VARCHAR(10),
    source           VARCHAR(10)  NOT NULL CHECK (source IN ('user', 'logic')),
    rule             VARCHAR(40),
    changed_by       VARCHAR(255),
    note             TEXT         NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_ai_asset_signal_changes_asset_time
    ON public.ai_asset_signal_changes (asset_key, changed_at DESC);
