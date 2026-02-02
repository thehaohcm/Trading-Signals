package models

import "time"

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

type UpdateSignalRequest struct {
	UserID         string `json:"user_id"`
	Symbol         string `json:"symbol"`
	BreakEvenPrice int    `json:"break_even_price"`
}

type PriceAlert struct {
	Symbol         string     `json:"symbol"`
	AssetType      string     `json:"asset_type"`
	AlertPrice     float64    `json:"alert_price"`
	Operator       string     `json:"operator"`
	IsActive       bool       `json:"is_active"`
	LastNotifiedAt *time.Time `json:"last_notified_at,omitempty"`
	CreatedAt      time.Time  `json:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at"`
}

type JournalEntry struct {
	ID        int       `json:"id"`
	UserID    string    `json:"user_id"`
	AssetType string    `json:"asset_type"`
	Symbol    string    `json:"symbol"`
	Quantity  float64   `json:"quantity"`
	Price     float64   `json:"price"`
	EntryDate time.Time `json:"entry_date"`
	Notes     string    `json:"notes"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type CreateJournalEntryRequest struct {
	AssetType string    `json:"asset_type"`
	Symbol    string    `json:"symbol"`
	Quantity  float64   `json:"quantity"`
	Price     float64   `json:"price"`
	EntryDate time.Time `json:"entry_date"`
	Notes     string    `json:"notes"`
}

type UpdateJournalEntryRequest struct {
	ID        int       `json:"id"`
	AssetType string    `json:"asset_type"`
	Symbol    string    `json:"symbol"`
	Quantity  float64   `json:"quantity"`
	Price     float64   `json:"price"`
	EntryDate time.Time `json:"entry_date"`
	Notes     string    `json:"notes"`
}

type CreateAlertRequest struct {
	Symbol     string  `json:"symbol"`
	AssetType  string  `json:"asset_type"`
	AlertPrice float64 `json:"alert_price"`
	Operator   string  `json:"operator"`
}

type UpdateAlertRequest struct {
	AlertPrice float64 `json:"alert_price,omitempty"`
	Operator   string  `json:"operator,omitempty"`
	IsActive   *bool   `json:"is_active,omitempty"`
}

type CommunityPost struct {
	ID        int       `json:"id"`
	UserID    string    `json:"user_id"`
	UserName  string    `json:"user_name"`
	UserCode  string    `json:"user_code"`
	Content   string    `json:"content"`
	Image     string    `json:"image"`
	Likes     int       `json:"likes"`
	CreatedAt time.Time `json:"created_at"`
}

type CreateCommunityPostRequest struct {
	UserID   string `json:"user_id"`
	UserName string `json:"user_name"`
	UserCode string `json:"user_code"`
	Content  string `json:"content"`
	Image    string `json:"image"`
}

type CommunityComment struct {
	ID        int       `json:"id"`
	PostID    int       `json:"post_id"`
	UserID    string    `json:"user_id"`
	UserName  string    `json:"user_name"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}

type CreateCommunityCommentRequest struct {
	PostID   int    `json:"post_id"`
	UserID   string `json:"user_id"`
	UserName string `json:"user_name"`
	Content  string `json:"content"`
}

type RealEstatePrice struct {
	ID           int64     `json:"id"`
	Region       string    `json:"region"`
	Location     string    `json:"location"`
	PriceText    string    `json:"price_text"`
	PriceNumeric int64     `json:"price_numeric"`
	PropertyType string    `json:"property_type"`
	URL          string    `json:"url"`
	FetchedAt    time.Time `json:"fetched_at"`
	Area         float64   `json:"area"`
}
