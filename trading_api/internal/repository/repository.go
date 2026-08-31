package repository

import (
	"database/sql"
	"fmt"
	"strconv"
	"strings"
	"time"

	"trading_api/internal/models"
)

type Repository struct {
	DB *sql.DB
}

func NewRepository(db *sql.DB) *Repository {
	return &Repository{DB: db}
}

// Watchlist methods
func signalTypeLabel(signalType string) string {
	switch signalType {
	case "near_52w_ath":
		return "Highest 52W"
	case "ema9_above_ema21":
		return "Uptrend"
	case "top_growth_20d":
		return "Top Growth 20D"
	default:
		return signalType
	}
}

func (r *Repository) GetPotentialSymbols(signalType string) ([]models.SymbolData, time.Time, error) {
	baseQuery := "SELECT symbol, signal_type, volume, highest_price, lowest_price, COALESCE(score_diff, 0) FROM symbols_watchlist"
	maxUpdatedQuery := "SELECT MAX(updated_at) FROM symbols_watchlist"
	args := []interface{}{}
	if signalType != "" {
		baseQuery += " WHERE signal_type = $1"
		maxUpdatedQuery += " WHERE signal_type = $1"
		args = append(args, signalType)
	}
	baseQuery += " ORDER BY volume DESC, symbol ASC, signal_type ASC"

	rows, err := r.DB.Query(baseQuery, args...)
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var symbols []models.SymbolData
	for rows.Next() {
		var s models.SymbolData
		if err := rows.Scan(&s.Symbol, &s.SignalType, &s.Volume, &s.HighestPrice, &s.LowestPrice, &s.ScoreDiff); err != nil {
			return nil, time.Time{}, err
		}
		s.SignalLabel = signalTypeLabel(s.SignalType)
		symbols = append(symbols, s)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow(maxUpdatedQuery, args...).Scan(&latestUpdated)

	if symbols == nil {
		symbols = []models.SymbolData{}
	}

	return symbols, latestUpdated.Time, nil
}

func (r *Repository) GetPotentialWorldSymbols() ([]models.WorldSymbolData, time.Time, error) {
	rows, err := r.DB.Query("SELECT symbol, country FROM world_symbols_watchlist")
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var symbols []models.WorldSymbolData
	for rows.Next() {
		var s models.WorldSymbolData
		if err := rows.Scan(&s.Symbol, &s.Country); err != nil {
			return nil, time.Time{}, err
		}
		symbols = append(symbols, s)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow("SELECT MAX(updated_at) FROM world_symbols_watchlist").Scan(&latestUpdated)

	if symbols == nil {
		symbols = []models.WorldSymbolData{}
	}

	return symbols, latestUpdated.Time, nil
}

func cryptoSignalTypeLabel(signalType string) string {
	switch signalType {
	case "near_52w_ath":
		return "Near 52W High"
	case "near_ath":
		return "Near ATH"
	case "ema9_above_ema21":
		return "Uptrend"
	default:
		return signalType
	}
}

func (r *Repository) GetPotentialCoins(signalType string) ([]models.CryptoData, time.Time, error) {
	baseQuery := "SELECT crypto, is_ath, signal_type, COALESCE(highest_price, 0), COALESCE(market_cap, 0), COALESCE(score_diff, 0) FROM cryptos_watchlist"
	maxUpdatedQuery := "SELECT MAX(updated_at) FROM cryptos_watchlist"
	args := []interface{}{}
	if signalType != "" {
		baseQuery += " WHERE signal_type = $1"
		maxUpdatedQuery += " WHERE signal_type = $1"
		args = append(args, signalType)
	}
	baseQuery += " ORDER BY signal_type ASC, crypto ASC"

	rows, err := r.DB.Query(baseQuery, args...)
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var cryptos []models.CryptoData
	for rows.Next() {
		var c models.CryptoData
		if err := rows.Scan(&c.Crypto, &c.IsAth, &c.SignalType, &c.HighestPrice, &c.MarketCap, &c.ScoreDiff); err != nil {
			return nil, time.Time{}, err
		}
		c.SignalLabel = cryptoSignalTypeLabel(c.SignalType)
		cryptos = append(cryptos, c)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow(maxUpdatedQuery, args...).Scan(&latestUpdated)

	if cryptos == nil {
		cryptos = []models.CryptoData{}
	}

	return cryptos, latestUpdated.Time, nil
}

func futuresSignalTypeLabel(signalType string) string {
	switch signalType {
	case "near_52w_high":
		return "Near 52W High"
	case "ema9_above_ema21":
		return "Uptrend"
	default:
		return signalType
	}
}

func (r *Repository) GetPotentialFuturesCoins(signalType string) ([]models.FuturesData, time.Time, error) {
	baseQuery := "SELECT symbol, signal_type, COALESCE(highest_price, 0), COALESCE(market_cap, 0) FROM futures_watchlist"
	maxUpdatedQuery := "SELECT MAX(updated_at) FROM futures_watchlist"
	args := []interface{}{}
	if signalType != "" {
		baseQuery += " WHERE signal_type = $1"
		maxUpdatedQuery += " WHERE signal_type = $1"
		args = append(args, signalType)
	}
	baseQuery += " ORDER BY signal_type ASC, symbol ASC"

	rows, err := r.DB.Query(baseQuery, args...)
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var futures []models.FuturesData
	for rows.Next() {
		var f models.FuturesData
		if err := rows.Scan(&f.Symbol, &f.SignalType, &f.HighestPrice, &f.MarketCap); err != nil {
			return nil, time.Time{}, err
		}
		f.SignalLabel = futuresSignalTypeLabel(f.SignalType)
		futures = append(futures, f)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow(maxUpdatedQuery, args...).Scan(&latestUpdated)

	if futures == nil {
		futures = []models.FuturesData{}
	}

	return futures, latestUpdated.Time, nil
}


func (r *Repository) GetPotentialForexPairs() ([]models.ForexPair, time.Time, error) {
	rows, err := r.DB.Query("SELECT pair, action, score_diff, note, updated_at FROM forex_watchlist ORDER BY score_diff DESC")
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var forexPairs []models.ForexPair
	var latestUpdated time.Time
	for rows.Next() {
		var fp models.ForexPair
		var note sql.NullString
		if err := rows.Scan(&fp.Pair, &fp.Action, &fp.ScoreDiff, &note, &fp.UpdatedAt); err != nil {
			return nil, time.Time{}, err
		}
		if note.Valid {
			fp.Note = note.String
		}
		forexPairs = append(forexPairs, fp)
		if fp.UpdatedAt.After(latestUpdated) {
			latestUpdated = fp.UpdatedAt
		}
	}

	if forexPairs == nil {
		forexPairs = []models.ForexPair{}
	}

	return forexPairs, latestUpdated, nil
}

// User methods
func (r *Repository) UpsertUserInfo(info models.UserInfo) error {
	_, err := r.DB.Exec(`
        INSERT INTO user_info (id, otp)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE
        SET otp = EXCLUDED.otp
    `, info.ID, info.OTP)
	return err
}

// Journal methods
func (r *Repository) GetJournalEntries(userID string) ([]models.JournalEntry, error) {
	rows, err := r.DB.Query(`
		SELECT id, user_id, asset_type, symbol, quantity, price, currency, entry_date, notes, current_price, created_at, updated_at
		FROM journal_entries
		WHERE user_id = $1
		ORDER BY entry_date DESC
	`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []models.JournalEntry
	for rows.Next() {
		var e models.JournalEntry
		var symbol sql.NullString // Handle potential NULLs if schema allowed it, though struct implies string
		if err := rows.Scan(&e.ID, &e.UserID, &e.AssetType, &symbol, &e.Quantity, &e.Price, &e.Currency, &e.EntryDate, &e.Notes, &e.CurrentPrice, &e.CreatedAt, &e.UpdatedAt); err != nil {
			return nil, err
		}
		if symbol.Valid {
			e.Symbol = symbol.String
		}
		entries = append(entries, e)
	}

	if entries == nil {
		entries = []models.JournalEntry{}
	}
	return entries, nil
}

func (r *Repository) CreateJournalEntry(userID string, req models.CreateJournalEntryRequest) error {
	currency := req.Currency
	if currency == "" {
		currency = "VND"
	}
	_, err := r.DB.Exec(`
		INSERT INTO journal_entries (user_id, asset_type, symbol, quantity, price, currency, entry_date, notes, current_price)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`, userID, req.AssetType, req.Symbol, req.Quantity, req.Price, currency, req.EntryDate, req.Notes, req.CurrentPrice)
	return err
}

func (r *Repository) UpdateJournalEntry(userID string, req models.UpdateJournalEntryRequest) error {
	currency := req.Currency
	if currency == "" {
		currency = "VND"
	}
	_, err := r.DB.Exec(`
		UPDATE journal_entries
		SET asset_type = $1, symbol = $2, quantity = $3, price = $4, currency = $5, entry_date = $6, notes = $7, current_price = $8, updated_at = CURRENT_TIMESTAMP
		WHERE id = $9 AND user_id = $10
	`, req.AssetType, req.Symbol, req.Quantity, req.Price, currency, req.EntryDate, req.Notes, req.CurrentPrice, req.ID, userID)
	return err
}

func (r *Repository) DeleteJournalEntry(userID string, id int) error {
	_, err := r.DB.Exec(`DELETE FROM journal_entries WHERE id = $1 AND user_id = $2`, id, userID)
	return err
}

// Community methods
func (r *Repository) GetCommunityPosts() ([]models.CommunityPost, error) {
	rows, err := r.DB.Query("SELECT id, user_id, user_name, user_code, content, COALESCE(image, ''), likes, created_at FROM community_posts ORDER BY created_at DESC")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var posts []models.CommunityPost
	for rows.Next() {
		var p models.CommunityPost
		if err := rows.Scan(&p.ID, &p.UserID, &p.UserName, &p.UserCode, &p.Content, &p.Image, &p.Likes, &p.CreatedAt); err != nil {
			return nil, err
		}
		posts = append(posts, p)
	}

	if posts == nil {
		posts = []models.CommunityPost{}
	}
	return posts, nil
}

func (r *Repository) CreateCommunityPost(req models.CreateCommunityPostRequest) (models.CommunityPost, error) {
	var newID int
	err := r.DB.QueryRow(`
		INSERT INTO community_posts (user_id, user_name, user_code, content, image, likes)
		VALUES ($1, $2, $3, $4, $5, 0)
		RETURNING id
	`, req.UserID, req.UserName, req.UserCode, req.Content, req.Image).Scan(&newID)

	if err != nil {
		return models.CommunityPost{}, err
	}

	return models.CommunityPost{
		ID:        newID,
		UserID:    req.UserID,
		UserName:  req.UserName,
		UserCode:  req.UserCode,
		Content:   req.Content,
		Image:     req.Image,
		Likes:     0,
		CreatedAt: time.Now(), // Approximation, ideally return from DB
	}, nil
}

func (r *Repository) DeleteCommunityPost(id int) error {
	_, err := r.DB.Exec(`DELETE FROM community_posts WHERE id = $1`, id)
	return err
}

func (r *Repository) UpdateCommunityPost(id int, content string) error {
	_, err := r.DB.Exec("UPDATE community_posts SET content = $1 WHERE id = $2", content, id)
	return err
}

func (r *Repository) GetCommunityComments(postID int) ([]models.CommunityComment, error) {
	rows, err := r.DB.Query("SELECT id, post_id, user_id, user_name, content, created_at FROM community_comments WHERE post_id = $1 ORDER BY created_at ASC", postID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var comments []models.CommunityComment
	for rows.Next() {
		var c models.CommunityComment
		if err := rows.Scan(&c.ID, &c.PostID, &c.UserID, &c.UserName, &c.Content, &c.CreatedAt); err != nil {
			return nil, err
		}
		comments = append(comments, c)
	}

	if comments == nil {
		comments = []models.CommunityComment{}
	}
	return comments, nil
}

func (r *Repository) CreateCommunityComment(req models.CreateCommunityCommentRequest) (models.CommunityComment, error) {
	var newID int
	err := r.DB.QueryRow(`
		INSERT INTO community_comments (post_id, user_id, user_name, content)
		VALUES ($1, $2, $3, $4)
		RETURNING id
	`, req.PostID, req.UserID, req.UserName, req.Content).Scan(&newID)

	if err != nil {
		return models.CommunityComment{}, err
	}

	return models.CommunityComment{
		ID:        newID,
		PostID:    req.PostID,
		UserID:    req.UserID,
		UserName:  req.UserName,
		Content:   req.Content,
		CreatedAt: time.Now(),
	}, nil
}

func (r *Repository) DeleteCommunityComment(id int) error {
	_, err := r.DB.Exec("DELETE FROM community_comments WHERE id = $1", id)
	return err
}

func (r *Repository) UpdateCommunityComment(id int, content string) error {
	_, err := r.DB.Exec("UPDATE community_comments SET content = $1 WHERE id = $2", content, id)
	return err
}

// Price Alert methods
func (r *Repository) GetPriceAlerts(assetType string) ([]models.PriceAlert, error) {
	var rows *sql.Rows
	var err error

	if assetType != "" {
		rows, err = r.DB.Query(`
			SELECT symbol, asset_type, alert_price, operator, is_active, last_notified_at, created_at, updated_at
			FROM price_alerts
			WHERE asset_type = $1
			ORDER BY created_at DESC
		`, assetType)
	} else {
		rows, err = r.DB.Query(`
			SELECT symbol, asset_type, alert_price, operator, is_active, last_notified_at, created_at, updated_at
			FROM price_alerts
			ORDER BY created_at DESC
		`)
	}

	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var alerts []models.PriceAlert
	for rows.Next() {
		var alert models.PriceAlert
		err := rows.Scan(&alert.Symbol, &alert.AssetType,
			&alert.AlertPrice, &alert.Operator, &alert.IsActive, &alert.LastNotifiedAt,
			&alert.CreatedAt, &alert.UpdatedAt)
		if err != nil {
			continue
		}
		alerts = append(alerts, alert)
	}

	if alerts == nil {
		alerts = []models.PriceAlert{}
	}
	return alerts, nil
}

func (r *Repository) CreatePriceAlert(req models.CreateAlertRequest) error {
	_, err := r.DB.Exec(`
		INSERT INTO price_alerts (symbol, asset_type, alert_price, operator, is_active)
		VALUES ($1, $2, $3, $4, true)
		ON CONFLICT (symbol, asset_type)
		DO UPDATE SET alert_price = $3, operator = $4, is_active = true, updated_at = CURRENT_TIMESTAMP
	`, req.Symbol, req.AssetType, req.AlertPrice, req.Operator)
	return err
}

func (r *Repository) UpdatePriceAlert(symbol, assetType string, req models.UpdateAlertRequest) error {
	query := "UPDATE price_alerts SET updated_at = CURRENT_TIMESTAMP"
	args := []interface{}{}
	argCount := 1

	if req.AlertPrice > 0 {
		query += fmt.Sprintf(", alert_price = $%d", argCount)
		args = append(args, req.AlertPrice)
		argCount++
	}

	if req.Operator != "" && (req.Operator == "<=" || req.Operator == ">=") {
		query += fmt.Sprintf(", operator = $%d", argCount)
		args = append(args, req.Operator)
		argCount++
	}

	if req.IsActive != nil {
		query += fmt.Sprintf(", is_active = $%d", argCount)
		args = append(args, *req.IsActive)
		argCount++
	}

	query += fmt.Sprintf(" WHERE symbol = $%d AND asset_type = $%d", argCount, argCount+1)
	args = append(args, symbol, assetType)

	_, err := r.DB.Exec(query, args...)
	return err
}

func (r *Repository) DeletePriceAlert(symbol, assetType string) error {
	_, err := r.DB.Exec("DELETE FROM price_alerts WHERE symbol = $1 AND asset_type = $2", symbol, assetType)
	return err
}

func (r *Repository) GetTriggeredAlerts() ([]models.TriggeredAlert, error) {
	rows, err := r.DB.Query(`
		SELECT id, asset_type, symbol, price, message, is_read, created_at
		FROM triggered_alerts
		WHERE is_read = false
		ORDER BY created_at ASC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var alerts []models.TriggeredAlert
	for rows.Next() {
		var a models.TriggeredAlert
		if err := rows.Scan(&a.ID, &a.AssetType, &a.Symbol, &a.Price, &a.Message, &a.IsRead, &a.CreatedAt); err != nil {
			return nil, err
		}
		alerts = append(alerts, a)
	}

	if alerts == nil {
		alerts = []models.TriggeredAlert{}
	}
	return alerts, nil
}

func (r *Repository) GetLatestTriggeredAlerts(limit int) ([]models.TriggeredAlert, error) {
	rows, err := r.DB.Query(`
		SELECT id, asset_type, symbol, price, message, is_read, created_at
		FROM (
			SELECT DISTINCT ON (symbol) id, asset_type, symbol, price, message, is_read, created_at
			FROM triggered_alerts
			ORDER BY symbol, id DESC
		) sub
		ORDER BY id DESC
		LIMIT $1
	`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var alerts []models.TriggeredAlert
	for rows.Next() {
		var a models.TriggeredAlert
		if err := rows.Scan(&a.ID, &a.AssetType, &a.Symbol, &a.Price, &a.Message, &a.IsRead, &a.CreatedAt); err != nil {
			return nil, err
		}
		alerts = append(alerts, a)
	}

	if alerts == nil {
		alerts = []models.TriggeredAlert{}
	}
	return alerts, nil
}

func (r *Repository) MarkTriggeredAlertsAsRead(ids []int) error {
	if len(ids) == 0 {
		_, err := r.DB.Exec("UPDATE triggered_alerts SET is_read = true WHERE is_read = false")
		return err
	}

	for _, id := range ids {
		_, err := r.DB.Exec("UPDATE triggered_alerts SET is_read = true WHERE id = $1", id)
		if err != nil {
			return err
		}
	}
	return nil
}

func (r *Repository) GetSystemSettings() (map[string]interface{}, error) {
	rows, err := r.DB.Query("SELECT key, value FROM system_settings")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	settings := map[string]interface{}{
		"scan_stock_vn":               true,
		"scan_stock_us":               true,
		"scan_crypto":                 true,
		"scan_futures":                true,
		"scan_commodities":            true,
		"scan_forex":                  true,
		"ai_enabled":                  true,
		"ai_prompt_template":          "",
		"ai_world_state_prompt":       "",
		"ai_signal_extraction_prompt": "",
		"ai_analysis_modules":         "{\"theses\":{\"real_estate_vn\":true,\"cash_allocation\":true,\"rwa_strategy\":true,\"forex_pairs\":true,\"asset_weights\":true},\"world_state\":{\"central_banks\":true,\"energy_commodities\":true,\"global_liquidity\":true},\"extraction\":{\"policy\":true,\"liquidity\":true,\"inflation\":true,\"growth\":true,\"sentiment\":true}}",
	}
	for rows.Next() {
		var key, val string
		if err := rows.Scan(&key, &val); err != nil {
			return nil, err
		}
		if val == "true" {
			settings[key] = true
		} else if val == "false" {
			settings[key] = false
		} else {
			settings[key] = val
		}
	}
	return settings, nil
}

func (r *Repository) UpdateSystemSetting(key string, val string) error {
	_, err := r.DB.Exec(`
		INSERT INTO system_settings (key, value, updated_at)
		VALUES ($1, $2, CURRENT_TIMESTAMP)
		ON CONFLICT (key) DO UPDATE
		SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
	`, key, val)
	return err
}

func (r *Repository) GetTradingSettings(maskSecrets bool) (*models.TradingSettings, error) {
	rows, err := r.DB.Query(`
		SELECT key, value FROM system_settings 
		WHERE key IN (
			'trading_mode', 'binance_api_key', 'binance_api_secret', 'binance_testnet', 
			'binance_trade_amount_usdt', 'mt5_account', 'mt5_password', 'mt5_server', 
			'mt5_path', 'mt5_lot_size'
		)
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	settings := &models.TradingSettings{
		TradingMode:            "demo",
		BinanceTestnet:         false,
		BinanceTradeAmountUSDT: 20.0,
		MT5LotSize:             0.01,
	}

	for rows.Next() {
		var key, val string
		if err := rows.Scan(&key, &val); err != nil {
			return nil, err
		}
		switch key {
		case "trading_mode":
			if val != "" {
				settings.TradingMode = val
			}
		case "binance_api_key":
			settings.BinanceAPIKey = val
			settings.HasBinanceKey = len(val) > 0
		case "binance_api_secret":
			settings.BinanceAPISecret = val
			settings.HasBinanceSecret = len(val) > 0
		case "binance_testnet":
			settings.BinanceTestnet = (val == "true")
		case "binance_trade_amount_usdt":
			if amt, err := strconv.ParseFloat(val, 64); err == nil && amt > 0 {
				settings.BinanceTradeAmountUSDT = amt
			}
		case "mt5_account":
			settings.MT5Account = val
		case "mt5_password":
			settings.MT5Password = val
			settings.HasMT5Password = len(val) > 0
		case "mt5_server":
			settings.MT5Server = val
		case "mt5_path":
			settings.MT5Path = val
		case "mt5_lot_size":
			if lot, err := strconv.ParseFloat(val, 64); err == nil && lot > 0 {
				settings.MT5LotSize = lot
			}
		}
	}

	if maskSecrets {
		if len(settings.BinanceAPIKey) > 8 {
			settings.BinanceAPIKey = settings.BinanceAPIKey[:4] + "...." + settings.BinanceAPIKey[len(settings.BinanceAPIKey)-4:]
		} else if len(settings.BinanceAPIKey) > 0 {
			settings.BinanceAPIKey = "********"
		}

		if len(settings.BinanceAPISecret) > 8 {
			settings.BinanceAPISecret = settings.BinanceAPISecret[:4] + "...." + settings.BinanceAPISecret[len(settings.BinanceAPISecret)-4:]
		} else if len(settings.BinanceAPISecret) > 0 {
			settings.BinanceAPISecret = "********"
		}

		if len(settings.MT5Password) > 0 {
			settings.MT5Password = "********"
		}
	}

	return settings, nil
}

func (r *Repository) UpdateTradingSettings(settings models.TradingSettings) error {
	tx, err := r.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	upsertStmt := `
		INSERT INTO system_settings (key, value, updated_at)
		VALUES ($1, $2, CURRENT_TIMESTAMP)
		ON CONFLICT (key) DO UPDATE
		SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
	`

	updates := map[string]string{
		"trading_mode":               settings.TradingMode,
		"binance_testnet":            fmt.Sprintf("%t", settings.BinanceTestnet),
		"binance_trade_amount_usdt":  fmt.Sprintf("%.2f", settings.BinanceTradeAmountUSDT),
		"mt5_account":                settings.MT5Account,
		"mt5_server":                 settings.MT5Server,
		"mt5_path":                   settings.MT5Path,
		"mt5_lot_size":               fmt.Sprintf("%.4f", settings.MT5LotSize),
	}

	// Only update secrets if non-empty and not masked
	if settings.BinanceAPIKey != "" && !strings.Contains(settings.BinanceAPIKey, "....") && !strings.Contains(settings.BinanceAPIKey, "****") {
		updates["binance_api_key"] = settings.BinanceAPIKey
	}
	if settings.BinanceAPISecret != "" && !strings.Contains(settings.BinanceAPISecret, "....") && !strings.Contains(settings.BinanceAPISecret, "****") {
		updates["binance_api_secret"] = settings.BinanceAPISecret
	}
	if settings.MT5Password != "" && !strings.Contains(settings.MT5Password, "****") {
		updates["mt5_password"] = settings.MT5Password
	}

	for k, v := range updates {
		if _, err := tx.Exec(upsertStmt, k, v); err != nil {
			return err
		}
	}

	return tx.Commit()
}

// --- Breakout & Pyramiding Paper Trading Repository Methods ---

func (r *Repository) GetBreakoutWatchlist() ([]models.BreakoutWatchlistItem, error) {
	query := `
		SELECT 
			w.id, w.symbol, w.asset_type, COALESCE(w.name, ''), w.ath_price,
			w.initial_budget, w.step_pct, w.pyramid_ratio, w.sl_pct, w.max_pyramids,
			w.is_active, COALESCE(w.is_real_trading, false), COALESCE(w.notes, ''), w.created_at, w.updated_at,
			EXISTS(SELECT 1 FROM public.paper_positions p WHERE p.watchlist_id = w.id AND p.status = 'OPEN') as has_open_pos,
			COALESCE((SELECT p.current_price FROM public.paper_positions p WHERE p.watchlist_id = w.id AND p.status = 'OPEN' ORDER BY p.id DESC LIMIT 1), 0) as cur_price
		FROM public.breakout_watchlist w
		ORDER BY w.is_active DESC, w.created_at DESC;
	`
	rows, err := r.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []models.BreakoutWatchlistItem
	for rows.Next() {
		var item models.BreakoutWatchlistItem
		if err := rows.Scan(
			&item.ID, &item.Symbol, &item.AssetType, &item.Name, &item.ATHPrice,
			&item.InitialBudget, &item.StepPct, &item.PyramidRatio, &item.SLPct, &item.MaxPyramids,
			&item.IsActive, &item.IsRealTrading, &item.Notes, &item.CreatedAt, &item.UpdatedAt,
			&item.HasOpenPosition, &item.CurrentPrice,
		); err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	if items == nil {
		items = []models.BreakoutWatchlistItem{}
	}
	return items, nil
}

func (r *Repository) AddBreakoutWatchlistItem(item models.BreakoutWatchlistItem) (*models.BreakoutWatchlistItem, error) {
	if item.InitialBudget <= 0 {
		item.InitialBudget = 1000.00
	}
	if item.StepPct <= 0 {
		item.StepPct = 5.00
	}
	if item.PyramidRatio <= 0 {
		item.PyramidRatio = 0.67
	}
	if item.SLPct <= 0 {
		item.SLPct = 3.00
	}
	if item.MaxPyramids <= 0 {
		item.MaxPyramids = 3
	}

	query := `
		INSERT INTO public.breakout_watchlist (
			symbol, asset_type, name, ath_price, initial_budget,
			step_pct, pyramid_ratio, sl_pct, max_pyramids, is_active, is_real_trading, notes,
			created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT (symbol, asset_type) DO UPDATE SET
			name = EXCLUDED.name,
			ath_price = EXCLUDED.ath_price,
			initial_budget = EXCLUDED.initial_budget,
			step_pct = EXCLUDED.step_pct,
			pyramid_ratio = EXCLUDED.pyramid_ratio,
			sl_pct = EXCLUDED.sl_pct,
			max_pyramids = EXCLUDED.max_pyramids,
			is_active = EXCLUDED.is_active,
			is_real_trading = EXCLUDED.is_real_trading,
			notes = EXCLUDED.notes,
			updated_at = CURRENT_TIMESTAMP
		RETURNING id, created_at, updated_at;
	`
	err := r.DB.QueryRow(
		query,
		item.Symbol, item.AssetType, item.Name, item.ATHPrice, item.InitialBudget,
		item.StepPct, item.PyramidRatio, item.SLPct, item.MaxPyramids, item.IsActive, item.IsRealTrading, item.Notes,
	).Scan(&item.ID, &item.CreatedAt, &item.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateBreakoutWatchlistItem(item models.BreakoutWatchlistItem) error {
	query := `
		UPDATE public.breakout_watchlist
		SET name = $1, ath_price = $2, initial_budget = $3, step_pct = $4,
		    pyramid_ratio = $5, sl_pct = $6, max_pyramids = $7, is_active = $8,
		    is_real_trading = $9, notes = $10, updated_at = CURRENT_TIMESTAMP
		WHERE id = $11;
	`
	_, err := r.DB.Exec(
		query,
		item.Name, item.ATHPrice, item.InitialBudget, item.StepPct,
		item.PyramidRatio, item.SLPct, item.MaxPyramids, item.IsActive,
		item.IsRealTrading, item.Notes, item.ID,
	)
	if err != nil {
		return err
	}

	// Đồng bộ stop_loss_price cho các vị thế OPEN tương ứng nếu có sửa sl_pct
	syncPosQuery := `
		UPDATE public.paper_positions
		SET stop_loss_price = CASE 
			WHEN current_layer = 1 THEN avg_entry_price * (1.0 - $1 / 100.0)
			ELSE GREATEST(avg_entry_price, last_buy_price * (1.0 - $1 / 100.0))
		END,
		updated_at = CURRENT_TIMESTAMP
		WHERE watchlist_id = $2 AND status = 'OPEN';
	`
	_, _ = r.DB.Exec(syncPosQuery, item.SLPct, item.ID)

	return nil
}


func (r *Repository) DeleteBreakoutWatchlistItem(id int) error {
	_, err := r.DB.Exec("DELETE FROM public.breakout_watchlist WHERE id = $1;", id)
	return err
}

func (r *Repository) GetPaperPositions(status string) ([]models.PaperPosition, error) {
	query := `
		SELECT 
			id, watchlist_id, symbol, asset_type, status, current_layer,
			total_invested, total_units, avg_entry_price, last_buy_price,
			highest_price, current_price, stop_loss_price, next_pyramid_price,
			unrealized_pnl, unrealized_roi_pct, realized_pnl, opened_at, closed_at,
			COALESCE(close_reason, ''), updated_at
		FROM public.paper_positions
	`
	var rows *sql.Rows
	var err error
	if status != "" {
		query += " WHERE status = $1 ORDER BY opened_at DESC;"
		rows, err = r.DB.Query(query, status)
	} else {
		query += " ORDER BY opened_at DESC;"
		rows, err = r.DB.Query(query)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var positions []models.PaperPosition
	for rows.Next() {
		var p models.PaperPosition
		if err := rows.Scan(
			&p.ID, &p.WatchlistID, &p.Symbol, &p.AssetType, &p.Status, &p.CurrentLayer,
			&p.TotalInvested, &p.TotalUnits, &p.AvgEntryPrice, &p.LastBuyPrice,
			&p.HighestPrice, &p.CurrentPrice, &p.StopLossPrice, &p.NextPyramidPrice,
			&p.UnrealizedPnL, &p.UnrealizedROIPct, &p.RealizedPnL, &p.OpenedAt, &p.ClosedAt,
			&p.CloseReason, &p.UpdatedAt,
		); err != nil {
			return nil, err
		}

		// Fetch child orders
		orders, _ := r.GetPaperOrders(p.ID)
		p.Orders = orders

		positions = append(positions, p)
	}
	if positions == nil {
		positions = []models.PaperPosition{}
	}
	return positions, nil
}

func (r *Repository) GetPaperOrders(positionID int) ([]models.PaperOrder, error) {
	query := `
		SELECT id, position_id, symbol, order_type, layer, price, amount_usd, units, COALESCE(reason, ''), created_at
		FROM public.paper_orders
		WHERE position_id = $1
		ORDER BY layer ASC, id ASC;
	`
	rows, err := r.DB.Query(query, positionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var orders []models.PaperOrder
	for rows.Next() {
		var o models.PaperOrder
		if err := rows.Scan(
			&o.ID, &o.PositionID, &o.Symbol, &o.OrderType, &o.Layer,
			&o.Price, &o.AmountUSD, &o.Units, &o.Reason, &o.CreatedAt,
		); err != nil {
			return nil, err
		}
		orders = append(orders, o)
	}
	if orders == nil {
		orders = []models.PaperOrder{}
	}
	return orders, nil
}

func (r *Repository) ClosePaperPosition(positionID int, reason string) error {
	// Query current position info
	var symbol string
	var currentLayer int
	var currentPrice, totalUnits, avgEntryPrice float64
	err := r.DB.QueryRow(`
		SELECT symbol, current_layer, current_price, total_units, avg_entry_price
		FROM public.paper_positions
		WHERE id = $1 AND status = 'OPEN';
	`, positionID).Scan(&symbol, &currentLayer, &currentPrice, &totalUnits, &avgEntryPrice)
	if err != nil {
		return fmt.Errorf("position not found or already closed: %w", err)
	}

	realizedPnL := (currentPrice - avgEntryPrice) * totalUnits
	closeReason := reason
	if closeReason == "" {
		closeReason = "MANUAL_CLOSE"
	}

	// Update position
	_, err = r.DB.Exec(`
		UPDATE public.paper_positions
		SET status = 'CLOSED_MANUAL',
		    realized_pnl = $1,
		    unrealized_pnl = 0,
		    closed_at = CURRENT_TIMESTAMP,
		    close_reason = $2,
		    updated_at = CURRENT_TIMESTAMP
		WHERE id = $3;
	`, realizedPnL, closeReason, positionID)
	if err != nil {
		return err
	}

	// Insert order record
	_, err = r.DB.Exec(`
		INSERT INTO public.paper_orders (
			position_id, symbol, order_type, layer, price, amount_usd, units, reason, created_at
		) VALUES ($1, $2, 'MANUAL_CLOSE', $3, $4, $5, $6, $7, CURRENT_TIMESTAMP);
	`, positionID, symbol, currentLayer, currentPrice, currentPrice*totalUnits, totalUnits, "Đóng lệnh thủ công bởi Admin")

	return err
}

func (r *Repository) GetBreakoutLeaderboard() ([]models.BreakoutLeaderboardItem, error) {
	query := `
		SELECT 
			symbol,
			asset_type,
			COUNT(id) as total_trades,
			COUNT(CASE WHEN (status = 'CLOSED_SL' AND realized_pnl > 0) OR (status = 'CLOSED_MANUAL' AND realized_pnl > 0) OR (status = 'OPEN' AND unrealized_pnl > 0) THEN 1 END) as win_count,
			COALESCE(SUM(realized_pnl), 0) as total_realized_pnl,
			COALESCE(MAX(CASE WHEN status = 'OPEN' THEN unrealized_roi_pct ELSE ((current_price - avg_entry_price)/NULLIF(avg_entry_price,0))*100 END), 0) as max_roi,
			COALESCE(AVG(CASE WHEN status = 'OPEN' THEN unrealized_roi_pct ELSE ((current_price - avg_entry_price)/NULLIF(avg_entry_price,0))*100 END), 0) as avg_roi,
			COALESCE((SELECT status FROM public.paper_positions p2 WHERE p2.symbol = p.symbol ORDER BY p2.id DESC LIMIT 1), 'CLOSED') as current_status,
			COALESCE((SELECT unrealized_pnl FROM public.paper_positions p2 WHERE p2.symbol = p.symbol AND p2.status = 'OPEN' LIMIT 1), 0) as cur_pnl,
			COALESCE((SELECT unrealized_roi_pct FROM public.paper_positions p2 WHERE p2.symbol = p.symbol AND p2.status = 'OPEN' LIMIT 1), 0) as cur_roi,
			COALESCE((SELECT current_layer FROM public.paper_positions p2 WHERE p2.symbol = p.symbol AND p2.status = 'OPEN' LIMIT 1), 0) as cur_layer
		FROM public.paper_positions p
		GROUP BY symbol, asset_type
		ORDER BY cur_roi DESC, total_realized_pnl DESC;
	`
	rows, err := r.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.BreakoutLeaderboardItem
	for rows.Next() {
		var item models.BreakoutLeaderboardItem
		var winCount int
		if err := rows.Scan(
			&item.Symbol, &item.AssetType, &item.TotalTrades, &winCount,
			&item.TotalRealizedPnL, &item.MaxROI, &item.AvgROI,
			&item.CurrentStatus, &item.CurrentPnL, &item.CurrentROI, &item.CurrentLayer,
		); err != nil {
			return nil, err
		}
		item.WinningTrades = winCount
		if item.TotalTrades > 0 {
			item.WinRatePct = (float64(winCount) / float64(item.TotalTrades)) * 100.0
		}
		list = append(list, item)
	}
	if list == nil {
		list = []models.BreakoutLeaderboardItem{}
	}
	return list, nil
}

func (r *Repository) GetEconomicCalendar(startDate, endDate string) ([]models.EconomicEvent, error) {
	query := `
		SELECT id, title, country, event_time, COALESCE(impact, 'Low'),
		       COALESCE(forecast, ''), COALESCE(previous, ''), COALESCE(actual, ''),
		       COALESCE(surprise, ''), COALESCE(status, 'SCHEDULED'), updated_at
		FROM public.economic_calendar
	`
	var args []interface{}
	if startDate != "" && endDate != "" {
		query += ` WHERE event_time >= $1 AND event_time <= $2`
		args = append(args, startDate, endDate)
	} else if startDate != "" {
		query += ` WHERE event_time >= $1`
		args = append(args, startDate)
	}
	query += ` ORDER BY event_time ASC;`

	rows, err := r.DB.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []models.EconomicEvent
	for rows.Next() {
		var e models.EconomicEvent
		if err := rows.Scan(
			&e.ID, &e.Title, &e.Country, &e.Date, &e.Impact,
			&e.Forecast, &e.Previous, &e.Actual, &e.Surprise,
			&e.Status, &e.UpdatedAt,
		); err != nil {
			return nil, err
		}
		events = append(events, e)
	}
	if events == nil {
		events = []models.EconomicEvent{}
	}
	return events, nil
}

// Podcast methods
func (r *Repository) GetLatestPodcast() (*models.OsintPodcast, error) {
	var p models.OsintPodcast
	err := r.DB.QueryRow(`
		SELECT id, session, session_name, title, audio_url, duration_seconds, script_text, created_at
		FROM osint_podcasts
		ORDER BY created_at DESC
		LIMIT 1
	`).Scan(&p.ID, &p.Session, &p.SessionName, &p.Title, &p.AudioURL, &p.DurationSeconds, &p.ScriptText, &p.CreatedAt)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	return &p, nil
}

func (r *Repository) GetPodcasts(limit int) ([]models.OsintPodcast, error) {
	if limit <= 0 || limit > 50 {
		limit = 10
	}
	rows, err := r.DB.Query(`
		SELECT id, session, session_name, title, audio_url, duration_seconds, script_text, created_at
		FROM osint_podcasts
		WHERE created_at >= (NOW() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AT TIME ZONE 'Asia/Ho_Chi_Minh'
		ORDER BY created_at DESC
		LIMIT $1
	`, limit)
	if err != nil {
		return []models.OsintPodcast{}, err
	}
	defer rows.Close()

	var podcasts []models.OsintPodcast
	for rows.Next() {
		var p models.OsintPodcast
		if err := rows.Scan(&p.ID, &p.Session, &p.SessionName, &p.Title, &p.AudioURL, &p.DurationSeconds, &p.ScriptText, &p.CreatedAt); err != nil {
			return nil, err
		}
		podcasts = append(podcasts, p)
	}

	if podcasts == nil {
		podcasts = []models.OsintPodcast{}
	}
	return podcasts, nil
}



