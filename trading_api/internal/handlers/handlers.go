package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"trading_api/internal/models"
	"trading_api/internal/repository"
)

type Handler struct {
	Repo *repository.Repository
}

func NewHandler(repo *repository.Repository) *Handler {
	return &Handler{Repo: repo}
}

// Helpers
func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if data != nil {
		json.NewEncoder(w).Encode(data)
	}
}

func respondError(w http.ResponseWriter, status int, message string) {
	log.Println("Error:", message)
	http.Error(w, message, status)
}

func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

// Health Check
func (h *Handler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

// Watchlist Handlers
func (h *Handler) GetPotentialSymbols(w http.ResponseWriter, r *http.Request) {
	symbols, latestUpdated, err := h.Repo.GetPotentialSymbols()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to query database: "+err.Error())
		return
	}

	response := models.SymbolDataResponse{
		Data:          symbols,
		LatestUpdated: latestUpdated,
	}
	respondJSON(w, http.StatusOK, response)
}

func (h *Handler) GetPotentialWorldSymbols(w http.ResponseWriter, r *http.Request) {
	symbols, latestUpdated, err := h.Repo.GetPotentialWorldSymbols()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to query database: "+err.Error())
		return
	}

	response := models.WorldSymbolDataResponse{
		Data:          symbols,
		LatestUpdated: latestUpdated,
	}
	respondJSON(w, http.StatusOK, response)
}

func (h *Handler) GetPotentialCoins(w http.ResponseWriter, r *http.Request) {
	cryptos, latestUpdated, err := h.Repo.GetPotentialCoins()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to query database: "+err.Error())
		return
	}

	response := models.CryptoDataResponse{
		Data:          cryptos,
		LatestUpdated: latestUpdated,
	}
	respondJSON(w, http.StatusOK, response)
}

func (h *Handler) GetPotentialForexPairs(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	pairs, latestUpdated, err := h.Repo.GetPotentialForexPairs()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to query database: "+err.Error())
		return
	}

	response := models.ForexPairResponse{
		Data:          pairs,
		LatestUpdated: latestUpdated,
	}
	respondJSON(w, http.StatusOK, response)
}

// User Handlers
func (h *Handler) InputOTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var userInfo models.UserInfo
	if err := json.NewDecoder(r.Body).Decode(&userInfo); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body: "+err.Error())
		return
	}

	if err := h.Repo.UpsertUserInfo(userInfo); err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to insert/update data: "+err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Data inserted/updated successfully")
}

func (h *Handler) UserTrade(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req models.UserTradeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body: "+err.Error())
		return
	}

	var err error
	switch req.Operator {
	case "Add", "Update":
		err = h.Repo.UpdateUserTrades(req.UserID, req.Stocks)
	case "Delete":
		err = h.Repo.DeleteUserTrades(req.UserID, req.Stocks)
	default:
		respondError(w, http.StatusBadRequest, "Invalid operator")
		return
	}

	if err != nil {
		respondError(w, http.StatusInternalServerError, "Operation failed: "+err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Operation completed successfully")
}

func (h *Handler) GetUserTrade(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		respondError(w, http.StatusBadRequest, "Invalid user_id parameter")
		return
	}

	trades, err := h.Repo.GetUserTrades(userID)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get user trades: "+err.Error())
		return
	}

	respondJSON(w, http.StatusOK, trades)
}

func (h *Handler) UpdateTradingSignal(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var updates []models.UpdateSignalRequest
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body: "+err.Error())
		return
	}

	if err := h.Repo.UpdateTradingSignals(updates); err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to update trading signals: "+err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Portfolio updated successfully")
}

