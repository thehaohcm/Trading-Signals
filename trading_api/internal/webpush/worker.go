package webpush

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"
)

const (
	maxFailures       = 10
	workerInterval    = 5 * time.Second
	alertLookback     = "15 minutes"
	newsLookback      = "30 minutes"
	maxPayloadBodyLen = 600
)

// Payload là nội dung JSON gửi tới service worker (public/sw.js).
type Payload struct {
	Kind               string          `json:"kind"` // alert | news | test
	Title              string          `json:"title"`
	Body               string          `json:"body"`
	Tag                string          `json:"tag,omitempty"`
	URL                string          `json:"url,omitempty"`
	RequireInteraction bool            `json:"requireInteraction,omitempty"`
	News               json.RawMessage `json:"news,omitempty"`
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// StartWorker chạy nền: lấy cảnh báo mới (triggered_alerts) và tin Telegram mới (news_items)
// rồi gửi Web Push tới các trình duyệt đã đăng ký. Chạy được trên nhiều instance cùng lúc
// (VPS + Fly.io) mà không gửi trùng nhờ bảng push_dispatch_log.
// Tắt bằng PUSH_WORKER_ENABLED=false.
func StartWorker(db *sql.DB) {
	if strings.EqualFold(os.Getenv("PUSH_WORKER_ENABLED"), "false") {
		log.Println("ℹ️ [WebPush] Worker bị tắt (PUSH_WORKER_ENABLED=false)")
		return
	}

	var keys *VAPIDKeys
	for {
		k, err := GetKeys(db)
		if err == nil {
			keys = k
			break
		}
		log.Printf("⚠️ [WebPush] Chưa lấy được khoá VAPID (%v), thử lại sau 30s", err)
		time.Sleep(30 * time.Second)
	}

	// Chỉ gửi những gì phát sinh SAU khi worker khởi động (không bắn lại tin cũ khi deploy)
	var lastAlertID, lastNewsID int64
	_ = db.QueryRow(`SELECT COALESCE(MAX(id), 0) FROM public.triggered_alerts`).Scan(&lastAlertID)
	_ = db.QueryRow(`SELECT COALESCE(MAX(id), 0) FROM public.news_items`).Scan(&lastNewsID)
	log.Printf("🔔 [WebPush] Worker đã chạy (alert>%d, news>%d)", lastAlertID, lastNewsID)

	lastCleanup := time.Now()
	for {
		lastAlertID = dispatchAlerts(db, keys, lastAlertID)
		lastNewsID = dispatchNews(db, keys, lastNewsID)
		if time.Since(lastCleanup) > time.Hour {
			_, _ = db.Exec(`DELETE FROM public.push_dispatch_log WHERE created_at < NOW() - INTERVAL '3 days'`)
			lastCleanup = time.Now()
		}
		time.Sleep(workerInterval)
	}
}

// claim đảm bảo mỗi sự kiện chỉ được gửi 1 lần dù có nhiều instance API cùng chạy worker.
func claim(db *sql.DB, key string) bool {
	res, err := db.Exec(`INSERT INTO public.push_dispatch_log (event_key) VALUES ($1) ON CONFLICT (event_key) DO NOTHING`, key)
	if err != nil {
		log.Printf("⚠️ [WebPush] claim %s lỗi: %v", key, err)
		return false
	}
	n, _ := res.RowsAffected()
	return n == 1
}

func alertTitle(symbol, assetType, message string) (string, bool) {
	upper := strings.ToUpper(message)
	critical := strings.Contains(upper, "LỖI LỆNH THẬT") || strings.Contains(upper, "CẦN XỬ LÝ THỦ CÔNG")
	icon := "🔔"
	switch {
	case critical:
		icon = "🚨"
	case strings.Contains(upper, "CẮT LỖ"):
		icon = "🛑"
	case strings.Contains(upper, "ĐÃ VÀO LỆNH"), strings.Contains(upper, "ĐÃ NHỒI LỆNH"):
		icon = "🚀"
	case strings.Contains(upper, "CHUẨN BỊ"):
		icon = "⏳"
	}
	if symbol == "" {
		symbol = "Cảnh báo"
	}
	title := icon + " " + symbol
	if assetType != "" {
		title += " (" + strings.ToUpper(assetType) + ")"
	}
	return title, critical || strings.Contains(upper, "CẮT LỖ")
}

func dispatchAlerts(db *sql.DB, keys *VAPIDKeys, lastID int64) int64 {
	rows, err := db.Query(`
		SELECT id, COALESCE(asset_type, ''), COALESCE(symbol, ''), COALESCE(message, '')
		FROM public.triggered_alerts
		WHERE id > $1 AND created_at > NOW() - INTERVAL '`+alertLookback+`'
		ORDER BY id ASC LIMIT 50`, lastID)
	if err != nil {
		log.Printf("⚠️ [WebPush] Lỗi đọc triggered_alerts: %v", err)
		return lastID
	}
	type alertRow struct {
		id                         int64
		assetType, symbol, message string
	}
	var items []alertRow
	for rows.Next() {
		var a alertRow
		if err := rows.Scan(&a.id, &a.assetType, &a.symbol, &a.message); err == nil {
			items = append(items, a)
		}
	}
	rows.Close()

	for _, a := range items {
		if a.id > lastID {
			lastID = a.id
		}
		if !claim(db, fmt.Sprintf("alert:%d", a.id)) {
			continue
		}
		title, sticky := alertTitle(a.symbol, a.assetType, a.message)
		broadcast(db, keys, "alerts", Payload{
			Kind:               "alert",
			Title:              title,
			Body:               truncate(a.message, maxPayloadBodyLen),
			Tag:                fmt.Sprintf("alert-%d", a.id),
			URL:                "/",
			RequireInteraction: sticky,
		})
	}
	return lastID
}

func telegramChannels() map[string]bool {
	raw := os.Getenv("TG_CHANNELS")
	if raw == "" {
		raw = "vnwallstreet,vnwallstreetcoin,tintucvnws" // giống GetTelegramNews
	}
	m := map[string]bool{}
	for _, c := range strings.Split(raw, ",") {
		if c = strings.ToLower(strings.TrimSpace(c)); c != "" {
			m[c] = true
		}
	}
	return m
}

// channelFromURL: https://t.me/<channel>/<id> -> <channel>
func channelFromURL(u string) string {
	l := strings.ToLower(u)
	const prefix = "https://t.me/"
	if !strings.HasPrefix(l, prefix) {
		return ""
	}
	rest := l[len(prefix):]
	if i := strings.Index(rest, "/"); i > 0 {
		return rest[:i]
	}
	return ""
}

func dispatchNews(db *sql.DB, keys *VAPIDKeys, lastID int64) int64 {
	rows, err := db.Query(`
		SELECT id, COALESCE(title, ''), COALESCE(content, ''), COALESCE(source_url, ''), created_at
		FROM public.news_items
		WHERE id > $1 AND source_url ILIKE 'https://t.me/%' AND created_at > NOW() - INTERVAL '`+newsLookback+`'
		ORDER BY id ASC LIMIT 20`, lastID)
	if err != nil {
		log.Printf("⚠️ [WebPush] Lỗi đọc news_items: %v", err)
		return lastID
	}
	type newsRow struct {
		id                   int64
		title, content, link string
		createdAt            time.Time
	}
	var items []newsRow
	for rows.Next() {
		var n newsRow
		if err := rows.Scan(&n.id, &n.title, &n.content, &n.link, &n.createdAt); err == nil {
			items = append(items, n)
		}
	}
	rows.Close()

	channels := telegramChannels()
	for _, n := range items {
		if n.id > lastID {
			lastID = n.id
		}
		ch := channelFromURL(n.link)
		if !channels[ch] {
			continue
		}
		if !claim(db, fmt.Sprintf("news:%d", n.id)) {
			continue
		}
		headline := n.title
		if strings.TrimSpace(headline) == "" {
			headline = n.content
		}
		// Cùng cấu trúc với item mà NavBar.vue phát qua sự kiện 'open-news-panel'
		newsJSON, _ := json.Marshal(map[string]any{
			"id":          n.id,
			"channel":     ch,
			"title":       truncate(n.title, 300),
			"description": truncate(n.content, 1500),
			"link":        n.link,
			"date":        n.createdAt,
		})
		broadcast(db, keys, "news", Payload{
			Kind:  "news",
			Title: "📰 BREAKING NEWS · " + ch,
			Body:  truncate(headline, maxPayloadBodyLen),
			Tag:   fmt.Sprintf("news-%d", n.id),
			URL:   "/",
			News:  newsJSON,
		})
	}
	return lastID
}

type storedSub struct {
	Subscription
	id int64
}

// broadcast gửi payload tới mọi subscription đã bật loại thông báo tương ứng (alerts | news).
// Trả về (số gửi thành công, tổng số thiết bị).
func broadcast(db *sql.DB, keys *VAPIDKeys, kind string, p Payload) (int, int) {
	column := "notify_alerts"
	if kind == "news" {
		column = "notify_news"
	}
	rows, err := db.Query(`SELECT id, endpoint, p256dh, auth FROM public.push_subscriptions
		WHERE `+column+` = true AND failure_count < $1`, maxFailures)
	if err != nil {
		log.Printf("⚠️ [WebPush] Lỗi đọc push_subscriptions: %v", err)
		return 0, 0
	}
	var subs []storedSub
	for rows.Next() {
		var s storedSub
		if err := rows.Scan(&s.id, &s.Endpoint, &s.Keys.P256dh, &s.Keys.Auth); err == nil {
			subs = append(subs, s)
		}
	}
	rows.Close()
	if len(subs) == 0 {
		return 0, 0
	}

	payload, _ := json.Marshal(p)
	urgency := "normal"
	if p.Kind == "alert" {
		urgency = "high"
	}
	opt := Options{Subject: vapidSubject(), TTL: 30 * time.Minute, Urgency: urgency}

	var wg sync.WaitGroup
	sem := make(chan struct{}, 8)
	sent := 0
	var mu sync.Mutex
	for _, s := range subs {
		wg.Add(1)
		sem <- struct{}{}
		go func(s storedSub) {
			defer wg.Done()
			defer func() { <-sem }()
			status, err := Send(keys, s.Subscription, payload, opt)
			recordResult(db, s.id, status, err)
			if err == nil {
				mu.Lock()
				sent++
				mu.Unlock()
			}
		}(s)
	}
	wg.Wait()
	log.Printf("📤 [WebPush] %s %q → %d/%d trình duyệt", p.Kind, truncate(p.Title, 60), sent, len(subs))
	return sent, len(subs)
}

func recordResult(db *sql.DB, id int64, status int, err error) {
	switch {
	case err == nil:
		_, _ = db.Exec(`UPDATE public.push_subscriptions SET failure_count = 0, last_success_at = NOW() WHERE id = $1`, id)
	case status == 404 || status == 410:
		// Trình duyệt đã huỷ đăng ký / hết hạn
		_, _ = db.Exec(`DELETE FROM public.push_subscriptions WHERE id = $1`, id)
	default:
		log.Printf("⚠️ [WebPush] Gửi tới subscription #%d lỗi: %v", id, err)
		_, _ = db.Exec(`UPDATE public.push_subscriptions SET failure_count = failure_count + 1 WHERE id = $1`, id)
	}
}
