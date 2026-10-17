#!/usr/bin/env python3
"""
check_alert_status.py — Kiểm tra alert.py có đang chạy đúng không (CHỈ ĐỌC, không ghi gì vào DB).

Chạy cùng thư mục với alert.py (dùng chung .env, cùng logic):
    python3 scripts/check_alert_status.py            # báo cáo đầy đủ
    python3 scripts/check_alert_status.py --hours 6  # cảnh báo trong 6 giờ gần nhất (mặc định 24)
"""
import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alert as A  # dùng lại đúng cấu hình & hàm của alert.py (không chạy main)

OK, WARN, BAD, INFO = "✅", "⚠️ ", "❌", "  "


def q(sql, params=None):
    conn = A.get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def section(title):
    print(f"\n{'═' * 78}\n {title}\n{'═' * 78}")


def safe(fn):
    try:
        fn()
    except Exception as e:
        print(f"{BAD} Lỗi khi kiểm tra: {e}")


def age_str(ts):
    if ts is None:
        return "chưa có"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - ts).total_seconds())
    return f"{s}s trước" if s < 120 else (f"{s // 60} phút trước" if s < 7200 else f"{s // 3600} giờ trước")


def age_seconds(ts):
    if ts is None:
        return 10 ** 9
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).total_seconds()


# ─────────────────────────────────────────────────────────────────────────────
def check_heartbeat():
    section("1. alert.py CÓ ĐANG CHẠY KHÔNG? (heartbeat mỗi vòng quét ~15s + thời gian quét)")
    rows = q("SELECT updated_at FROM public.system_settings WHERE key = 'alert_script_last_heartbeat'")
    ts = rows[0][0] if rows else None
    sec = age_seconds(ts)
    if sec < 120:
        print(f"{OK} Heartbeat {age_str(ts)} → script ĐANG CHẠY")
    elif sec < 600:
        print(f"{WARN} Heartbeat {age_str(ts)} → vòng quét đang chậm (nhiều mã / API chậm) hoặc vừa dừng")
    else:
        print(f"{BAD} Heartbeat {age_str(ts)} → script KHÔNG chạy. Kiểm tra process / log của alert.py")


def check_toggles():
    section("2. CÔNG TẮC HỆ THỐNG (system_settings)")
    rows = dict(q("SELECT key, value FROM public.system_settings"))
    scans = ["scan_stock_vn", "scan_stock_us", "scan_crypto", "scan_futures", "scan_commodities", "scan_forex", "scan_yields"]
    print("Quét tín hiệu (mặc định BẬT nếu chưa có key):")
    for k in scans:
        v = str(rows.get(k, "true")).lower() == "true"
        print(f"  {'🟢' if v else '🔴'} {k}")
    mode = rows.get("trading_mode", "demo")
    live = str(rows.get("is_live_trade_enabled", "true")).lower() != "false"
    print(f"\nGiao dịch: trading_mode = {mode!r} {'(LỆNH THẬT với mã bật is_real_trading)' if mode == 'real' else '(chỉ DEMO)'}")
    print(f"  {'🟢' if live else '🔴'} is_live_trade_enabled (tắt = không mở vị thế / nhồi lệnh mới, chỉ còn cảnh báo & cắt lỗ)")
    for asset, key in sorted(set(A.TRADE_TOGGLE_KEYS.items()), key=lambda x: x[1]):
        if asset == "commodities":
            continue
        v = str(rows.get(key, "true")).lower() != "false"
        print(f"  {'🟢' if v else '🔴'} {key}")


def check_market_hours():
    section("3. GIỜ GIAO DỊCH LÚC NÀY (scanner chỉ quét khi thị trường mở)")
    vn, us = A.get_vn_time(), A.get_us_time()
    for name, opened, now in [
        ("Stock VN (09:00-11:30, 13:00-14:45)", A.is_vn_stock_market_open(vn), vn.strftime("%a %H:%M VN")),
        ("Stock US (09:30-16:00 ET)", A.is_us_stock_market_open(us), us.strftime("%a %H:%M ET")),
        ("Forex / Hàng hoá / Lợi suất (CN 17h → T6 17h ET)", A.is_fx_market_open(us), us.strftime("%a %H:%M ET")),
        ("Crypto / Futures", True, "24/7"),
    ]:
        print(f"  {'🟢 MỞ ' if opened else '⚪ ĐÓNG'}  {name:<48} [{now}]")
    if A._holidays_lib is None and not (A._VN_EXTRA_HOLIDAYS or A._US_EXTRA_HOLIDAYS):
        print(f"{WARN} Chưa lọc ngày lễ (chưa cài 'holidays' và chưa khai báo VN/US_MARKET_HOLIDAYS)")


