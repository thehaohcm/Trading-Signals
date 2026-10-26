package handlers

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"
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

// marketBriefNewsPlaceholder / marketBriefTimePlaceholder are substituted in the saved
// `ai_market_brief_prompt` template (edited in MacroIntelHub > AI Settings > Edit Prompt).
const (
	marketBriefNewsPlaceholder = "{{NEWS_ITEMS}}"
	marketBriefTimePlaceholder = "{{CURRENT_TIME}}"
)

// loadMarketBriefTemplate returns the saved template, falling back to the legacy key only
// when it clearly belongs to the market brief editor (contains {{NEWS_ITEMS}}).
func loadMarketBriefTemplate(db *sql.DB) string {
	var tpl string
	if err := db.QueryRow(`SELECT value FROM system_settings WHERE key = 'ai_market_brief_prompt'`).Scan(&tpl); err == nil && strings.TrimSpace(tpl) != "" {
		return tpl
	}
	var legacy string
	if err := db.QueryRow(`SELECT value FROM system_settings WHERE key = 'ai_prompt_template'`).Scan(&legacy); err == nil &&
		strings.Contains(legacy, marketBriefNewsPlaceholder) {
		return legacy
	}
	return ""
}

// Generate AI Prompt
func GenerateStrategyPrompt(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`SELECT id, name FROM news_groups ORDER BY id`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		type group struct {
			id   int
			name string
		}
		var groups []group
		for rows.Next() {
			var g group
			if err := rows.Scan(&g.id, &g.name); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			groups = append(groups, g)
		}

		var news strings.Builder
		for _, g := range groups {
			itemRows, err := db.Query(`SELECT title, importance, created_at FROM news_items
				WHERE group_id=$1 AND status='active' ORDER BY importance DESC, created_at DESC`, g.id)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			var lines []string
			for itemRows.Next() {
				var title string
				var importance int
				var createdAt time.Time
				if err := itemRows.Scan(&title, &importance, &createdAt); err != nil {
					itemRows.Close()
					http.Error(w, err.Error(), 500)
					return
				}
				lines = append(lines, fmt.Sprintf("• [%s] %s (Độ quan trọng: %d/5)",
					createdAt.In(vnLocation).Format("02/01/2006"), strings.TrimSpace(title), importance))
			}
			itemRows.Close()
			if len(lines) > 0 {
				news.WriteString("\n📂 Nhóm chủ đề: " + g.name + "\n" + strings.Join(lines, "\n") + "\n")
			}
		}
		newsItems := strings.TrimSpace(news.String())
		if newsItems == "" {
			newsItems = "(Chưa có tin tức nào đang active)"
		}
		now := vnNowString()

		var prompt string
		if tpl := loadMarketBriefTemplate(db); tpl != "" {
			prompt = strings.ReplaceAll(tpl, marketBriefTimePlaceholder, now)
			// {{MARKET_PRICES}} is only filled by scripts/fetch_latest_news_signal_llm.py
			prompt = strings.ReplaceAll(prompt, "{{MARKET_PRICES}}", "(Hãy dùng dữ liệu giá mới nhất mà bạn truy cập được; nếu không có, nói rõ.)")
			if strings.Contains(prompt, marketBriefNewsPlaceholder) {
				prompt = strings.ReplaceAll(prompt, marketBriefNewsPlaceholder, newsItems)
			} else {
				prompt += "\n\nDANH SÁCH TIN TỨC ĐANG THEO DÕI:\n" + newsItems
			}
		} else {
			prompt = "Bạn là chuyên gia phân tích kinh tế vĩ mô và cố vấn phân bổ danh mục đầu tư cao cấp.\n" +
				"Thời điểm hiện tại: " + now + ".\n" +
				"Hãy đánh giá các sự kiện vĩ mô và dòng tin tức đang diễn ra dưới đây (độ quan trọng 1-5, 5 là cao nhất) để đưa ra bức tranh toàn cảnh:\n\n" +
				newsItems + "\n" +
				"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
				"YÊU CẦU TRẢ LỜI CẤU TRÚC THEO 3 PHẦN:\n" +
				"1. ĐÁNH GIÁ DÒNG TIỀN & TÁC ĐỘNG CHÉO (Flow of Funds):\n" +
				"   - Phân tích tác động trực tiếp tới USD (DXY), Lợi suất Trái phiếu Mỹ (Yields), Giá Vàng (XAU), Dầu thô và Crypto.\n" +
				"   - Thị trường Việt Nam: Tác động tỷ giá USD/VND, nhóm ngành Chứng khoán & Bất động sản hưởng lợi hoặc chịu áp lực.\n\n" +
				"2. CẢNH BÁO PHÂN KỲ & RỦI RO (Divergence & Blindspots):\n" +
				"   - Chỉ ra sự phân kỳ (nếu có) giữa kỳ vọng tin tức và diễn biến giá thực tế (nếu bạn có quyền truy cập dữ liệu giá mới nhất; nếu không, nói rõ là giả định).\n" +
				"   - Bổ sung các biến số vĩ mô quan trọng đang cận kề nhưng chưa có trong danh sách trên (ghi rõ cần kiểm chứng).\n\n" +
				"3. CHIẾN LƯỢC HÀNH ĐỘNG CỤ THỂ (Actionable Allocation):\n" +
				"   - Nếu có dòng tiền nhàn rỗi lúc này: Nên ưu tiên phân bổ vào đâu? (Tỷ lệ gợi ý giữa Tiền mặt / Vàng / Cổ phiếu / Kênh khác) và điều kiện khiến khuyến nghị thay đổi.\n" +
				"   - QUY TẮC PHÒNG THỦ: nếu NHTW lớn nghiêng về thắt chặt (căn cứ tin trong danh sách) VÀ có ít nhất một dấu hiệu: vàng giảm, BTC giảm hoặc chứng khoán giảm mạnh (theo giá thực tế nếu có; không có dữ liệu giá thì nói rõ là không xác nhận được) thì ưu tiên giữ tiền mặt làm tỷ trọng chủ đạo, nêu điều kiện đã kích hoạt và điều kiện để quay lại giải ngân; ngược lại không ép giữ tiền mặt.\n" +
				"   - Trình bày ngắn gọn, dạng gạch đầu dòng súc tích, đi thẳng vào trọng tâm hành động.\n\n" +
				"Quy tắc: không bịa số liệu giá/ngày tháng; phân biệt tin đã xảy ra với tin chưa xác minh."
		}
		json.NewEncoder(w).Encode(map[string]string{"prompt": prompt})
	}
}

