package webpush

import (
	"crypto/ecdh"
	"crypto/rand"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"
)

// Sinh một "trình duyệt giả", mã hoá + gửi tới server TLS giả, xuất dữ liệu cho Python kiểm chứng.
func TestEncryptAndSend(t *testing.T) {
	keys, err := GenerateVAPIDKeys()
	if err != nil {
		t.Fatal(err)
	}
	// round-trip parse
	if _, err := ParseVAPIDKeys(keys.PublicB64, keys.PrivateB64); err != nil {
		t.Fatal(err)
	}
	if _, err := ParseVAPIDKeys("BAD", keys.PrivateB64); err == nil {
		t.Fatal("expected mismatch error")
	}

	uaPriv, _ := ecdh.P256().GenerateKey(rand.Reader)
	auth := make([]byte, 16)
	rand.Read(auth)

	var gotBody []byte
	var gotHeaders http.Header
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/gone") {
			w.WriteHeader(410)
			return
		}
		gotBody, _ = io.ReadAll(r.Body)
		gotHeaders = r.Header.Clone()
		w.WriteHeader(201)
	}))
	defer srv.Close()
	httpClient = srv.Client()

	var sub Subscription
	sub.Endpoint = srv.URL + "/push/abc"
	sub.Keys.P256dh = b64.EncodeToString(uaPriv.PublicKey().Bytes())
	sub.Keys.Auth = b64.EncodeToString(auth)

	msg := `{"title":"🚀 BTCUSDT","body":"Đã vào lệnh — tiếng Việt có dấu"}`
	status, err := Send(keys, sub, []byte(msg), Options{Subject: "https://tradesign.io.vn", TTL: time.Minute, Urgency: "high"})
	if err != nil || status != 201 {
		t.Fatalf("send: %d %v", status, err)
	}
	if gotHeaders.Get("Content-Encoding") != "aes128gcm" || gotHeaders.Get("TTL") != "60" || gotHeaders.Get("Urgency") != "high" {
		t.Fatalf("headers: %v", gotHeaders)
	}

	sub2 := sub
	sub2.Endpoint = srv.URL + "/gone"
	if st, err := Send(keys, sub2, []byte("x"), Options{Subject: "https://x"}); st != 410 || err == nil {
		t.Fatalf("expected 410, got %d %v", st, err)
	}

	big := strings.Repeat("a", 4000)
	if _, err := Encrypt(sub, []byte(big)); err == nil {
		t.Fatal("expected too-large error")
	}

	out, _ := json.Marshal(map[string]string{
		"ua_private": b64.EncodeToString(uaPriv.Bytes()),
		"auth":       sub.Keys.Auth,
		"body":       b64.EncodeToString(gotBody),
		"authz":      gotHeaders.Get("Authorization"),
		"vapid_pub":  keys.PublicB64,
		"aud":        srv.URL,
		"plaintext":  msg,
	})
	os.WriteFile(os.Getenv("OUT"), out, 0644)
}

func TestHelpers(t *testing.T) {
	if channelFromURL("https://t.me/VNWallStreet/12345") != "vnwallstreet" || channelFromURL("https://x.com/a/1") != "" {
		t.Fatal("channelFromURL")
	}
	title, sticky := alertTitle("ETHUSDT", "crypto", "[LIVE TRADE THẬT] CẮT LỖ THEO GIÁ VỐN TB")
	if title != "🛑 ETHUSDT (CRYPTO)" || !sticky {
		t.Fatal(title)
	}
	title, sticky = alertTitle("BTC", "crypto", "[CHUẨN BỊ VÀO LỆNH] BTC")
	if title != "⏳ BTC (CRYPTO)" || sticky {
		t.Fatal(title)
	}
	if truncate("abcdef", 4) != "abc…" {
		t.Fatal("truncate")
	}
}
