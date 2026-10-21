-- Split the overloaded `ai_prompt_template` setting into dedicated keys.
--   ai_thesis_prompt        -> persona/focus for Platform Intelligence (generate_thesis, JSON output)
--   ai_market_brief_prompt  -> free-text template with {{NEWS_ITEMS}} used by "Generate Prompt"
--                              and scripts/fetch_latest_news_signal_llm.py
-- Previously both UIs wrote to `ai_prompt_template`, so saving one broke the other.

ALTER TABLE IF EXISTS public.system_settings ALTER COLUMN value TYPE TEXT;

-- Legacy value containing the {{NEWS_ITEMS}} placeholder came from the Market Brief editor.
INSERT INTO public.system_settings (key, value)
SELECT 'ai_market_brief_prompt', value
FROM public.system_settings
WHERE key = 'ai_prompt_template'
  AND btrim(value) <> ''
  AND value LIKE '%{{NEWS_ITEMS}}%'
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
WHERE btrim(public.system_settings.value) = '';

-- Any other non-empty legacy value is treated as the thesis prompt.
INSERT INTO public.system_settings (key, value)
SELECT 'ai_thesis_prompt', value
FROM public.system_settings
WHERE key = 'ai_prompt_template'
  AND btrim(value) <> ''
  AND value NOT LIKE '%{{NEWS_ITEMS}}%'
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
WHERE btrim(public.system_settings.value) = '';