def check_watchlists():
    section("4. NGUỒN MÃ ĐỂ QUÉT VƯỢT ĐỈNH")
    vn = A.get_watchlist_symbols()
    print(f"  Stock VN đủ 3 tín hiệu (EMA9>EMA21, gần đỉnh 52W, top tăng trưởng): {len(vn)} mã {list(vn)[:10]}")
    print(f"  Stock US (world_symbols_watchlist):  {len(A.get_us_watchlist_symbols())} mã")
    print(f"  Crypto spot (cryptos_watchlist):      {len(A.get_watchlist_cryptos())} mã")
    print(f"  Futures (futures_watchlist):          {len(A.get_watchlist_futures())} mã")
    print(f"  Forex:                                {len(A.get_watchlist_forex())} cặp")
    print(f"  Hàng hoá cố định:                     {', '.join(A.COMMODITIES_SYMBOLS.values())}")
    print(f"{INFO}Quy tắc báo: giá ≥ 99% đỉnh → báo 'tiệm cận'; giá > đỉnh → báo 'vượt đỉnh';")
    print(f"{INFO}chỉ báo lại khi lập đỉnh mới cao hơn lần báo trước ≥ +0.5% (forex +0.2%, hàng hoá +0.3%);")
    print(f"{INFO}giá lùi < 97% đỉnh thì lần tiệm cận sau được báo lại.")


def check_breakout_watchlist():
    section("5. BREAKOUT RADAR — MÃ ĐANG THEO DÕI & VIỆC SẮP XẢY RA")
    rows = q(f"""
        SELECT w.id, w.symbol, w.asset_type, w.ath_price, w.current_price, w.updated_at, w.is_active,
               w.initial_budget, w.sl_pct, w.step_pct, w.is_real_trading,
               p.id, p.current_layer, p.avg_entry_price, p.stop_loss_price, p.next_pyramid_price,
               p.last_buy_price, p.unrealized_roi_pct, w.max_pyramids
        FROM public.breakout_watchlist w
        LEFT JOIN public.paper_positions p ON p.watchlist_id = w.id AND p.status = 'OPEN'
        WHERE w.is_active = true
        ORDER BY (p.id IS NULL), w.asset_type, w.symbol
    """)
    if not rows:
        print(f"{INFO}Chưa có mã nào trong breakout_watchlist (scanner tự thêm khi giá tiệm cận đỉnh)")
        return
    print(f"{'MÃ':<12}{'LOẠI':<10}{'GIÁ':>14}{'ĐỈNH/ATH':>14}{'CÁCH':>8}  CẬP NHẬT        DỰ KIẾN")
    for (w_id, sym, at, ath, cur, upd, _act, budget, sl_pct, step_pct, is_real,
         pos_id, layer, avg, sl, nxt, last_buy, roi, max_pyr) in rows:
        ath, cur = float(ath or 0), float(cur or 0)
        dist = (ath - cur) / ath * 100 if ath and cur else None
        stale = age_seconds(upd) > 600 and A._is_market_open_for(at)
        if pos_id:
            sl, avg, nxt, last_buy = float(sl), float(avg), float(nxt), float(last_buy)
            target = max(last_buy * (1 + float(step_pct) / 100), nxt)
            sl_dist = (cur - sl) / cur * 100 if cur else 0
            if cur <= sl:
                plan = f"{BAD} DƯỚI SL {sl:,.4g} → lẽ ra đã CẮT LỖ (kiểm tra engine)"
            elif layer < max_pyr:
                plan = f"Vị thế tầng {layer}, ROI {float(roi):+.2f}% | SL {sl:,.4g} (cách {sl_dist:.2f}%) | nhồi tầng {layer + 1} ở {target:,.4g}"
            else:
                plan = f"Vị thế tầng {layer}/{max_pyr} (đủ tầng), ROI {float(roi):+.2f}% | SL {sl:,.4g} (cách {sl_dist:.2f}%)"
        elif not ath:
            plan = "Chưa có ATH"
        elif cur >= ath:
            plan = f"{WARN} GIÁ ≥ ATH nhưng chưa có vị thế → xem: công tắc giao dịch / circuit breaker / vốn quá nhỏ / lỗi lệnh thật"
        elif cur >= ath * 0.99:
            plan = "Vùng CHUẨN BỊ (≤1%) → đã/ sẽ gửi cảnh báo pre-trade; vào lệnh khi chạm ATH"
        else:
            plan = f"Chờ — vào lệnh khi giá ≥ {ath:,.4g}"
        tag = " [REAL]" if is_real else ""
        print(f"{sym:<12}{at:<10}{cur:>14,.4f}{ath:>14,.4f}{(f'{dist:.2f}%' if dist is not None else '-'):>8}  "
              f"{age_str(upd):<15}{'⚠️ GIÁ CŨ! ' if stale else ''}{plan}{tag}")
    print(f"\n{INFO}'GIÁ CŨ' = current_price không được cập nhật >10 phút dù thị trường đang mở → engine không lấy được giá mã đó.")


