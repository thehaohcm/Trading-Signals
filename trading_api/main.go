package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

const (
	host     = ""
	port     = 0
	user     = ""
	password = ""
	dbname   = ""
)

type SymbolData struct {
	Symbol       string  `json:"symbol"`
	HighestPrice float64 `json:"highest_price"`
	LowestPrice  float64 `json:"lowest_price"`
}

type WorldSymbolData struct {
	Symbol  string `json:"symbol"`
	Country string `json:"country"`
}

type SymbolDataResponse struct {
	Data          []SymbolData `json:"data"`
	LatestUpdated time.Time    `json:"latest_updated"`
}

type WorldSymbolDataResponse struct {
	Data          []WorldSymbolData `json:"data"`
	LatestUpdated time.Time         `json:"latest_updated"`
}

type CryptoData struct {
	Crypto string `json:"crypto"`
	IsAth  string `json:"is_ath"`
}

type CryptoDataResponse struct {
	Data          []CryptoData `json:"data"`
	LatestUpdated time.Time    `json:"latest_updated"`
}

type ForexPair struct {
	Pair      string    `json:"pair"`
	Action    string    `json:"action"`
	ScoreDiff float64   `json:"score_diff"`
	Note      string    `json:"note"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ForexPairResponse struct {
	Data          []ForexPair `json:"data"`
	LatestUpdated time.Time   `json:"latest_updated"`
}

type UserInfo struct {
	ID  int `json:"ID"`
	OTP int `json:"OTP"`
}

type StockWithEntryPrice struct {
	Symbol     string `json:"symbol"`
	EntryPrice int    `json:"entry_price"`
}

type UserTradeRequest struct {
	UserID   string                `json:"user_id"`
	Stocks   []StockWithEntryPrice `json:"stocks"`
	Operator string                `json:"operator"` // "Add", "Update", or "Delete"
}

type UserTradeResponse struct {
	Symbol        string  `json:"symbol"`
	EntryPrice    int     `json:"entry_price"`
	Signal        string  `json:"signal"`
	AvgPrice      int     `json:"avg_price"`
	CurrentPrice  int     `json:"current_price"`
	PercentChange float64 `json:"percent_change"`
}

// Add this struct definition
type UpdateSignalRequest struct {
	UserID         string `json:"user_id"`
	Symbol         string `json:"symbol"`
	BreakEvenPrice int    `json:"break_even_price"`
}

type PriceAlert struct {
	Symbol         string     `json:"symbol"`
	AssetType      string     `json:"asset_type"`
	AlertPrice     float64    `json:"alert_price"`
	IsActive       bool       `json:"is_active"`
	LastNotifiedAt *time.Time `json:"last_notified_at,omitempty"`
	CreatedAt      time.Time  `json:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at"`
}

type CreateAlertRequest struct {
	Symbol     string  `json:"symbol"`
	AssetType  string  `json:"asset_type"`
	AlertPrice float64 `json:"alert_price"`
}

type UpdateAlertRequest struct {
	AlertPrice float64 `json:"alert_price,omitempty"`
	IsActive   *bool   `json:"is_active,omitempty"`
}

