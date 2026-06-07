package handlers

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"trading_api/internal/models"
)

var (
	thesesCache = make(map[string]cachedTheses)
	cacheMutex  sync.RWMutex
)

type cachedTheses struct {
	Theses []models.OsintThesis
	Hash   string
	Expiry time.Time
}

// OSINT Handlers

func (h *Handler) GetWorldState(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	state, err := h.Repo.GetWorldState()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get world state: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, state)
}

func (h *Handler) GetSignals(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	signals, err := h.Repo.GetSignals()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get signals: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, signals)
}

func (h *Handler) GetTheses(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	userID := r.URL.Query().Get("user_id")
	bypassCache := r.URL.Query().Get("refresh") == "true" || r.URL.Query().Get("force") == "true"

	theses, err := h.Repo.GetTheses()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get theses: "+err.Error())
		return
	}

	if userID != "" && userID != "undefined" && userID != "null" {
		entries, err := h.Repo.GetJournalEntries(userID)
		if err == nil && len(entries) > 0 {
			var sb strings.Builder
			for _, t := range theses {
				sb.WriteString(t.UpdatedAt.Format(time.RFC3339Nano))
			}
			for _, e := range entries {
				sb.WriteString(e.UpdatedAt.Format(time.RFC3339Nano))
				sb.WriteString(fmt.Sprintf("%f", e.Quantity))
				sb.WriteString(fmt.Sprintf("%f", e.Price))
			}
			hashBytes := sha256.Sum256([]byte(sb.String()))
			hashStr := hex.EncodeToString(hashBytes[:])

			cacheMutex.RLock()
			cached, exists := thesesCache[userID]
			cacheMutex.RUnlock()

			if !bypassCache && exists && cached.Hash == hashStr && time.Now().Before(cached.Expiry) {
				theses = cached.Theses
			} else {
				theses = h.PersonalizeTheses(theses, entries)
				
				cacheMutex.Lock()
				thesesCache[userID] = cachedTheses{
					Theses: theses,
					Hash:   hashStr,
					Expiry: time.Now().Add(24 * time.Hour),
				}
				cacheMutex.Unlock()
			}
		}
	}

	respondJSON(w, http.StatusOK, theses)
}

func (h *Handler) PersonalizeTheses(theses []models.OsintThesis, entries []models.JournalEntry) []models.OsintThesis {
	if len(theses) == 0 || len(entries) == 0 {
		return theses
	}

	var portfolioStr string
	for _, e := range entries {
		portfolioStr += fmt.Sprintf("- %s: %s (Qty: %.2f, Price: %.2f %s)\n", e.AssetType, e.Symbol, e.Quantity, e.Price, e.Currency)
	}

	var thesesStr string
	for i, t := range theses {
		thesesStr += fmt.Sprintf("[%d] ID: %s\nThesis: %s\nOriginal Advice: %s\n", i, t.ID, t.Thesis, t.SupportingEvidence)
	}

	prompt := fmt.Sprintf(`Bạn là AI cố vấn quản lý tài sản cá nhân.
Dưới đây là các Nhận định vĩ mô hiện tại:
%s

Dưới đây là Danh mục tài sản hiện tại của người dùng (từ Journal):
%s

Nhiệm vụ của bạn là: Cập nhật phần "Hành động & Bảo vệ tài sản" (Original Advice) của từng nhận định sao cho CỤ THỂ HÓA đối với danh mục tài sản của người dùng.
Chỉ trả về JSON theo định dạng sau (không markdown, không giải thích thêm):
{
  "theses": [
    {
      "id": "ID của nhận định",
      "personalized_advice": "Lời khuyên hành động mới, dựa trên cả nhận định vĩ mô và danh mục hiện tại của người dùng. (Nêu cụ thể người dùng nên làm gì với các mã tài sản họ đang giữ)"
    }
  ]
}`, thesesStr, portfolioStr)

	geminiAPIKey := os.Getenv("GEMINI_API_KEY")
	if geminiAPIKey == "" {
		return theses
	}

	geminiReq := GeminiRequest{
		Contents: []GeminiContent{
			{Parts: []GeminiPart{{Text: prompt}}},
		},
	}

	jsonData, _ := json.Marshal(geminiReq)
	geminiURL := "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
	req, _ := http.NewRequest("POST", geminiURL, bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-goog-api-key", geminiAPIKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return theses
	}
	defer resp.Body.Close()

	var geminiResp GeminiResponse
	if err := json.NewDecoder(resp.Body).Decode(&geminiResp); err != nil {
		return theses
	}

	if len(geminiResp.Candidates) == 0 || len(geminiResp.Candidates[0].Content.Parts) == 0 {
		return theses
	}

	responseText := geminiResp.Candidates[0].Content.Parts[0].Text
	responseText = strings.TrimPrefix(strings.TrimSpace(responseText), "```json")
	responseText = strings.TrimSuffix(strings.TrimSpace(responseText), "```")

	var result struct {
		Theses []struct {
			ID                 string `json:"id"`
			PersonalizedAdvice string `json:"personalized_advice"`
		} `json:"theses"`
	}

	if err := json.Unmarshal([]byte(responseText), &result); err != nil {
		return theses
	}

	adviceMap := make(map[string]string)
	for _, t := range result.Theses {
		adviceMap[t.ID] = t.PersonalizedAdvice
	}

	var personalizedTheses []models.OsintThesis
	for _, t := range theses {
		if adv, ok := adviceMap[t.ID]; ok && adv != "" {
			t.SupportingEvidence = adv
		}
		personalizedTheses = append(personalizedTheses, t)
	}

	return personalizedTheses
}
