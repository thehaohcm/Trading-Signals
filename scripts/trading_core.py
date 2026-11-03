"""
Logic thuần (không I/O, không DB, không mạng) của engine Breakout Radar.

Tách ra khỏi alert.py để kiểm thử được bằng unittest (scripts/tests). alert.py chỉ lo lấy dữ liệu
(DB / sàn / giá) rồi gọi các hàm ở đây để QUYẾT ĐỊNH.
"""
import math

# ---------------------------------------------------------------------------
# Dựng lệnh & SL trailing (giữ nguyên hành vi cũ của alert.py)
# ---------------------------------------------------------------------------


def size_order(asset_type, budget, price, vn_lot_size=100):
    """Tính (khối lượng, giá trị lệnh). Cổ phiếu VN làm tròn xuống theo lô chẵn."""
    if price <= 0 or budget <= 0:
        return 0.0, 0.0
    units = budget / price
    if asset_type == 'stock_vn':
        units = math.floor(units / vn_lot_size) * vn_lot_size
    return units, units * price


def compute_stop_loss(avg_entry, highest, layer, max_pyramids, sl_pct, spread_pct, sl_mode,
                      prev_sl=0.0, trailing_activation_pct=1.0):
    """
    Trả về (stop_loss, breakeven):
    - Trước khi trailing kích hoạt: SL = giá vốn TB * (1 - sl_pct).
    - Khi trailing kích hoạt: SL = max(hoà vốn có tính spread, đỉnh * (1 - sl_pct)).
    - BREAKEVEN_HOLD: từ tầng 2 trở đi luôn khoá tối thiểu ở hoà vốn.
    - Ratchet: SL chỉ được nâng lên, không bao giờ hạ xuống.
    """
    breakeven = avg_entry * (1.0 + spread_pct / 100.0)
    base_sl = avg_entry * (1.0 - sl_pct / 100.0)
    trailing_from_peak = highest * (1.0 - sl_pct / 100.0)
    trailing_active = (highest >= avg_entry * (1.0 + trailing_activation_pct / 100.0)) or \
                      (highest >= avg_entry * (1.0 + sl_pct / 100.0)) or \
                      (layer >= max_pyramids)
    if sl_mode == 'BREAKEVEN_HOLD' and layer >= 2:
        trailing_active = True
    sl = max(breakeven, trailing_from_peak) if trailing_active else base_sl
    if prev_sl and prev_sl > sl:
        sl = prev_sl
    return sl, breakeven


# ---------------------------------------------------------------------------
# Lọc breakout giả
# ---------------------------------------------------------------------------

def evaluate_breakout_confirmation(price, ath, now, since, rejected=False, *,
                                   margin_pct=0.0, hold_sec=0.0, max_chase_pct=0.0,
                                   vol_ratio=None, min_vol_ratio=0.0, max_wait_sec=900.0):
    """
    Quyết định có vào lệnh khi giá chạm/vượt đỉnh (ATH) hay không.

    Tham số trạng thái: `since` = thời điểm (epoch giây) giá bắt đầu nằm trên mốc kích hoạt trong "đợt" hiện tại
    (None nếu chưa), `rejected` = đợt này đã bị loại (không thử lại cho tới khi giá rơi xuống dưới mốc).

    Trả về (action, reason, new_since, new_rejected). action:
      'idle'    giá chưa tới mốc kích hoạt (caller nên reset trạng thái; nếu trước đó có đợt → breakout thất bại)
      'wait'    đang chờ xác nhận (giữ trên mốc đủ lâu / khối lượng)
      'enter'   đã xác nhận → vào lệnh
      'reject'  loại đợt breakout này (đuổi giá quá xa / thiếu khối lượng quá lâu)
    """
    trigger = ath * (1.0 + margin_pct / 100.0)
    if price < trigger:
        return 'idle', None, None, False
    if rejected:
        return 'idle', 'rejected', since, True   # vẫn trên mốc nhưng đợt này đã bị loại → im lặng chờ giá về dưới mốc
    since = since if since is not None else now

    if max_chase_pct > 0 and price > ath * (1.0 + max_chase_pct / 100.0):
        gap = (price / ath - 1.0) * 100.0
        return 'reject', f"giá đã chạy xa {gap:.2f}% so với mốc đỉnh (> {max_chase_pct:g}%) — không đuổi giá", since, True

    held = now - since
    if held < hold_sec:
        return 'wait', f"mới giữ trên mốc {held:.0f}s/{hold_sec:.0f}s", since, False

    if min_vol_ratio > 0 and vol_ratio is not None and vol_ratio < min_vol_ratio:
        if max_wait_sec and held > max_wait_sec:
            return 'reject', (f"khối lượng chỉ {vol_ratio:.2f}x trung bình (cần ≥ {min_vol_ratio:g}x) "
                              f"sau {held / 60:.0f} phút — nghi breakout giả"), since, True
        return 'wait', f"khối lượng {vol_ratio:.2f}x < {min_vol_ratio:g}x trung bình", since, False

    return 'enter', "đã xác nhận breakout", since, False


