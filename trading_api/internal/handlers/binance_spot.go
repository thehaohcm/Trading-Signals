package handlers

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// binanceSpot là client Binance Spot tối giản (REST có ký HMAC) dùng cho thao tác đóng vị thế thủ công.
type binanceSpot struct {
	baseURL string
	key     string
	secret  string
	client  *http.Client
}

func newBinanceSpot(key, secret string, testnet bool) *binanceSpot {
	base := "https://api.binance.com"
	if testnet {
		base = "https://testnet.binance.vision"
	}
	return &binanceSpot{baseURL: base, key: key, secret: secret, client: &http.Client{Timeout: 10 * time.Second}}
}

func (b *binanceSpot) do(method, path string, params url.Values, signed bool) ([]byte, int, error) {
	if params == nil {
		params = url.Values{}
	}
	if signed {
		params.Set("timestamp", strconv.FormatInt(time.Now().UnixMilli(), 10))
		params.Set("recvWindow", "5000")
		q := params.Encode()
		mac := hmac.New(sha256.New, []byte(b.secret))
		mac.Write([]byte(q))
		params.Set("signature", hex.EncodeToString(mac.Sum(nil)))
	}
	req, err := http.NewRequest(method, b.baseURL+path+"?"+params.Encode(), nil)
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("X-MBX-APIKEY", b.key)
	resp, err := b.client.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 2<<20))
	return body, resp.StatusCode, nil
}

func binanceErr(body []byte, status int) error {
	return fmt.Errorf("Binance HTTP %d: %s", status, strings.TrimSpace(string(body)))
}

// cancelOpenStops huỷ mọi lệnh SELL loại STOP* đang mở của symbol, trả về số lệnh đã huỷ.
func (b *binanceSpot) cancelOpenStops(symbol string) (int, error) {
	body, st, err := b.do("GET", "/api/v3/openOrders", url.Values{"symbol": {symbol}}, true)
	if err != nil {
		return 0, err
	}
	if st != http.StatusOK {
		return 0, binanceErr(body, st)
	}
	var orders []struct {
		OrderID int64  `json:"orderId"`
		Type    string `json:"type"`
		Side    string `json:"side"`
	}
	if err := json.Unmarshal(body, &orders); err != nil {
		return 0, err
	}
	n := 0
	for _, o := range orders {
		if o.Side != "SELL" || !strings.Contains(strings.ToUpper(o.Type), "STOP") {
			continue
		}
		cb, cs, cerr := b.do("DELETE", "/api/v3/order", url.Values{"symbol": {symbol}, "orderId": {strconv.FormatInt(o.OrderID, 10)}}, true)
		if cerr != nil {
			return n, cerr
		}
		if cs != http.StatusOK {
			return n, binanceErr(cb, cs)
		}
		n++
	}
	return n, nil
}

func (b *binanceSpot) freeBalance(asset string) (float64, error) {
	body, st, err := b.do("GET", "/api/v3/account", nil, true)
	if err != nil {
		return 0, err
	}
	if st != http.StatusOK {
		return 0, binanceErr(body, st)
	}
	var acc struct {
		Balances []struct {
			Asset string `json:"asset"`
			Free  string `json:"free"`
		} `json:"balances"`
	}
	if err := json.Unmarshal(body, &acc); err != nil {
		return 0, err
	}
	for _, bal := range acc.Balances {
		if strings.EqualFold(bal.Asset, asset) {
			return strconv.ParseFloat(bal.Free, 64)
		}
	}
	return 0, nil
}

// lotStep trả về stepSize của bộ lọc LOT_SIZE (khối lượng phải là bội số của nó).
func (b *binanceSpot) lotStep(symbol string) (float64, error) {
	body, st, err := b.do("GET", "/api/v3/exchangeInfo", url.Values{"symbol": {symbol}}, false)
	if err != nil {
		return 0, err
	}
	if st != http.StatusOK {
		return 0, binanceErr(body, st)
	}
	var info struct {
		Symbols []struct {
			Filters []struct {
				FilterType string `json:"filterType"`
				StepSize   string `json:"stepSize"`
			} `json:"filters"`
		} `json:"symbols"`
	}
	if err := json.Unmarshal(body, &info); err != nil {
		return 0, err
	}
	for _, s := range info.Symbols {
		for _, f := range s.Filters {
			if f.FilterType == "LOT_SIZE" {
				return strconv.ParseFloat(f.StepSize, 64)
			}
		}
	}
	return 0, fmt.Errorf("không tìm thấy LOT_SIZE cho %s", symbol)
}

// floorToStep làm tròn xuống theo bội số step (chống lỗi dấu phẩy động, vd 0.3/0.1).
func floorToStep(qty, step float64) float64 {
	if step <= 0 {
		return qty
	}
	n := math.Floor(qty/step + 1e-9)
	decimals := 0
	for s := step; s < 1 && decimals < 12; s *= 10 {
		decimals++
	}
	p := math.Pow(10, float64(decimals))
	return math.Round(n*step*p) / p
}

// closeSpotPosition đóng vị thế Spot thật: huỷ SL của sàn → bán tối đa min(units, free) bằng lệnh market.
// alreadyClosed=true khi không còn gì để bán (SL phía sàn đã khớp hoặc đã bán tay).
// Chỉ bán đúng khối lượng của vị thế — KHÔNG bán phần số dư khác của người dùng.
func (b *binanceSpot) closeSpotPosition(symbol string, units float64) (sold float64, cancelled int, alreadyClosed bool, err error) {
	symbol = strings.ToUpper(symbol)
	if !strings.HasSuffix(symbol, "USDT") {
		return 0, 0, false, fmt.Errorf("symbol %q không phải cặp USDT", symbol)
	}
	cancelled, err = b.cancelOpenStops(symbol)
	if err != nil {
		return 0, cancelled, false, fmt.Errorf("không huỷ được lệnh SL trên sàn: %w", err)
	}
	free, err := b.freeBalance(strings.TrimSuffix(symbol, "USDT"))
	if err != nil {
		return 0, cancelled, false, err
	}
	qty := free
	if units > 0 && units < free {
		qty = units
	}
	step, err := b.lotStep(symbol)
	if err != nil {
		return 0, cancelled, false, err
	}
	qty = floorToStep(qty, step)
	if qty < step || qty <= 0 {
		return 0, cancelled, true, nil
	}
	body, st, err := b.do("POST", "/api/v3/order", url.Values{
		"symbol": {symbol}, "side": {"SELL"}, "type": {"MARKET"},
		"quantity": {strconv.FormatFloat(qty, 'f', -1, 64)},
	}, true)
	if err != nil {
		return 0, cancelled, false, err
	}
	if st != http.StatusOK {
		return 0, cancelled, false, binanceErr(body, st)
	}
	return qty, cancelled, false, nil
}