func updateTradingSignal(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var updates []UpdateSignalRequest
	err := json.NewDecoder(r.Body).Decode(&updates)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		log.Println("Invalid request body:", err)
		return
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	if len(updates) > 0 {
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

		_, err = db.Exec(queryBuilder.String(), vals...)
		if err != nil {
			http.Error(w, "Failed to update database", http.StatusInternalServerError)
			log.Println("Failed to update database:", err)
			return
		}
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Portfolio updated successfully")
}

func getPotentialSymbols(w http.ResponseWriter, r *http.Request) {
	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	rows, err := db.Query("SELECT symbol, highest_price, lowest_price FROM symbols_watchlist")
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	var symbols []SymbolData
	for rows.Next() {
		var s SymbolData
		if err := rows.Scan(&s.Symbol, &s.HighestPrice, &s.LowestPrice); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		symbols = append(symbols, s)
	}

	if err := rows.Err(); err != nil {
		http.Error(w, "Error during row iteration", http.StatusInternalServerError)
		log.Println("Error during row iteration:", err)
		return
	}

	// Query to get the latest updated
	row := db.QueryRow("SELECT MAX(updated_at) FROM symbols_watchlist LIMIT 1")
	var latestUpdated time.Time
	if err = row.Scan(&latestUpdated); err != nil {
		http.Error(w, "Failed to scan row", http.StatusInternalServerError)
		log.Println("Failed to scan row:", err)
		return
	}

	response := SymbolDataResponse{
		Data:          symbols,
		LatestUpdated: latestUpdated,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getPotentialWorldSymbols(w http.ResponseWriter, r *http.Request) {
	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	rows, err := db.Query("SELECT symbol, country FROM world_symbols_watchlist")
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	var symbols []WorldSymbolData
	for rows.Next() {
		var s WorldSymbolData
		if err := rows.Scan(&s.Symbol, &s.Country); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		symbols = append(symbols, s)
	}

	if err := rows.Err(); err != nil {
		http.Error(w, "Error during row iteration", http.StatusInternalServerError)
		log.Println("Error during row iteration:", err)
		return
	}

	// Query to get the latest updated
	row := db.QueryRow("SELECT MAX(updated_at) FROM world_symbols_watchlist LIMIT 1")
	var latestUpdated time.Time
	if err = row.Scan(&latestUpdated); err != nil {
		http.Error(w, "Failed to scan row", http.StatusInternalServerError)
		log.Println("Failed to scan row:", err)
		return
	}

	response := WorldSymbolDataResponse{
		Data:          symbols,
		LatestUpdated: latestUpdated,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getPotentialCoins(w http.ResponseWriter, r *http.Request) {
	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	rows, err := db.Query("SELECT crypto, is_ath FROM cryptos_watchlist ORDER BY is_ath ASC;")
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	var cryptos []CryptoData
	for rows.Next() {
		var c CryptoData
		if err := rows.Scan(&c.Crypto, &c.IsAth); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		cryptos = append(cryptos, c)
	}

	if err := rows.Err(); err != nil {
		http.Error(w, "Error during row iteration", http.StatusInternalServerError)
		log.Println("Error during row iteration:", err)
		return
	}

	// Query to get the latest updated
	row := db.QueryRow("SELECT MAX(updated_at) FROM cryptos_watchlist LIMIT 1")
	var latestUpdated time.Time
	if err = row.Scan(&latestUpdated); err != nil {
		http.Error(w, "Failed to scan row", http.StatusInternalServerError)
		log.Println("Failed to scan row:", err)
		return
	}

	response := CryptoDataResponse{
		Data:          cryptos,
		LatestUpdated: latestUpdated,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

func inputOTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var userInfo UserInfo
	err := json.NewDecoder(r.Body).Decode(&userInfo)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		log.Println("Invalid request body:", err)
		return
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}
	// UPSERT into user_info table
	_, err = db.Exec(`
        INSERT INTO user_info (id, otp)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE
        SET otp = EXCLUDED.otp
    `, userInfo.ID, userInfo.OTP)

	if err != nil {
		http.Error(w, "Failed to insert/update data", http.StatusInternalServerError)
		log.Println("Failed to insert/update data:", err)
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Data inserted/updated successfully")
}

func userTrade(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req UserTradeRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		log.Println("Invalid request body:", err)
		return
	}

	if req.Operator != "Add" && req.Operator != "Update" && req.Operator != "Delete" {
		http.Error(w, "Invalid operator", http.StatusBadRequest)
		log.Println("Invalid operator:", req.Operator)
		return
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	switch req.Operator {
	case "Add", "Update":
		for _, stock := range req.Stocks {
			_, err = db.Exec(`
	               INSERT INTO user_trading_symbols (user_id, symbol, entry_price, avg_price)
	               VALUES ($1, $2, $3, 0)
	               ON CONFLICT (user_id, symbol) DO UPDATE
				   SET entry_price = EXCLUDED.entry_price
	           `, req.UserID, stock.Symbol, stock.EntryPrice)
			if err != nil {
				http.Error(w, "Failed to insert data", http.StatusInternalServerError)
				log.Println("Failed to insert data:", err)
				return
			}
		}
	case "Delete":
		for _, stock := range req.Stocks {
			_, err = db.Exec(`
	               DELETE FROM user_trading_symbols
	               WHERE user_id = $1 AND symbol = $2
	           `, req.UserID, stock.Symbol)
			if err != nil {
				http.Error(w, "Failed to delete data", http.StatusInternalServerError)
				log.Println("Failed to delete data:", err)
				return
			}
		}
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Operation completed successfully")
}

func getUserTrade(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
		log.Println("Invalid user_id parameter: empty string")
		return
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	rows, err := db.Query("SELECT symbol, entry_price, avg_price, current_price FROM user_trading_symbols WHERE user_id = $1", userID)
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	signalRows, err := db.Query("SELECT symbol FROM symbols_watchlist")
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}

	var signalItems []string
	for i := 0; signalRows.Next(); i++ {
		var signal string
		if err := signalRows.Scan(&signal); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		signalItems = append(signalItems, signal)
	}

	var responses []UserTradeResponse
	for rows.Next() {
		var symbol string
		var entryPrice int
		var avgPrice int
		var currentPrice int
		if err := rows.Scan(&symbol, &entryPrice, &avgPrice, &currentPrice); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		userTradeResponse := UserTradeResponse{
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

	if err := rows.Err(); err != nil {
		http.Error(w, "Error during row iteration", http.StatusInternalServerError)
		log.Println("Error during row iteration:", err)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(responses)
}

// Chat request/response structs
type ChatRequest struct {
	Message string `json:"message"`
}

type ChatResponse struct {
	Response string `json:"response"`
}

type GroqMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type GroqRequest struct {
	Model     string        `json:"model"`
	Messages  []GroqMessage `json:"messages"`
	MaxTokens int           `json:"max_tokens,omitempty"`
}

type GroqResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

func chatHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var chatReq ChatRequest
	err := json.NewDecoder(r.Body).Decode(&chatReq)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		log.Println("Invalid request body:", err)
		return
	}

	if chatReq.Message == "" {
		http.Error(w, "Message cannot be empty", http.StatusBadRequest)
		return
	}

	// Get Groq API key from environment
	groqAPIKey := os.Getenv("GROQ_API_KEY")
	if groqAPIKey == "" {
		http.Error(w, "Groq API key not configured", http.StatusInternalServerError)
		log.Println("Groq API key not found in environment variables")
		return
	}

	// Prepare Groq API request
	groqReq := GroqRequest{
		Model: "qwen/qwen3-32b",
		Messages: []GroqMessage{
			{
				Role:    "user",
				Content: chatReq.Message,
			},
		},
		MaxTokens: 1000,
	}

	jsonData, err := json.Marshal(groqReq)
	if err != nil {
		http.Error(w, "Failed to marshal request", http.StatusInternalServerError)
		log.Println("Failed to marshal request:", err)
		return
	}

	// Make request to Groq API
	req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		http.Error(w, "Failed to create request", http.StatusInternalServerError)
		log.Println("Failed to create request:", err)
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+groqAPIKey)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "Failed to call Groq API", http.StatusInternalServerError)
		log.Println("Failed to call Groq API:", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		http.Error(w, "Groq API returned error", resp.StatusCode)
		log.Printf("Groq API error: %s", string(body))
		return
	}

	var groqResp GroqResponse
	err = json.NewDecoder(resp.Body).Decode(&groqResp)
	if err != nil {
		http.Error(w, "Failed to decode Groq response", http.StatusInternalServerError)
		log.Println("Failed to decode Groq response:", err)
		return
	}

	if len(groqResp.Choices) == 0 {
		http.Error(w, "No response from Groq", http.StatusInternalServerError)
		log.Println("No choices returned from Groq")
		return
	}

	// Send response back to client
	chatResp := ChatResponse{
		Response: groqResp.Choices[0].Message.Content,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(chatResp)
}

func getPotentialForexPairs(w http.ResponseWriter, r *http.Request) {
	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		http.Error(w, "Failed to ping database", http.StatusInternalServerError)
		log.Println("Failed to ping database:", err)
		return
	}

	rows, err := db.Query("SELECT pair, action, score_diff, note, updated_at FROM forex_watchlist ORDER BY score_diff DESC")
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	var forexPairs []ForexPair
	var latestUpdated time.Time
	for rows.Next() {
		var fp ForexPair
		var note sql.NullString
		if err := rows.Scan(&fp.Pair, &fp.Action, &fp.ScoreDiff, &note, &fp.UpdatedAt); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		if note.Valid {
			fp.Note = note.String
		} else {
			fp.Note = ""
		}
		forexPairs = append(forexPairs, fp)
		if fp.UpdatedAt.After(latestUpdated) {
			latestUpdated = fp.UpdatedAt
		}
	}

	if err = rows.Err(); err != nil {
		http.Error(w, "Error iterating rows", http.StatusInternalServerError)
		log.Println("Error iterating rows:", err)
		return
	}

	response := ForexPairResponse{
		Data:          forexPairs,
		LatestUpdated: latestUpdated,
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	json.NewEncoder(w).Encode(response)
}

// priceAlertsHandler handles GET (list alerts) and POST (create alert)
func priceAlertsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	if r.Method == http.MethodGet {
		// List all alerts or filter by asset_type
		assetType := r.URL.Query().Get("asset_type")

		var rows *sql.Rows
		var err error

		if assetType != "" {
			rows, err = db.Query(`
				SELECT symbol, asset_type, alert_price, is_active, last_notified_at, created_at, updated_at
				FROM price_alerts
				WHERE asset_type = $1
				ORDER BY created_at DESC
			`, assetType)
		} else {
			rows, err = db.Query(`
				SELECT symbol, asset_type, alert_price, is_active, last_notified_at, created_at, updated_at
				FROM price_alerts
				ORDER BY created_at DESC
			`)
		}

		if err != nil {
			http.Error(w, "Failed to query alerts", http.StatusInternalServerError)
			log.Println("Failed to query alerts:", err)
			return
		}
		defer rows.Close()

		alerts := []PriceAlert{}
		for rows.Next() {
			var alert PriceAlert
			err := rows.Scan(&alert.Symbol, &alert.AssetType,
				&alert.AlertPrice, &alert.IsActive, &alert.LastNotifiedAt,
				&alert.CreatedAt, &alert.UpdatedAt)
			if err != nil {
				log.Println("Error scanning row:", err)
				continue
			}
			alerts = append(alerts, alert)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(alerts)

	} else if r.Method == http.MethodPost {
		// Create new alert
		var req CreateAlertRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		if err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}

		if req.Symbol == "" || req.AssetType == "" || req.AlertPrice <= 0 {
			http.Error(w, "Missing required fields", http.StatusBadRequest)
			return
		}

		_, err = db.Exec(`
			INSERT INTO price_alerts (symbol, asset_type, alert_price, is_active)
			VALUES ($1, $2, $3, true)
			ON CONFLICT (symbol, asset_type)
			DO UPDATE SET alert_price = $3, is_active = true, updated_at = CURRENT_TIMESTAMP
		`, req.Symbol, req.AssetType, req.AlertPrice)

		if err != nil {
			http.Error(w, "Failed to create alert", http.StatusInternalServerError)
			log.Println("Failed to create alert:", err)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"message": "Alert created successfully",
		})
	} else {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// priceAlertHandler handles PUT (update) and DELETE operations on specific alert
func priceAlertHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Extract symbol and asset_type from URL path
	// Expected format: /priceAlerts/{symbol}/{asset_type}
	pathParts := strings.Split(strings.TrimPrefix(r.URL.Path, "/priceAlerts/"), "/")
	if len(pathParts) < 2 {
		http.Error(w, "Invalid URL format. Expected: /priceAlerts/{symbol}/{asset_type}", http.StatusBadRequest)
		return
	}
	symbol := pathParts[0]
	assetType := pathParts[1]

	dbHost := os.Getenv("DB_HOST")
	dbPort, _ := strconv.Atoi(os.Getenv("DB_PORT"))
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
		log.Println("Failed to connect to database:", err)
		return
	}
	defer db.Close()

	if r.Method == http.MethodPut {
		// Update alert
		var req UpdateAlertRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		if err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}

		query := "UPDATE price_alerts SET updated_at = CURRENT_TIMESTAMP"
		args := []interface{}{}
		argCount := 1

		if req.AlertPrice > 0 {
			query += fmt.Sprintf(", alert_price = $%d", argCount)
			args = append(args, req.AlertPrice)
			argCount++
		}

		if req.IsActive != nil {
			query += fmt.Sprintf(", is_active = $%d", argCount)
			args = append(args, *req.IsActive)
			argCount++
		}

		query += fmt.Sprintf(" WHERE symbol = $%d AND asset_type = $%d", argCount, argCount+1)
		args = append(args, symbol, assetType)

		result, err := db.Exec(query, args...)
		if err != nil {
			http.Error(w, "Failed to update alert", http.StatusInternalServerError)
			log.Println("Failed to update alert:", err)
			return
		}

		rowsAffected, _ := result.RowsAffected()
		if rowsAffected == 0 {
			http.Error(w, "Alert not found", http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"message": "Alert updated successfully"})

	} else if r.Method == http.MethodDelete {
		// Delete alert
		result, err := db.Exec("DELETE FROM price_alerts WHERE symbol = $1 AND asset_type = $2", symbol, assetType)
		if err != nil {
			http.Error(w, "Failed to delete alert", http.StatusInternalServerError)
			log.Println("Failed to delete alert:", err)
			return
		}

		rowsAffected, _ := result.RowsAffected()
		if rowsAffected == 0 {
			http.Error(w, "Alert not found", http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"message": "Alert deleted successfully"})
	} else {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func main() {
	http.HandleFunc("/getPotentialSymbols", getPotentialSymbols)
	http.HandleFunc("/getPotentialWorldSymbols", getPotentialWorldSymbols)
	http.HandleFunc("/getPotentialCoins", getPotentialCoins)
	http.HandleFunc("/getPotentialForexPairs", getPotentialForexPairs)
	http.HandleFunc("/health", healthCheck)
	http.HandleFunc("/inputOTP", inputOTP)
	http.HandleFunc("/userTrade", userTrade)
	http.HandleFunc("/getUserTrade", getUserTrade)
	http.HandleFunc("/updateTradingSignal", updateTradingSignal) // Add the new handler
	http.HandleFunc("/api/chat", chatHandler)
	http.HandleFunc("/priceAlerts", priceAlertsHandler)
	http.HandleFunc("/priceAlerts/", priceAlertHandler)
	fmt.Println("Server listening on :8080")
	addr := net.JoinHostPort("::", "8080")
	server := &http.Server{Addr: addr}
	log.Fatalln(server.ListenAndServe())
}
