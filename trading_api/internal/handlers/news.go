package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"
	"trading_api/internal/models"
)

// CRUD for NewsGroup
func GetNewsGroups(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`SELECT id, user_id, name, description, conclusion, created_at FROM news_groups ORDER BY created_at DESC`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()
		var groups []models.NewsGroup
		for rows.Next() {
			var g models.NewsGroup
			if err := rows.Scan(&g.ID, &g.UserID, &g.Name, &g.Description, &g.Conclusion, &g.CreatedAt); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			groups = append(groups, g)
		}
		json.NewEncoder(w).Encode(groups)
	}
}

func CreateNewsGroup(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var g models.NewsGroup
		if err := json.NewDecoder(r.Body).Decode(&g); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		err := db.QueryRow(`INSERT INTO news_groups (user_id, name, description, conclusion) VALUES ($1, $2, $3, $4) RETURNING id, created_at`, g.UserID, g.Name, g.Description, g.Conclusion).Scan(&g.ID, &g.CreatedAt)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		json.NewEncoder(w).Encode(g)
	}
}

func UpdateNewsGroup(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		var g models.NewsGroup
		if err := json.NewDecoder(r.Body).Decode(&g); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		res, err := db.Exec(`UPDATE news_groups SET name=$1, description=$2, conclusion=$3 WHERE id=$4`, g.Name, g.Description, g.Conclusion, id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if n, _ := res.RowsAffected(); n == 0 {
			http.Error(w, "Not found", 404)
			return
		}
		w.WriteHeader(204)
	}
}

func DeleteNewsGroup(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		res, err := db.Exec(`DELETE FROM news_groups WHERE id=$1`, id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if n, _ := res.RowsAffected(); n == 0 {
			http.Error(w, "Not found", 404)
			return
		}
		w.WriteHeader(204)
	}
}

// CRUD for NewsItem
func GetNewsItems(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		groupID := r.URL.Query().Get("group_id")
		rows, err := db.Query(`SELECT id, group_id, title, content, source_url, importance, status, created_at FROM news_items WHERE group_id = $1 ORDER BY created_at DESC`, groupID)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()
		var items []models.NewsItem
		for rows.Next() {
			var ni models.NewsItem
			if err := rows.Scan(&ni.ID, &ni.GroupID, &ni.Title, &ni.Content, &ni.SourceURL, &ni.Importance, &ni.Status, &ni.CreatedAt); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			items = append(items, ni)
		}
		json.NewEncoder(w).Encode(items)
	}
}

func CreateNewsItem(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		groupID := r.URL.Query().Get("group_id")
		var ni models.NewsItem
		if err := json.NewDecoder(r.Body).Decode(&ni); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		err := db.QueryRow(`INSERT INTO news_items (group_id, title, content, source_url, importance, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, created_at`, groupID, ni.Title, ni.Content, ni.SourceURL, ni.Importance, ni.Status).Scan(&ni.ID, &ni.CreatedAt)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		json.NewEncoder(w).Encode(ni)
	}
}

func UpdateNewsItem(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		var ni models.NewsItem
		if err := json.NewDecoder(r.Body).Decode(&ni); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		res, err := db.Exec(`UPDATE news_items SET title=$1, content=$2, source_url=$3, importance=$4, status=$5 WHERE id=$6`, ni.Title, ni.Content, ni.SourceURL, ni.Importance, ni.Status, id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if n, _ := res.RowsAffected(); n == 0 {
			http.Error(w, "Not found", 404)
			return
		}
		w.WriteHeader(204)
	}
}

func DeleteNewsItem(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		res, err := db.Exec(`DELETE FROM news_items WHERE id=$1`, id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if n, _ := res.RowsAffected(); n == 0 {
			http.Error(w, "Not found", 404)
			return
		}
		w.WriteHeader(204)
	}
}

// Toggle status (active/expired)
func ToggleNewsItemStatus(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		var status string
		err := db.QueryRow(`SELECT status FROM news_items WHERE id=$1`, id).Scan(&status)
		if err != nil {
			http.Error(w, "Not found", 404)
			return
		}
		newStatus := "active"
		if status == "active" {
			newStatus = "expired"
		}
		_, err = db.Exec(`UPDATE news_items SET status=$1 WHERE id=$2`, newStatus, id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		w.WriteHeader(204)
	}
}

// Generate AI Prompt
func GenerateStrategyPrompt(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`SELECT id, name FROM news_groups`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()
		prompt := "Bạn là chuyên gia phân tích vĩ mô. Dưới đây là các sự kiện kinh tế vĩ mô đang diễn ra:\n"
		for rows.Next() {
			var groupID int
			var groupName string
			if err := rows.Scan(&groupID, &groupName); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			prompt += "\nNhóm: " + groupName + "\n"
			itemRows, err := db.Query(`SELECT title, importance FROM news_items WHERE group_id=$1 AND status='active'`, groupID)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			for itemRows.Next() {
				var title string
				var importance int
				if err := itemRows.Scan(&title, &importance); err != nil {
					http.Error(w, err.Error(), 500)
					return
				}
				prompt += "- " + title + " (" + strconv.Itoa(importance) + " sao)\n"
			}
			itemRows.Close()
		}
		prompt += "\nYêu cầu: Phân tích tác động chéo, dòng tiền (flow of funds) và đưa ra nhận định cho Vàng, USD (DXY), Chứng khoán."
		json.NewEncoder(w).Encode(map[string]string{"prompt": prompt})
	}
}
