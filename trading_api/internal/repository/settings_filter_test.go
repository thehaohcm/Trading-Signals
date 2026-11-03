package repository

import "testing"

func TestIsSensitiveSettingKey(t *testing.T) {
	hidden := []string{"binance_api_key", "binance_api_secret", "okx_passphrase", "okx_secret_key", "bybit_api_key",
		"mt5_password", "mt5_login", "mt5_server", "gemini_api_key", "ssh_password", "telegram_bot_token", "binance_testnet"}
	for _, k := range hidden {
		if !IsSensitiveSettingKey(k) {
			t.Errorf("%q phải bị ẩn", k)
		}
	}
	shown := []string{"scan_stock_vn", "scan_crypto", "ai_enabled", "ai_prompt_template", "ai_world_state_prompt",
		"ai_signal_extraction_prompt", "ai_market_brief_prompt", "ai_analysis_modules", "podcast_auto_generate", "notebooklm_auto_generate"}
	for _, k := range shown {
		if IsSensitiveSettingKey(k) {
			t.Errorf("%q không được ẩn (UI cần)", k)
		}
	}
}
