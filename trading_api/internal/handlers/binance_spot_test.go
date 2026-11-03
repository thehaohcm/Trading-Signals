package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"sync"
	"testing"
)

// fakeBinance mô phỏng Binance Spot: SL STOP_LOSS_LIMIT khoá số dư cho tới khi bị huỷ.
type fakeBinance struct {
	mu          sync.Mutex
	free        float64
	stops       map[int64]float64 // orderId -> số lượng bị khoá
	sells       []float64
	cancelFails bool
	sellFails   bool
	step        string
	log         []string
}

func (f *fakeBinance) handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.mu.Lock()
		defer f.mu.Unlock()
		f.log = append(f.log, r.Method+" "+r.URL.Path)
		if r.URL.Path != "/api/v3/exchangeInfo" && r.URL.Query().Get("signature") == "" {
			http.Error(w, `{"code":-1022,"msg":"Signature missing"}`, 400)
			return
		}
		switch {
		case r.URL.Path == "/api/v3/openOrders":
			var out []map[string]interface{}
			for id := range f.stops {
				out = append(out, map[string]interface{}{"orderId": id, "type": "STOP_LOSS_LIMIT", "side": "SELL"})
			}
			// một lệnh LIMIT mua không liên quan phải được giữ nguyên
			out = append(out, map[string]interface{}{"orderId": 999, "type": "LIMIT", "side": "BUY"})
			json.NewEncoder(w).Encode(out)
		case r.URL.Path == "/api/v3/order" && r.Method == "DELETE":
			if f.cancelFails {
				http.Error(w, `{"code":-2011,"msg":"Unknown order"}`, 400)
				return
			}
			id, _ := strconv.ParseInt(r.URL.Query().Get("orderId"), 10, 64)
			f.free += f.stops[id]
			delete(f.stops, id)
			w.Write([]byte(`{}`))
		case r.URL.Path == "/api/v3/account":
			fmt.Fprintf(w, `{"balances":[{"asset":"USDT","free":"1000"},{"asset":"BTC","free":"%s"}]}`, strconv.FormatFloat(f.free, 'f', -1, 64))
		case r.URL.Path == "/api/v3/exchangeInfo":
			fmt.Fprintf(w, `{"symbols":[{"filters":[{"filterType":"PRICE_FILTER"},{"filterType":"LOT_SIZE","stepSize":"%s"}]}]}`, f.step)
		case r.URL.Path == "/api/v3/order" && r.Method == "POST":
			if f.sellFails {
				http.Error(w, `{"code":-2010,"msg":"insufficient balance"}`, 400)
				return
			}
			q, _ := strconv.ParseFloat(r.URL.Query().Get("quantity"), 64)
			if q > f.free+1e-12 {
				http.Error(w, `{"code":-2010,"msg":"insufficient balance"}`, 400)
				return
			}
			f.free -= q
			f.sells = append(f.sells, q)
			w.Write([]byte(`{"status":"FILLED"}`))
		default:
			http.NotFound(w, r)
		}
	})
}

func newTestBinance(t *testing.T, f *fakeBinance) *binanceSpot {
	srv := httptest.NewServer(f.handler())
	t.Cleanup(srv.Close)
	b := newBinanceSpot("key", "secret", false)
	b.baseURL = srv.URL
	return b
}

func TestCloseSpotPositionCancelsStopAndSellsOnlyPositionUnits(t *testing.T) {
	// Người dùng có 2.0 BTC free + 0.5 BTC đang bị SL khoá; vị thế chỉ gồm 0.5 BTC
	f := &fakeBinance{free: 2.0, stops: map[int64]float64{1: 0.5}, step: "0.00100000"}
	b := newTestBinance(t, f)
	sold, cancelled, already, err := b.closeSpotPosition("BTCUSDT", 0.5)
	if err != nil || already {
		t.Fatalf("err=%v already=%v", err, already)
	}
	if cancelled != 1 || len(f.stops) != 0 {
		t.Errorf("phải huỷ đúng 1 SL, cancelled=%d còn=%d", cancelled, len(f.stops))
	}
	if sold != 0.5 || len(f.sells) != 1 || f.sells[0] != 0.5 {
		t.Errorf("chỉ được bán 0.5 BTC của vị thế, sold=%v sells=%v", sold, f.sells)
	}
	if f.free != 2.0 {
		t.Errorf("số dư khác của người dùng không được bị đụng tới, free=%v", f.free)
	}
}

func TestCloseSpotPositionSellFromLockedBalanceOnly(t *testing.T) {
	// Toàn bộ số dư đang bị SL khoá (free=0) — trước đây bán 0 và vẫn đánh dấu đã đóng
	f := &fakeBinance{free: 0, stops: map[int64]float64{7: 0.5}, step: "0.001"}
	b := newTestBinance(t, f)
	sold, _, already, err := b.closeSpotPosition("BTCUSDT", 0.5)
	if err != nil || already || sold != 0.5 {
		t.Fatalf("sold=%v already=%v err=%v", sold, already, err)
	}
}

func TestCloseSpotPositionAlreadyClosedByExchangeStop(t *testing.T) {
	f := &fakeBinance{free: 0, stops: map[int64]float64{}, step: "0.001"}
	b := newTestBinance(t, f)
	sold, _, already, err := b.closeSpotPosition("BTCUSDT", 0.5)
	if err != nil || !already || sold != 0 || len(f.sells) != 0 {
		t.Fatalf("sold=%v already=%v err=%v sells=%v", sold, already, err, f.sells)
	}
}

func TestCloseSpotPositionCapsUnitsAtFree(t *testing.T) {
	f := &fakeBinance{free: 0.3, stops: map[int64]float64{}, step: "0.1"}
	b := newTestBinance(t, f)
	sold, _, _, err := b.closeSpotPosition("BTCUSDT", 0.5)
	if err != nil || sold != 0.3 {
		t.Fatalf("sold=%v err=%v", sold, err)
	}
}

func TestCloseSpotPositionErrorsAreSurfaced(t *testing.T) {
	f := &fakeBinance{free: 1, stops: map[int64]float64{1: 0.5}, cancelFails: true, step: "0.001"}
	if _, _, _, err := newTestBinance(t, f).closeSpotPosition("BTCUSDT", 0.5); err == nil {
		t.Error("huỷ SL lỗi phải trả về lỗi (không được bán tiếp)")
	}
	if len(f.sells) != 0 {
		t.Error("không được bán khi huỷ SL thất bại")
	}
	f2 := &fakeBinance{free: 1, stops: map[int64]float64{}, sellFails: true, step: "0.001"}
	if _, _, _, err := newTestBinance(t, f2).closeSpotPosition("BTCUSDT", 0.5); err == nil {
		t.Error("bán lỗi phải trả về lỗi để KHÔNG đánh dấu vị thế đã đóng")
	}
	if _, _, _, err := newTestBinance(t, f2).closeSpotPosition("BTCEUR", 1); err == nil {
		t.Error("cặp không phải USDT phải bị từ chối")
	}
}

func TestFloorToStep(t *testing.T) {
	cases := []struct{ q, step, want float64 }{
		{0.3, 0.1, 0.3}, {0.29999, 0.1, 0.2}, {1.23456, 0.001, 1.234}, {5, 1, 5}, {0.0005, 0.001, 0}, {7.9, 0, 7.9},
	}
	for _, c := range cases {
		if got := floorToStep(c.q, c.step); got != c.want {
			t.Errorf("floorToStep(%v,%v)=%v want %v", c.q, c.step, got, c.want)
		}
	}
	_ = strings.TrimSpace
}
