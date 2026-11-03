#!/usr/bin/env python3
"""
Backtest chiến lược breakout + nhồi lệnh của alert.py bằng nến lịch sử Binance.

Dùng CHÍNH logic trong trading_core (compute_stop_loss) nên kết quả bám sát engine thật.
Toàn bộ phép tính chạy bằng code — KHÔNG tốn token AI. Chỉ khi thêm --ai-summary mới gọi AI
đúng 1 lần cho TẤT CẢ symbol (gom batch) để nhận xét ngắn gọn.

Ví dụ:
  python3 backtest.py --symbols BTCUSDT,ETHUSDT,SOLUSDT --interval 15m --days 90
  python3 backtest.py --symbols BTCUSDT --csv btc_15m.csv        # chạy offline từ CSV (ts,open,high,low,close,volume)
  python3 backtest.py --symbols BTCUSDT,ETHUSDT --sl-pct 2 --grid # thử lưới tham số
  python3 backtest.py --symbols BTCUSDT,ETHUSDT --ai-summary      # 1 lần gọi AI (cần GEMINI_API_KEY)

Giả định (đã cố ý thận trọng): vào lệnh ở GIÁ ĐÓNG nến breakout (không nhìn trước), SL khớp ở giá SL
(hoặc giá mở cửa nếu gap xuống), có phí + trượt giá hai chiều. Backtest KHÔNG đảm bảo kết quả tương lai.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trading_core as core  # noqa: E402

INTERVAL_MS = {'1m': 60_000, '3m': 180_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
               '1h': 3_600_000, '2h': 7_200_000, '4h': 14_400_000, '1d': 86_400_000}


@dataclass
class Params:
    market: str = 'crypto'        # 'crypto' hoặc 'vn' (cổ phiếu VN: T+2, biên độ giá, lô 100, thuế bán)
    vn_price_band_pct: float = 7.0   # biên độ trần/sàn mỗi phiên: HOSE 7%, HNX 10%, UPCOM 15%
    vn_t_plus_bars: int = 2          # KHÔNG được bán trước T+2 (cổ phiếu mới mua chưa về tài khoản)
    vn_lot_size: int = 100           # khối lượng phải là bội số lô
    vn_tax_sell_pct: float = 0.1     # thuế bán (trên giá trị bán), cộng thêm vào fee_pct khi market='vn'
    lookback: int = 96            # đỉnh của N nến trước (15m x 96 = 1 ngày)
    margin_pct: float = 0.05      # phải đóng cửa trên đỉnh ít nhất margin %
    max_chase_pct: float = 2.0    # bỏ qua nếu giá đóng đã vượt đỉnh quá % này (không đuổi giá)
    min_vol_ratio: float = 1.2    # khối lượng nến breakout / trung bình 20 nến trước
    sl_pct: float = 2.0
    spread_pct: float = 0.1
    sl_mode: str = 'TRAILING_PEAK'
    max_pyramids: int = 3
    pyramid_step_pct: float = 2.0
    max_hold_bars: int = 0        # 0 = không giới hạn
    fee_pct: float = 0.1          # mỗi chiều
    slippage_pct: float = 0.05    # mỗi chiều
    cooldown_bars: int = 0        # nghỉ sau khi đóng lệnh


def fetch_klines(symbol, interval, days, base='https://api.binance.com'):
    step = INTERVAL_MS[interval]
    end = int(time.time() * 1000)
    start = end - days * 86_400_000
    out = []
    while start < end:
        url = f"{base}/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start}&limit=1000"
        with urllib.request.urlopen(url, timeout=20) as r:
            rows = json.loads(r.read())
        if not rows:
            break
        out.extend(rows)
        start = rows[-1][0] + step
        if len(rows) < 1000:
            break
    return [dict(t=int(r[0]), o=float(r[1]), h=float(r[2]), l=float(r[3]), c=float(r[4]), v=float(r[5])) for r in out]


def load_csv(path):
    rows = []
    with open(path, newline='') as f:
        for r in csv.reader(f):
            try:
                rows.append(dict(t=int(float(r[0])), o=float(r[1]), h=float(r[2]), l=float(r[3]), c=float(r[4]), v=float(r[5])))
            except (ValueError, IndexError):
                continue  # bỏ dòng tiêu đề
    return rows


def _vn_capped(bar, prev_close, band_pct):
    """Giá trong phiên bị kẹp trong [sàn, trần] so với giá tham chiếu (đóng cửa phiên trước)."""
    if prev_close is None or band_pct <= 0:
        return bar
    ceil_p = prev_close * (1 + band_pct / 100.0)
    floor_p = prev_close * (1 - band_pct / 100.0)
    return dict(bar, o=min(max(bar['o'], floor_p), ceil_p), h=min(bar['h'], ceil_p),
                l=max(bar['l'], floor_p), c=min(max(bar['c'], floor_p), ceil_p))


def simulate(bars, p: Params):
    """Chạy mô phỏng trên danh sách nến. Trả về danh sách lệnh (mỗi lệnh gồm pnl_pct, bars_held, layers, reason)."""
    is_vn = p.market == 'vn'
    if is_vn:
        capped, prev = [], None
        for b in bars:
            cb = _vn_capped(b, prev, p.vn_price_band_pct)
            capped.append(cb)
            prev = cb['c']
        bars = capped
    trades = []
    n = len(bars)
    pos = None
    cooldown_until = -1
    start = max(p.lookback, 21)
    cost = (p.fee_pct + p.slippage_pct) / 100.0
    if is_vn:
        cost += p.vn_tax_sell_pct / 100.0 / 2.0  # thuế chỉ tính phía bán, cộng tương đương để chia đều 2 chiều
    for i in range(start, n):
        b = bars[i]
        if pos is not None:
            can_sell = (not is_vn) or (i - pos['i0'] >= p.vn_t_plus_bars)
            exit_price, reason = None, None
            if can_sell and b['l'] <= pos['sl']:
                exit_price, reason = min(pos['sl'], b['o']), 'SL'   # gap xuống → khớp ở giá mở cửa
            else:
                pos['highest'] = max(pos['highest'], b['h'])
                # nhồi lệnh: có thể nhồi nhiều tầng trong 1 nến nếu giá vượt nhiều mốc
                lot = p.vn_lot_size if is_vn else 1.0
                while pos['layer'] < p.max_pyramids and b['h'] >= pos['next_pyr']:
                    add_price = max(pos['next_pyr'], b['o'])
                    pos['cost_total'] += add_price * lot
                    pos['units'] += lot
                    pos['avg'] = pos['cost_total'] / pos['units']
                    pos['layer'] += 1
                    pos['last_buy'] = add_price
                    pos['next_pyr'] = add_price * (1 + p.pyramid_step_pct / 100.0)
                pos['sl'], _ = core.compute_stop_loss(pos['avg'], pos['highest'], pos['layer'], p.max_pyramids,
                                                      p.sl_pct, p.spread_pct, p.sl_mode, prev_sl=pos['sl'])
                if p.max_hold_bars and i - pos['i0'] >= p.max_hold_bars:
                    exit_price, reason = b['c'], 'TIMEOUT'
            if exit_price is not None:
                gross = (exit_price * (1 - cost) - pos['avg'] * (1 + cost)) / (pos['avg'] * (1 + cost))
                lot_norm = p.vn_lot_size if is_vn else 1.0
                trades.append(dict(pnl_pct=gross * 100.0, bars_held=i - pos['i0'], layers=pos['layer'], reason=reason,
                                   weight=pos['units'] / lot_norm))
                pos = None
                cooldown_until = i + p.cooldown_bars
            continue
        if i <= cooldown_until:
            continue
        level = max(x['h'] for x in bars[i - p.lookback:i])
        trigger = level * (1 + p.margin_pct / 100.0)
        if b['c'] < trigger:
            continue
        if p.max_chase_pct > 0 and b['c'] > level * (1 + p.max_chase_pct / 100.0):
            continue
        avg_vol = sum(x['v'] for x in bars[i - 20:i]) / 20.0
        if p.min_vol_ratio > 0 and avg_vol > 0 and b['v'] / avg_vol < p.min_vol_ratio:
            continue
        entry = b['c']
        lot = p.vn_lot_size if is_vn else 1.0
        sl, _ = core.compute_stop_loss(entry, entry, 1, p.max_pyramids, p.sl_pct, p.spread_pct, p.sl_mode)
        pos = dict(i0=i, avg=entry, cost_total=entry * lot, units=lot, layer=1, highest=entry, last_buy=entry,
                   next_pyr=entry * (1 + p.pyramid_step_pct / 100.0), sl=sl)
    if pos is not None:  # đóng lệnh còn mở ở nến cuối để thống kê
        last = bars[-1]['c']
        pnl = (last * (1 - cost) - pos['avg'] * (1 + cost)) / (pos['avg'] * (1 + cost))
        lot_norm = p.vn_lot_size if is_vn else 1.0
        trades.append(dict(pnl_pct=pnl * 100.0, bars_held=n - 1 - pos['i0'], layers=pos['layer'], reason='OPEN_AT_END', weight=pos['units'] / lot_norm))
    return trades


def stats(trades):
    if not trades:
        return dict(trades=0, win_rate=0.0, avg_pnl_pct=0.0, profit_factor=None, total_pnl_pct=0.0, max_drawdown_pct=0.0,
                    avg_bars=0.0, sl_exits=0)
    # total_pnl_pct = tổng (pnl% × số tầng) = % lãi/lỗ tính trên vốn của MỘT tầng; lệnh nhồi nhiều tầng có trọng số lớn hơn.
    # Vì vậy avg_pnl_pct (trung bình theo lệnh) và total_pnl_pct có thể ngược dấu khi lệnh thắng được nhồi nhiều.
    pnls = [t['pnl_pct'] for t in trades]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x <= 0]
    gl = -sum(losses)
    equity, peak, mdd = 0.0, 0.0, 0.0
    for t in trades:
        equity += t['pnl_pct'] * t['weight']
        peak = max(peak, equity)
        mdd = max(mdd, peak - equity)
    return dict(trades=len(trades), win_rate=round(100.0 * len(wins) / len(trades), 1),
                avg_pnl_pct=round(sum(pnls) / len(pnls), 3),
                profit_factor=(round(sum(wins) / gl, 2) if gl > 0 else None),
                total_pnl_pct=round(equity, 2), max_drawdown_pct=round(mdd, 2),
                avg_bars=round(sum(t['bars_held'] for t in trades) / len(trades), 1),
                sl_exits=sum(1 for t in trades if t['reason'] == 'SL'))


def grid_params(base: Params):
    for sl in (1.5, 2.0, 3.0):
        for look in (48, 96, 192):
            for vol in (0.0, 1.2, 1.5):
                q = Params(**asdict(base))
                q.sl_pct, q.lookback, q.min_vol_ratio = sl, look, vol
                yield q


def ai_summary(results):
    """GOM tất cả kết quả vào 1 prompt, gọi AI đúng 1 lần (~vài nghìn token)."""
    key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not key:
        return '(bỏ qua --ai-summary: chưa có GEMINI_API_KEY)'
    from google import genai
    prompt = ("Bạn là chuyên gia quản trị rủi ro giao dịch. Dưới đây là kết quả backtest chiến lược breakout + nhồi lệnh "
              "(JSON, số liệu đã tính sẵn bằng code, đừng tính lại). Nhận xét ngắn gọn bằng tiếng Việt (tối đa 12 dòng): "
              "symbol nào nên NÊN/KHÔNG NÊN giao dịch theo chiến lược này, điểm yếu chính, và 2 gợi ý chỉnh tham số.\n"
              + json.dumps(results, ensure_ascii=False))
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model=os.getenv('BACKTEST_AI_MODEL', 'gemini-2.5-flash'), contents=prompt)
    return resp.text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--symbols', required=True)
    ap.add_argument('--interval', default='15m', choices=sorted(INTERVAL_MS))
    ap.add_argument('--vn-exchange', choices=('hose', 'hnx', 'upcom'), help='tắt --market vn và tự set biên độ: HOSE 7%%, HNX 10%%, UPCOM 15%%')
    ap.add_argument('--days', type=int, default=90)
    ap.add_argument('--csv', help='CSV nến (ts,open,high,low,close,volume); dùng cho 1 symbol, chạy offline — BẮT BUỘC cho --market vn (chưa có nguồn nến VN online)')
    ap.add_argument('--grid', action='store_true', help='thử lưới tham số (SL x lookback x volume)')
    ap.add_argument('--ai-summary', action='store_true', help='gọi AI đúng 1 lần cho toàn bộ kết quả')
    ap.add_argument('--json', help='ghi kết quả ra file JSON')
    d = Params()
    for f, v in asdict(d).items():
        ap.add_argument('--' + f.replace('_', '-'), type=type(v), default=v)
    a = ap.parse_args(argv)
    base = Params(**{f: getattr(a, f) for f in asdict(d)})
    if a.vn_exchange:
        base.market = 'vn'
        base.vn_price_band_pct = {'hose': 7.0, 'hnx': 10.0, 'upcom': 15.0}[a.vn_exchange]
    results = {}
    for sym in [s.strip().upper() for s in a.symbols.split(',') if s.strip()]:
        bars = load_csv(a.csv) if a.csv else fetch_klines(sym, a.interval, a.days)
        if len(bars) < base.lookback + 30:
            print(f'{sym}: không đủ dữ liệu ({len(bars)} nến)')
            continue
        if a.grid:
            rows = sorted(((stats(simulate(bars, q)), q) for q in grid_params(base)),
                          key=lambda x: x[0]['total_pnl_pct'], reverse=True)[:5]
            results[sym] = [dict(params=dict(sl_pct=q.sl_pct, lookback=q.lookback, min_vol_ratio=q.min_vol_ratio), **s) for s, q in rows]
            print(f'\n== {sym}: top 5 tham số (nhớ: tối ưu trên quá khứ dễ bị quá khớp) ==')
            for r in results[sym]:
                print(r)
        else:
            results[sym] = stats(simulate(bars, base))
            print(f'{sym}: {results[sym]}')
    if a.ai_summary and results:
        print('\n--- Nhận xét AI (1 lần gọi) ---')
        print(ai_summary(results))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == '__main__':
    main()