def volume_ratio(volumes, open_ms, interval_ms, now_ms, lookback=20, min_fraction=0.2):
    """
    Tỉ lệ khối lượng hiện tại so với trung bình `lookback` nến đã đóng trước đó.
    `volumes` = khối lượng các nến từ cũ → mới, PHẦN TỬ CUỐI là nến đang chạy (chưa đóng) mở lúc `open_ms`.
    Khối lượng nến đang chạy được quy đổi (chiếu) ra cả nến theo tỉ lệ thời gian đã trôi.
    Trả về max(nến vừa đóng, nến đang chạy đã chiếu) / trung bình; None nếu không đủ dữ liệu.
    """
    if not volumes or len(volumes) < 4:
        return None
    closed = [float(v) for v in volumes[:-1]]
    prior = closed[-(lookback + 1):-1] if len(closed) > lookback else closed[:-1]
    if not prior:
        return None
    avg = sum(prior) / len(prior)
    if avg <= 0:
        return None
    frac = min(1.0, max(min_fraction, (now_ms - open_ms) / float(interval_ms)))
    projected = float(volumes[-1]) / frac
    return max(closed[-1], projected) / avg


# ---------------------------------------------------------------------------
# Cổng rủi ro danh mục
# ---------------------------------------------------------------------------

def portfolio_gate(stats, limits, kind='open', is_real=False):
    """
    Cổng rủi ro toàn danh mục. Trả về (allowed, reason).

    stats:  open_total, open_real, sl_today_total, pnl_today, pnl_week  (pnl của nhóm tiền tệ của lệnh đang xét)
    limits: max_open, max_open_real, max_daily_sl_total, daily_loss_cap, weekly_loss_cap  (giá trị <= 0 = tắt)
    kind:   'open' = mở vị thế MỚI (kiểm tra tất cả); 'add' = nhồi lệnh vào vị thế sẵn có
            (chỉ chặn bởi giới hạn lỗ — không bị giới hạn số vị thế, vì không tạo vị thế mới).
    """
    daily_cap = float(limits.get('daily_loss_cap') or 0)
    weekly_cap = float(limits.get('weekly_loss_cap') or 0)
    pnl_today = float(stats.get('pnl_today') or 0)
    pnl_week = float(stats.get('pnl_week') or 0)
    if daily_cap > 0 and pnl_today <= -daily_cap:
        return False, f"đã lỗ {-pnl_today:,.2f} trong ngày, chạm trần lỗ ngày {daily_cap:,.2f}"
    if weekly_cap > 0 and pnl_week <= -weekly_cap:
        return False, f"đã lỗ {-pnl_week:,.2f} trong tuần, chạm trần lỗ tuần {weekly_cap:,.2f}"
    if kind == 'add':
        return True, None
    max_open = int(limits.get('max_open') or 0)
    if max_open > 0 and int(stats.get('open_total') or 0) >= max_open:
        return False, f"đang có {int(stats['open_total'])} vị thế mở (tối đa {max_open})"
    max_real = int(limits.get('max_open_real') or 0)
    if is_real and max_real > 0 and int(stats.get('open_real') or 0) >= max_real:
        return False, f"đang có {int(stats['open_real'])} vị thế THẬT mở (tối đa {max_real})"
    max_sl = int(limits.get('max_daily_sl_total') or 0)
    if max_sl > 0 and int(stats.get('sl_today_total') or 0) >= max_sl:
        return False, f"toàn danh mục đã cắt lỗ {int(stats['sl_today_total'])} lệnh hôm nay (tối đa {max_sl})"
    return True, None


