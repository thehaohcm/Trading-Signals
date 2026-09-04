package models

import "time"

type SymbolData struct {
	Symbol       string  `json:"symbol"`
	SignalType   string  `json:"signal_type"`
	SignalLabel  string  `json:"signal_label"`
	Volume       int64   `json:"volume"`
	HighestPrice float64 `json:"highest_price"`
	LowestPrice  float64 `json:"lowest_price"`
	ScoreDiff    float64 `json:"score_diff"`
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
	Crypto       string  `json:"crypto"`
	IsAth        string  `json:"is_ath"`
	SignalType   string  `json:"signal_type"`
	SignalLabel  string  `json:"signal_label"`
	HighestPrice float64 `json:"highest_price"`
	MarketCap    float64 `json:"market_cap"`
	ScoreDiff    float64 `json:"score_diff"`
}

type CryptoDataResponse struct {
	Data          []CryptoData `json:"data"`
	LatestUpdated time.Time    `json:"latest_updated"`
}

type FuturesData struct {
	Symbol       string  `json:"symbol"`
	SignalType   string  `json:"signal_type"`
	SignalLabel  string  `json:"signal_label"`
	HighestPrice float64 `json:"highest_price"`
	MarketCap    float64 `json:"market_cap"`
}

type FuturesDataResponse struct {
	Data          []FuturesData `json:"data"`
	LatestUpdated time.Time     `json:"latest_updated"`
}

