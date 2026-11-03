package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync"
	"testing"
)

type fakeFutures struct {
	mu        sync.Mutex
	amt       float64
	posSide   string
	stops     map[int64]bool
	orders    []map[string]string
	cancelErr bool
	orderErr  bool
}

func (f *fakeFutures) handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.mu.Lock()
		defer f.mu.Unlock()
		if r.URL.Path != "/fapi/v1/exchangeInfo" && r.URL.Query().Get("signature") == "" {
			http.Error(w, `{"code":-1022}`, 400)
			return
		}
		switch {
		case r.URL.Path == "/fapi/v1/openOrders":
			out := []map[string]interface{}{{"orderId": 999, "type": "LIMIT"}}
			for id := range f.stops {
				out = append(out, map[string]interface{}{"orderId": id, "type": "STOP_MARKET"})
			}
			json.NewEncoder(w).Encode(out)
		case r.URL.Path == "/fapi/v1/order" && r.Method == "DELETE":
			if f.cancelErr {
				http.Error(w, `{"code":-2011}`, 400)
				return
			}
			id, _ := strconv.ParseInt(r.URL.Query().Get("orderId"), 10, 64)
			delete(f.stops, id)
			w.Write([]byte(`{}`))
		case r.URL.Path == "/fapi/v2/positionRisk":
			side := f.posSide
			if side == "" {
				side = "BOTH"
			}
			fmt.Fprintf(w, `[{"positionAmt":"0","positionSide":"LONG"},{"positionAmt":"%s","positionSide":"%s"}]`, strconv.FormatFloat(f.amt, 'f', -1, 64), side)
		case r.URL.Path == "/fapi/v1/exchangeInfo":
			w.Write([]byte(`{"symbols":[{"symbol":"ETHUSDT","filters":[{"filterType":"LOT_SIZE","stepSize":"0.001"},{"filterType":"MARKET_LOT_SIZE","stepSize":"0.01"}]}]}`))
		case r.URL.Path == "/fapi/v1/order" && r.Method == "POST":
			if f.orderErr {
				http.Error(w, `{"code":-2022}`, 400)
				return
			}
			o := map[string]string{}
			for k := range r.URL.Query() {
				o[k] = r.URL.Query().Get(k)
			}
			f.orders = append(f.orders, o)
			w.Write([]byte(`{"status":"NEW"}`))
		default:
			http.NotFound(w, r)
		}
	})
}

func newTestFutures(t *testing.T, f *fakeFutures) *binanceFutures {
	srv := httptest.NewServer(f.handler())
	t.Cleanup(srv.Close)
	b := newBinanceFutures("k", "s", false)
	b.baseURL = srv.URL
	return b
}

func TestCloseFuturesLongReduceOnlyAndCancelsStops(t *testing.T) {
	f := &fakeFutures{amt: 2.5, stops: map[int64]bool{1: true}}
	closed, c, already, err := newTestFutures(t, f).closeFuturesPosition("ETHUSDT", 1.234)
	if err != nil || already || c != 1 || len(f.stops) != 0 {
		t.Fatalf("closed=%v c=%d already=%v err=%v stops=%d", closed, c, already, err, len(f.stops))
	}
	if closed != 1.23 { // bước MARKET_LOT_SIZE 0.01
		t.Errorf("closed=%v", closed)
	}
	o := f.orders[0]
	if o["side"] != "SELL" || o["reduceOnly"] != "true" || o["type"] != "MARKET" {
		t.Errorf("order=%v", o)
	}
}

func TestCloseFuturesShortUsesBuy(t *testing.T) {
	f := &fakeFutures{amt: -1, stops: map[int64]bool{}}
	closed, _, _, err := newTestFutures(t, f).closeFuturesPosition("ETHUSDT", 5)
	if err != nil || closed != 1 || f.orders[0]["side"] != "BUY" {
		t.Fatalf("closed=%v err=%v orders=%v", closed, err, f.orders)
	}
}

func TestCloseFuturesHedgeModeUsesPositionSide(t *testing.T) {
	f := &fakeFutures{amt: 1, posSide: "LONG", stops: map[int64]bool{}}
	_, _, _, err := newTestFutures(t, f).closeFuturesPosition("ETHUSDT", 1)
	o := f.orders[0]
	if err != nil || o["positionSide"] != "LONG" || o["reduceOnly"] != "" {
		t.Fatalf("err=%v order=%v", err, o)
	}
}

func TestCloseFuturesAlreadyFlat(t *testing.T) {
	f := &fakeFutures{amt: 0, stops: map[int64]bool{}}
	_, _, already, err := newTestFutures(t, f).closeFuturesPosition("ETHUSDT", 1)
	if err != nil || !already || len(f.orders) != 0 {
		t.Fatalf("already=%v err=%v orders=%v", already, err, f.orders)
	}
}

func TestCloseFuturesErrorsDoNotMarkClosed(t *testing.T) {
	f := &fakeFutures{amt: 1, stops: map[int64]bool{1: true}, cancelErr: true}
	if _, _, _, err := newTestFutures(t, f).closeFuturesPosition("ETHUSDT", 1); err == nil || len(f.orders) != 0 {
		t.Error("huỷ SL lỗi phải báo lỗi và không gửi lệnh đóng")
	}
	f2 := &fakeFutures{amt: 1, stops: map[int64]bool{}, orderErr: true}
	if _, _, _, err := newTestFutures(t, f2).closeFuturesPosition("ETHUSDT", 1); err == nil {
		t.Error("lệnh đóng lỗi phải báo lỗi")
	}
	if _, _, _, err := newTestFutures(t, f2).closeFuturesPosition("ETHEUR", 1); err == nil {
		t.Error("cặp không phải USDT phải bị từ chối")
	}
}
