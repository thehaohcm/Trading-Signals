package handlers

import (
	"database/sql"

	"github.com/gorilla/mux"
)

func RegisterNewsRoutes(r *mux.Router, db *sql.DB) {
	// News Groups
	r.HandleFunc("/api/news-groups", GetNewsGroups(db)).Methods("GET")
	r.HandleFunc("/api/news-groups", CreateNewsGroup(db)).Methods("POST")
	r.HandleFunc("/api/news-groups/{id}", UpdateNewsGroup(db)).Methods("PUT")
	r.HandleFunc("/api/news-groups/{id}", DeleteNewsGroup(db)).Methods("DELETE")

	// News Items
	r.HandleFunc("/api/news-groups/{group_id}/items", GetNewsItems(db)).Methods("GET")
	r.HandleFunc("/api/news-groups/{group_id}/items", CreateNewsItem(db)).Methods("POST")
	r.HandleFunc("/api/news-items/{id}", UpdateNewsItem(db)).Methods("PUT")
	r.HandleFunc("/api/news-items/{id}", DeleteNewsItem(db)).Methods("DELETE")
	r.HandleFunc("/api/news-items/{id}/toggle", ToggleNewsItemStatus(db)).Methods("POST")

	// Generate AI Prompt
	r.HandleFunc("/api/news-groups/generate-prompt", GenerateStrategyPrompt(db)).Methods("GET")
}
