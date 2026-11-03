package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

// binanceFutures: client USDⓈ-M Futures tối giản, tái dùng phần ký/gửi request của binanceSpot.
type binanceFutures struct{ *binanceSpot }

func newBinanceFutures(key, secret string, testnet bool) *binanceFutures {
	b := newBinanceSpot(key, secret, false)
	if testnet {
		b.baseURL = "https://testnet.binancefuture.com"
	} else {
		b.baseURL = "https://fapi.binance.com"
	}
	return &binanceFutures{b}
}

// cancelOpenStops huỷ các lệnh điều kiện (STOP/TAKE_PROFIT/TRAILING) đang mở của symbol.
func (f *binanceFutures) cancelOpenStops(symbol string) (int, error) {
	body, st, err := f.do("GET", "/fapi/v1/openOrders", url.Values{"symbol": {symbol}}, true)
	if err != nil {
		return 0, err
	}
	if st != http.StatusOK {
		return 0, binanceErr(body, st)
	}
	var orders []struct {
		OrderID int64  `json:"orderId"`
		Type    string `json:"type"`
	}
	if err := json.Unmarshal(body, &orders); err != nil {
		return 0, err
	}
	n := 0
	for _, o := range orders {
		t := strings.ToUpper(o.Type)
		if !strings.Contains(t, "STOP") && !strings.Contains(t, "TAKE_PROFIT") && !strings.Contains(t, "TRAILING") {
			continue
		}
		cb, cs, cerr := f.do("DELETE", "/fapi/v1/order", url.Values{"symbol": {symbol}, "orderId": {strconv.FormatInt(o.OrderID, 10)}}, true)
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

type futuresPos struct {
	Amt          float64
	PositionSide string
}

// openPosition trả về vị thế đang mở (khác 0) của symbol; ok=false nếu không có.
func (f *binanceFutures) openPosition(symbol string) (futuresPos, bool, error) {
	body, st, err := f.do("GET", "/fapi/v2/positionRisk", url.Values{"symbol": {symbol}}, true)
	if err != nil {
		return futuresPos{}, false, err
	}
	if st != http.StatusOK {
		return futuresPos{}, false, binanceErr(body, st)
	}
	var rows []struct {
		PositionAmt  string `json:"positionAmt"`
		PositionSide string `json:"positionSide"`
	}
	if err := json.Unmarshal(body, &rows); err != nil {
		return futuresPos{}, false, err
	}
	for _, r := range rows {
		amt, _ := strconv.ParseFloat(r.PositionAmt, 64)
		if amt != 0 {
			return futuresPos{Amt: amt, PositionSide: r.PositionSide}, true, nil
		}
	}
	return futuresPos{}, false, nil
}

func (f *binanceFutures) marketLotStep(symbol string) (float64, error) {
	body, st, err := f.do("GET", "/fapi/v1/exchangeInfo", nil, false)
	if err != nil {
		return 0, err
	}
	if st != http.StatusOK {
		return 0, binanceErr(body, st)
	}
	var info struct {
		Symbols []struct {
			Symbol  string `json:"symbol"`
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
		if s.Symbol != symbol {
			continue
		}
		step := 0.0
		for _, fl := range s.Filters {
			if fl.FilterType == "MARKET_LOT_SIZE" || (fl.FilterType == "LOT_SIZE" && step == 0) {
				if v, e := strconv.ParseFloat(fl.StepSize, 64); e == nil && v > 0 {
					step = v
				}
			}
		}
		if step > 0 {
			return step, nil
		}
	}
	return 0, fmt.Errorf("không tìm thấy LOT_SIZE futures cho %s", symbol)
}

// closeFuturesPosition: huỷ SL/TP của sàn → đóng tối đa min(|positionAmt|, units) bằng MARKET reduceOnly.
// Chỉ đóng phần của vị thế này, không đụng phần còn lại của tài khoản. Hỗ trợ one-way và hedge mode.
func (f *binanceFutures) closeFuturesPosition(symbol string, units float64) (closed float64, cancelled int, alreadyClosed bool, err error) {
	symbol = strings.ToUpper(symbol)
	if !strings.HasSuffix(symbol, "USDT") {
		return 0, 0, false, fmt.Errorf("symbol %q không phải cặp USDT", symbol)
	}
	cancelled, err = f.cancelOpenStops(symbol)
	if err != nil {
		return 0, cancelled, false, fmt.Errorf("không huỷ được lệnh SL trên sàn futures: %w", err)
	}
	pos, ok, err := f.openPosition(symbol)
	if err != nil {
		return 0, cancelled, false, err
	}
	if !ok {
		return 0, cancelled, true, nil
	}
	size := pos.Amt
	if size < 0 {
		size = -size
	}
	qty := size
	if units > 0 && units < size {
		qty = units
	}
	step, err := f.marketLotStep(symbol)
	if err != nil {
		return 0, cancelled, false, err
	}
	qty = floorToStep(qty, step)
	if qty < step || qty <= 0 {
		return 0, cancelled, true, nil
	}
	side := "SELL"
	if pos.Amt < 0 {
		side = "BUY"
	}
	params := url.Values{
		"symbol": {symbol}, "side": {side}, "type": {"MARKET"},
		"quantity": {strconv.FormatFloat(qty, 'f', -1, 64)},
	}
	if pos.PositionSide == "" || pos.PositionSide == "BOTH" {
		params.Set("reduceOnly", "true")
	} else {
		params.Set("positionSide", pos.PositionSide) // hedge mode không nhận reduceOnly
	}
	body, st, err := f.do("POST", "/fapi/v1/order", params, true)
	if err != nil {
		return 0, cancelled, false, err
	}
	if st != http.StatusOK {
		return 0, cancelled, false, binanceErr(body, st)
	}
	return qty, cancelled, false, nil
}
