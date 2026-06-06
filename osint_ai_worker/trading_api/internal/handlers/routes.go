package handlers

import (
	"database/sql"

	"github.com/gorilla/mux"
)

func RegisterNewsRoutes(r *mux.Router, db *sql.DB) {
	// Generate AI Prompt
	r.HandleFunc("/api/news-groups/generate-prompt", GenerateStrategyPrompt(db)).Methods("GET")

	// News Items - register toggle before generic items endpoint
	r.HandleFunc("/api/news-items/toggle", ToggleNewsItemStatus(db)).Methods("POST")
	r.HandleFunc("/api/news-items", GetNewsItems(db)).Methods("GET")
	r.HandleFunc("/api/news-items", CreateNewsItem(db)).Methods("POST")
	r.HandleFunc("/api/news-items", UpdateNewsItem(db)).Methods("PUT")
	r.HandleFunc("/api/news-items", DeleteNewsItem(db)).Methods("DELETE")

	// News Groups
	r.HandleFunc("/api/news-groups", GetNewsGroups(db)).Methods("GET")
	r.HandleFunc("/api/news-groups", CreateNewsGroup(db)).Methods("POST")
	r.HandleFunc("/api/news-groups", UpdateNewsGroup(db)).Methods("PUT")
	r.HandleFunc("/api/news-groups", DeleteNewsGroup(db)).Methods("DELETE")
}
