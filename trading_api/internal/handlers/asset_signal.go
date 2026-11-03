package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"trading_api/internal/models"
)

// AssetSignalsHandler serves the AI buy/avoid status per asset group.
//
//	GET  /api/asset-signals  -> list (public, same as theses)
//	POST /api/asset-signals  -> set / clear the admin override (requires a signed-in user)
func (h *Handler) AssetSignalsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	switch r.Method {
	case http.MethodGet:
		signals, err := h.Repo.GetAssetSignals()
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Failed to get asset signals: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, signals)

	case http.MethodPost, http.MethodPut:
		if !isRequestAuthorized(r) {
			respondError(w, http.StatusUnauthorized, "Yêu cầu đăng nhập admin để thay đổi trạng thái")
			return
		}
		var req models.SetAssetSignalOverrideRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		if r := []rune(strings.TrimSpace(req.Note)); len(r) > 500 {
			req.Note = string(r[:500])
		}
		req.AssetKey = strings.ToLower(strings.TrimSpace(req.AssetKey))
		req.Status = strings.ToLower(strings.TrimSpace(req.Status))
		if req.AssetKey == "" {
			respondError(w, http.StatusBadRequest, "asset_key is required")
			return
		}
		if req.Status != "" && req.Status != "ai" && req.Status != "buy" && req.Status != "avoid" {
			respondError(w, http.StatusBadRequest, "status must be 'buy', 'avoid' or 'ai'")
			return
		}
		updatedBy := strings.TrimSpace(req.UpdatedBy)
		if updatedBy == "" {
			updatedBy = authorizedSubject(r) // nhãn lấy từ JWT đã xác thực
		}
		if err := h.Repo.SetAssetSignalOverride(req.AssetKey, req.Status, updatedBy, req.Note); err != nil {
			respondError(w, http.StatusBadRequest, "Failed to update asset signal: "+err.Error())
			return
		}
		signals, err := h.Repo.GetAssetSignals()
		if err != nil {
			respondError(w, http.StatusInternalServerError, "Updated, but failed to reload: "+err.Error())
			return
		}
		respondJSON(w, http.StatusOK, signals)

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// AssetSignalHistoryHandler returns the audit trail of admin-status changes (who: user / automatic logic, which rule, note).
//
//	GET /api/asset-signals/history?asset_key=gold&limit=50
func (h *Handler) AssetSignalHistoryHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != http.MethodGet {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	changes, err := h.Repo.GetAssetSignalChanges(strings.ToLower(strings.TrimSpace(r.URL.Query().Get("asset_key"))), limit)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get asset signal history: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, changes)
}
