package handlers

import (
	"encoding/json"
	"net/http"
)

func (h *Handler) GetRealEstate(w http.ResponseWriter, r *http.Request) {
	// Enable CORS if needed (though usually handled by middleware or main)
	w.Header().Set("Access-Control-Allow-Origin", "*")

	region := r.URL.Query().Get("region")
	propType := r.URL.Query().Get("type")

	data, err := h.Repo.GetRealEstatePrices(region, propType)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}
