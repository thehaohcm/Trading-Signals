package webpush

import (
	"database/sql"
	"errors"
	"log"
	"os"
	"sync"
)

var (
	keysMu     sync.Mutex
	cachedKeys *VAPIDKeys
)

// GetKeys trả về cặp khoá VAPID dùng chung cho mọi instance của API.
// Thứ tự ưu tiên: biến môi trường VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY → bảng web_push_config
// (tự sinh lần đầu, lưu vào DB để VPS và Fly.io dùng chung một cặp khoá).
func GetKeys(db *sql.DB) (*VAPIDKeys, error) {
	keysMu.Lock()
	defer keysMu.Unlock()
	if cachedKeys != nil {
		return cachedKeys, nil
	}

	if pub, priv := os.Getenv("VAPID_PUBLIC_KEY"), os.Getenv("VAPID_PRIVATE_KEY"); pub != "" && priv != "" {
		k, err := ParseVAPIDKeys(pub, priv)
		if err != nil {
			return nil, err
		}
		cachedKeys = k
		return k, nil
	}

	var pub, priv string
	err := db.QueryRow(`SELECT public_key, private_key FROM public.web_push_config WHERE id = 1`).Scan(&pub, &priv)
	if errors.Is(err, sql.ErrNoRows) {
		gen, genErr := GenerateVAPIDKeys()
		if genErr != nil {
			return nil, genErr
		}
		// ON CONFLICT: nếu instance khác vừa tạo trước thì dùng khoá của instance đó
		if _, err := db.Exec(`
			INSERT INTO public.web_push_config (id, public_key, private_key)
			VALUES (1, $1, $2) ON CONFLICT (id) DO NOTHING`, gen.PublicB64, gen.PrivateB64); err != nil {
			return nil, err
		}
		err = db.QueryRow(`SELECT public_key, private_key FROM public.web_push_config WHERE id = 1`).Scan(&pub, &priv)
		if err == nil {
			log.Println("🔑 [WebPush] Đã tạo cặp khoá VAPID mới và lưu vào web_push_config")
		}
	}
	if err != nil {
		return nil, err
	}
	k, err := ParseVAPIDKeys(pub, priv)
	if err != nil {
		return nil, err
	}
	cachedKeys = k
	return k, nil
}

// subject VAPID: thông tin liên hệ gửi kèm cho push service (Google/Mozilla/Microsoft/Apple).
func vapidSubject() string {
	if s := os.Getenv("VAPID_SUBJECT"); s != "" {
		return s
	}
	return "https://tradesign.io.vn"
}