def check_circuit_breaker():
    section("6. RISK GUARD — số vị thế bị cắt lỗ HÔM NAY (≥3 trong cùng nhóm → ngừng mở vị thế mới)")
    rows = q("""
        SELECT asset_type, COUNT(*) FROM public.paper_positions
        WHERE status = 'CLOSED_SL'
          AND DATE(closed_at AT TIME ZONE 'Asia/Ho_Chi_Minh') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Ho_Chi_Minh')
        GROUP BY asset_type
    """)
    if not rows:
        print(f"{OK} Hôm nay chưa có vị thế nào bị cắt lỗ")
    for at, n in rows:
        print(f"  {BAD if n >= 3 else WARN} {at}: {n} lần cắt lỗ {'→ ĐANG TẠM DỪNG mở vị thế mới' if n >= 3 else ''}")


def check_recent_alerts(hours):
    section(f"7. CẢNH BÁO ĐÃ GHI ({hours} giờ gần nhất) & CÓ ĐƯỢC GỬI LÊN NTFY KHÔNG")
    rows = q("""
        SELECT created_at, asset_type, symbol, message FROM public.triggered_alerts
        WHERE created_at > NOW() - make_interval(hours => %s)
        ORDER BY created_at DESC LIMIT 30
    """, (hours,))
    print(f"{INFO}Lưu ý: bảng chỉ giữ 1 cảnh báo mới nhất mỗi mã, tối đa 200 dòng, xoá sau 5 ngày.")
    if not rows:
        print(f"{WARN} Không có cảnh báo nào — bình thường nếu thị trường đóng / chưa mã nào tiệm cận đỉnh")
        return
    ntfy_on = os.getenv("NTFY_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    for ts, at, sym, msg in rows:
        sent = ntfy_on and A.is_ntfy_allowed_asset(at, sym)
        crit = any(k in (msg or "").upper() for k in ("LỖI LỆNH THẬT", "CẦN XỬ LÝ THỦ CÔNG"))
        flag = "📲 ntfy" if (sent or crit) else "🚫 không ntfy"
        print(f"  {age_str(ts):<14} {flag:<13} {at:<12} {sym:<10} {(msg or '')[:90]}")
    print(f"\n{INFO}🚫 không ntfy = loại tài sản bị lọc (cổ phiếu Mỹ, lợi suất, hàng hoá ngoài vàng/bạc/dầu)"
          f"{'' if ntfy_on else ' — VÀ NTFY_NOTIFICATIONS_ENABLED đang tắt'}")


def check_recent_orders():
    section("8. LỆNH GẦN NHẤT (paper_orders)")
    rows = q("""
        SELECT o.created_at, o.symbol, o.order_type, o.layer, o.price, o.amount_usd, o.reason, p.is_real
        FROM public.paper_orders o LEFT JOIN public.paper_positions p ON p.id = o.position_id
        ORDER BY o.created_at DESC LIMIT 10
    """)
    if not rows:
        print(f"{INFO}Chưa có lệnh nào")
    for ts, sym, typ, layer, price, amt, reason, is_real in rows:
        print(f"  {age_str(ts):<14} {'REAL' if is_real else 'DEMO'} {typ:<12} {sym:<10} L{layer} @ {float(price):,.4f} "
              f"vốn {float(amt):,.0f} | {(reason or '')[:60]}")


def check_ntfy():
    section("9. SERVER NTFY")
    if os.getenv("NTFY_NOTIFICATIONS_ENABLED", "true").lower() != "true":
        print(f"{WARN} NTFY_NOTIFICATIONS_ENABLED=false → alert.py KHÔNG gửi ntfy")
    url = os.getenv("NTFY_SERVER_URL", "http://localhost:8088").rstrip("/")
    topic = os.getenv("NTFY_TOPIC", "trading_signals_alerts")
    try:
        r = A.requests.get(f"{url}/v1/health", timeout=5)
        print(f"{OK if r.ok else BAD} {url}/v1/health → {r.status_code} {r.text.strip()[:60]}")
    except Exception as e:
        print(f"{BAD} Không kết nối được {url}: {e}")
        return
    try:
        r = A.requests.get(f"{url}/{topic}/json", params={"poll": "1", "since": "24h"}, timeout=10)
        lines = [l for l in r.text.splitlines() if '"event":"message"' in l]
        print(f"{OK if lines else WARN} Topic '{topic}': {len(lines)} tin trong 24h qua trên server ntfy")
    except Exception as e:
        print(f"{WARN} Không đọc được lịch sử topic: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    args = ap.parse_args()
    print(f"Báo cáo lúc {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} — DB {os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'trading')}")
    for fn in (check_heartbeat, check_toggles, check_market_hours, check_watchlists, check_breakout_watchlist,
               check_circuit_breaker, lambda: check_recent_alerts(args.hours), check_recent_orders, check_ntfy):
        safe(fn)
    print()


if __name__ == "__main__":
    main()
