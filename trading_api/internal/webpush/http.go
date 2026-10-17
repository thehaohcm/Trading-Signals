package webpush

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const maxSubscriptions = 1000

func cors(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func validEndpoint(endpoint string) bool {
	u, err := url.Parse(endpoint)
	return err == nil && u.Scheme == "https" && u.Host != "" && len(endpoint) <= 2048
}

// PublicKeyHandler: GET /api/push/vapid-public-key
func PublicKeyHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cors(w)
		if r.Method == http.MethodOptions {
			return
		}
		keys, err := GetKeys(db)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"publicKey": keys.PublicB64})
	}
}

type subscribeRequest struct {
	Subscription Subscription `json:"subscription"`
	NotifyAlerts *bool        `json:"notify_alerts"`
	NotifyNews   *bool        `json:"notify_news"`
	// Khi trình duyệt tự làm mới subscription (pushsubscriptionchange), sw.js gửi kèm endpoint cũ
	// để giữ nguyên tuỳ chọn bật/tắt của người dùng.
	OldEndpoint string `json:"old_endpoint"`
}

// SubscribeHandler: POST /api/push/subscribe — tạo mới hoặc cập nhật tuỳ chọn của subscription.
func SubscribeHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cors(w)
		if r.Method == http.MethodOptions {
			return
		}
		var req subscribeRequest
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 16<<10)).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "JSON không hợp lệ"})
			return
		}
		s := req.Subscription
		if !validEndpoint(s.Endpoint) || s.Keys.P256dh == "" || s.Keys.Auth == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Subscription không hợp lệ"})
			return
		}
		// Kiểm tra khoá của trình duyệt có dùng được để mã hoá không
		if _, err := Encrypt(s, []byte("{}")); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		alerts, news := true, false // Breaking News mặc định tắt cho tới khi người dùng bật
		if req.OldEndpoint != "" && req.OldEndpoint != s.Endpoint {
			var oa, on bool
			if err := db.QueryRow(`SELECT notify_alerts, notify_news FROM public.push_subscriptions WHERE endpoint = $1`, req.OldEndpoint).Scan(&oa, &on); err == nil {
				alerts, news = oa, on
			}
			_, _ = db.Exec(`DELETE FROM public.push_subscriptions WHERE endpoint = $1`, req.OldEndpoint)
		}
		if req.NotifyAlerts != nil {
			alerts = *req.NotifyAlerts
		}
		if req.NotifyNews != nil {
			news = *req.NotifyNews
		}

		var exists bool
		_ = db.QueryRow(`SELECT EXISTS(SELECT 1 FROM public.push_subscriptions WHERE endpoint = $1)`, s.Endpoint).Scan(&exists)
		if !exists {
			var count int
			_ = db.QueryRow(`SELECT COUNT(*) FROM public.push_subscriptions`).Scan(&count)
			if count >= maxSubscriptions {
				writeJSON(w, http.StatusTooManyRequests, map[string]string{"error": "Đã đạt giới hạn số trình duyệt đăng ký"})
				return
			}
		}

		ua := r.UserAgent()
		if len(ua) > 300 {
			ua = ua[:300]
		}
		_, err := db.Exec(`
			INSERT INTO public.push_subscriptions (endpoint, p256dh, auth, user_agent, notify_alerts, notify_news)
			VALUES ($1, $2, $3, $4, $5, $6)
			ON CONFLICT (endpoint) DO UPDATE SET
				p256dh = EXCLUDED.p256dh,
				auth = EXCLUDED.auth,
				user_agent = EXCLUDED.user_agent,
				notify_alerts = EXCLUDED.notify_alerts,
				notify_news = EXCLUDED.notify_news,
				failure_count = 0,
				updated_at = NOW()`,
			s.Endpoint, s.Keys.P256dh, s.Keys.Auth, ua, alerts, news)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "notify_alerts": alerts, "notify_news": news})
	}
}

type endpointRequest struct {
	Endpoint string `json:"endpoint"`
}

// UnsubscribeHandler: POST /api/push/unsubscribe
func UnsubscribeHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cors(w)
		if r.Method == http.MethodOptions {
			return
		}
		var req endpointRequest
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<10)).Decode(&req); err != nil || req.Endpoint == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Thiếu endpoint"})
			return
		}
		_, _ = db.Exec(`DELETE FROM public.push_subscriptions WHERE endpoint = $1`, req.Endpoint)
		writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
	}
}

// TestHandler: POST /api/push/test — gửi 1 thông báo thử tới chính trình duyệt đang yêu cầu.
func TestHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cors(w)
		if r.Method == http.MethodOptions {
			return
		}
		var req endpointRequest
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<10)).Decode(&req); err != nil || req.Endpoint == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Thiếu endpoint"})
			return
		}
		var s storedSub
		err := db.QueryRow(`SELECT id, endpoint, p256dh, auth FROM public.push_subscriptions WHERE endpoint = $1`, req.Endpoint).
			Scan(&s.id, &s.Endpoint, &s.Keys.P256dh, &s.Keys.Auth)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "Trình duyệt này chưa đăng ký nhận thông báo"})
			return
		}
		keys, err := GetKeys(db)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}
		payload, _ := json.Marshal(Payload{
			Kind:  "test",
			Title: "✅ Trading Signals — Thông báo thử",
			Body:  "Web Push đã hoạt động! Bạn sẽ nhận cảnh báo kể cả khi đã đóng tab.",
			Tag:   "push-test",
			URL:   "/",
		})
		status, err := Send(keys, s.Subscription, payload, Options{Subject: vapidSubject(), TTL: 5 * time.Minute, Urgency: "high"})
		recordResult(db, s.id, status, err)
		if err != nil {
			msg := err.Error()
			if strings.Contains(msg, "403") {
				msg += " (khoá VAPID đã đổi — hãy tắt rồi bật lại thông báo)"
			}
			writeJSON(w, http.StatusBadGateway, map[string]string{"error": msg})
			return
		}
		writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
	}
}
