// Package webpush gửi Web Push (RFC 8030) tới Chrome / Edge / Firefox / Safari
// với mã hoá payload aes128gcm (RFC 8291) và xác thực VAPID (RFC 8292).
// Chỉ dùng thư viện chuẩn của Go (crypto/ecdh, crypto/hkdf, crypto/ecdsa, crypto/aes).
package webpush

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/ecdh"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/hkdf"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/big"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// VAPIDKeys là cặp khoá P-256 dùng để ký JWT VAPID.
type VAPIDKeys struct {
	PublicKey  []byte // 65 bytes, dạng uncompressed (0x04 || X || Y)
	privateKey *ecdsa.PrivateKey
	PublicB64  string // base64url (không padding) — gửi cho trình duyệt làm applicationServerKey
	PrivateB64 string
}

// Subscription là thông tin đăng ký do trình duyệt cấp (PushSubscription.toJSON()).
type Subscription struct {
	Endpoint string `json:"endpoint"`
	Keys     struct {
		P256dh string `json:"p256dh"`
		Auth   string `json:"auth"`
	} `json:"keys"`
}

// Options cho mỗi lần gửi.
type Options struct {
	Subject string        // "mailto:..." hoặc "https://..."
	TTL     time.Duration // thời gian push service giữ tin nếu trình duyệt đang offline
	Urgency string        // very-low | low | normal | high
}

var b64 = base64.RawURLEncoding

func decodeB64(s string) ([]byte, error) {
	s = strings.TrimRight(strings.TrimSpace(s), "=")
	s = strings.NewReplacer("+", "-", "/", "_").Replace(s)
	return b64.DecodeString(s)
}

// GenerateVAPIDKeys tạo cặp khoá VAPID mới.
func GenerateVAPIDKeys() (*VAPIDKeys, error) {
	priv, err := ecdh.P256().GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	return ParseVAPIDKeys(b64.EncodeToString(priv.PublicKey().Bytes()), b64.EncodeToString(priv.Bytes()))
}

// ParseVAPIDKeys đọc khoá từ chuỗi base64url (định dạng chuẩn của web-push / pywebpush).
func ParseVAPIDKeys(publicB64, privateB64 string) (*VAPIDKeys, error) {
	d, err := decodeB64(privateB64)
	if err != nil || len(d) != 32 {
		return nil, errors.New("VAPID private key không hợp lệ (cần 32 bytes base64url)")
	}
	ecdhPriv, err := ecdh.P256().NewPrivateKey(d)
	if err != nil {
		return nil, fmt.Errorf("VAPID private key không hợp lệ: %w", err)
	}
	pub := ecdhPriv.PublicKey().Bytes()
	if publicB64 != "" {
		given, err := decodeB64(publicB64)
		if err != nil || !bytes.Equal(given, pub) {
			return nil, errors.New("VAPID public key không khớp với private key")
		}
	}
	x, y := elliptic.Unmarshal(elliptic.P256(), pub) //nolint:staticcheck // cần X,Y cho ecdsa.PrivateKey
	if x == nil {
		return nil, errors.New("VAPID public key không hợp lệ")
	}
	priv := &ecdsa.PrivateKey{
		PublicKey: ecdsa.PublicKey{Curve: elliptic.P256(), X: x, Y: y},
		D:         new(big.Int).SetBytes(d),
	}
	return &VAPIDKeys{
		PublicKey:  pub,
		privateKey: priv,
		PublicB64:  b64.EncodeToString(pub),
		PrivateB64: b64.EncodeToString(d),
	}, nil
}

// vapidJWT tạo JWT ES256 cho origin của push service.
func (k *VAPIDKeys) vapidJWT(audience, subject string, exp time.Time) (string, error) {
	header := b64.EncodeToString([]byte(`{"typ":"JWT","alg":"ES256"}`))
	claims, _ := json.Marshal(map[string]any{"aud": audience, "exp": exp.Unix(), "sub": subject})
	signingInput := header + "." + b64.EncodeToString(claims)
	digest := sha256.Sum256([]byte(signingInput))
	r, s, err := ecdsa.Sign(rand.Reader, k.privateKey, digest[:])
	if err != nil {
		return "", err
	}
	sig := make([]byte, 64)
	r.FillBytes(sig[:32])
	s.FillBytes(sig[32:])
	return signingInput + "." + b64.EncodeToString(sig), nil
}

