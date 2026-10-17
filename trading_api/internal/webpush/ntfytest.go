package webpush

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

// Bấm "Thử nghiệm Âm báo" trên website → gửi 1 tin thử ra TẤT CẢ kênh thông báo:
//   - ntfy  → app ntfy trên điện thoại, loa Raspberry Pi
//   - Web Push → mọi thiết bị đã bật thông báo (iPhone/iPad từ icon Màn hình chính, Android, PC)
// để kiểm tra toàn bộ đường đi website → server → kênh thông báo → thiết bị.
//
// Cấu hình (trading_api/.env):
//   NTFY_SERVER_URL  mặc định http://ntfy:80 (service "ntfy" trong osint_ai_worker/docker-compose.yaml)
//   NTFY_TOPIC       mặc định trading_signals_alerts
//   NTFY_TOKEN       (tuỳ chọn) access token nếu ntfy bật xác thực

const ntfyTestCooldown = 20 * time.Second // chống bấm liên tục / spam ntfy từ endpoint công khai

var (
	ntfyTestMu   sync.Mutex
	ntfyTestLast time.Time
	ntfyClient   = &http.Client{Timeout: 8 * time.Second}
)

func ntfyConfig() (server, topic, token string) {
	server = strings.TrimRight(strings.TrimSpace(os.Getenv("NTFY_SERVER_URL")), "/")
	if server == "" {
		server = "http://ntfy:80"
	}
	topic = strings.TrimSpace(os.Getenv("NTFY_TOPIC"))
	if topic == "" {
		topic = "trading_signals_alerts"
	}
	return server, topic, strings.TrimSpace(os.Getenv("NTFY_TOKEN"))
}

func sendNtfyTest(message string) error {
	server, topic, token := ntfyConfig()
	body, _ := json.Marshal(map[string]any{
		"topic":    topic,
		"title":    "🔔 Thử nghiệm âm báo — Trading Signals",
		"message":  message,
		"priority": 4,
		"tags":     []string{"bell", "test_tube"},
	})
	req, err := http.NewRequest(http.MethodPost, server+"/", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := ntfyClient.Do(req)
	if err != nil {
		return fmt.Errorf("không kết nối được ntfy (%s): %v — kiểm tra NTFY_SERVER_URL của trading_api", server, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("ntfy trả về HTTP %d (topic %q) — kiểm tra NTFY_TOKEN / quyền ghi topic", resp.StatusCode, topic)
	}
	return nil
}

type channelResult struct {
	OK    bool   `json:"ok"`
	Sent  int    `json:"sent,omitempty"`
	Total int    `json:"total,omitempty"`
	Error string `json:"error,omitempty"`
}

// NotifyTestHandler: POST /api/notify/test — gửi tin thử qua ntfy + Web Push (mọi thiết bị đã bật).
func NotifyTestHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cors(w)
		if r.Method == http.MethodOptions {
			return
		}

		ntfyTestMu.Lock()
		wait := ntfyTestCooldown - time.Since(ntfyTestLast)
		if wait > 0 {
			ntfyTestMu.Unlock()
			writeJSON(w, http.StatusTooManyRequests, map[string]string{
				"error": fmt.Sprintf("Vừa gửi thử rồi, đợi %d giây nữa nhé", int(wait.Seconds())+1),
			})
			return
		}
		ntfyTestLast = time.Now()
		ntfyTestMu.Unlock()

		now := time.Now().In(time.FixedZone("ICT", 7*3600)).Format("15:04")
		message := fmt.Sprintf("Đây là tin thử nghiệm từ website lúc %s. Nếu bạn thấy hoặc nghe được tin này, kênh thông báo đang hoạt động bình thường.", now)

		var ntfyRes, pushRes channelResult
		var wg sync.WaitGroup
		wg.Add(2)
		go func() {
			defer wg.Done()
			if err := sendNtfyTest(message); err != nil {
				ntfyRes.Error = err.Error()
			} else {
				ntfyRes.OK = true
			}
		}()
		go func() {
			defer wg.Done()
			if db == nil {
				pushRes.Error = "không có DB"
				return
			}
			keys, err := GetKeys(db)
			if err != nil {
				pushRes.Error = err.Error()
				return
			}
			sent, total := broadcast(db, keys, "alerts", Payload{
				Kind:  "test",
				Title: "🔔 Thử nghiệm âm báo — Trading Signals",
				Body:  message,
				Tag:   "notify-test",
				URL:   "/",
			})
			pushRes.Sent, pushRes.Total, pushRes.OK = sent, total, total > 0 && sent == total
			if total == 0 {
				pushRes.Error = "chưa có thiết bị nào bật thông báo (hoặc đã tắt Cảnh báo giao dịch)"
			} else if sent < total {
				pushRes.Error = fmt.Sprintf("%d thiết bị gửi lỗi — xem log [WebPush] của trading_api", total-sent)
			}
		}()
		wg.Wait()

		status := http.StatusOK
		if !ntfyRes.OK && pushRes.Sent == 0 {
			status = http.StatusBadGateway
		}
		writeJSON(w, status, map[string]any{"ntfy": ntfyRes, "push": pushRes})
	}
}
