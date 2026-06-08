package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"trading_api/internal/models"
)

// CRUD for NewsGroup
func GetNewsGroups(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userID := r.URL.Query().Get("user_id")
		var rows *sql.Rows
		var err error
		if userID != "" {
			rows, err = db.Query(`SELECT id, user_id, name, description, conclusion, created_at FROM news_groups WHERE user_id = $1 OR name = 'Telegram News' ORDER BY created_at DESC`, userID)
		} else {
			rows, err = db.Query(`SELECT id, user_id, name, description, conclusion, created_at FROM news_groups ORDER BY created_at DESC`)
		}
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()
		var groups []models.NewsGroup
		for rows.Next() {
			var g models.NewsGroup
			var desc, conc sql.NullString
			if err := rows.Scan(&g.ID, &g.UserID, &g.Name, &desc, &conc, &g.CreatedAt); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			if desc.Valid {
				g.Description = desc.String
			}
			if conc.Valid {
				g.Conclusion = conc.String
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
		// Validate name is not empty
		if strings.TrimSpace(g.Name) == "" {
			http.Error(w, "Name is required", 400)
			return
		}
		if strings.EqualFold(strings.TrimSpace(g.Name), "Telegram News") {
			http.Error(w, "Cannot manually create Telegram News group", 403)
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
		
		// Check if target is Telegram News
		var existingName string
		err := db.QueryRow(`SELECT name FROM news_groups WHERE id = $1`, id).Scan(&existingName)
		if err == nil && strings.EqualFold(existingName, "Telegram News") {
			http.Error(w, "Cannot modify Telegram News group", 403)
			return
		}

		var g models.NewsGroup
		if err := json.NewDecoder(r.Body).Decode(&g); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		if strings.EqualFold(strings.TrimSpace(g.Name), "Telegram News") {
			http.Error(w, "Cannot rename group to Telegram News", 403)
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
		// Check if target is Telegram News
		var existingName string
		err := db.QueryRow(`SELECT name FROM news_groups WHERE id = $1`, id).Scan(&existingName)
		if err == nil && strings.EqualFold(existingName, "Telegram News") {
			http.Error(w, "Cannot delete Telegram News group", 403)
			return
		}

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
		
		// Check if target group is Telegram News
		var groupName string
		err := db.QueryRow(`SELECT name FROM news_groups WHERE id = $1`, groupID).Scan(&groupName)
		if err == nil && strings.EqualFold(groupName, "Telegram News") {
			http.Error(w, "Cannot manually add news to Telegram News", 403)
			return
		}

		var ni models.NewsItem
		if err := json.NewDecoder(r.Body).Decode(&ni); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		err = db.QueryRow(`INSERT INTO news_items (group_id, title, content, source_url, importance, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, created_at`, groupID, ni.Title, ni.Content, ni.SourceURL, ni.Importance, ni.Status).Scan(&ni.ID, &ni.CreatedAt)
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
		
		// Check if item belongs to Telegram News
		var groupName string
		err := db.QueryRow(`SELECT g.name FROM news_items i JOIN news_groups g ON i.group_id = g.id WHERE i.id = $1`, id).Scan(&groupName)
		if err == nil && strings.EqualFold(groupName, "Telegram News") {
			http.Error(w, "Cannot modify Telegram News items", 403)
			return
		}

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
		
		// Check if item belongs to Telegram News
		var groupName string
		err := db.QueryRow(`SELECT g.name FROM news_items i JOIN news_groups g ON i.group_id = g.id WHERE i.id = $1`, id).Scan(&groupName)
		if err == nil && strings.EqualFold(groupName, "Telegram News") {
			http.Error(w, "Cannot delete Telegram News items", 403)
			return
		}

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
		
		// Check if item belongs to Telegram News
		var groupName string
		var status string
		err := db.QueryRow(`SELECT g.name, i.status FROM news_items i JOIN news_groups g ON i.group_id = g.id WHERE i.id = $1`, id).Scan(&groupName, &status)
		if err != nil {
			http.Error(w, "Not found", 404)
			return
		}
		if strings.EqualFold(groupName, "Telegram News") {
			http.Error(w, "Cannot modify Telegram News items status", 403)
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
		prompt := "Bạn là chuyên gia phân tích vĩ mô. Hãy xác thực các sự kiện kinh tế vĩ mô đang diễn ra dưới đây là đúng hay sai, đã kết hạn (đã xảy ra) hay chưa, đưa ra các tin liên quan (nếu có) và phân tích tác động của chúng:\n"
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
		prompt += "\nYêu cầu: Phân tích tác động chéo, dòng tiền (flow of funds) và đưa ra nhận định cho Vàng, USD (DXY), lợi suất trái phiếu, Crypto, Chứng khoán Mỹ, Chứng khoán Việt Nam (các nhóm ngành hưởng lợi), bất động sản Việt Nam. Trình bày dưới dạng Bullet points, súc tích, đi thẳng vào vấn đề. Nếu có sự phân kỳ (Divergence) giữa tin tức và biểu đồ kỹ thuật (giả định), hãy đưa ra cảnh báo cho nhà đầu tư. Nếu có tin tức nào quan trọng nhưng chưa xuất hiện trong danh sách trên, hãy bổ sung vào phân tích. Nếu có tiền, tôi nên để vào đâu lúc này?"
		json.NewEncoder(w).Encode(map[string]string{"prompt": prompt})
	}
}

// triggered for deploy
