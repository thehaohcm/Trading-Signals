// Package auth xác thực phiên đăng nhập Clerk ở phía Go API.
//
// Trước đây API chỉ kiểm tra "có header Authorization không rỗng" nên ai gửi
// `Authorization: Bearer x` cũng đặt được lệnh live trade / đọc khoá sàn.
// Package này kiểm tra JWT thật của Clerk (RS256 + JWKS), chỉ dùng thư viện chuẩn.
//
// Cấu hình (biến môi trường):
//
//	CLERK_ISSUER           vd https://hot-sunbird-569.clerk.accounts.dev  (bắt buộc nếu không có CLERK_PUBLISHABLE_KEY)
//	CLERK_PUBLISHABLE_KEY  pk_test_... / pk_live_... → tự suy ra issuer (có thể dùng thay CLERK_ISSUER)
//	CLERK_JWKS_URL         mặc định <issuer>/.well-known/jwks.json
//	ADMIN_CLERK_USER_IDS   danh sách user_id Clerk được phép (phân tách bằng dấu phẩy).
//	                       Để trống = mọi tài khoản đăng nhập hợp lệ trong ứng dụng Clerk đều là admin.
//
// Fail-closed: chưa cấu hình issuer → mọi request cần quyền đều bị từ chối.
package auth