// Encrypt mã hoá payload theo RFC 8291 (Content-Encoding: aes128gcm).
func Encrypt(sub Subscription, plaintext []byte) ([]byte, error) {
	uaPublic, err := decodeB64(sub.Keys.P256dh)
	if err != nil {
		return nil, fmt.Errorf("p256dh không hợp lệ: %w", err)
	}
	authSecret, err := decodeB64(sub.Keys.Auth)
	if err != nil || len(authSecret) == 0 {
		return nil, errors.New("auth secret không hợp lệ")
	}
	uaPub, err := ecdh.P256().NewPublicKey(uaPublic)
	if err != nil {
		return nil, fmt.Errorf("p256dh không phải khoá P-256: %w", err)
	}

	asPriv, err := ecdh.P256().GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	asPublic := asPriv.PublicKey().Bytes()
	ecdhSecret, err := asPriv.ECDH(uaPub)
	if err != nil {
		return nil, err
	}

	keyInfo := append(append([]byte("WebPush: info\x00"), uaPublic...), asPublic...)
	ikm, err := hkdf.Key(sha256.New, ecdhSecret, authSecret, string(keyInfo), 32)
	if err != nil {
		return nil, err
	}

	salt := make([]byte, 16)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return nil, err
	}
	cek, err := hkdf.Key(sha256.New, ikm, salt, "Content-Encoding: aes128gcm\x00", 16)
	if err != nil {
		return nil, err
	}
	nonce, err := hkdf.Key(sha256.New, ikm, salt, "Content-Encoding: nonce\x00", 12)
	if err != nil {
		return nil, err
	}

	block, err := aes.NewCipher(cek)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	// Một record duy nhất: plaintext || 0x02 (delimiter của record cuối)
	record := append(append([]byte{}, plaintext...), 0x02)
	ciphertext := gcm.Seal(nil, nonce, record, nil)

	const recordSize = 4096
	if len(ciphertext)+86 > recordSize {
		return nil, errors.New("payload quá lớn cho Web Push (tối đa ~3990 bytes)")
	}
	out := make([]byte, 0, 86+len(ciphertext))
	out = append(out, salt...)
	rs := make([]byte, 4)
	binary.BigEndian.PutUint32(rs, recordSize)
	out = append(out, rs...)
	out = append(out, byte(len(asPublic)))
	out = append(out, asPublic...)
	out = append(out, ciphertext...)
	return out, nil
}

var httpClient = &http.Client{Timeout: 15 * time.Second}

// Send mã hoá và gửi payload tới push service. Trả về HTTP status code.
// 201/200/202 = thành công; 404/410 = subscription đã hết hạn (nên xoá).
func Send(keys *VAPIDKeys, sub Subscription, payload []byte, opt Options) (int, error) {
	u, err := url.Parse(sub.Endpoint)
	if err != nil || u.Scheme != "https" || u.Host == "" {
		return 0, errors.New("endpoint không hợp lệ")
	}
	body, err := Encrypt(sub, payload)
	if err != nil {
		return 0, err
	}
	if opt.TTL <= 0 {
		opt.TTL = time.Hour
	}
	if opt.Urgency == "" {
		opt.Urgency = "normal"
	}
	jwt, err := keys.vapidJWT(u.Scheme+"://"+u.Host, opt.Subject, time.Now().Add(12*time.Hour))
	if err != nil {
		return 0, err
	}

	req, err := http.NewRequest(http.MethodPost, sub.Endpoint, bytes.NewReader(body))
	if err != nil {
		return 0, err
	}
	req.Header.Set("Content-Type", "application/octet-stream")
	req.Header.Set("Content-Encoding", "aes128gcm")
	req.Header.Set("TTL", fmt.Sprintf("%d", int(opt.TTL.Seconds())))
	req.Header.Set("Urgency", opt.Urgency)
	req.Header.Set("Authorization", fmt.Sprintf("vapid t=%s, k=%s", jwt, keys.PublicB64))

	resp, err := httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		msg, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		return resp.StatusCode, fmt.Errorf("push service trả về %d: %s", resp.StatusCode, strings.TrimSpace(string(msg)))
	}
	return resp.StatusCode, nil
}