type TriggeredAlert struct {
	ID        int       `json:"id"`
	AssetType string    `json:"asset_type"`
	Symbol    string    `json:"symbol"`
	Price     float64   `json:"price"`
	Message   string    `json:"message"`
	IsRead    bool      `json:"is_read"`
	CreatedAt time.Time `json:"created_at"`
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
	ID           int       `json:"id"`
	UserID       string    `json:"user_id"`
	AssetType    string    `json:"asset_type"`
	Symbol       string    `json:"symbol"`
	Quantity     float64   `json:"quantity"`
	Price        float64   `json:"price"`
	Currency     string    `json:"currency"`
	EntryDate    time.Time `json:"entry_date"`
	Notes        string    `json:"notes"`
	CurrentPrice *float64  `json:"current_price,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type CreateJournalEntryRequest struct {
	AssetType    string    `json:"asset_type"`
	Symbol       string    `json:"symbol"`
	Quantity     float64   `json:"quantity"`
	Price        float64   `json:"price"`
	Currency     string    `json:"currency"`
	EntryDate    time.Time `json:"entry_date"`
	Notes        string    `json:"notes"`
	CurrentPrice *float64  `json:"current_price,omitempty"`
}

type UpdateJournalEntryRequest struct {
	ID           int       `json:"id"`
	AssetType    string    `json:"asset_type"`
	Symbol       string    `json:"symbol"`
	Quantity     float64   `json:"quantity"`
	Price        float64   `json:"price"`
	Currency     string    `json:"currency"`
	EntryDate    time.Time `json:"entry_date"`
	Notes        string    `json:"notes"`
	CurrentPrice *float64  `json:"current_price,omitempty"`
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

// Breakout Watchlist & Paper Trading Models
type BreakoutWatchlistItem struct {
	ID            int       `json:"id"`
	Symbol        string    `json:"symbol"`
	AssetType     string    `json:"asset_type"`
	Name          string    `json:"name"`
	ATHPrice      float64   `json:"ath_price"`
	InitialBudget float64   `json:"initial_budget"`
	StepPct       float64   `json:"step_pct"`
	PyramidRatio  float64   `json:"pyramid_ratio"`
	SLPct         float64   `json:"sl_pct"`
	MaxPyramids   int       `json:"max_pyramids"`
	IsActive      bool      `json:"is_active"`
	IsRealTrading bool      `json:"is_real_trading"`
	SpreadPct     float64   `json:"spread_pct"`
	Notes         string    `json:"notes"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`

	// Enriched fields
	HasOpenPosition bool    `json:"has_open_position"`
	CurrentPrice    float64 `json:"current_price,omitempty"`
}

type PaperPosition struct {
	ID               int          `json:"id"`
	WatchlistID      int          `json:"watchlist_id"`
	Symbol           string       `json:"symbol"`
	AssetType        string       `json:"asset_type"`
	Status           string       `json:"status"` // OPEN, CLOSED_SL, CLOSED_TP, CLOSED_MANUAL
	CurrentLayer     int          `json:"current_layer"`
	TotalInvested    float64      `json:"total_invested"`
	TotalUnits       float64      `json:"total_units"`
	AvgEntryPrice    float64      `json:"avg_entry_price"`
	LastBuyPrice     float64      `json:"last_buy_price"`
	HighestPrice     float64      `json:"highest_price"`
	CurrentPrice     float64      `json:"current_price"`
	StopLossPrice    float64      `json:"stop_loss_price"`
	NextPyramidPrice float64      `json:"next_pyramid_price"`
	SpreadPct        float64      `json:"spread_pct"`
	BreakevenPrice   float64      `json:"breakeven_price"`
	UnrealizedPnL    float64      `json:"unrealized_pnl"`
	UnrealizedROIPct float64      `json:"unrealized_roi_pct"`
	RealizedPnL      float64      `json:"realized_pnl"`
	OpenedAt         time.Time    `json:"opened_at"`
	ClosedAt         *time.Time   `json:"closed_at,omitempty"`
	CloseReason      string       `json:"close_reason,omitempty"`
	UpdatedAt        time.Time    `json:"updated_at"`
	Orders           []PaperOrder `json:"orders,omitempty"`
}

type PaperOrder struct {
	ID         int       `json:"id"`
	PositionID int       `json:"position_id"`
	Symbol     string    `json:"symbol"`
	OrderType  string    `json:"order_type"` // INITIAL_BUY, PYRAMID_BUY, STOP_LOSS, MANUAL_CLOSE
	Layer      int       `json:"layer"`
	Price      float64   `json:"price"`
	AmountUSD  float64   `json:"amount_usd"`
	Units      float64   `json:"units"`
	Reason     string    `json:"reason"`
	CreatedAt  time.Time `json:"created_at"`
}

type BreakoutLeaderboardItem struct {
	Symbol           string  `json:"symbol"`
	AssetType        string  `json:"asset_type"`
	TotalTrades      int     `json:"total_trades"`
	WinningTrades    int     `json:"winning_trades"`
	WinRatePct       float64 `json:"win_rate_pct"`
	TotalRealizedPnL float64 `json:"total_realized_pnl"`
	MaxROI           float64 `json:"max_roi"`
	AvgROI           float64 `json:"avg_roi"`
	CurrentStatus    string  `json:"current_status"`
	CurrentPnL       float64 `json:"current_pnl"`
	CurrentROI       float64 `json:"current_roi"`
	CurrentLayer     int     `json:"current_layer"`
}

type EconomicEvent struct {
	ID        int       `json:"id"`
	Title     string    `json:"title"`
	Country   string    `json:"country"`
	Date      time.Time `json:"date"`
	Impact    string    `json:"impact"`
	Forecast  string    `json:"forecast"`
	Previous  string    `json:"previous"`
	Actual    string    `json:"actual"`
	Surprise  string    `json:"surprise"`
	Status    string    `json:"status"`
	UpdatedAt time.Time `json:"updated_at"`
}

type OsintPodcast struct {
	ID              string    `json:"id"`
	Session         string    `json:"session"`
	SessionName     string    `json:"session_name"`
	Title           string    `json:"title"`
	AudioURL        string    `json:"audio_url"`
	DurationSeconds int       `json:"duration_seconds"`
	ScriptText      string    `json:"script_text"`
	CreatedAt       time.Time `json:"created_at"`
}

type TakeNote struct {
	ID        int64     `json:"id"`
	UserID    string    `json:"user_id"`
	Text      string    `json:"text"`
	Edited    bool      `json:"edited"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type CreateTakeNoteRequest struct {
	Text string `json:"text"`
}

type UpdateTakeNoteRequest struct {
	ID   int64  `json:"id"`
	Text string `json:"text"`
}

// Live Trading & API Settings Models
type TradingSettings struct {
	TradingMode    string `json:"trading_mode"`    // "demo" | "real"
	CryptoExchange string `json:"crypto_exchange"` // "binance" | "okx" | "bybit"

	// Binance
	BinanceAPIKey          string  `json:"binance_api_key"`
	BinanceAPISecret       string  `json:"binance_api_secret"`
	BinanceTestnet         bool    `json:"binance_testnet"`
	BinanceTradeAmountUSDT float64 `json:"binance_trade_amount_usdt"`
	HasBinanceKey          bool    `json:"has_binance_key"`
	HasBinanceSecret       bool    `json:"has_binance_secret"`

	// OKX
	OKXAPIKey          string  `json:"okx_api_key"`
	OKXSecretKey       string  `json:"okx_secret_key"`
	OKXPassphrase      string  `json:"okx_passphrase"`
	OKXSimulated       bool    `json:"okx_simulated"`
	OKXTradeAmountUSDT float64 `json:"okx_trade_amount_usdt"`
	HasOKXKey          bool    `json:"has_okx_key"`
	HasOKXSecret       bool    `json:"has_okx_secret"`
	HasOKXPassphrase   bool    `json:"has_okx_passphrase"`

	// Bybit
	BybitAPIKey          string  `json:"bybit_api_key"`
	BybitAPISecret       string  `json:"bybit_api_secret"`
	BybitTestnet         bool    `json:"bybit_testnet"`
	BybitTradeAmountUSDT float64 `json:"bybit_trade_amount_usdt"`
	HasBybitKey          bool    `json:"has_bybit_key"`
	HasBybitSecret       bool    `json:"has_bybit_secret"`

	// MT5
	MT5Account     string  `json:"mt5_account"`
	MT5Password    string  `json:"mt5_password"`
	MT5Server      string  `json:"mt5_server"`
	MT5Path        string  `json:"mt5_path"`
	MT5LotSize     float64 `json:"mt5_lot_size"`
	HasMT5Password bool    `json:"has_mt5_password"`
}

type TestTradingConnectionRequest struct {
	Platform string `json:"platform"`
}

type TestTradingConnectionResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Latency int64  `json:"latency_ms,omitempty"`
}
