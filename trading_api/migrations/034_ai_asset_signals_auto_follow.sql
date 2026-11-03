-- Auto-follow-AI rule for admin overrides (see osint_ai_worker.save_asset_signals):
-- if the admin override has not been changed for 21 days AND the AI has returned the opposite status
-- on every run for 14 days, the override is cleared and the asset follows the AI again.
-- ai_disagree_since = when the AI's current verdict started to differ from admin_status (NULL = they agree / no override).
ALTER TABLE public.ai_asset_signals ADD COLUMN IF NOT EXISTS ai_disagree_since TIMESTAMPTZ;

-- Existing overrides that already disagree with the AI start counting from now.
UPDATE public.ai_asset_signals
SET ai_disagree_since = CURRENT_TIMESTAMP
WHERE admin_status IS NOT NULL AND admin_status <> ai_status AND ai_disagree_since IS NULL;
