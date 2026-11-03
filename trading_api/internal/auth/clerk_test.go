package auth

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"math/big"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func b64(b []byte) string { return base64.RawURLEncoding.EncodeToString(b) }

func sign(t *testing.T, key *rsa.PrivateKey, kid, alg string, claims map[string]interface{}) string {
	t.Helper()
	h, _ := json.Marshal(map[string]string{"alg": alg, "typ": "JWT", "kid": kid})
	p, _ := json.Marshal(claims)
	in := b64(h) + "." + b64(p)
	sum := sha256.Sum256([]byte(in))
	sig, err := rsa.SignPKCS1v15(rand.Reader, key, crypto.SHA256, sum[:])
	if err != nil {
		t.Fatal(err)
	}
	return in + "." + b64(sig)
}

func jwksServer(t *testing.T, kid string, pub *rsa.PublicKey, hits *int) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		*hits++
		json.NewEncoder(w).Encode(map[string]interface{}{"keys": []map[string]string{{
			"kty": "RSA", "kid": kid, "alg": "RS256", "use": "sig",
			"n": b64(pub.N.Bytes()), "e": b64(big.NewInt(int64(pub.E)).Bytes()),
		}}})
	}))
}

func TestVerifyAndMiddleware(t *testing.T) {
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	other, _ := rsa.GenerateKey(rand.Reader, 2048)
	hits := 0
	srv := jwksServer(t, "k1", &key.PublicKey, &hits)
	defer srv.Close()

	const iss = "https://example.clerk.accounts.dev"
	v := NewVerifier(iss, srv.URL, nil)
	now := time.Now()
	good := map[string]interface{}{"sub": "user_1", "iss": iss, "exp": now.Add(time.Minute).Unix(), "nbf": now.Add(-time.Minute).Unix()}

	if c, err := v.Verify(sign(t, key, "k1", "RS256", good)); err != nil || c.Subject != "user_1" {
		t.Fatalf("token hợp lệ bị từ chối: %v", err)
	}

	cases := map[string]string{
		"sai chữ ký":    sign(t, other, "k1", "RS256", good),
		"alg none":      sign(t, key, "k1", "none", good),
		"alg HS256":     sign(t, key, "k1", "HS256", good),
		"kid lạ":        sign(t, key, "zzz", "RS256", good),
		"literal token": "clerk_session",
		"rỗng":          "",
		"hết hạn":       sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": iss, "exp": now.Add(-time.Hour).Unix()}),
		"nbf tương lai": sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": iss, "exp": now.Add(time.Hour).Unix(), "nbf": now.Add(time.Hour).Unix()}),
		"sai issuer":    sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": "https://evil.example", "exp": now.Add(time.Hour).Unix()}),
		"thiếu sub":     sign(t, key, "k1", "RS256", map[string]interface{}{"iss": iss, "exp": now.Add(time.Hour).Unix()}),
		"thiếu exp":     sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": iss}),
	}
	for name, tok := range cases {
		if _, err := v.Verify(tok); err == nil {
			t.Errorf("%s: lẽ ra phải bị từ chối", name)
		}
	}
	// Payload bị sửa nhưng giữ chữ ký cũ
	parts := strings.Split(sign(t, key, "k1", "RS256", good), ".")
	forged, _ := json.Marshal(map[string]interface{}{"sub": "admin", "iss": iss, "exp": now.Add(time.Hour).Unix()})
	if _, err := v.Verify(parts[0] + "." + b64(forged) + "." + parts[2]); err == nil {
		t.Error("payload giả mạo lẽ ra phải bị từ chối")
	}

	// Cache JWKS: nhiều lần verify chỉ gọi JWKS một lần (+ tối đa 1 lần cho kid lạ do giới hạn tần suất)
	if hits > 2 {
		t.Errorf("JWKS bị tải quá nhiều: %d", hits)
	}

	// Middleware
	called := false
	h := v.Require(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
		if r.Method != "POST" {
			return // GET/OPTIONS đi qua không cần xác thực → không có claims
		}
		if c, ok := FromContext(r.Context()); !ok || c.Subject != "user_1" {
			t.Error("claims không có trong context")
		}
	}), "POST")
	do := func(method, tok string) int {
		called = false
		req := httptest.NewRequest(method, "/x", nil)
		if tok != "" {
			req.Header.Set("Authorization", "Bearer "+tok)
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		return rec.Code
	}
	if c := do("POST", ""); c != 401 || called {
		t.Errorf("POST không token: %d", c)
	}
	if c := do("POST", "clerk_session"); c != 401 || called {
		t.Errorf("POST token literal: %d", c)
	}
	if c := do("POST", sign(t, key, "k1", "RS256", good)); c != 200 || !called {
		t.Errorf("POST token đúng: %d", c)
	}
	if c := do("GET", ""); c != 200 || !called { // GET không nằm trong danh sách method cần auth
		t.Errorf("GET công khai: %d", c)
	}
	if c := do("OPTIONS", ""); c != 200 {
		t.Errorf("OPTIONS: %d", c)
	}
}

