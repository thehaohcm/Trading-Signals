package repository

import (
	"database/sql"
	"fmt"
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
func (r *Repository) GetPotentialSymbols() ([]models.SymbolData, time.Time, error) {
	rows, err := r.DB.Query("SELECT symbol, highest_price, lowest_price FROM symbols_watchlist")
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var symbols []models.SymbolData
	for rows.Next() {
		var s models.SymbolData
		if err := rows.Scan(&s.Symbol, &s.HighestPrice, &s.LowestPrice); err != nil {
			return nil, time.Time{}, err
		}
		symbols = append(symbols, s)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow("SELECT MAX(updated_at) FROM symbols_watchlist").Scan(&latestUpdated)

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

func (r *Repository) GetPotentialCoins() ([]models.CryptoData, time.Time, error) {
	rows, err := r.DB.Query("SELECT crypto, is_ath FROM cryptos_watchlist ORDER BY is_ath ASC;")
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var cryptos []models.CryptoData
	for rows.Next() {
		var c models.CryptoData
		if err := rows.Scan(&c.Crypto, &c.IsAth); err != nil {
			return nil, time.Time{}, err
		}
		cryptos = append(cryptos, c)
	}

	var latestUpdated sql.NullTime
	_ = r.DB.QueryRow("SELECT MAX(updated_at) FROM cryptos_watchlist").Scan(&latestUpdated)

	if cryptos == nil {
		cryptos = []models.CryptoData{}
	}

	return cryptos, latestUpdated.Time, nil
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

func (r *Repository) UpdateUserTrades(userID string, stocks []models.StockWithEntryPrice) error {
	for _, stock := range stocks {
		_, err := r.DB.Exec(`
               INSERT INTO user_trading_symbols (user_id, symbol, entry_price, avg_price)
               VALUES ($1, $2, $3, 0)
               ON CONFLICT (user_id, symbol) DO UPDATE
			   SET entry_price = EXCLUDED.entry_price
           `, userID, stock.Symbol, stock.EntryPrice)
		if err != nil {
			return err
		}
	}
	return nil
}

func (r *Repository) DeleteUserTrades(userID string, stocks []models.StockWithEntryPrice) error {
	for _, stock := range stocks {
		_, err := r.DB.Exec(`
               DELETE FROM user_trading_symbols
               WHERE user_id = $1 AND symbol = $2
           `, userID, stock.Symbol)
		if err != nil {
			return err
		}
	}
	return nil
}

func (r *Repository) GetUserTrades(userID string) ([]models.UserTradeResponse, error) {
	rows, err := r.DB.Query("SELECT symbol, entry_price, avg_price, current_price FROM user_trading_symbols WHERE user_id = $1", userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Get signal items for comparison
	signalRows, err := r.DB.Query("SELECT symbol FROM symbols_watchlist")
	if err != nil {
		return nil, err
	}
	defer signalRows.Close()

	var signalItems []string
	for signalRows.Next() {
		var signal string
		if err := signalRows.Scan(&signal); err != nil {
			return nil, err
		}
		signalItems = append(signalItems, signal)
	}

	var responses []models.UserTradeResponse
	for rows.Next() {
		var symbol string
		var entryPrice int
		var avgPrice int
		var currentPrice int
		if err := rows.Scan(&symbol, &entryPrice, &avgPrice, &currentPrice); err != nil {
			return nil, err
		}
		userTradeResponse := models.UserTradeResponse{
			Symbol:       symbol,
			EntryPrice:   entryPrice,
			Signal:       "Sell",
			AvgPrice:     avgPrice,
			CurrentPrice: currentPrice,
		}

		if avgPrice > 0 && currentPrice > 0 {
			userTradeResponse.PercentChange = float64(currentPrice-avgPrice) / float64(avgPrice)
		}

		for _, item := range signalItems {
			if item == symbol {
				userTradeResponse.Signal = "BUY AND HOLD"
			}
		}
		responses = append(responses, userTradeResponse)
	}

	if responses == nil {
		responses = []models.UserTradeResponse{}
	}

	return responses, nil
}

func (r *Repository) UpdateTradingSignals(updates []models.UpdateSignalRequest) error {
	if len(updates) == 0 {
		return nil
	}

	var queryBuilder strings.Builder
	queryBuilder.WriteString(`
           INSERT INTO user_trading_symbols (user_id, symbol, entry_price, avg_price)
           VALUES
       `)

	vals := []interface{}{}
	for i, update := range updates {
		queryBuilder.WriteString(fmt.Sprintf("($%d, $%d, 0, $%d)", i*3+1, i*3+2, i*3+3))
		if i < len(updates)-1 {
			queryBuilder.WriteString(",")
		}
		vals = append(vals, update.UserID, update.Symbol, update.BreakEvenPrice)
	}

	queryBuilder.WriteString(`
           ON CONFLICT (user_id, symbol) DO UPDATE
           SET avg_price = EXCLUDED.avg_price;
       `)

	_, err := r.DB.Exec(queryBuilder.String(), vals...)
	return err
}

// Journal methods
func (r *Repository) GetJournalEntries(userID string) ([]models.JournalEntry, error) {
	rows, err := r.DB.Query(`
		SELECT id, user_id, asset_type, symbol, quantity, price, entry_date, notes, created_at, updated_at
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
		if err := rows.Scan(&e.ID, &e.UserID, &e.AssetType, &symbol, &e.Quantity, &e.Price, &e.EntryDate, &e.Notes, &e.CreatedAt, &e.UpdatedAt); err != nil {
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
	_, err := r.DB.Exec(`
		INSERT INTO journal_entries (user_id, asset_type, symbol, quantity, price, entry_date, notes)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, userID, req.AssetType, req.Symbol, req.Quantity, req.Price, req.EntryDate, req.Notes)
	return err
}

func (r *Repository) UpdateJournalEntry(userID string, req models.UpdateJournalEntryRequest) error {
	_, err := r.DB.Exec(`
		UPDATE journal_entries
		SET asset_type = $1, symbol = $2, quantity = $3, price = $4, entry_date = $5, notes = $6, updated_at = CURRENT_TIMESTAMP
		WHERE id = $7 AND user_id = $8
	`, req.AssetType, req.Symbol, req.Quantity, req.Price, req.EntryDate, req.Notes, req.ID, userID)
	return err
}

func (r *Repository) DeleteJournalEntry(userID string, id int) error {
	_, err := r.DB.Exec(`DELETE FROM journal_entries WHERE id = $1 AND user_id = $2`, id, userID)
	return err
}

// Community methods
func (r *Repository) GetCommunityPosts() ([]models.CommunityPost, error) {
	rows, err := r.DB.Query("SELECT id, user_id, user_name, user_code, content, COALESCE(image, ''), likes, created_at FROM community_posts WHERE TRIM(content) != '' OR (image IS NOT NULL AND image != '') ORDER BY created_at DESC")
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