import (
	"context"
	"crypto"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math/big"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

const (
	leeway          = 60 * time.Second
	jwksTTL         = time.Hour
	jwksMinInterval = 30 * time.Second // chống bị spam kid lạ làm gọi JWKS liên tục
	maxTokenLen     = 8192
)

// Claims là phần thông tin cần dùng từ JWT.
type Claims struct {
	Subject string
	Issuer  string
	Expires time.Time
}

type ctxKey struct{}

// FromContext lấy claims đã xác thực từ context (sau middleware).
func FromContext(ctx context.Context) (Claims, bool) {
	c, ok := ctx.Value(ctxKey{}).(Claims)
	return c, ok
}

// Verifier xác thực JWT Clerk.
type Verifier struct {
	issuer  string
	jwksURL string
	admins  map[string]bool
	client  *http.Client
	now     func() time.Time

	mu        sync.Mutex
	keys      map[string]*rsa.PublicKey
	fetchedAt time.Time
	lastTry   time.Time
}

// NewVerifier tạo verifier thủ công (dùng trong test).
func NewVerifier(issuer, jwksURL string, admins []string) *Verifier {
	issuer = strings.TrimRight(strings.TrimSpace(issuer), "/")
	if jwksURL == "" && issuer != "" {
		jwksURL = issuer + "/.well-known/jwks.json"
	}
	m := map[string]bool{}
	for _, a := range admins {
		if a = strings.TrimSpace(a); a != "" {
			m[a] = true
		}
	}
	return &Verifier{
		issuer:  issuer,
		jwksURL: jwksURL,
		admins:  m,
		client:  &http.Client{Timeout: 8 * time.Second},
		now:     time.Now,
	}
}

// NewFromEnv đọc cấu hình từ biến môi trường. Trả về verifier (có thể chưa cấu hình → fail-closed).
func NewFromEnv() *Verifier {
	issuer := os.Getenv("CLERK_ISSUER")
	if issuer == "" {
		if pk := os.Getenv("CLERK_PUBLISHABLE_KEY"); pk != "" {
			if host, err := issuerFromPublishableKey(pk); err == nil {
				issuer = "https://" + host
			} else {
				log.Printf("⚠️ [Auth] CLERK_PUBLISHABLE_KEY không hợp lệ: %v", err)
			}
		}
	}
	var admins []string
	if raw := os.Getenv("ADMIN_CLERK_USER_IDS"); raw != "" {
		admins = strings.Split(raw, ",")
	}
	v := NewVerifier(issuer, os.Getenv("CLERK_JWKS_URL"), admins)
	switch {
	case v.issuer == "":
		log.Println("🔒 [Auth] CHƯA cấu hình CLERK_ISSUER/CLERK_PUBLISHABLE_KEY → mọi endpoint cần đăng nhập sẽ bị từ chối (401).")
	case len(v.admins) == 0:
		log.Printf("⚠️ [Auth] Issuer=%s nhưng ADMIN_CLERK_USER_IDS trống → MỌI tài khoản Clerk đăng nhập được đều có quyền admin. Nên đặt ADMIN_CLERK_USER_IDS.", v.issuer)
	default:
		log.Printf("🔒 [Auth] Clerk issuer=%s, %d admin được phép.", v.issuer, len(v.admins))
	}
	return v
}

// Configured cho biết đã có issuer hay chưa.
func (v *Verifier) Configured() bool { return v != nil && v.issuer != "" }

// issuerFromPublishableKey: pk_test_<base64url("host$")> → host.
func issuerFromPublishableKey(pk string) (string, error) {
	parts := strings.SplitN(strings.TrimSpace(pk), "_", 3)
	if len(parts) != 3 || parts[0] != "pk" {
		return "", errors.New("định dạng phải là pk_test_... hoặc pk_live_...")
	}
	raw := parts[2]
	b, err := base64.RawStdEncoding.DecodeString(strings.TrimRight(raw, "="))
	if err != nil {
		return "", err
	}
	host := strings.TrimSuffix(string(b), "$")
	if host == "" || strings.ContainsAny(host, "/ $") {
		return "", errors.New("host giải mã không hợp lệ")
	}
	return host, nil
}

// TokenFromRequest lấy bearer token từ Authorization (hoặc x-auth-token).
func TokenFromRequest(r *http.Request) string {
	h := strings.TrimSpace(r.Header.Get("Authorization"))
	if h == "" {
		h = strings.TrimSpace(r.Header.Get("x-auth-token"))
	}
	if h == "" {
		return ""
	}
	if f := strings.Fields(h); len(f) == 2 && strings.EqualFold(f[0], "Bearer") {
		return f[1]
	}
	return h
}

// Authenticate xác thực request: token Clerk hợp lệ (KHÔNG kiểm tra danh sách admin) — dùng cho dữ liệu theo từng người dùng.
func (v *Verifier) Authenticate(r *http.Request) (Claims, error) {
	if !v.Configured() {
		return Claims{}, errors.New("máy chủ chưa cấu hình xác thực Clerk")
	}
	tok := TokenFromRequest(r)
	if tok == "" {
		return Claims{}, errors.New("thiếu token")
	}
	return v.Verify(tok)
}

// Authorize xác thực request như Authenticate và (nếu có cấu hình ADMIN_CLERK_USER_IDS) yêu cầu thuộc danh sách admin.
func (v *Verifier) Authorize(r *http.Request) (Claims, error) {
	c, err := v.Authenticate(r)
	if err != nil {
		return Claims{}, err
	}
	if len(v.admins) > 0 && !v.admins[c.Subject] {
		return Claims{}, errors.New("tài khoản không có quyền admin")
	}
	return c, nil
}

// Verify kiểm tra chữ ký RS256, exp, nbf, iss.
func (v *Verifier) Verify(token string) (Claims, error) {
	if len(token) > maxTokenLen {
		return Claims{}, errors.New("token quá dài")
	}
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return Claims{}, errors.New("token không phải JWT")
	}
	var hdr struct {
		Alg string `json:"alg"`
		Kid string `json:"kid"`
	}
	if err := decodeSegment(parts[0], &hdr); err != nil {
		return Claims{}, fmt.Errorf("header: %w", err)
	}
	if hdr.Alg != "RS256" { // chặn alg=none / HS256 confusion
		return Claims{}, fmt.Errorf("alg %q không được chấp nhận", hdr.Alg)
	}
	sig, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		return Claims{}, errors.New("chữ ký lỗi base64")
	}
	key, err := v.keyFor(hdr.Kid)
	if err != nil {
		return Claims{}, err
	}
	sum := sha256.Sum256([]byte(parts[0] + "." + parts[1]))
	if err := rsa.VerifyPKCS1v15(key, crypto.SHA256, sum[:], sig); err != nil {
		return Claims{}, errors.New("chữ ký không hợp lệ")
	}

	var cl struct {
		Sub string  `json:"sub"`
		Iss string  `json:"iss"`
		Exp float64 `json:"exp"`
		Nbf float64 `json:"nbf"`
	}
	if err := decodeSegment(parts[1], &cl); err != nil {
		return Claims{}, fmt.Errorf("payload: %w", err)
	}
	now := v.now()
	if cl.Exp == 0 {
		return Claims{}, errors.New("token thiếu exp")
	}
	exp := time.Unix(int64(cl.Exp), 0)
	if now.After(exp.Add(leeway)) {
		return Claims{}, errors.New("token đã hết hạn")
	}
	if cl.Nbf != 0 && now.Add(leeway).Before(time.Unix(int64(cl.Nbf), 0)) {
		return Claims{}, errors.New("token chưa có hiệu lực")
	}
	if strings.TrimRight(cl.Iss, "/") != v.issuer {
		return Claims{}, errors.New("issuer không khớp")
	}
	if cl.Sub == "" {
		return Claims{}, errors.New("token thiếu sub")
	}
	return Claims{Subject: cl.Sub, Issuer: cl.Iss, Expires: exp}, nil
}