func TestAdminAllowlistAndFailClosed(t *testing.T) {
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	hits := 0
	srv := jwksServer(t, "k1", &key.PublicKey, &hits)
	defer srv.Close()
	const iss = "https://example.clerk.accounts.dev"
	claims := func(sub string) map[string]interface{} {
		return map[string]interface{}{"sub": sub, "iss": iss, "exp": time.Now().Add(time.Minute).Unix()}
	}
	req := func(tok string) *http.Request {
		r := httptest.NewRequest("POST", "/x", nil)
		r.Header.Set("Authorization", "Bearer "+tok)
		return r
	}

	v := NewVerifier(iss, srv.URL, []string{"user_admin"})
	if _, err := v.Authorize(req(sign(t, key, "k1", "RS256", claims("user_admin")))); err != nil {
		t.Errorf("admin bị từ chối: %v", err)
	}
	if _, err := v.Authorize(req(sign(t, key, "k1", "RS256", claims("user_other")))); err == nil {
		t.Error("user không thuộc allowlist lẽ ra bị từ chối")
	}

	unconfigured := NewVerifier("", "", nil)
	if _, err := unconfigured.Authorize(req(sign(t, key, "k1", "RS256", claims("user_admin")))); err == nil {
		t.Error("chưa cấu hình issuer phải fail-closed")
	}
	var nilV *Verifier
	if nilV.Configured() {
		t.Error("nil verifier không được coi là đã cấu hình")
	}
}

func TestIssuerFromPublishableKey(t *testing.T) {
	host, err := issuerFromPublishableKey("pk_test_aG90LXN1bmJpcmQtNTY5LmNsZXJrLmFjY291bnRzLmRldiQ")
	if err != nil || host != "hot-sunbird-569.clerk.accounts.dev" {
		t.Fatalf("got %q, %v", host, err)
	}
	for _, bad := range []string{"", "abc", "sk_test_xxx", "pk_test_!!!"} {
		if _, err := issuerFromPublishableKey(bad); err == nil && bad != "sk_test_xxx" {
			t.Errorf("%q lẽ ra lỗi", bad)
		}
	}
}

func TestJWKSOutageUsesCache(t *testing.T) {
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	hits := 0
	srv := jwksServer(t, "k1", &key.PublicKey, &hits)
	const iss = "https://example.clerk.accounts.dev"
	v := NewVerifier(iss, srv.URL, nil)
	tok := sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": iss, "exp": time.Now().Add(time.Minute).Unix()})
	if _, err := v.Verify(tok); err != nil {
		t.Fatal(err)
	}
	srv.Close() // Clerk sập
	base := time.Now().Add(2 * time.Hour)
	v.now = func() time.Time { return base }
	tok2 := sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "u", "iss": iss, "exp": base.Add(time.Minute).Unix()})
	if _, err := v.Verify(tok2); err != nil {
		t.Errorf("JWKS sập nhưng còn cache, lẽ ra vẫn verify được: %v", err)
	}
}

func TestRequireUserAcceptsNonAdmin(t *testing.T) {
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	hits := 0
	srv := jwksServer(t, "k1", &key.PublicKey, &hits)
	defer srv.Close()
	const iss = "https://example.clerk.accounts.dev"
	v := NewVerifier(iss, srv.URL, []string{"user_admin"})
	tok := sign(t, key, "k1", "RS256", map[string]interface{}{"sub": "user_regular", "iss": iss, "exp": time.Now().Add(time.Minute).Unix()})
	ok := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if c, found := FromContext(r.Context()); !found || c.Subject != "user_regular" {
			t.Error("claims thiếu")
		}
	})
	do := func(h http.Handler, tok string) int {
		req := httptest.NewRequest("GET", "/x", nil)
		if tok != "" {
			req.Header.Set("Authorization", "Bearer "+tok)
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		return rec.Code
	}
	if c := do(v.RequireUser(ok), tok); c != 200 {
		t.Errorf("user thường phải qua RequireUser: %d", c)
	}
	if c := do(v.Require(ok), tok); c != 401 {
		t.Errorf("user thường không được qua Require(admin): %d", c)
	}
	if c := do(v.RequireUser(ok), ""); c != 401 {
		t.Errorf("không token phải 401: %d", c)
	}
}