// SummarizeYouTubeNews calls the osint_ai_worker trigger server on port 8081 to extract transcripts and summarize video
func SummarizeYouTubeNews(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	var reqBody struct {
		URL string `json:"url"`
	}
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil || strings.TrimSpace(reqBody.URL) == "" {
		http.Error(w, "URL YouTube không hợp lệ hoặc bị trống", http.StatusBadRequest)
		return
	}

	workerURL := os.Getenv("WORKER_URL")
	if workerURL == "" {
		// Default to local/docker worker container name
		workerURL = "http://worker:8081"
	}

	jsonData, _ := json.Marshal(reqBody)
	client := &http.Client{Timeout: 3 * time.Minute}
	resp, err := client.Post(workerURL+"/trigger-youtube-summary", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		// Fallback to localhost if worker host is unreachable
		resp, err = client.Post("http://localhost:8081/trigger-youtube-summary", "application/json", bytes.NewBuffer(jsonData))
	}

	if err != nil {
		http.Error(w, fmt.Sprintf("Không thể kết nối đến OSINT AI Worker: %v", err), http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		http.Error(w, "Lỗi giải mã phản hồi từ AI Worker", http.StatusInternalServerError)
		return
	}

	if resp.StatusCode != http.StatusOK {
		msg := "Lỗi trích xuất và phân tích video YouTube"
		if val, ok := result["message"]; ok {
			msg = fmt.Sprintf("%v", val)
		}
		http.Error(w, msg, resp.StatusCode)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}