// Journal Handlers
func (h *Handler) JournalHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	userID := r.URL.Query().Get("user_id")
	// For GET, user_id is required. For others, it might be in body or implicit (in a real app from auth context),
	// but here we follow original logic which used user_id from query or hardcoded checking.
	// Original logic:
	// GET: needs user_id in query
	// POST/PUT/DELETE: userID comes from... wait, original logic used `userID := r.URL.Query().Get("user_id")` at top level for all methods?
	// Let's check original code. Yes, line 1162: `userID := r.URL.Query().Get("user_id")`.

	if userID == "" && (r.Method == http.MethodGet || r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodDelete) {
		respondError(w, http.StatusBadRequest, "Missing user_id parameter")
		return
	}

	switch r.Method {
	case http.MethodGet:
		entries, err := h.Repo.GetJournalEntries(userID)
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to get entries: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, entries)

	case http.MethodPost:
		var req models.CreateJournalEntryRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if err := h.Repo.CreateJournalEntry(userID, req); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to create entry: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Entry created successfully"})

	case http.MethodPut:
		var req models.UpdateJournalEntryRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if err := h.Repo.UpdateJournalEntry(userID, req); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to update entry: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Entry updated successfully"})

	case http.MethodDelete:
		idStr := r.URL.Query().Get("id")
		if idStr == "" {
			respondError(w, http.StatusBadRequest, "Missing id parameter")
			return
		}
		id, _ := strconv.Atoi(idStr)
		if err := h.Repo.DeleteJournalEntry(userID, id); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to delete entry: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Entry deleted successfully"})

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// Community Handlers
func (h *Handler) CommunityPostsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	switch r.Method {
	case http.MethodGet:
		posts, err := h.Repo.GetCommunityPosts()
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to get posts: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, posts)

	case http.MethodPost:
		var req models.CreateCommunityPostRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if req.Content == "" && req.Image == "" {
			respondError(w, http.StatusBadRequest, "Content or Image is required")
			return
		}
		post, err := h.Repo.CreateCommunityPost(req)
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to create post: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, post)

	case http.MethodDelete:
		idStr := r.URL.Query().Get("id")
		if idStr == "" {
			respondError(w, http.StatusBadRequest, "Missing id parameter")
			return
		}
		id, _ := strconv.Atoi(idStr)
		if err := h.Repo.DeleteCommunityPost(id); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to delete post: "+err.Error())
			return
		}
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "Post deleted successfully")

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (h *Handler) CommunityCommentsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	switch r.Method {
	case http.MethodGet:
		postIDStr := r.URL.Query().Get("post_id")
		if postIDStr == "" {
			respondError(w, http.StatusBadRequest, "Missing post_id parameter")
			return
		}
		postID, _ := strconv.Atoi(postIDStr)
		comments, err := h.Repo.GetCommunityComments(postID)
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to get comments: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, comments)

	case http.MethodPost:
		var req models.CreateCommunityCommentRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if req.Content == "" {
			respondError(w, http.StatusBadRequest, "Content is required")
			return
		}
		comment, err := h.Repo.CreateCommunityComment(req)
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to create comment: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, comment)

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// Price Alert Handlers
func (h *Handler) PriceAlertsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	switch r.Method {
	case http.MethodGet:
		assetType := r.URL.Query().Get("asset_type")
		alerts, err := h.Repo.GetPriceAlerts(assetType)
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to get alerts: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, alerts)

	case http.MethodPost:
		var req models.CreateAlertRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if req.Symbol == "" || req.AssetType == "" || req.AlertPrice <= 0 {
			respondError(w, http.StatusBadRequest, "Missing required fields")
			return
		}
		if req.Operator != "<=" && req.Operator != ">=" {
			req.Operator = "<="
		}
		if err := h.Repo.CreatePriceAlert(req); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to create alert: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Alert created successfully"})

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (h *Handler) PriceAlertHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	pathParts := strings.Split(strings.TrimPrefix(r.URL.Path, "/priceAlerts/"), "/")
	if len(pathParts) < 2 {
		respondError(w, http.StatusBadRequest, "Invalid URL format. Expected: /priceAlerts/{symbol}/{asset_type}")
		return
	}
	symbol := pathParts[0]
	assetType := pathParts[1]

	switch r.Method {
	case http.MethodPut:
		var req models.UpdateAlertRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if err := h.Repo.UpdatePriceAlert(symbol, assetType, req); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to update alert: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Alert updated successfully"})

	case http.MethodDelete:
		if err := h.Repo.DeletePriceAlert(symbol, assetType); err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to delete alert: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, map[string]string{"message": "Alert deleted successfully"})

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// Chat Handler
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

func (h *Handler) ChatHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var chatReq ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&chatReq); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if chatReq.Message == "" {
		respondError(w, http.StatusBadRequest, "Message cannot be empty")
		return
	}

	groqAPIKey := os.Getenv("GROQ_API_KEY")
	if groqAPIKey == "" {
		respondError(w, http.StatusInternalServerError, "Groq API key not configured")
		return
	}

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
		respondError(w, http.StatusInternalServerError, "Failed to marshal request: "+err.Error())
		return
	}

	req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to create request: "+err.Error())
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+groqAPIKey)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to call Groq API: "+err.Error())
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		log.Printf("Groq API error: %s", string(body))
		respondError(w, resp.StatusCode, "Groq API returned error")
		return
	}

	var groqResp GroqResponse
	if err := json.NewDecoder(resp.Body).Decode(&groqResp); err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to decode Groq response: "+err.Error())
		return
	}

	if len(groqResp.Choices) == 0 {
		respondError(w, http.StatusInternalServerError, "No response from Groq")
		return
	}

	chatResp := ChatResponse{
		Response: groqResp.Choices[0].Message.Content,
	}
	respondJSON(w, http.StatusOK, chatResp)
}
