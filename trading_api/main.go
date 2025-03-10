package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"strconv"

	_ "github.com/lib/pq"
)

const (
	host     = "url"
	port     = 5432
	user     = "user"
	password = "password"
	dbname   = "db"
)

type SymbolData struct {
	Symbol       string  `json:"symbol"`
	HighestPrice float64 `json:"highest_price"`
	LowestPrice  float64 `json:"lowest_price"`
}

type UserInfo struct {
	ID  int `json:"ID"`
	OTP int `json:"OTP"`
}

type UserTradeRequest struct {
	UserID   int      `json:"user_id"`
	Stocks   []string `json:"stocks"`
	Operator string   `json:"operator"` // "Add", "Update", or "Delete"
}

func getPotentialSymbols(w http.ResponseWriter, r *http.Request) {
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

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

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(symbols)
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

	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

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

	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

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
	case "Add":
		for _, stock := range req.Stocks {
			_, err = db.Exec(`
                INSERT INTO user_trading_symbols (user_id, symbol, entry_price, avg_price)
                VALUES ($1, $2, 0, 0)
                ON CONFLICT (user_id, symbol) DO NOTHING
            `, req.UserID, stock)
			if err != nil {
				http.Error(w, "Failed to insert data", http.StatusInternalServerError)
				log.Println("Failed to insert data:", err)
				return
			}
		}
	case "Update":
		for _, stock := range req.Stocks {
			_, err = db.Exec(`
                UPDATE user_trading_symbols
                SET entry_price = 0, avg_price = 0
                WHERE user_id = $1 AND symbol = $2
            `, req.UserID, stock)
			if err != nil {
				http.Error(w, "Failed to update data", http.StatusInternalServerError)
				log.Println("Failed to update data:", err)
				return
			}
		}
	case "Delete":
		for _, stock := range req.Stocks {
			_, err = db.Exec(`
                DELETE FROM user_trading_symbols
                WHERE user_id = $1 AND symbol = $2
            `, req.UserID, stock)
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

	userIDStr := r.URL.Query().Get("user_id")
	userID, err := strconv.Atoi(userIDStr)
	if err != nil {
		http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
		log.Println("Invalid user_id parameter:", err)
		return
	}

	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

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

	rows, err := db.Query("SELECT symbol FROM user_trading_symbols WHERE user_id = $1", userID)
	if err != nil {
		http.Error(w, "Failed to query database", http.StatusInternalServerError)
		log.Println("Failed to query database:", err)
		return
	}
	defer rows.Close()

	var symbols []string
	for rows.Next() {
		var symbol string
		if err := rows.Scan(&symbol); err != nil {
			http.Error(w, "Failed to scan row", http.StatusInternalServerError)
			log.Println("Failed to scan row:", err)
			return
		}
		symbols = append(symbols, symbol)
	}

	if err := rows.Err(); err != nil {
		http.Error(w, "Error during row iteration", http.StatusInternalServerError)
		log.Println("Error during row iteration:", err)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(symbols)
}

func main() {
	http.HandleFunc("/getPotentialSymbols", getPotentialSymbols)
	http.HandleFunc("/health", healthCheck)
	http.HandleFunc("/inputOTP", inputOTP)
	http.HandleFunc("/userTrade", userTrade)
	http.HandleFunc("/getUserTrade", getUserTrade)
	fmt.Println("Server listening on :8080")
	addr := net.JoinHostPort("::", "8080")
	server := &http.Server{Addr: addr}
	log.Fatalln(server.ListenAndServe())
}
