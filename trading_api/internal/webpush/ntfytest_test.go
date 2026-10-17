package webpush

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestNtfyTestHandler(t *testing.T) {
	var got map[string]any
	var auth string
	fake := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		b, _ := io.ReadAll(r.Body)
		json.Unmarshal(b, &got)
		auth = r.Header.Get("Authorization")
		w.WriteHeader(200)
	}))
	defer fake.Close()
	t.Setenv("NTFY_SERVER_URL", fake.URL+"/")
	t.Setenv("NTFY_TOPIC", "my_topic")
	t.Setenv("NTFY_TOKEN", "tk_abc")

	h := NotifyTestHandler(nil)
	rec := httptest.NewRecorder()
	h(rec, httptest.NewRequest(http.MethodPost, "/api/notify/test", nil))
	var res map[string]map[string]any
	json.Unmarshal(rec.Body.Bytes(), &res)
	if res["ntfy"]["ok"] != true || res["push"]["error"] == nil {
		t.Fatalf("result: %s", rec.Body.String())
	}
	if rec.Code != 200 || got["topic"] != "my_topic" || !strings.Contains(got["message"].(string), "thử nghiệm") || auth != "Bearer tk_abc" {
		t.Fatalf("send: code=%d got=%v auth=%q body=%s", rec.Code, got, auth, rec.Body.String())
	}

	rec2 := httptest.NewRecorder()
	h(rec2, httptest.NewRequest(http.MethodPost, "/api/notify/test", nil))
	if rec2.Code != http.StatusTooManyRequests {
		t.Fatalf("cooldown expected 429, got %d", rec2.Code)
	}

	ntfyTestLast = time.Time{}
	t.Setenv("NTFY_SERVER_URL", "http://127.0.0.1:1")
	rec3 := httptest.NewRecorder()
	h(rec3, httptest.NewRequest(http.MethodPost, "/api/notify/test", nil))
	if rec3.Code != http.StatusBadGateway || !strings.Contains(rec3.Body.String(), "không kết nối được ntfy") {
		t.Fatalf("unreachable expected 502, got %d %s", rec3.Code, rec3.Body.String())
	}
}