func decodeSegment(seg string, out interface{}) error {
	b, err := base64.RawURLEncoding.DecodeString(seg)
	if err != nil {
		return err
	}
	return json.Unmarshal(b, out)
}

// keyFor trả về public key theo kid, tải lại JWKS khi hết hạn hoặc gặp kid lạ (có giới hạn tần suất).
func (v *Verifier) keyFor(kid string) (*rsa.PublicKey, error) {
	v.mu.Lock()
	defer v.mu.Unlock()
	now := v.now()
	if k, ok := v.keys[kid]; ok && now.Sub(v.fetchedAt) < jwksTTL {
		return k, nil
	}
	if v.keys == nil || now.Sub(v.fetchedAt) >= jwksTTL || now.Sub(v.lastTry) >= jwksMinInterval {
		v.lastTry = now
		keys, err := v.fetchJWKS()
		if err != nil {
			// Còn cache cũ chứa kid → vẫn dùng, tránh sập khi Clerk chập chờn.
			if k, ok := v.keys[kid]; ok {
				return k, nil
			}
			return nil, fmt.Errorf("không tải được JWKS: %w", err)
		}
		v.keys, v.fetchedAt = keys, now
	}
	if k, ok := v.keys[kid]; ok {
		return k, nil
	}
	return nil, errors.New("kid không tồn tại trong JWKS")
}

func (v *Verifier) fetchJWKS() (map[string]*rsa.PublicKey, error) {
	resp, err := v.client.Get(v.jwksURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return nil, err
	}
	var set struct {
		Keys []struct {
			Kty string `json:"kty"`
			Kid string `json:"kid"`
			N   string `json:"n"`
			E   string `json:"e"`
		} `json:"keys"`
	}
	if err := json.Unmarshal(body, &set); err != nil {
		return nil, err
	}
	out := map[string]*rsa.PublicKey{}
	for _, k := range set.Keys {
		if k.Kty != "RSA" || k.Kid == "" {
			continue
		}
		nb, err1 := base64.RawURLEncoding.DecodeString(k.N)
		eb, err2 := base64.RawURLEncoding.DecodeString(k.E)
		if err1 != nil || err2 != nil || len(nb) == 0 || len(eb) == 0 {
			continue
		}
		e := new(big.Int).SetBytes(eb)
		if !e.IsInt64() || e.Int64() < 3 || e.Int64() > 1<<31-1 {
			continue
		}
		out[k.Kid] = &rsa.PublicKey{N: new(big.Int).SetBytes(nb), E: int(e.Int64())}
	}
	if len(out) == 0 {
		return nil, errors.New("JWKS không có khoá RSA")
	}
	return out, nil
}

// Require bọc handler: yêu cầu ADMIN (token hợp lệ + thuộc ADMIN_CLERK_USER_IDS nếu có cấu hình) cho các method liệt kê
// (rỗng = mọi method trừ OPTIONS). OPTIONS (preflight CORS) luôn đi qua.
func (v *Verifier) Require(next http.Handler, methods ...string) http.Handler {
	return v.guard(next, v.Authorize, methods)
}

// RequireUser như Require nhưng chỉ cần token Clerk hợp lệ (mọi người dùng đã đăng nhập), không cần là admin.
func (v *Verifier) RequireUser(next http.Handler, methods ...string) http.Handler {
	return v.guard(next, v.Authenticate, methods)
}

func (v *Verifier) guard(next http.Handler, check func(*http.Request) (Claims, error), methods []string) http.Handler {
	need := map[string]bool{}
	for _, m := range methods {
		need[strings.ToUpper(m)] = true
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodOptions || (len(need) > 0 && !need[r.Method]) {
			next.ServeHTTP(w, r)
			return
		}
		c, err := check(r)
		if err != nil {
			log.Printf("🔒 [Auth] từ chối %s %s từ %s: %v", r.Method, r.URL.Path, r.RemoteAddr, err)
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			_ = json.NewEncoder(w).Encode(map[string]string{
				"status": "error", "message": "Yêu cầu đăng nhập", "error": "unauthorized",
			})
			return
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), ctxKey{}, c)))
	})
}

// RequireFunc là tiện ích cho http.HandlerFunc.
func (v *Verifier) RequireFunc(next http.HandlerFunc, methods ...string) http.Handler {
	return v.Require(next, methods...)
}