# ---------------------------------------------------------------------------
# ATR & SL theo biến động
# ---------------------------------------------------------------------------

def atr_percent(highs, lows, closes, period=14):
    """ATR(period) theo % giá đóng cửa cuối. None nếu không đủ dữ liệu."""
    n = min(len(highs), len(lows), len(closes))
    if n < period + 1:
        return None
    trs = []
    for i in range(1, n):
        h, l, pc = float(highs[i]), float(lows[i]), float(closes[i - 1])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    window = trs[-period:]
    atr = sum(window) / len(window)
    last = float(closes[n - 1])
    return atr / last * 100.0 if last > 0 else None


def effective_sl_pct(base_sl_pct, atr_pct, mult=0.0, min_pct=None, max_pct=None):
    """
    SL% hiệu lực. mult <= 0 hoặc thiếu ATR → giữ nguyên base_sl_pct (tắt tính năng).
    Ngược lại SL% = atr_pct * mult, kẹp trong [min_pct, max_pct] (mặc định [base_sl_pct, 4 * base_sl_pct]):
    biến động càng lớn thì SL càng rộng nên không bị quét SL bởi nhiễu, nhưng không bao giờ chặt hơn mức người dùng đặt.
    """
    if not mult or mult <= 0 or atr_pct is None or atr_pct <= 0:
        return base_sl_pct
    lo = base_sl_pct if min_pct is None else min_pct
    hi = base_sl_pct * 4.0 if max_pct is None else max_pct
    return max(lo, min(hi, atr_pct * mult))


def position_size_for_risk(equity_risk_amount, entry_price, sl_pct):
    """Khối lượng sao cho lỗ tại SL đúng bằng equity_risk_amount (risk-based sizing). 0 nếu dữ liệu không hợp lệ."""
    if equity_risk_amount <= 0 or entry_price <= 0 or sl_pct <= 0:
        return 0.0
    return equity_risk_amount / (entry_price * sl_pct / 100.0)


# ---------------------------------------------------------------------------
# Chế độ thị trường BTC (lọc altcoin)
# ---------------------------------------------------------------------------

def ema(values, period):
    if not values:
        return None
    k = 2.0 / (period + 1.0)
    e = float(values[0])
    for v in values[1:]:
        e = float(v) * k + e * (1.0 - k)
    return e


def btc_regime_ok(closes_1h, ema_period=50, max_drop_pct_4h=3.0):
    """
    BTC có đang "risk-off"? Trả về (ok, reason).
    Không ok khi: giá BTC dưới EMA(ema_period) khung 1h VÀ EMA đang dốc xuống, hoặc BTC giảm > max_drop_pct_4h% trong 4 giờ qua.
    Thiếu dữ liệu → ok (fail-open).
    """
    if not closes_1h or len(closes_1h) < max(ema_period, 6):
        return True, None
    last = float(closes_1h[-1])
    drop4h = (last / float(closes_1h[-5]) - 1.0) * 100.0
    if max_drop_pct_4h > 0 and drop4h <= -max_drop_pct_4h:
        return False, f"BTC giảm {drop4h:.2f}% trong 4 giờ"
    e_now = ema(closes_1h, ema_period)
    e_prev = ema(closes_1h[:-3], ema_period)
    if e_now is not None and e_prev is not None and last < e_now and e_now < e_prev:
        return False, f"BTC dưới EMA{ema_period} (1h) và xu hướng đang đi xuống"
    return True, None


# ---------------------------------------------------------------------------
# AI: độ cũ của dữ liệu
# ---------------------------------------------------------------------------

def effective_ai_status(status, source, ai_updated_epoch, now, stale_hours=48.0):
    """
    Trạng thái AI/Admin dùng cho cổng giao dịch. Trả về (status_or_None, stale).
    - Admin đã đặt ('admin'): luôn tôn trọng.
    - Trạng thái AI cũ hơn stale_hours (hoặc chưa từng cập nhật mà đang là 'avoid'... ) → coi như không biết (None = cho phép).
    """
    if source == 'admin':
        return status, False
    if ai_updated_epoch is None:
        return status, False   # chưa có lần chạy AI nào → dữ liệu seed mặc định 'buy', giữ nguyên hành vi cũ
    if stale_hours and (now - ai_updated_epoch) > stale_hours * 3600.0:
        return None, True
    return status, False
