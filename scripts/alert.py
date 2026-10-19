#!/usr/bin/env python3
# Trading Signals Alert & Pyramiding Trading Engine
import time
import os
import sys
import math
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import psycopg2
import psycopg2.pool
try:
    from vnstock import Quote
except ImportError:
    Quote = None

try:
    import holidays as _holidays_lib  # optional: pip install holidays
except ImportError:
    _holidays_lib = None


try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from economic_calendar import init_economic_calendar_table, monitor_economic_calendar_step
except ImportError:
    def init_economic_calendar_table(): pass
    def monitor_economic_calendar_step(): pass


# Load environment variables
env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_file_path):
    load_dotenv(env_file_path)
else:
    load_dotenv()

# Setup cross-platform Beep alert sound with audio profiles
try:
    import winsound
    def play_alert(symbol, asset_type, alert_type="default"):
        """
        Play differentiated alert sounds based on alert_type:
        - 'pre_trade': 2 quick gentle beeps (650Hz, 120ms each)
        - 'executed': 1 prolonged high beep (1000Hz, 350ms)
        - 'stop_loss': 2 low-pitched alert beeps (400Hz, 250ms each)
        - 'default': 1 standard beep (800Hz, 250ms)
        """
        try:
            if alert_type == 'pre_trade':
                winsound.Beep(650, 120)
                time.sleep(0.08)
                winsound.Beep(650, 120)
                print(f">>> [PRE-TRADE WARNING] SẮP VÀO LỆNH CHO {symbol} ({asset_type.upper()})! <<<")
            elif alert_type == 'executed':
                winsound.Beep(1000, 350)
                print(f">>> [ORDER EXECUTED] ĐÃ VÀO LỆNH CHO {symbol} ({asset_type.upper()})! <<<")
            elif alert_type == 'stop_loss':
                winsound.Beep(450, 200)
                time.sleep(0.08)
                winsound.Beep(350, 300)
                print(f">>> [STOP LOSS TRIGGERED] CẮT LỖ CHO {symbol} ({asset_type.upper()})! <<<")
            else:
                winsound.Beep(800, 250)
                print(f">>> CẢNH BÁO GIÁ CHO {symbol} ({asset_type.upper()})! <<<")
        except Exception:
            pass
except ImportError:
    # Fallback for macOS/Linux using terminal bell
    def play_alert(symbol, asset_type, alert_type="default"):
        print("\a", end="", flush=True)  # Terminal bell
        if alert_type == 'pre_trade':
            print(f">>> [PRE-TRADE WARNING] SẮP VÀO LỆNH CHO {symbol} ({asset_type.upper()})! <<<")
        elif alert_type == 'executed':
            print(f">>> [ORDER EXECUTED] ĐÃ VÀO LỆNH CHO {symbol} ({asset_type.upper()})! <<<")
        elif alert_type == 'stop_loss':
            print(f">>> [STOP LOSS TRIGGERED] CẮT LỖ CHO {symbol} ({asset_type.upper()})! <<<")
        else:
            print(f">>> CẢNH BÁO GIÁ CHO {symbol} ({asset_type.upper()})! <<<")


# =====================================================================
# Cấu hình chiến lược (đọc từ .env, mặc định giữ nguyên hành vi cũ)
# =====================================================================
def _env_float(key, default):
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return float(default)

# Dung sai cho cảnh báo giá tuỳ chỉnh (%). 1.0 = báo khi giá cách mức đặt <= 1% (hành vi cũ).
PRICE_ALERT_TOLERANCE_PCT = _env_float('PRICE_ALERT_TOLERANCE_PCT', 1.0)
# Thời gian chờ giữa 2 lần báo cùng một cảnh báo giá (giờ)
PRICE_ALERT_COOLDOWN_HOURS = _env_float('PRICE_ALERT_COOLDOWN_HOURS', 1.0)
# true = cảnh báo giá chỉ báo 1 lần rồi tự tắt (is_active=false) khi giá THỰC SỰ chạm mức
PRICE_ALERT_ONE_SHOT = os.getenv('PRICE_ALERT_ONE_SHOT', 'false').lower() == 'true'

# Tham số mặc định khi scanner tự thêm mã vào breakout_watchlist
BREAKOUT_DEFAULT_STEP_PCT = _env_float('BREAKOUT_DEFAULT_STEP_PCT', 1.0)
BREAKOUT_DEFAULT_SL_PCT = _env_float('BREAKOUT_DEFAULT_SL_PCT', 2.0)
BREAKOUT_DEFAULT_PYRAMID_RATIO = _env_float('BREAKOUT_DEFAULT_PYRAMID_RATIO', 0.67)
BREAKOUT_DEFAULT_MAX_PYRAMIDS = int(_env_float('BREAKOUT_DEFAULT_MAX_PYRAMIDS', 3))
BREAKOUT_DEFAULT_BUDGET_USD = _env_float('BREAKOUT_DEFAULT_BUDGET_USD', 1000.0)
BREAKOUT_DEFAULT_BUDGET_VND = _env_float('BREAKOUT_DEFAULT_BUDGET_VND', 10_000_000.0)
# Lợi nhuận đỉnh (so với giá vốn TB) cần đạt để bật Trailing Stop (trước đây cố định 5%)
TRAILING_ACTIVATION_PCT = _env_float('TRAILING_ACTIVATION_PCT', 5.0)
# Nhắc lại cảnh báo "CHUẨN BỊ VÀO LỆNH / NHỒI LỆNH" mỗi N phút khi giá vẫn ở vùng cách mốc ≤ 2% mà chưa vượt.
# 0 = chỉ báo 1 lần. VD 0.25 = nhắc mỗi 15 giây (mỗi vòng quét).
PRE_TRADE_REMINDER_MINUTES = _env_float('PRE_TRADE_REMINDER_MINUTES', 5.0)
# Số lần NHẮC LẠI tối đa cho cảnh báo "CHUẨN BỊ NHỒI LỆNH" (không tính lần báo đầu). Sau đó im lặng
# đến khi giá lùi xa mốc > 2% (reset) hoặc đã nhồi xong tầng đó. 0 = chỉ báo 1 lần; âm = không giới hạn.
PRE_PYRAMID_MAX_REMINDERS = int(_env_float('PRE_PYRAMID_MAX_REMINDERS', 3))
# Tương tự cho cảnh báo "CHUẨN BỊ VÀO LỆNH" (tầng 1, giá tiệm cận ATH).
PRE_TRADE_MAX_REMINDERS = int(_env_float('PRE_TRADE_MAX_REMINDERS', 3))
# Vùng chuẩn bị: báo lần đầu khi cách mốc ≤ 1%; nhắc lại khi vẫn trong ≤ 2%; lùi xa hơn 2% thì reset.
PRE_TRADE_FIRST_PCT = 1.0
PRE_TRADE_ZONE_PCT = 2.0
# Sự kiện giao dịch của Breakout Radar luôn gửi ntfy (loa Pi / app ntfy) bất kể loại tài sản,
# vì mã trong Radar là do người dùng chủ động theo dõi. Đặt false để áp dụng bộ lọc tài sản như tin quét.
NTFY_RADAR_ALL_ASSETS = os.getenv('NTFY_RADAR_ALL_ASSETS', 'true').lower() == 'true'
RADAR_TRADE_EVENTS = ('pre_trade', 'pre_pyramid', 'initial_buy', 'pyramid_buy', 'stop_loss')
# Trạng thái "đã báo" (chống báo trùng) tự hết hạn sau N ngày — giống thời hạn cảnh báo trên banner (5 ngày).
# Chỉ ảnh hưởng việc GỬI THÔNG BÁO, không ảnh hưởng việc vào lệnh (vào lệnh chỉ dựa trên giá so với ATH).
ALERT_DEDUPE_TTL_DAYS = _env_float('ALERT_DEDUPE_TTL_DAYS', 5.0)
# Thời gian chờ trước khi thử lại lệnh thật sau khi sàn trả lỗi (giây)
REAL_ORDER_RETRY_COOLDOWN_SEC = _env_float('REAL_ORDER_RETRY_COOLDOWN_SEC', 600)
# Lô chẵn cổ phiếu VN
VN_STOCK_LOT_SIZE = int(_env_float('VN_STOCK_LOT_SIZE', 100))

# Spread / chi phí khứ hồi mặc định theo loại tài sản (%) — đồng bộ với migration 022
def default_spread_pct(asset_type, symbol=""):
    sym = (symbol or "").upper()
    if asset_type in ('commodity', 'commodities') or sym in ('XAUUSD', 'GOLD', 'XAGUSD', 'SILVER'):
        return 1.45
    return {
        'crypto': 0.10,
        'futures': 0.08,
        'stock_vn': 0.25,
        'stock_us': 0.08,
        'forex': 0.05,
    }.get(asset_type, 0.10)


# =====================================================================
# Database (connection pool để không mở/đóng kết nối liên tục mỗi mã)
# =====================================================================
_db_pool = None
_db_pool_lock = threading.Lock()

def _db_params():
    return dict(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'trading'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

class _PooledConnection:
    """Wrapper: conn.close() trả kết nối về pool thay vì đóng hẳn."""
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
        self._returned = False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        if self._returned:
            return
        self._returned = True
        broken = bool(self._conn.closed)
        if not broken:
            try:
                # Huỷ transaction dở dang (nếu có lỗi giữa chừng) trước khi trả về pool
                self._conn.rollback()
            except Exception:
                broken = True
        try:
            self._pool.putconn(self._conn, close=broken)
        except Exception:
            pass

def get_db_connection():
    """Lấy kết nối DB từ pool (fallback: kết nối trực tiếp)."""
    global _db_pool
    if _db_pool is None:
        with _db_pool_lock:
            if _db_pool is None:
                try:
                    _db_pool = psycopg2.pool.ThreadedConnectionPool(1, 10, **_db_params())
                except Exception as e:
                    print(f"[DB] Không tạo được connection pool, dùng kết nối trực tiếp: {e}")
                    return psycopg2.connect(**_db_params())
    try:
        conn = _db_pool.getconn()
        if conn.closed:
            _db_pool.putconn(conn, close=True)
            conn = _db_pool.getconn()
        return _PooledConnection(_db_pool, conn)
    except Exception as e:
        print(f"[DB] Lỗi lấy kết nối từ pool, dùng kết nối trực tiếp: {e}")
        return psycopg2.connect(**_db_params())

def get_scan_toggles():
    """Fetch scan toggles from public.system_settings, defaulting to True if not set"""
    toggles = {
        'scan_stock_vn': True,
        'scan_stock_us': True,
        'scan_crypto': True,
        'scan_futures': True,
        'scan_commodities': True,
        'scan_forex': True,
        'scan_yields': True
    }
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM public.system_settings;")
        rows = cur.fetchall()
        for row in rows:
            key, val = row[0], row[1]
            if key in toggles:
                toggles[key] = (str(val).lower() == 'true')
        cur.close()
    except Exception as e:
        # Default to True on failure (nhưng phải log để biết DB đang lỗi)
        print(f"[CẢNH BÁO] Không đọc được scan toggles từ DB, dùng mặc định (bật tất cả): {e}")
    finally:
        if conn:
            conn.close()
    return toggles

def update_heartbeat():
    """Update heartbeat timestamp in database to signal the script is alive"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.system_settings (key, value)
            VALUES ('alert_script_last_heartbeat', 'true')
            ON CONFLICT (key) DO UPDATE SET value = 'true', updated_at = CURRENT_TIMESTAMP;
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[CẢNH BÁO] Không cập nhật được heartbeat: {e}")
    finally:
        if conn:
            conn.close()

def get_vn_time():
    """Get current time in Vietnam timezone (Asia/Ho_Chi_Minh) with UTC+7 fallback"""
    try:
        return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=7)))

def get_us_time():
    """Get current time in US Eastern timezone (America/New_York) with fallback"""
    try:
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now_utc = datetime.now(timezone.utc)
        month = now_utc.month
        offset_hours = -4 if 3 <= month <= 11 else -5
        return now_utc.astimezone(timezone(timedelta(hours=offset_hours)))


# =====================================================================
# Giờ giao dịch & ngày lễ
# =====================================================================
def _parse_holiday_env(key):
    """Đọc danh sách ngày nghỉ bổ sung từ .env, dạng: 2026-01-01,2026-04-30"""
    result = set()
    for part in os.getenv(key, '').split(','):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(date.fromisoformat(part))
        except ValueError:
            print(f"[CẢNH BÁO] Ngày nghỉ không hợp lệ trong {key}: {part}")
    return result

_VN_EXTRA_HOLIDAYS = _parse_holiday_env('VN_MARKET_HOLIDAYS')
_US_EXTRA_HOLIDAYS = _parse_holiday_env('US_MARKET_HOLIDAYS')
_holiday_cache = {}

def _is_holiday(market, d):
    if market == 'vn' and d in _VN_EXTRA_HOLIDAYS:
        return True
    if market == 'us' and d in _US_EXTRA_HOLIDAYS:
        return True
    if _holidays_lib is None:
        return False
    key = (market, d.year)
    if key not in _holiday_cache:
        try:
            if market == 'vn':
                _holiday_cache[key] = _holidays_lib.country_holidays('VN', years=d.year)
            else:
                _holiday_cache[key] = _holidays_lib.financial_holidays('NYSE', years=d.year)
        except Exception:
            _holiday_cache[key] = {}
    return d in _holiday_cache[key]

def is_vn_stock_market_open(vn_now=None):
    """HOSE/HNX: T2-T6, 09:00-11:30 và 13:00-14:45 (nghỉ trưa), trừ ngày lễ."""
    vn_now = vn_now or get_vn_time()
    if vn_now.weekday() >= 5 or _is_holiday('vn', vn_now.date()):
        return False
    hm = vn_now.hour * 60 + vn_now.minute
    return (9 * 60 <= hm < 11 * 60 + 30) or (13 * 60 <= hm <= 14 * 60 + 45)

def is_us_stock_market_open(us_now=None):
    """NYSE/NASDAQ: T2-T6, 09:30-16:00 ET, trừ ngày lễ."""
    us_now = us_now or get_us_time()
    if us_now.weekday() >= 5 or _is_holiday('us', us_now.date()):
        return False
    hm = us_now.hour * 60 + us_now.minute
    return 9 * 60 + 30 <= hm < 16 * 60

def is_fx_market_open(us_now=None):
    """Forex / hàng hoá / lợi suất: Chủ nhật 17:00 ET → Thứ 6 17:00 ET."""
    us_now = us_now or get_us_time()
    wd = us_now.weekday()  # Mon=0 ... Sun=6
    if wd == 5:
        return False
    if wd == 6:
        return us_now.hour >= 17
    if wd == 4:
        return us_now.hour < 17
    return True

def get_us_watchlist_symbols():
    """Get all US stock symbols currently in the world_symbols_watchlist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        SELECT symbol
        FROM public.world_symbols_watchlist
        WHERE country = 'Mỹ';
        """
        cur.execute(query)
        rows = cur.fetchall()
        # Map each US symbol to a dummy 0.0 highest_price (no breakout comparison is in schema)
        symbols = {row[0]: 0.0 for row in rows}
        cur.close()
        return symbols
    except Exception as e:
        print(f"Lỗi query world_symbols_watchlist: {e}")
        return {}
    finally:
        if conn:
            conn.close()

class PersistentCache:
    """
    Bộ nhớ chống báo trùng (dict) được LƯU VÀO DB (bảng alert_dedupe_state) để khởi động lại
    alert.py không báo lại các mã đang ở gần đỉnh. DB lỗi thì vẫn hoạt động trong bộ nhớ như cũ.
    Mỗi khoá tự hết hạn sau ALERT_DEDUPE_TTL_DAYS ngày kể từ lần cập nhật cuối (kể cả khi script chạy liên tục).
    Khoá là chuỗi (VD 'BTCUSDT') hoặc tuple (VD (12, 'layer_1')).
    """

    def __init__(self, namespace):
        self.ns = namespace
        self._d = {}
        self._ts = {}
        self._loaded = False

    @staticmethod
    def _ttl_seconds():
        return max(ALERT_DEDUPE_TTL_DAYS, 0.0) * 86400

    @staticmethod
    def _enc(key):
        if isinstance(key, tuple):
            return "t:" + "|".join(str(k) for k in key)
        return "s:" + str(key)

    @staticmethod
    def _dec(raw):
        if raw.startswith("t:"):
            return tuple(int(p) if p.lstrip("-").isdigit() else p for p in raw[2:].split("|"))
        return raw[2:] if raw.startswith("s:") else raw

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT key, value, EXTRACT(EPOCH FROM updated_at) FROM public.alert_dedupe_state
                WHERE namespace = %s AND updated_at > NOW() - make_interval(secs => %s)
            """, (self.ns, self._ttl_seconds()))
            for k, v, ts in cur.fetchall():
                key = self._dec(k)
                self._d[key] = float(v)
                self._ts[key] = float(ts)
            cur.close()
        except Exception as e:
            print(f"[CẢNH BÁO] Không đọc được trạng thái chống báo trùng '{self.ns}' từ DB: {e}")
        finally:
            if conn:
                conn.close()

    def _write(self, sql, params):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"[CẢNH BÁO] Không lưu được trạng thái chống báo trùng '{self.ns}': {e}")
        finally:
            if conn:
                conn.close()

    def _alive(self, key):
        """Nạp dữ liệu nếu cần và bỏ khoá đã quá hạn. Trả về True nếu khoá còn hiệu lực."""
        self._ensure_loaded()
        if key not in self._d:
            return False
        if time.time() - self._ts.get(key, 0) > self._ttl_seconds():
            self.pop(key)
            return False
        return True

    def __contains__(self, key):
        return self._alive(key)

    def __getitem__(self, key):
        if not self._alive(key):
            raise KeyError(key)
        return self._d[key]

    def get(self, key, default=None):
        return self._d[key] if self._alive(key) else default

    def __setitem__(self, key, value):
        self._ensure_loaded()
        self._d[key] = value
        self._ts[key] = time.time()
        self._write("""
            INSERT INTO public.alert_dedupe_state (namespace, key, value, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (namespace, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """, (self.ns, self._enc(key), float(value)))

    def pop(self, key, default=None):
        self._ensure_loaded()
        if key not in self._d:
            return default
        val = self._d.pop(key)
        self._ts.pop(key, None)
        self._write("DELETE FROM public.alert_dedupe_state WHERE namespace = %s AND key = %s",
                    (self.ns, self._enc(key)))
        return val

    def __iter__(self):
        self._ensure_loaded()
        return iter([k for k in list(self._d.keys()) if self._alive(k)])

    def __len__(self):
        return len(list(iter(self)))


def scanner_should_notify(radar_result, is_break):
    """
    Gộp thông báo: bộ quét đã phát hiện tiệm cận/vượt đỉnh và giao mã cho Breakout Radar.
    Bộ quét CHỈ tự gửi tin khi Radar không báo gì, để mỗi sự kiện chỉ có 1 thông báo:
    - Radar vừa gửi tin (chuẩn bị vào lệnh / đã vào lệnh / nhồi / cắt lỗ / lỗi lệnh) → bỏ tin bộ quét
    - Mã đang có vị thế mở → Radar đã quản lý (nhồi lệnh, cắt lỗ) → bỏ tin bộ quét
    - Tin "tiệm cận" khi Radar đã báo "chuẩn bị vào lệnh" cho lần tiệm cận này → bỏ
    radar_result = None khi mã không được Radar theo dõi (đã tắt / loại tài sản không giao dịch).
    """
    if not radar_result:
        return True
    if radar_result.get("events") or radar_result.get("has_position"):
        return False
    if not is_break and radar_result.get("pretrade_active"):
        return False
    return True


def should_alert_breakout(cache, key, current_price, reference_high, step_mult=1.005,
                          step_abs=None, near_pct=0.99, reset_pct=0.97):
    """
    Quyết định có báo breakout/tiệm cận đỉnh hay không, chống báo trùng:
    - Báo lần đầu khi giá >= near_pct * đỉnh.
    - Sau đó chỉ báo lại khi giá lập đỉnh mới cao hơn lần báo trước (step_mult hoặc step_abs).
    - Nếu giá lùi xa (< reset_pct * đỉnh) thì xoá cache để lần tiệm cận sau được báo lại.
    """
    if not reference_high or reference_high <= 0 or current_price is None:
        return False
    if current_price < reference_high * near_pct:
        if current_price < reference_high * reset_pct:
            cache.pop(key, None)
        return False
    last = cache.get(key, 0.0)
    if last <= 0:
        should = True
    elif step_abs is not None:
        should = current_price >= last + step_abs
    else:
        should = current_price >= last * step_mult
    if should:
        cache[key] = current_price
    return should

def monitor_us_stocks_step(us_symbols, last_alerted_prices):
    """Performs one scan cycle on the list of US stock symbols using Yahoo Finance"""
    if not us_symbols:
        return

    print(f"[US STOCK] Đang quét {list(us_symbols.keys())}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for symbol in us_symbols:
        try:
            ticker = symbol.split(':')[-1]
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            results = data.get("chart", {}).get("result", [])
            if not results:
                continue

            meta = results[0].get("meta", {})
            current_price = meta.get("regularMarketPrice")
            fifty_two_high = meta.get("fiftyTwoWeekHigh")

            if current_price is None or fifty_two_high is None or fifty_two_high <= 0:
                continue

            # --- Check custom price alerts FIRST ---
            check_custom_stock_alerts(symbol, current_price, market='us')

            # Check if US stock price is breaking/approaching the 52-week high (within 1%)
            if should_alert_breakout(last_alerted_prices, symbol, current_price, fifty_two_high, step_mult=1.005):
                clean_sym = symbol.split(":")[-1] if ":" in symbol else symbol
                is_break = current_price > fifty_two_high
                action = "vượt đỉnh" if is_break else "tiệm cận đỉnh"
                message = f"Cảnh báo Stock US: Cổ phiếu {clean_sym} đã {action} 52 tuần tại ${current_price:,.2f} (Đỉnh 52 tuần: ${fifty_two_high:,.2f})."
                print(f"[US Stock Breakout] {clean_sym} tại giá ${current_price:,.2f} >= 99% Đỉnh 52 tuần ${fifty_two_high:,.2f}")
                radar = auto_trigger_breakout_paper_trade(clean_sym, "stock_us", current_price, fifty_two_high)
                if scanner_should_notify(radar, is_break):
                    play_alert(clean_sym, "stock_us")
                    insert_triggered_alert("stock_us", clean_sym, current_price, message,
                                           event_type='breakout' if is_break else 'approach')
                else:
                    print(f"   ↳ {clean_sym}: Breakout Radar đã thông báo — bỏ tin trùng")

            time.sleep(0.3)  # Avoid rate limiting
        except Exception as e:
            print(f"Lỗi quét US stock {symbol}: {e}")


def get_watchlist_symbols():
    """Get stock symbols meeting all 3 signals (EMA9, 52W High, Top Growth)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        SELECT symbol, MAX(highest_price)
        FROM public.symbols_watchlist
        WHERE signal_type IN ('ema9_above_ema21', 'near_52w_ath', 'top_growth_20d')
        GROUP BY symbol
        HAVING COUNT(DISTINCT signal_type) = 3;
        """
        cur.execute(query)
        rows = cur.fetchall()
        symbols = {row[0]: float(row[1]) if row[1] is not None else 0.0 for row in rows}
        cur.close()
        return symbols
    except Exception as e:
        print(f"Lỗi query symbols_watchlist: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_watchlist_cryptos():
    """Get all cryptos currently in the cryptos_watchlist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        SELECT crypto, MAX(highest_price)
        FROM public.cryptos_watchlist
        GROUP BY crypto;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cryptos = {row[0]: float(row[1]) if row[1] is not None else 0.0 for row in rows}
        cur.close()
        return cryptos
    except Exception as e:
        print(f"Lỗi query cryptos_watchlist: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_watchlist_futures():
    """Get all futures contracts currently in the futures_watchlist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        SELECT symbol, MAX(highest_price)
        FROM public.futures_watchlist
        GROUP BY symbol;
        """
        cur.execute(query)
        rows = cur.fetchall()
        futures = {row[0]: float(row[1]) if row[1] is not None else 0.0 for row in rows}
        cur.close()
        return futures
    except Exception as e:
        print(f"Lỗi query futures_watchlist: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_watchlist_forex():
    """Get all forex pairs currently in the forex_watchlist or fallback to defaults including USDVND"""
    default_forex = {
        'EURUSD': 0.0,
        'USDJPY': 0.0,
        'GBPUSD': 0.0,
        'USDCHF': 0.0,
        'AUDUSD': 0.0,
        'USDCAD': 0.0,
        'USDVND': 0.0
    }
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        SELECT pair
        FROM public.forex_watchlist;
        """
        cur.execute(query)
        rows = cur.fetchall()
        if rows:
            forex = {row[0]: 0.0 for row in rows}
            if 'USDVND' not in forex:
                forex['USDVND'] = 0.0
            cur.close()
            return forex
        cur.close()
        return default_forex
    except Exception as e:
        return default_forex
    finally:
        if conn:
            conn.close()

def send_slack_message(text):
    """Send alert message to Slack if enabled"""
    slack_enabled = os.getenv('SLACK_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not slack_enabled or not slack_webhook_url:
        return
    
    try:
        res = requests.post(slack_webhook_url, json={"text": text}, timeout=5)
        if res.status_code == 200:
            print("Đã gửi cảnh báo thành công qua Slack!")
        else:
            print(f"Lỗi gửi Slack: status={res.status_code}")
    except Exception as e:
        print(f"Lỗi kết nối gửi Slack: {e}")

def is_ntfy_allowed_asset(asset_type, symbol):
    """
    Check if asset qualifies for NTFY notification.
    Allowed:
    - VN Stocks (stock_vn, stock)
    - Forex (forex)
    - Crypto & Futures (crypto, futures)
    - Gold (XAUUSD, GOLD, GC=F)
    - Silver (XAGUSD, SILVER, SI=F)
    - Oil (USOIL, UKOIL, CL=F, BZ=F, WTI, BRENT)
    Disallowed:
    - US Stocks (stock_us, AAPL, TSLA, NVDA, SPX...)
    - Other commodities (copper, natural gas, agriculture, etc.)
    - Yields (yield, bonds)
    """
    if not asset_type or not symbol:
        return False
    
    a_type = str(asset_type).lower().strip()
    sym = str(symbol).upper().strip().split(':')[-1]

    # Explicitly disallowed: US stock, yield, bond
    if a_type in ('stock_us', 'yield', 'yields', 'bond', 'bonds'):
        return False

    # Known US tickers
    us_tickers = ('AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'SPX', 'SPY', 'QQQ', 'DIA', 'IWM', 'NFLX', 'AMD', 'INTC')
    if sym in us_tickers:
        return False

    # 1. VN Stocks
    if a_type in ('stock_vn', 'stock_vietnam', 'stock'):
        return True

    # 2. Forex
    if a_type == 'forex':
        return True

    # 3. Crypto & Futures
    if a_type in ('crypto', 'futures'):
        return True

    # 4. Commodities: ONLY Gold, Silver, Oil are allowed
    if a_type in ('commodity', 'commodities', 'metals', 'energy'):
        gold_syms = ('XAUUSD', 'GOLD', 'GC=F')
        silver_syms = ('XAGUSD', 'SILVER', 'SI=F')
        oil_syms = ('USOIL', 'UKOIL', 'CL=F', 'BZ=F', 'WTI', 'BRENT')
        if any(g in sym for g in gold_syms) or any(s in sym for s in silver_syms) or any(o in sym for o in oil_syms):
            return True
        return False

    # Fallback check by symbol name if asset_type was generic
    if any(g in sym for g in ('XAUUSD', 'GOLD', 'XAGUSD', 'SILVER', 'USOIL', 'UKOIL', 'WTI', 'BRENT')):
        return True

    return False

def send_ntfy_notification(title, message, event_type="trade", asset_type=None, symbol=None, price=None, force=False):
    """
    Send push notification via self-hosted ntfy server (or ntfy.sh).
    Filters only allowed assets: VN Stocks, Forex, Crypto, Gold, Silver, Oil.
    Excludes US stocks and other commodities.
    force=True: luôn gửi (dùng cho lỗi lệnh thật / việc cần xử lý thủ công).
    """
    if not force and not is_ntfy_allowed_asset(asset_type, symbol):
        return

    ntfy_enabled = os.getenv('NTFY_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
    if not ntfy_enabled:
        return

    ntfy_server_url = os.getenv('NTFY_SERVER_URL', 'http://localhost:8088').rstrip('/')
    ntfy_topic = os.getenv('NTFY_TOPIC', 'trading_signals_alerts').strip()
    ntfy_token = os.getenv('NTFY_TOKEN', '')
    click_url = os.getenv('NTFY_CLICK_URL', '')

    if not ntfy_topic:
        return

    endpoint = f"{ntfy_server_url}/{ntfy_topic}"

    # Configure headers based on event_type
    headers = {
        "Title": title.encode('utf-8'),
        "Priority": "high",
        "Tags": "chart_with_upwards_trend"
    }

    if event_type == 'stop_loss':
        headers["Priority"] = "urgent"
        headers["Tags"] = "rotating_light,warning,x"
    elif event_type in ('initial_buy', 'executed'):
        headers["Priority"] = "high"
        headers["Tags"] = "rocket,gem,zap"
    elif event_type == 'pyramid_buy':
        headers["Priority"] = "high"
        headers["Tags"] = "triangular_flag_on_post,moneybag,chart_with_upwards_trend"
    elif event_type == 'breakout':
        headers["Priority"] = "high"
        headers["Tags"] = "fire,chart_with_upwards_trend,rocket"
    elif event_type == 'pre_trade':
        headers["Priority"] = "default"
        headers["Tags"] = "hourglass_flowing_sand,eyes,bell"
    elif event_type == 'approach':
        headers["Priority"] = "default"
        headers["Tags"] = "eyes,chart_with_upwards_trend"
    elif event_type == 'price_alert':
        headers["Priority"] = "high"
        headers["Tags"] = "bell,dart"
    elif event_type in ('trade_failed', 'manual_action'):
        headers["Priority"] = "urgent"
        headers["Tags"] = "sos,warning,x"

    if click_url:
        headers["Click"] = click_url

    if ntfy_token:
        headers["Authorization"] = f"Bearer {ntfy_token}"

    try:
        res = requests.post(
            endpoint,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=5
        )
        if res.status_code == 200:
            print(f"[NTFY] Đã gửi thông báo thành công cho {symbol} ({event_type}) qua {endpoint}!")
        else:
            print(f"[NTFY] Lỗi gửi: status={res.status_code}, response={res.text}")
    except Exception as e:
        print(f"[NTFY] Lỗi kết nối gửi ntfy ({endpoint}): {e}")

CRYPTO_QUOTE_SUFFIXES = ('/USDT', 'USDT', 'BUSD', 'USDC', 'FDUSD')

def crypto_base_symbol(symbol):
    """BTCUSDT -> BTC, BTC/USDT -> BTC, BTCUSDT.P -> BTC (chỉ dùng cho crypto/futures)."""
    s = (symbol or '').split(':')[-1].upper().strip()
    if s.endswith('.P'):
        s = s[:-2]
    for suffix in CRYPTO_QUOTE_SUFFIXES:
        if s.endswith(suffix) and len(s) > len(suffix):
            return s[:-len(suffix)]
    return s

# Tiêu đề thông báo theo loại sự kiện (truyền trực tiếp, không đoán từ nội dung tin nhắn nữa)
EVENT_TITLE_PREFIX = {
    'breakout': '[VƯỢT ĐỈNH] BỨT PHÁ GIÁ',
    'approach': '[TIỆM CẬN ĐỈNH]',
    'pre_trade': '[CHUẨN BỊ VÀO LỆNH]',
    'pre_pyramid': '[CHUẨN BỊ NHỒI LỆNH]',
    'initial_buy': 'ĐÃ VÀO LỆNH',
    'pyramid_buy': 'ĐÃ NHỒI LỆNH',
    'stop_loss': 'CẮT LỖ',
    'price_alert': '[CẢNH BÁO GIÁ]',
    'trade_failed': '[LỖI LỆNH THẬT]',
    'manual_action': '[CẦN XỬ LÝ THỦ CÔNG]',
}

def insert_triggered_alert(asset_type, symbol, price, message, event_type='breakout', is_real=None):
    """
    Log the alert to public.triggered_alerts so the web UI reads it in real-time.
    event_type: breakout | approach | pre_trade | pre_pyramid | initial_buy | pyramid_buy |
                stop_loss | price_alert | trade_failed | manual_action
    is_real: True/False cho các sự kiện giao dịch để gắn nhãn [LIVE]/[DEMO] đúng thực tế.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Chỉ coi BTCUSDT và BTC là cùng một mã với crypto/futures (tránh biến USDCAD -> AD)
        if asset_type in ('crypto', 'futures'):
            base_symbol = crypto_base_symbol(symbol)
        else:
            base_symbol = (symbol or '').split(':')[-1].strip()

        # Giữ 1 cảnh báo mới nhất cho mỗi (asset_type, symbol) — không xoá chéo giữa Spot và Futures
        cur.execute(
            "DELETE FROM public.triggered_alerts WHERE asset_type = %s AND (symbol = %s OR symbol = %s);",
            (asset_type, symbol, base_symbol)
        )

        query = """
        INSERT INTO public.triggered_alerts (asset_type, symbol, price, message, is_read)
        VALUES (%s, %s, %s, %s, false);
        """
        cur.execute(query, (asset_type, symbol, price, message))
        conn.commit()
        cur.close()
        print(f"Đã cập nhật báo động mới nhất cho {symbol} ({asset_type}) vào website database!")
    except Exception as e:
        print(f"Lỗi ghi triggered_alert vào DB: {e}")
    finally:
        if conn:
            conn.close()

    # Thông báo ra ngoài vẫn được gửi kể cả khi ghi DB lỗi
    send_slack_message(message)

    critical = event_type in ('trade_failed', 'manual_action')
    radar_event = NTFY_RADAR_ALL_ASSETS and event_type in RADAR_TRADE_EVENTS
    force_ntfy = critical or radar_event
    if force_ntfy or is_ntfy_allowed_asset(asset_type, symbol):
        title_prefix = EVENT_TITLE_PREFIX.get(event_type, '[CẢNH BÁO]')
        if event_type in ('initial_buy', 'pyramid_buy', 'stop_loss'):
            mode = '[LIVE TRADE THẬT]' if is_real else '[DEMO TRADE]'
            title_prefix = f"{mode} {title_prefix}"
        ntfy_event = 'pre_trade' if event_type == 'pre_pyramid' else event_type

        send_ntfy_notification(
            title=f"{title_prefix}: {symbol} ({str(asset_type).upper()})",
            message=message,
            event_type=ntfy_event,
            asset_type=asset_type,
            symbol=symbol,
            price=price,
            force=force_ntfy
        )

def cleanup_triggered_alerts():
    """Dọn dẹp bảng triggered_alerts:
    - Xóa các bản ghi quá 5 ngày
    - Xóa các cảnh báo pre-trade đã lỗi thời nếu symbol đã có vị thế OPEN
    - Giữ tối đa 200 bản ghi mới nhất
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Xóa các cảnh báo pre-trade cũ nếu symbol đó đang có vị thế OPEN trong paper_positions
        cur.execute("""
            DELETE FROM public.triggered_alerts
            WHERE (message ILIKE '%chuẩn bị%' OR message ILIKE '%pre-trade%' OR message ILIKE '%tiệm cận%')
            AND (
                symbol IN (SELECT symbol FROM public.paper_positions WHERE status = 'OPEN')
                OR symbol IN (SELECT REPLACE(REPLACE(REPLACE(symbol, '/USDT', ''), 'USDT', ''), '.P', '') FROM public.paper_positions WHERE status = 'OPEN' AND asset_type IN ('crypto', 'futures'))
            );
        """)
        deleted_stale_pretrade = cur.rowcount

        # 2. Xóa bản ghi quá 5 ngày
        cur.execute("DELETE FROM public.triggered_alerts WHERE created_at < NOW() - INTERVAL '5 days';")
        deleted_old = cur.rowcount

        # 3. Nếu còn hơn 200 bản ghi, xóa các bản ghi cũ nhất, chỉ giữ 200 bản ghi mới nhất
        cur.execute("""
            DELETE FROM public.triggered_alerts
            WHERE id IN (
                SELECT id FROM public.triggered_alerts
                ORDER BY created_at DESC
                OFFSET 200
            );
        """)
        deleted_excess = cur.rowcount

        total_deleted = deleted_stale_pretrade + deleted_old + deleted_excess
        if total_deleted > 0:
            print(f"Đã dọn dẹp {total_deleted} bản ghi từ triggered_alerts ({deleted_stale_pretrade} pre-trade đã vào lệnh, {deleted_old} quá hạn, {deleted_excess} vượt giới hạn).")

        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Lỗi dọn dẹp triggered_alerts: {e}")
    finally:
        if conn:
            conn.close()

def monitor_stocks_step(symbols, last_alerted_breakout_prices):
    """Performs one scan cycle on VN stock symbols for price breakouts (New Higher High)"""
    if not symbols:
        return
    if Quote is None:
        print("[STOCK VN] Chưa cài thư viện vnstock — bỏ qua quét Stock VN.")
        return

    print(f"[STOCK VN] Đang quét {list(symbols.keys())}...")
    for symbol in symbols:
        try:
            highest_price = symbols[symbol]
            q = Quote(symbol=symbol, source='kbs')
            df = q.intraday(page_size=10, show_log=False)
            if df is None or df.empty:
                continue

            recent_trades = df.tail(5)
            if recent_trades.empty:
                continue

            # KBS price is in thousands (e.g. 52.5 means 52,500 VND)
            current_price_vnd = float(recent_trades.iloc[-1]['price']) * 1000.0
            
            # 1. Check custom price alerts FIRST
            check_custom_stock_alerts(symbol, current_price_vnd, market='vn')

            # 2. Check for price breakout (Only alert on first breakout OR when price reaches a new higher high >= +0.5%)
            if should_alert_breakout(last_alerted_breakout_prices, symbol, current_price_vnd, highest_price, step_mult=1.005):
                clean_sym = symbol.split(':')[-1] if ':' in symbol else symbol
                is_break = current_price_vnd > highest_price
                message = f"Cảnh báo Chứng khoán Việt Nam: Cổ phiếu {clean_sym} đã "
                if is_break:
                    message = message + f"vượt đỉnh ở mức {current_price_vnd:,.0f}đ (Đỉnh cũ: {highest_price:,.0f}đ)."
                else:
                    message = message + f"tiệm cận đỉnh ở mức {current_price_vnd:,.0f}đ (Đỉnh cũ: {highest_price:,.0f}đ)."
                print(f"[VN Stock Breakout] {clean_sym} tại {current_price_vnd:,.0f}đ (Đỉnh cũ: {highest_price:,.0f}đ)")
                radar = auto_trigger_breakout_paper_trade(clean_sym, "stock_vn", current_price_vnd, highest_price)
                if scanner_should_notify(radar, is_break):
                    play_alert(clean_sym, "stock")
                    insert_triggered_alert("stock", clean_sym, current_price_vnd, message,
                                           event_type='breakout' if is_break else 'approach')
                else:
                    print(f"   ↳ {clean_sym}: Breakout Radar đã thông báo — bỏ tin trùng")

            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét stock {symbol}: {e}")

def monitor_cryptos_step(cryptos, last_alerted_breakout_prices):
    """Performs one scan cycle on Binance spot cryptos for price breakouts (New Higher High)"""
    if not cryptos:
        return

    print(f"[CRYPTO] Đang quét {list(cryptos.keys())}...")
    for crypto in cryptos:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={crypto}"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            current_price = float(data.get("price", 0.0))
            if current_price <= 0:
                continue
            
            # 1. Check custom price alerts FIRST
            check_custom_crypto_alerts(crypto, current_price)
            
            # 2. Check for price breakout (Only alert on first breakout OR when price reaches a new higher high >= +0.5%)
            highest_price = cryptos[crypto]
            if should_alert_breakout(last_alerted_breakout_prices, crypto, current_price, highest_price, step_mult=1.005):
                is_break = current_price > highest_price
                message = f"Cảnh báo tiền điện tử: Coin {crypto} đã "
                if is_break:
                    message = message + f"vượt đỉnh ở mức ${current_price:,.4f} (Đỉnh cũ: ${highest_price:,.4f})."
                else:
                    message = message + f"tiệm cận đỉnh ở mức ${current_price:,.4f} (Đỉnh cũ: ${highest_price:,.4f})."
                print(f"[Crypto Breakout] {crypto} tại {current_price} >= 99% Đỉnh cũ {highest_price}")
                radar = auto_trigger_breakout_paper_trade(crypto, "crypto", current_price, highest_price)
                if scanner_should_notify(radar, is_break):
                    play_alert(crypto, "crypto")
                    insert_triggered_alert("crypto", crypto, current_price, message,
                                           event_type='breakout' if is_break else 'approach')
                else:
                    print(f"   ↳ {crypto}: Breakout Radar đã thông báo — bỏ tin trùng")
            
            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét crypto {crypto}: {e}")

def monitor_futures_step(futures, last_alerted_breakout_prices):
    """Performs one scan cycle on Binance Futures contracts for price breakouts (New Higher High)"""
    if not futures:
        return

    print(f"[FUTURES] Đang quét {list(futures.keys())}...")
    for symbol in futures:
        try:
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            current_price = float(data.get("price", 0.0))
            if current_price <= 0:
                continue
            
            # 1. Check custom price alerts FIRST
            check_custom_futures_alerts(symbol, current_price)
            
            # 2. Check for price breakout (Only alert on first breakout OR when price reaches a new higher high >= +0.5%)
            highest_price = futures[symbol]
            if should_alert_breakout(last_alerted_breakout_prices, symbol, current_price, highest_price, step_mult=1.005):
                is_break = current_price > highest_price
                message = f"Cảnh báo phái sinh {symbol} đã "
                if is_break:
                    message = message + f"vượt đỉnh cũ ở mức ${current_price:,.4f} (Đỉnh cũ: ${highest_price:,.4f})."
                else:
                    message = message + f"tiệm cận đỉnh cũ ở mức ${current_price:,.4f} (Đỉnh cũ: ${highest_price:,.4f})."
                print(f"[Futures Breakout] {symbol} tại {current_price} tiệm cận hoặc vượt đỉnh cũ {highest_price}")
                radar = auto_trigger_breakout_paper_trade(symbol, "futures", current_price, highest_price)
                if scanner_should_notify(radar, is_break):
                    play_alert(symbol, "futures")
                    insert_triggered_alert("futures", symbol, current_price, message,
                                           event_type='breakout' if is_break else 'approach')
                else:
                    print(f"   ↳ {symbol}: Breakout Radar đã thông báo — bỏ tin trùng")

            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét futures {symbol}: {e}")

def fetch_tradingview_yields(tickers):
    """Fetches yields from TradingView scanner API"""
    url = "https://scanner.tradingview.com/global/scan"
    payload = {
        "symbols": {
            "tickers": tickers
        },
        "columns": ["close", "price_52_week_high"]
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    results = {}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("data", []):
                s = item.get("s")
                d = item.get("d", [])
                if len(d) >= 2:
                    close = d[0]
                    high_52w = d[1]
                    if close is not None and high_52w is not None:
                        results[s] = (float(close), float(high_52w))
    except Exception as e:
        print(f"Error fetching from TradingView scanner: {e}")
    return results

YIELD_SYMBOLS = {
    # US — ^IRX là tín phiếu 13 tuần (không phải 2 năm) nên lấy US02Y từ TradingView
    'TVC:US02Y': 'US02Y',
    '^FVX': 'US05Y',
    '^TNX': 'US10Y',
    '^TYX': 'US30Y',
    # Japan
    'TVC:JP02Y': 'JP02Y',
    'TVC:JP10Y': 'JP10Y',
    'TVC:JP30Y': 'JP30Y',
    # UK
    'TVC:GB02Y': 'GB02Y',
    'TVC:GB10Y': 'GB10Y',
    'TVC:GB30Y': 'GB30Y',
    # Germany (Europe)
    'TVC:DE02Y': 'DE02Y',
    'TVC:DE10Y': 'DE10Y',
    'TVC:DE30Y': 'DE30Y'
}


def _as_utc(ts):
    if ts is None:
        return None
    return ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _evaluate_price_alert(operator, alert_price, current_price):
    """
    Trả về (triggered, crossed, condition_text):
    - crossed: giá đã THỰC SỰ chạm/vượt mức đặt.
    - triggered: crossed hoặc đã vào vùng dung sai PRICE_ALERT_TOLERANCE_PCT.
    """
    tol = max(PRICE_ALERT_TOLERANCE_PCT, 0.0) / 100.0
    if operator == '<=':
        crossed = current_price <= alert_price
        triggered = crossed or current_price <= alert_price * (1.0 + tol)
        return triggered, crossed, ("giảm xuống dưới hoặc bằng" if crossed else "đang tiệm cận (từ trên xuống)")
    if operator == '>=':
        crossed = current_price >= alert_price
        triggered = crossed or current_price >= alert_price * (1.0 - tol)
        return triggered, crossed, ("tăng lên trên hoặc bằng" if crossed else "đang tiệm cận (từ dưới lên)")
    return False, False, ""


def check_custom_price_alerts(lookup_asset_types, lookup_symbols, current_price, out_asset_type,
                              out_symbol, label, price_fmt="{:,.4f}", price_unit=""):
    """
    Hàm chung kiểm tra cảnh báo giá người dùng đặt trong public.price_alerts
    (PK của bảng là (symbol, asset_type) nên mỗi mã chỉ có 1 cảnh báo / loại tài sản).

    lookup_asset_types / lookup_symbols: các asset_type & alias symbol dùng để tìm cảnh báo.
    out_asset_type / out_symbol: asset_type & symbol ghi vào triggered_alerts.
    out_symbol có thể là None -> dùng symbol của chính cảnh báo.
    """
    if current_price is None or current_price <= 0:
        return
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, asset_type, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = ANY(%s)
            AND symbol = ANY(%s)
            AND is_active = true;
        """, (list(set(lookup_asset_types)), list(set(lookup_symbols))))
        alerts = cur.fetchall()

        for alert_symbol, alert_asset_type, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            if alert_price <= 0:
                continue
            triggered, crossed, condition = _evaluate_price_alert(operator, alert_price, current_price)
            if not triggered:
                continue

            last_notified = _as_utc(last_notified_at)
            if last_notified and datetime.now(timezone.utc) - last_notified < timedelta(hours=PRICE_ALERT_COOLDOWN_HOURS):
                continue

            sym_out = out_symbol or alert_symbol
            p_cur = price_fmt.format(current_price) + price_unit
            p_alert = price_fmt.format(alert_price) + price_unit
            if crossed:
                message = f"Cảnh báo {label}: Giá {sym_out} đã {condition} mức {p_alert} (Giá hiện tại: {p_cur})."
            else:
                dist = abs(current_price - alert_price) / alert_price * 100.0
                message = f"Cảnh báo {label}: Giá {sym_out} {condition} mức {p_alert}, chỉ còn cách {dist:.2f}% (Giá hiện tại: {p_cur})."
            print(f"[{label} Price Alert] {sym_out} tại {current_price} kích hoạt {operator} {alert_price} (crossed={crossed})")

            play_alert(sym_out, out_asset_type)
            insert_triggered_alert(out_asset_type, sym_out, current_price, message, event_type='price_alert')

            deactivate = PRICE_ALERT_ONE_SHOT and crossed
            cur.execute("""
                UPDATE public.price_alerts
                SET last_notified_at = CURRENT_TIMESTAMP,
                    is_active = CASE WHEN %s THEN false ELSE is_active END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s AND asset_type = %s;
            """, (deactivate, alert_symbol, alert_asset_type))
            conn.commit()

        cur.close()
    except Exception as e:
        print(f"Lỗi check custom {label} alerts cho {lookup_symbols}: {e}")
    finally:
        if conn:
            conn.close()


def check_custom_yield_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this yield"""
    check_custom_price_alerts(['yield'], [symbol], current_price, 'yield', symbol,
                              'Lợi suất', price_fmt="{:.3f}", price_unit="%")


def check_custom_crypto_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this crypto"""
    clean_symbol = symbol.split(':')[-1]
    check_custom_price_alerts(['crypto'], [symbol, clean_symbol], current_price, 'crypto', None, 'Crypto')


def check_custom_futures_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this futures contract"""
    clean_symbol = symbol.split(':')[-1]
    check_custom_price_alerts(['futures'], [symbol, clean_symbol], current_price, 'futures', None, 'Futures')


def check_custom_stock_alerts(symbol, current_price, market='vn'):
    """Check if any user price alerts in the database are triggered for this stock (market: 'vn' | 'us')"""
    clean_symbol = symbol.split(':')[-1]
    if market == 'us':
        check_custom_price_alerts(['stock', 'stock_us'], [symbol, clean_symbol], current_price,
                                  'stock_us', None, 'Cổ phiếu Mỹ', price_fmt="{:,.2f}")
    else:
        check_custom_price_alerts(['stock', 'stock_vn'], [symbol, clean_symbol], current_price,
                                  'stock', None, 'Cổ phiếu', price_fmt="{:,.0f}", price_unit="đ")


def monitor_yields_step(yield_symbols, last_alerted_yields):
    """Performs one scan cycle on Treasury Yields using yfinance (with HTTP fallback) or TradingView scanner"""
    if not yield_symbols:
        return

    print(f"[YIELDS] Đang quét {list(yield_symbols.values())}...")
    
    # Batch fetch TradingView tickers
    tv_tickers = [t for t in yield_symbols.keys() if t.startswith("TVC:")]
    tv_data = {}
    if tv_tickers:
        tv_data = fetch_tradingview_yields(tv_tickers)
        
    for ticker, symbol in yield_symbols.items():
        try:
            current_price = None
            fifty_two_high = None
            
            if ticker.startswith("TVC:"):
                # Use TradingView data
                if ticker in tv_data:
                    current_price, fifty_two_high = tv_data[ticker]
            else:
                # 1. Try using yfinance library if available
                if yf is not None:
                    try:
                        t = yf.Ticker(ticker)
                        hist_1d = t.history(period="1d")
                        if not hist_1d.empty:
                            current_price = float(hist_1d["Close"].iloc[-1])
                            
                        hist_1y = t.history(period="1y")
                        if not hist_1y.empty:
                            prices_1y = hist_1y["Close"].dropna()
                            if not prices_1y.empty:
                                fifty_two_high = float(prices_1y.max())
                    except Exception as yfe:
                        print(f"yfinance library error for {symbol}: {yfe}. Trying HTTP fallback...")
                
                # 2. HTTP Fallback
                if current_price is None or fifty_two_high is None:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                    res = requests.get(url, headers=headers, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        results = data.get("chart", {}).get("result", [])
                        if results:
                            meta = results[0].get("meta", {})
                            current_price = meta.get("regularMarketPrice")
                            fifty_two_high = meta.get("fiftyTwoWeekHigh")

            if current_price is None or fifty_two_high is None or fifty_two_high <= 0:
                continue

            # CBOE yields are 10x the actual yield rate (e.g. 38.8 means 3.88%)
            if not ticker.startswith("TVC:") and (current_price > 10.0 or fifty_two_high > 10.0):
                current_price = current_price / 10.0
                fifty_two_high = fifty_two_high / 10.0

            # Check 52-Week High Breakout (check within 1%)
            # Only alert on first breakout OR when yield reaches a new higher high (>= +0.005 điểm %)
            if should_alert_breakout(last_alerted_yields, symbol, current_price, fifty_two_high, step_abs=0.005):
                country = "Mỹ"
                if symbol.startswith("JP"):
                    country = "Nhật Bản"
                elif symbol.startswith("GB"):
                    country = "Anh"
                elif symbol.startswith("DE"):
                    country = "Đức (Châu Âu)"

                is_break = current_price > fifty_two_high
                action = "vượt đỉnh" if is_break else "tiệm cận đỉnh"
                message = f"Cảnh báo Lợi suất: Lợi suất trái phiếu Chính phủ {country} {symbol} đã {action} 52 tuần tại mức {current_price:.3f}% (Đỉnh 52 tuần: {fifty_two_high:.3f}%)."
                print(f"[Yield Breakout] {symbol} ({country}) tại lợi suất {current_price:.3f}% >= 99% Đỉnh 52 tuần {fifty_two_high:.3f}%")
                play_alert(symbol, "yield")
                insert_triggered_alert("yield", symbol, current_price, message,
                                       event_type='breakout' if is_break else 'approach')

            # Check custom user-configured alerts
            check_custom_yield_alerts(symbol, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét yield {symbol}: {e}")

COMMODITIES_SYMBOLS = {
    'GC=F': 'Vàng (XAUUSD)',
    'SI=F': 'Bạc (XAGUSD)',
    'BZ=F': 'Dầu Brent (UKOIL)',
    'CL=F': 'Dầu WTI (USOIL)'
}

COMMODITY_ALIASES = {
    'GC=F': ['GC=F', 'XAUUSD', 'GOLD', 'VÀNG', 'VANG'],
    'SI=F': ['SI=F', 'XAGUSD', 'SILVER', 'BẠC', 'BAC'],
    'CL=F': ['CL=F', 'USOIL', 'WTI', 'OIL', 'DẦU WTI'],
    'BZ=F': ['BZ=F', 'UKOIL', 'BRENT', 'DẦU BRENT']
}

def check_custom_commodity_alerts(symbol, name, current_price):
    """Check if any user price alerts in the database are triggered for this commodity"""
    aliases = list(set(COMMODITY_ALIASES.get(symbol, [symbol]) + [symbol]))
    display_sym = 'XAUUSD' if symbol == 'GC=F' else ('XAGUSD' if symbol == 'SI=F' else symbol)
    check_custom_price_alerts(['commodities', 'commodity', 'gold', 'silver', 'oil', 'forex'], aliases,
                              current_price, 'commodities', display_sym, f"Hàng hóa {name}",
                              price_fmt="${:,.2f}")


def classify_high_breakout(cache, key, current_price, recent_high, fifty_two_high, step_mult):
    """
    Ưu tiên đỉnh 52 tuần (tín hiệu mạnh hơn), sau đó mới tới đỉnh gần nhất (30 ngày).
    Trước đây nhánh 52 tuần nằm sau `elif` nên không bao giờ chạy (đỉnh 52W luôn >= đỉnh 30 ngày).
    Trả về ('52w' | 'recent' | None, reference_high).
    """
    if fifty_two_high and fifty_two_high > 0 and current_price >= fifty_two_high * 0.99:
        if should_alert_breakout(cache, key, current_price, fifty_two_high, step_mult=step_mult):
            return '52w', fifty_two_high
        return None, fifty_two_high
    if recent_high and recent_high > 0:
        if should_alert_breakout(cache, key, current_price, recent_high, step_mult=step_mult):
            return 'recent', recent_high
    return None, recent_high


def _yahoo_daily_chart(symbol, headers):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
    res = requests.get(url, headers=headers, timeout=5)
    if res.status_code != 200:
        return None, None, None
    results = res.json().get("chart", {}).get("result", [])
    if not results:
        return None, None, None
    meta = results[0].get("meta", {})
    current_price = meta.get("regularMarketPrice")
    fifty_two_high = meta.get("fiftyTwoWeekHigh")
    # Calculate 30-day recent high from daily candles (excluding current in-progress candle)
    quotes = (results[0].get("indicators", {}).get("quote") or [{}])[0]
    highs = [h for h in (quotes.get("high") or []) if h is not None]
    recent_high = max(highs[:-1]) if len(highs) > 1 else (max(highs) if highs else fifty_two_high)
    return current_price, recent_high, fifty_two_high


def monitor_commodities_step(commodities_symbols, last_alerted_prices):
    """Performs one scan cycle on global commodities using Yahoo Finance"""
    if not commodities_symbols:
        return

    print(f"[COMMODITIES] Đang quét {list(commodities_symbols.keys())}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for symbol, name in commodities_symbols.items():
        try:
            current_price, recent_high, fifty_two_high = _yahoo_daily_chart(symbol, headers)
            if current_price is None:
                continue

            display_sym = 'XAUUSD' if symbol == 'GC=F' else ('XAGUSD' if symbol == 'SI=F' else symbol)

            # Only alert on first breakout OR when price reaches a new higher high (>= +0.3%)
            kind, ref_high = classify_high_breakout(last_alerted_prices, symbol, current_price,
                                                    recent_high, fifty_two_high, step_mult=1.003)
            if kind:
                is_break = current_price > ref_high
                action = "vượt" if is_break else "tiệm cận"
                level = "đỉnh 52 tuần" if kind == '52w' else "đỉnh gần nhất (30 ngày)"
                label = name if display_sym in name else f"{name} ({display_sym})"
                message = f"Cảnh báo Hàng hóa: {label} đã {action} {level} ở mức ${current_price:,.2f} (Đỉnh cũ: ${ref_high:,.2f})."
                print(f"[Commodity {kind.upper()} Breakout] {name} tại giá ${current_price:,.2f} >= 99% đỉnh ${ref_high:,.2f}")
                play_alert(display_sym, "commodities")
                insert_triggered_alert("commodities", display_sym, current_price, message,
                                       event_type='breakout' if is_break else 'approach')

            # Check for custom user-configured alerts
            check_custom_commodity_alerts(symbol, name, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét commodity {symbol}: {e}")

def map_forex_symbol_to_yahoo(symbol):
    """Map standard forex pair name to Yahoo Finance symbol"""
    mapping = {
        'EURUSD': 'EURUSD=X',
        'USDJPY': 'USDJPY=X',
        'GBPUSD': 'GBPUSD=X',
        'USDCHF': 'USDCHF=X',
        'AUDUSD': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
        'USDVND': 'USDVND=X',
        'XAUUSD': 'GC=F',
        'XAGUSD': 'SI=F',
        'WTI': 'CL=F',
        'DXY': 'DX-Y.NYB'
    }
    if symbol in mapping:
        return mapping[symbol]
    if len(symbol) == 6:
        return f"{symbol}=X"
    return symbol

def check_custom_forex_alerts(symbol, pair_name, current_price):
    """Check if any user price alerts in the database are triggered for this forex pair"""
    # Aliases for forex pairs (e.g. XAUUSD <-> GC=F, XAGUSD <-> SI=F, USDVND <-> USDVND=X)
    aliases = [symbol, pair_name]
    if pair_name == 'XAUUSD' or symbol == 'GC=F':
        aliases.extend(['XAUUSD', 'GC=F', 'GOLD', 'VÀNG'])
    elif pair_name == 'XAGUSD' or symbol == 'SI=F':
        aliases.extend(['XAGUSD', 'SI=F', 'SILVER', 'BẠC'])
    elif pair_name == 'WTI' or symbol == 'CL=F':
        aliases.extend(['WTI', 'CL=F', 'USOIL'])
    elif pair_name == 'DXY' or symbol == 'DX-Y.NYB':
        aliases.extend(['DXY', 'DX-Y.NYB'])
    elif pair_name == 'USDVND' or symbol == 'USDVND=X':
        aliases.extend(['USDVND', 'USDVND=X', 'USD/VND', 'TỶ GIÁ USD', 'TỶ GIÁ USD/VND'])

    check_custom_price_alerts(['forex', 'commodities', 'commodity', 'gold', 'silver'], aliases,
                              current_price, 'forex', pair_name, f"Forex {pair_name}")


def monitor_forex_step(forex_pairs, last_alerted_prices):
    """Performs one scan cycle on forex pairs using Yahoo Finance"""
    if not forex_pairs:
        return

    # Skip commodity pairs already handled in monitor_commodities_step to avoid duplicate alerts
    commodity_pairs = {'XAUUSD', 'XAGUSD', 'WTI', 'USOIL', 'UKOIL', 'BRENT'}
    filtered_pairs = {k: v for k, v in forex_pairs.items() if k.upper() not in commodity_pairs}
    if not filtered_pairs:
        return

    print(f"[FOREX] Đang quét {list(filtered_pairs.keys())}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for pair in filtered_pairs:
        try:
            # Map standard pair to Yahoo Finance symbol
            symbol = map_forex_symbol_to_yahoo(pair)
            current_price, recent_high, fifty_two_high = _yahoo_daily_chart(symbol, headers)
            if current_price is None:
                continue

            # Only alert on first breakout OR when price reaches a new higher high (>= +0.2%)
            kind, ref_high = classify_high_breakout(last_alerted_prices, pair, current_price,
                                                    recent_high, fifty_two_high, step_mult=1.002)
            if kind:
                is_break = current_price > ref_high
                action = "vượt" if is_break else "tiệm cận"
                level = "đỉnh 52 tuần" if kind == '52w' else "đỉnh gần nhất (30 ngày)"
                message = f"Cảnh báo Forex: Cặp tiền {pair} ({symbol}) đã {action} {level} ở mức {current_price:,.4f} (Đỉnh cũ: {ref_high:,.4f})."
                print(f"[Forex {kind.upper()} Breakout] {pair} tại giá {current_price:,.4f} >= 99% đỉnh {ref_high:,.4f}")
                radar = auto_trigger_breakout_paper_trade(pair, "forex", current_price, fifty_two_high) if kind == '52w' else None
                if scanner_should_notify(radar, is_break):
                    play_alert(pair, "forex")
                    insert_triggered_alert("forex", pair, current_price, message,
                                           event_type='breakout' if is_break else 'approach')
                else:
                    print(f"   ↳ {pair}: Breakout Radar đã thông báo — bỏ tin trùng")

            # Check for custom user-configured alerts
            check_custom_forex_alerts(symbol, pair, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"Lỗi quét forex {pair}: {e}")

def init_breakout_paper_trade_tables():
    """Ensure breakout_watchlist, paper_positions and paper_orders tables exist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.breakout_watchlist (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                asset_type VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                ath_price NUMERIC(20, 8) NOT NULL,
                initial_budget NUMERIC(20, 2) DEFAULT 1000.00 NOT NULL,
                step_pct NUMERIC(5, 2) DEFAULT 1.00 NOT NULL,
                pyramid_ratio NUMERIC(5, 2) DEFAULT 0.67 NOT NULL,
                sl_pct NUMERIC(5, 2) DEFAULT 2.00 NOT NULL,
                max_pyramids INT DEFAULT 3 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                current_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT uq_breakout_symbol_asset UNIQUE(symbol, asset_type)
            );

            -- CREATE TABLE IF NOT EXISTS does not add columns to an existing table.
            ALTER TABLE public.breakout_watchlist
                ADD COLUMN IF NOT EXISTS current_price NUMERIC(20, 8) DEFAULT 0 NOT NULL;

            CREATE TABLE IF NOT EXISTS public.paper_positions (
                id SERIAL PRIMARY KEY,
                watchlist_id INT REFERENCES public.breakout_watchlist(id) ON DELETE CASCADE,
                symbol VARCHAR(50) NOT NULL,
                asset_type VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
                current_layer INT DEFAULT 1 NOT NULL,
                total_invested NUMERIC(20, 2) DEFAULT 0 NOT NULL,
                total_units NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                avg_entry_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                last_buy_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                highest_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                current_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                stop_loss_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                next_pyramid_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                unrealized_pnl NUMERIC(20, 2) DEFAULT 0 NOT NULL,
                unrealized_roi_pct NUMERIC(10, 2) DEFAULT 0 NOT NULL,
                realized_pnl NUMERIC(20, 2) DEFAULT 0 NOT NULL,
                opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                closed_at TIMESTAMPTZ,
                close_reason VARCHAR(50),
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS public.paper_orders (
                id SERIAL PRIMARY KEY,
                position_id INT REFERENCES public.paper_positions(id) ON DELETE CASCADE,
                symbol VARCHAR(50) NOT NULL,
                order_type VARCHAR(30) NOT NULL,
                layer INT DEFAULT 1 NOT NULL,
                price NUMERIC(20, 8) NOT NULL,
                amount_usd NUMERIC(20, 2) NOT NULL,
                units NUMERIC(20, 8) NOT NULL,
                reason TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
            );

            -- Các cột từ migration 021/022/025 (đảm bảo tồn tại nếu DB chưa chạy migration)
            ALTER TABLE public.breakout_watchlist
                ADD COLUMN IF NOT EXISTS is_real_trading BOOLEAN DEFAULT FALSE NOT NULL,
                ADD COLUMN IF NOT EXISTS spread_pct NUMERIC(6, 4) DEFAULT 0.10 NOT NULL,
                ADD COLUMN IF NOT EXISTS sl_mode VARCHAR(30) DEFAULT 'TRAILING_PEAK' NOT NULL;

            ALTER TABLE public.paper_positions
                ADD COLUMN IF NOT EXISTS spread_pct NUMERIC(6, 4) DEFAULT 0.10 NOT NULL,
                ADD COLUMN IF NOT EXISTS breakeven_price NUMERIC(20, 8) DEFAULT 0 NOT NULL,
                ADD COLUMN IF NOT EXISTS sl_mode VARCHAR(30) DEFAULT 'TRAILING_PEAK' NOT NULL,
                -- Vị thế này có lệnh thật trên sàn hay không (cố định lúc mở, không phụ thuộc toggle về sau)
                ADD COLUMN IF NOT EXISTS is_real BOOLEAN DEFAULT FALSE NOT NULL,
                -- Khối lượng thực khớp trên sàn (Binance) để bán đúng số lượng khi cắt lỗ
                ADD COLUMN IF NOT EXISTS real_units NUMERIC(20, 8) DEFAULT 0 NOT NULL;
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Lỗi khởi tạo bảng breakout_watchlist / paper trading: {e}")
    finally:
        if conn:
            conn.close()

    # Chốt chặn ở DB: mỗi mã trong watchlist chỉ được có tối đa 1 vị thế OPEN
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_paper_positions_one_open
            ON public.paper_positions(watchlist_id) WHERE status = 'OPEN';
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[CẢNH BÁO] Không tạo được unique index chống trùng vị thế OPEN "
              f"(có thể đang có vị thế OPEN bị trùng — hãy kiểm tra paper_positions): {e}")
    finally:
        if conn:
            conn.close()

    # Trạng thái chống báo trùng (đã báo tiệm cận/vượt đỉnh/chuẩn bị vào lệnh) — giữ qua các lần restart
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.alert_dedupe_state (
                namespace VARCHAR(30) NOT NULL,
                key VARCHAR(120) NOT NULL,
                value DOUBLE PRECISION NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                PRIMARY KEY (namespace, key)
            );
        """)
        cur.execute("DELETE FROM public.alert_dedupe_state WHERE updated_at < NOW() - make_interval(secs => %s);",
                    (max(ALERT_DEDUPE_TTL_DAYS, 0.0) * 86400,))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[CẢNH BÁO] Không tạo được bảng alert_dedupe_state: {e}")
    finally:
        if conn:
            conn.close()

def fetch_live_price_for_breakout(symbol, asset_type):
    """Fetch current real-time price for any breakout asset"""
    clean_sym = symbol.split(':')[-1] if ':' in symbol else symbol
    clean_sym = clean_sym.upper().strip()

    try:
        if asset_type in ('crypto', 'futures'):
            # Fetch from Binance
            endpoint = "https://api.binance.com/api/v3/ticker/price" if asset_type == 'crypto' else "https://fapi.binance.com/fapi/v1/ticker/price"
            res = requests.get(f"{endpoint}?symbol={clean_sym}", timeout=4)
            if res.status_code == 200:
                return float(res.json().get('price', 0))
        elif asset_type == 'stock_vn':
            if Quote is None:
                return None
            # Try KBS Quote
            q = Quote(symbol=clean_sym, source='kbs')
            df = q.intraday(page_size=5, show_log=False)
            if df is not None and not df.empty:
                return float(df.iloc[-1]['price']) * 1000.0
        elif asset_type in ('stock_us', 'commodity', 'commodities', 'forex'):
            # Map ticker if needed for Yahoo Finance
            ticker = clean_sym
            if asset_type == 'forex':
                ticker = map_forex_symbol_to_yahoo(clean_sym)
            elif asset_type in ('commodity', 'commodities'):
                comm_map = {'XAUUSD': 'GC=F', 'GOLD': 'GC=F', 'SILVER': 'SI=F', 'XAGUSD': 'SI=F', 'USOIL': 'CL=F', 'UKOIL': 'BZ=F', 'COPPER': 'HG=F'}
                ticker = comm_map.get(clean_sym, clean_sym)
            
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}", headers=headers, timeout=5)
            if res.status_code == 200:
                results = res.json().get("chart", {}).get("result", [])
                if results:
                    meta = results[0].get("meta", {})
                    price = meta.get("regularMarketPrice")
                    if price:
                        return float(price)
    except Exception as e:
        print(f"Lỗi lấy giá trực tiếp cho {symbol} ({asset_type}): {e}")
    return None

# In-memory debounce cache for Pre-Trade Approaching Warnings: key = (watchlist_id, stage_key), value = alerted_price
last_pre_trade_alerts = PersistentCache('pretrade')
# Thời điểm lệnh thật gần nhất bị sàn từ chối: key = (watchlist_id, layer) -> epoch seconds
_real_order_failures = {}
# Mã cổ phiếu VN có vốn quá nhỏ để mua 1 lô (chỉ log 1 lần)
_undersized_budget_warned = set()

# Namespace cho pg advisory lock (chống 2 tiến trình/2 luồng xử lý cùng 1 mã cùng lúc)
_ADVISORY_LOCK_NS = 742001

# Cột đọc từ breakout_watchlist — dùng chung cho mọi nơi gọi process_breakout_paper_trading
BREAKOUT_ITEM_COLUMNS = """
    id, symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio,
    sl_pct, max_pyramids, is_real_trading, spread_pct, sl_mode
"""

BINANCE_ASSETS = ('crypto', 'futures')
MT5_ASSETS = ('forex', 'commodity', 'commodities', 'stock_us')

TRADE_TOGGLE_KEYS = {
    'crypto': 'trade_crypto_enabled',
    'stock_us': 'trade_us_stock_enabled',
    'stock_vn': 'trade_vn_stock_enabled',
    'forex': 'trade_forex_enabled',
    'commodity': 'trade_commodity_enabled',
    'commodities': 'trade_commodity_enabled',
    'futures': 'trade_futures_enabled',
}


def _pretrade_due(w_id, stage, current_price, target_price, max_reminders=-1):
    """
    Quyết định có gửi cảnh báo chuẩn bị (vào lệnh tầng 1 / nhồi tầng N) không.
    Trả về (gửi: bool, số_lần_nhắc: int, số_phút_đã_chờ: float). Lưu trạng thái vào DB (qua restart vẫn nhớ).
    - Lần đầu: khi giá cách mốc ≤ PRE_TRADE_FIRST_PCT (1%).
    - Nhắc lại: mỗi PRE_TRADE_REMINDER_MINUTES phút khi giá vẫn cách mốc ≤ PRE_TRADE_ZONE_PCT (2%).
    - max_reminders >= 0: nhắc lại tối đa N lần rồi thôi (đến khi reset). Âm = không giới hạn.
    """
    key, first_key, count_key = (w_id, stage), (w_id, f"{stage}_first"), (w_id, f"{stage}_count")
    now_ts = time.time()
    last_ts = last_pre_trade_alerts.get(key)
    if last_ts is None:
        if current_price < target_price * (1.0 - PRE_TRADE_FIRST_PCT / 100.0):
            return False, 0, 0.0
        last_pre_trade_alerts[key] = now_ts
        last_pre_trade_alerts[first_key] = now_ts
        last_pre_trade_alerts[count_key] = 0
        return True, 0, 0.0
    # Giá trị cũ (trước khi có nhắc lại) là giá thay vì thời gian → coi như vừa báo
    if last_ts < 1_000_000_000:
        last_pre_trade_alerts[key] = now_ts
        return False, 0, 0.0
    if PRE_TRADE_REMINDER_MINUTES <= 0 or now_ts - last_ts < PRE_TRADE_REMINDER_MINUTES * 60:
        return False, 0, 0.0
    count = int(last_pre_trade_alerts.get(count_key, 0) or 0) + 1
    if max_reminders >= 0 and count > max_reminders:
        return False, 0, 0.0
    first_ts = last_pre_trade_alerts.get(first_key, last_ts) or last_ts
    last_pre_trade_alerts[key] = now_ts
    last_pre_trade_alerts[count_key] = count
    return True, count, (now_ts - first_ts) / 60.0


def _pretrade_reset(w_id, stage):
    for suffix in ("", "_first", "_count"):
        last_pre_trade_alerts.pop((w_id, f"{stage}{suffix}"), None)


def _clear_pretrade_cache(w_id):
    for key in [k for k in last_pre_trade_alerts if k[0] == w_id]:
        last_pre_trade_alerts.pop(key, None)


def _real_order_in_cooldown(w_id, layer):
    ts = _real_order_failures.get((w_id, layer))
    return ts is not None and (time.time() - ts) < REAL_ORDER_RETRY_COOLDOWN_SEC


def _size_order(asset_type, budget, price):
    """Tính khối lượng & giá trị lệnh. Cổ phiếu VN làm tròn xuống theo lô chẵn."""
    if price <= 0 or budget <= 0:
        return 0.0, 0.0
    units = budget / price
    if asset_type == 'stock_vn':
        units = math.floor(units / VN_STOCK_LOT_SIZE) * VN_STOCK_LOT_SIZE
    return units, units * price


def _compute_stop_loss(avg_entry, highest, layer, max_pyramids, sl_pct, spread_pct, sl_mode, prev_sl=0.0):
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
    trailing_active = (highest >= avg_entry * (1.0 + TRAILING_ACTIVATION_PCT / 100.0)) or \
                      (highest >= avg_entry * (1.0 + sl_pct / 100.0)) or \
                      (layer >= max_pyramids)
    if sl_mode == 'BREAKEVEN_HOLD' and layer >= 2:
        trailing_active = True
    sl = max(breakeven, trailing_from_peak) if trailing_active else base_sl
    if prev_sl and prev_sl > sl:
        sl = prev_sl
    return sl, breakeven


def _execute_real_buy(symbol, asset_type, amount, price, sl_pct, layer):
    """
    Gửi lệnh mua thật. Trả về dict:
      supported (bool), success (bool), note (str), entry_price (float|None), units (float), error (str)
    """
    if asset_type in BINANCE_ASSETS:
        try:
            from live_trader_binance import execute_binance_order
            res = execute_binance_order(symbol, asset_type, amount, sl_pct=sl_pct, layer=layer)
        except Exception as e:
            return {'supported': True, 'success': False, 'error': str(e), 'note': f" [LIVE ERROR: {e}]"}
        if res.get('success'):
            return {
                'supported': True, 'success': True,
                'note': f" [BINANCE REAL ORDER #{res.get('order_id')}]",
                'entry_price': float(res['entry_price']) if res.get('entry_price') else None,
                'units': float(res.get('units') or 0.0),
            }
        return {'supported': True, 'success': False, 'error': res.get('error'),
                'note': f" [BINANCE REAL FAILED: {res.get('error')}]"}

    if asset_type in MT5_ASSETS:
        try:
            from live_trader_mt5 import execute_mt5_order
            res = execute_mt5_order(symbol, asset_type, price, sl_pct=sl_pct, layer=layer)
        except Exception as e:
            return {'supported': True, 'success': False, 'error': str(e), 'note': f" [LIVE ERROR: {e}]"}
        if res.get('success'):
            return {
                'supported': True, 'success': True,
                'note': f" [MT5 REAL TICKET #{res.get('ticket')}]",
                'entry_price': float(res['entry_price']) if res.get('entry_price') else None,
                'units': 0.0,  # MT5 tính theo lot, theo dõi qua ticket
            }
        return {'supported': True, 'success': False, 'error': res.get('error'),
                'note': f" [MT5 REAL FAILED: {res.get('error')}]"}

    return {'supported': False, 'success': False, 'note': " [KHÔNG HỖ TRỢ LỆNH THẬT CHO LOẠI TÀI SẢN NÀY — CHẠY DEMO]"}


def _report_real_failure(w_id, layer, symbol, asset_type, price, action, error):
    """Ghi nhận lỗi lệnh thật + bật cooldown để không spam lệnh / thông báo mỗi 15 giây."""
    _real_order_failures[(w_id, layer)] = time.time()
    msg = (f"[LỖI LỆNH THẬT] Không thể {action} {symbol} ({asset_type.upper()}) tầng {layer}: {error}. "
           f"Hệ thống KHÔNG ghi nhận vị thế/lệnh này và sẽ thử lại sau {int(REAL_ORDER_RETRY_COOLDOWN_SEC // 60)} phút.")
    print(f"\n{msg}\n")
    insert_triggered_alert(asset_type, symbol, price, msg, event_type='trade_failed')


def _close_real_position(symbol, asset_type, units):
    """
    Đóng vị thế thật khi chạm SL. Trả về (ok, note).
    Lưu ý: nếu Binance đang giữ lệnh STOP_LOSS_LIMIT (đặt lúc mua) thì số dư có thể bị khoá
    hoặc đã được bán bởi chính lệnh SL đó.
    """
    if asset_type in BINANCE_ASSETS:
        try:
            from live_trader_binance import execute_binance_sell_market
            res = execute_binance_sell_market(symbol, units if units and units > 0 else None, asset_type)
        except Exception as e:
            return False, f" [LIVE SL ERROR: {e}]"
        if res.get('success'):
            return True, f" [BINANCE REAL SELL #{res.get('order_id')}]"
        return False, f" [BINANCE SELL FAILED: {res.get('error')}]"
    if asset_type in MT5_ASSETS:
        return False, " [MT5: script chưa hỗ trợ tự đóng lệnh — SL phía broker chỉ là SL ban đầu, cần kiểm tra/đóng thủ công]"
    return False, " [KHÔNG HỖ TRỢ ĐÓNG LỆNH THẬT]"


def process_breakout_paper_trading(item, current_price):
    """
    Xử lý 1 mã của Breakout Radar. Trả về dict:
      {'events': [loại thông báo đã gửi...], 'has_position': bool}
    để bộ quét biết Radar đã thông báo chưa (tránh gửi 2 tin cho cùng 1 sự kiện).
    """
    ctx = {'events': [], 'has_position': False}
    _process_breakout_impl(item, current_price, ctx)
    return ctx


def _radar_notify(ctx, event, *args, **kwargs):
    ctx['events'].append(event)
    insert_triggered_alert(*args, **kwargs)


def _process_breakout_impl(item, current_price, ctx):
    """
    Core Pyramiding Live & Paper Trading Engine:
    - Triggers Pre-Trade Approaching Warning (when price is within 1% of ATH or Next Pyramid target)
    - Triggers Initial Buy upon ATH breakout
    - Pyramids orders (+step_pct mỗi tầng) with pyramid_ratio capital scaling & trailing stop loss
    - Executes automated Stop-Loss (sl_pct per item)
    - If system setting trading_mode == 'real' AND item.is_real_trading, dispatches live trade to Binance / MT5.
      Lệnh thật thất bại => KHÔNG ghi nhận vị thế/lệnh, gửi cảnh báo lỗi và chờ cooldown rồi thử lại.
    """
    w_id, symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct, max_pyramids = item[:10]
    is_real_trading = bool(item[10]) if len(item) > 10 and item[10] is not None else False
    spread_raw = item[11] if len(item) > 11 else None
    spread_pct = float(spread_raw) if (spread_raw is not None and float(spread_raw) > 0) else default_spread_pct(asset_type, symbol)
    sl_mode = str(item[12]).strip().upper() if len(item) > 12 and item[12] else 'TRAILING_PEAK'

    ath_price = float(ath_price or 0)
    initial_budget = float(initial_budget or 0)
    step_pct = float(step_pct or 0)
    pyramid_ratio = float(pyramid_ratio or 0)
    sl_pct = float(sl_pct) if (sl_pct and float(sl_pct) > 0) else 2.0
    max_pyramids = int(max_pyramids or 1)
    current_price = float(current_price)

    if current_price <= 0:
        return

    conn = None
    locked = False
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Chống xử lý song song cùng 1 mã (2 tiến trình, hoặc scanner + monitor cùng lúc)
        cur.execute("SELECT pg_try_advisory_lock(%s, %s);", (_ADVISORY_LOCK_NS, int(w_id)))
        locked = bool(cur.fetchone()[0])
        if not locked:
            print(f"[LIVE TRADE] {symbol} đang được xử lý ở tiến trình khác, bỏ qua lượt này.")
            cur.close()
            return

        # Đọc toàn bộ cấu hình giao dịch trong 1 truy vấn
        market_setting_key = TRADE_TOGGLE_KEYS.get(asset_type)
        keys = ['trading_mode', 'is_live_trade_enabled'] + ([market_setting_key] if market_setting_key else [])
        cur.execute("SELECT key, value FROM public.system_settings WHERE key = ANY(%s);", (keys,))
        settings = {k: (str(v).strip().lower() if v is not None else '') for k, v in cur.fetchall()}
        trading_mode = settings.get('trading_mode', 'demo') or 'demo'
        is_live_trade_enabled = settings.get('is_live_trade_enabled', 'true') != 'false'
        is_market_enabled = settings.get(market_setting_key, 'true') != 'false' if market_setting_key else True
        can_open_orders = is_live_trade_enabled and is_market_enabled

        # Execute real trade only if global mode is 'real' AND this specific item has is_real_trading enabled
        should_execute_real = (trading_mode == 'real' and is_real_trading)

        # Check existing OPEN position
        cur.execute("""
            SELECT id, current_layer, total_invested, total_units, avg_entry_price,
                   last_buy_price, highest_price, stop_loss_price, next_pyramid_price,
                   COALESCE(is_real, false), COALESCE(real_units, 0)
            FROM public.paper_positions
            WHERE watchlist_id = %s AND status = 'OPEN'
            ORDER BY id DESC LIMIT 1;
        """, (w_id,))
        pos_row = cur.fetchone()
        ctx['has_position'] = bool(pos_row)

        currency_symbol = "đ" if asset_type == 'stock_vn' else "$"

        # Always update current_price in public.breakout_watchlist on every scan cycle
        cur.execute("UPDATE public.breakout_watchlist SET current_price = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;", (current_price, w_id))
        conn.commit()

        if not pos_row:
            # === CASE A: NO OPEN POSITION ===
            if ath_price <= 0:
                cur.close()
                return

            # 1. Breakout Trigger: Mở Vị thế Tầng 1 khi giá >= ATH
            if current_price >= ath_price:
                _clear_pretrade_cache(w_id)

                # If Master Auto Trading is OFF or this specific market is OFF, do not open new position!
                if not can_open_orders:
                    cur.close()
                    return

                # RISK GUARD (CIRCUIT BREAKER): >= 3 vị thế cùng nhóm bị cắt lỗ trong hôm nay (giờ VN)
                cur.execute("""
                    SELECT COUNT(*)
                    FROM public.paper_positions
                    WHERE asset_type = %s
                      AND status = 'CLOSED_SL'
                      AND DATE(closed_at AT TIME ZONE 'Asia/Ho_Chi_Minh') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Ho_Chi_Minh');
                """, (asset_type,))
                sl_count_today = cur.fetchone()[0]
                if sl_count_today >= 3:
                    print(f"\n[CIRCUIT BREAKER] Tạm dừng mở vị thế mới cho {symbol} ({asset_type.upper()}): Nhóm này đã có {sl_count_today} vị thế bị cắt lỗ trong ngày hôm nay!\n")
                    cur.close()
                    return

                units, cost = _size_order(asset_type, initial_budget, current_price)
                if units <= 0:
                    if w_id not in _undersized_budget_warned:
                        _undersized_budget_warned.add(w_id)
                        print(f"[LIVE TRADE] Bỏ qua {symbol}: vốn {initial_budget:,.0f}{currency_symbol} không đủ mua 1 lô "
                              f"tại giá {current_price:,.2f}{currency_symbol}. Hãy tăng initial_budget trong breakout_watchlist.")
                    cur.close()
                    return

                entry_price = current_price
                is_real_pos = False
                real_units = 0.0
                real_trade_note = ""
                if should_execute_real:
                    if _real_order_in_cooldown(w_id, 1):
                        cur.close()
                        return
                    r = _execute_real_buy(symbol, asset_type, cost, current_price, sl_pct, 1)
                    real_trade_note = r['note']
                    if r['supported'] and not r['success']:
                        ctx['events'].append('trade_failed'); _report_real_failure(w_id, 1, symbol, asset_type, current_price, "mở vị thế", r.get('error'))
                        cur.close()
                        return
                    if r['success']:
                        is_real_pos = True
                        _real_order_failures.pop((w_id, 1), None)
                        if r.get('entry_price'):
                            entry_price = r['entry_price']
                        real_units = r.get('units') or 0.0
                        if real_units > 0:
                            units = real_units
                            cost = units * entry_price

                stop_loss = entry_price * (1.0 - sl_pct / 100.0)
                breakeven_price = entry_price * (1.0 + spread_pct / 100.0)
                next_pyramid = entry_price * (1.0 + step_pct / 100.0)

                try:
                    cur.execute("""
                        INSERT INTO public.paper_positions (
                            watchlist_id, symbol, asset_type, status, current_layer,
                            total_invested, total_units, avg_entry_price, last_buy_price,
                            highest_price, current_price, stop_loss_price, next_pyramid_price,
                            spread_pct, breakeven_price, sl_mode, is_real, real_units,
                            unrealized_pnl, unrealized_roi_pct, realized_pnl, opened_at, updated_at
                        ) VALUES (
                            %s, %s, %s, 'OPEN', 1,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            0, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        ) RETURNING id;
                    """, (w_id, symbol, asset_type, cost, units, entry_price, entry_price,
                          max(entry_price, current_price), current_price, stop_loss, next_pyramid,
                          spread_pct, breakeven_price, sl_mode, is_real_pos, real_units))
                    pos_id = cur.fetchone()[0]
                    ctx['has_position'] = True
                except psycopg2.IntegrityError:
                    conn.rollback()
                    print(f"[LIVE TRADE] {symbol} đã có vị thế OPEN (unique index), bỏ qua.")
                    cur.close()
                    return

                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'INITIAL_BUY', 1, %s, %s, %s, %s);
                """, (pos_id, symbol, entry_price, cost, units,
                      f"Vượt đỉnh ATH ({ath_price:,.2f}){real_trade_note}"[:100]))

                cur.execute("""
                    UPDATE public.breakout_watchlist
                    SET ath_price = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (max(entry_price, current_price), w_id))
                conn.commit()

                mode_tag = "[LIVE TRADE THẬT]" if is_real_pos else "[DEMO TRADE]"
                msg = (
                    f"{mode_tag} ĐÃ VÀO LỆNH MUA TẦNG 1: {symbol} ({asset_type.upper()}) tại giá {entry_price:,.2f}{currency_symbol} "
                    f"(Vốn: {cost:,.0f}{currency_symbol}, SL: {stop_loss:,.2f}{currency_symbol}){real_trade_note}"
                )
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type, alert_type="executed")
                _radar_notify(ctx, 'initial_buy', asset_type, symbol, entry_price, msg, event_type='initial_buy', is_real=is_real_pos)

            # 2. Pre-Trade Warning: báo khi cách ATH <= 1%, nhắc lại định kỳ khi vẫn cách <= 2% mà chưa vượt
            elif current_price >= ath_price * (1.0 - PRE_TRADE_ZONE_PCT / 100.0):
                if can_open_orders:
                    send, n_remind, waited = _pretrade_due(w_id, 'layer_1', current_price, ath_price,
                                                         max_reminders=PRE_TRADE_MAX_REMINDERS)
                    if send:
                        dist_pct = ((ath_price - current_price) / ath_price) * 100.0
                        expected_sl = ath_price * (1.0 - sl_pct / 100.0)
                        mode_tag = "[CHUẨN BỊ LIVE TRADE]" if should_execute_real else "[CHUẨN BỊ VÀO LỆNH]"
                        if n_remind:
                            mode_tag = (f"[NHẮC LẠI lần {n_remind}/{PRE_TRADE_MAX_REMINDERS}] " if PRE_TRADE_MAX_REMINDERS >= 0
                                        else f"[NHẮC LẠI lần {n_remind}] ") + mode_tag
                        waited_txt = f" Đã chờ {waited:.0f} phút." if n_remind else ""
                        msg = (
                            f"{mode_tag} {symbol} ({asset_type.upper()}) đang ở giá {current_price:,.2f}{currency_symbol} "
                            f"(cách mốc Vượt Đỉnh {ath_price:,.2f}{currency_symbol} chỉ {dist_pct:.2f}%).{waited_txt} "
                            f"Kế hoạch: Vốn {initial_budget:,.0f}{currency_symbol} | SL dự kiến: {expected_sl:,.2f}{currency_symbol}. "
                            f"Sẽ tự động mua khi chạm {ath_price:,.2f}{currency_symbol}."
                        )
                        print(f"\n{msg}\n")
                        play_alert(symbol, asset_type, alert_type="pre_trade")
                        _radar_notify(ctx, 'pre_trade', asset_type, symbol, current_price, msg, event_type='pre_trade')

            # 3. Reset Pre-Trade Cache nếu giá lùi sâu ra xa (> 2%)
            else:
                _pretrade_reset(w_id, 'layer_1')

        else:
            # === CASE B: ACTIVE POSITION ALREADY EXISTS ===
            (pos_id, current_layer, total_invested, total_units, avg_entry_price, last_buy_price,
             highest_price, stop_loss_price, next_pyramid_price, is_real_pos, real_units) = pos_row
            current_layer = int(current_layer)
            total_invested = float(total_invested)
            total_units = float(total_units)
            avg_entry_price = float(avg_entry_price)
            last_buy_price = float(last_buy_price)
            highest_price = float(highest_price)
            stop_loss_price = float(stop_loss_price)
            next_pyramid_price = float(next_pyramid_price)
            is_real_pos = bool(is_real_pos)
            real_units = float(real_units or 0)

            if avg_entry_price <= 0 or total_units <= 0:
                print(f"[LIVE TRADE] Vị thế #{pos_id} {symbol} có dữ liệu không hợp lệ (giá vốn/khối lượng = 0), bỏ qua.")
                cur.close()
                return

            # Update highest price tracked
            new_highest = max(highest_price, current_price)
            if new_highest > ath_price:
                cur.execute("UPDATE public.breakout_watchlist SET ath_price = %s WHERE id = %s;", (new_highest, w_id))

            stop_loss_price, breakeven_price = _compute_stop_loss(
                avg_entry_price, new_highest, current_layer, max_pyramids, sl_pct, spread_pct, sl_mode, stop_loss_price)

            # PnL ròng (đã trừ spread/chi phí khứ hồi): (giá hiện tại - giá hoà vốn) * khối lượng
            unrealized_pnl = (current_price - breakeven_price) * total_units
            unrealized_roi_pct = (unrealized_pnl / total_invested) * 100.0 if total_invested > 0 else 0.0

            cur.execute("""
                UPDATE public.paper_positions
                SET current_price = %s,
                    unrealized_pnl = %s,
                    unrealized_roi_pct = %s,
                    highest_price = %s,
                    stop_loss_price = %s,
                    spread_pct = %s,
                    breakeven_price = %s,
                    sl_mode = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (current_price, unrealized_pnl, unrealized_roi_pct, new_highest, stop_loss_price,
                  spread_pct, breakeven_price, sl_mode, pos_id))
            conn.commit()

            target_pyramid_price = max(last_buy_price * (1.0 + step_pct / 100.0), next_pyramid_price)
            is_breakeven_close = stop_loss_price >= breakeven_price

            # 1. Check STOP-LOSS TRIGGER
            if current_price <= stop_loss_price:
                realized_pnl = (current_price - breakeven_price) * total_units
                if is_breakeven_close:
                    close_reason_tag = "STOP_LOSS_TRAILING" if stop_loss_price > breakeven_price * 1.0001 else "STOP_LOSS_BREAKEVEN"
                else:
                    close_reason_tag = f"STOP_LOSS_AVG_ENTRY_{sl_pct:g}PCT"

                real_sl_note = ""
                real_close_ok = True
                if is_real_pos:
                    real_close_ok, real_sl_note = _close_real_position(symbol, asset_type, real_units or total_units)

                cur.execute("""
                    UPDATE public.paper_positions
                    SET status = 'CLOSED_SL',
                        current_price = %s,
                        highest_price = %s,
                        realized_pnl = %s,
                        unrealized_pnl = 0,
                        closed_at = CURRENT_TIMESTAMP,
                        close_reason = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (current_price, new_highest, realized_pnl, close_reason_tag[:50], pos_id))

                if is_breakeven_close:
                    sl_reason_text = f"Chạm SL bảo toàn {stop_loss_price:,.2f} (hoà vốn {breakeven_price:,.2f}){real_sl_note}"
                else:
                    sl_reason_text = f"Chạm SL {stop_loss_price:,.2f} (-{sl_pct}% từ giá vốn TB {avg_entry_price:,.2f}){real_sl_note}"
                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'STOP_LOSS', %s, %s, %s, %s, %s);
                """, (pos_id, symbol, current_layer, current_price, current_price * total_units, total_units, sl_reason_text[:100]))
                conn.commit()
                _clear_pretrade_cache(w_id)
                ctx['has_position'] = False

                mode_tag = "[LIVE TRADE THẬT]" if is_real_pos else "[DEMO TRADE]"
                if is_breakeven_close:
                    msg = (f"{mode_tag} CẮT LỖ BẢO TOÀN LỢI NHUẬN/VỐN {symbol} ({asset_type.upper()}) tại {current_price:,.2f}{currency_symbol} "
                           f"(SL {stop_loss_price:,.2f}{currency_symbol}, PnL: {realized_pnl:,.2f}{currency_symbol}){real_sl_note}")
                else:
                    msg = (f"{mode_tag} CẮT LỖ THEO GIÁ VỐN TB {symbol} ({asset_type.upper()}) tại {current_price:,.2f}{currency_symbol}: "
                           f"đã giảm {sl_pct}% từ Giá Vốn TB {avg_entry_price:,.2f}{currency_symbol} (PnL: {realized_pnl:,.2f}{currency_symbol}){real_sl_note}")
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type, alert_type="stop_loss")
                _radar_notify(ctx, 'stop_loss', asset_type, symbol, current_price, msg, event_type='stop_loss', is_real=is_real_pos)

                if is_real_pos and not real_close_ok:
                    manual_msg = (f"[CẦN XỬ LÝ THỦ CÔNG] Vị thế THẬT {symbol} ({asset_type.upper()}) đã chạm SL "
                                  f"{stop_loss_price:,.2f} nhưng script không đóng được trên sàn:{real_sl_note}. "
                                  f"Hãy kiểm tra và đóng lệnh trên sàn ngay!")
                    print(f"\n{manual_msg}\n")
                    _radar_notify(ctx, 'manual_action', asset_type, symbol, current_price, manual_msg, event_type='manual_action', is_real=True)

            # 2. Check PYRAMIDING BUY TRIGGER (Khi giá chạm hoặc vượt target_pyramid_price & trong giới hạn max_pyramids)
            elif current_price >= target_pyramid_price and current_layer < max_pyramids:
                new_layer = current_layer + 1

                if not can_open_orders:
                    cur.close()
                    return
                if is_real_pos and not should_execute_real:
                    # Vị thế thật nhưng đã tắt lệnh thật → không nhồi (tránh lệch giữa sổ sách và sàn)
                    cur.close()
                    return
                real_pyramid = is_real_pos and should_execute_real
                if real_pyramid and _real_order_in_cooldown(w_id, new_layer):
                    cur.close()
                    return

                # Calculate next order size: scaled by pyramid_ratio (e.g. 2/3 of previous buy amount)
                next_budget = initial_budget * (pyramid_ratio ** (new_layer - 1))
                new_units, new_cost = _size_order(asset_type, next_budget, current_price)
                if new_units <= 0:
                    cur.close()
                    return

                fill_price = current_price
                real_pyramid_note = ""
                added_real_units = 0.0
                if real_pyramid:
                    r = _execute_real_buy(symbol, asset_type, new_cost, current_price, sl_pct, new_layer)
                    real_pyramid_note = r['note']
                    if not r['success']:
                        ctx['events'].append('trade_failed'); _report_real_failure(w_id, new_layer, symbol, asset_type, current_price, "nhồi lệnh", r.get('error'))
                        cur.close()
                        return
                    _real_order_failures.pop((w_id, new_layer), None)
                    if r.get('entry_price'):
                        fill_price = r['entry_price']
                    added_real_units = r.get('units') or 0.0
                    if added_real_units > 0:
                        new_units = added_real_units
                    new_cost = new_units * fill_price

                _pretrade_reset(w_id, f'layer_{new_layer}')

                new_total_units = total_units + new_units
                new_total_invested = total_invested + new_cost
                new_avg_entry = new_total_invested / new_total_units
                new_highest = max(new_highest, fill_price)
                new_stop_loss, new_breakeven = _compute_stop_loss(
                    new_avg_entry, new_highest, new_layer, max_pyramids, sl_pct, spread_pct, sl_mode, stop_loss_price)
                new_next_pyramid = fill_price * (1.0 + step_pct / 100.0)
                new_unrealized = (current_price - new_breakeven) * new_total_units
                new_roi = (new_unrealized / new_total_invested) * 100.0 if new_total_invested > 0 else 0.0

                cur.execute("""
                    UPDATE public.paper_positions
                    SET current_layer = %s,
                        total_invested = %s,
                        total_units = %s,
                        avg_entry_price = %s,
                        last_buy_price = %s,
                        highest_price = %s,
                        current_price = %s,
                        stop_loss_price = %s,
                        next_pyramid_price = %s,
                        spread_pct = %s,
                        breakeven_price = %s,
                        sl_mode = %s,
                        real_units = real_units + %s,
                        unrealized_pnl = %s,
                        unrealized_roi_pct = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (new_layer, new_total_invested, new_total_units, new_avg_entry, fill_price,
                      new_highest, current_price, new_stop_loss, new_next_pyramid,
                      spread_pct, new_breakeven, sl_mode, added_real_units,
                      new_unrealized, new_roi, pos_id))

                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'PYRAMID_BUY', %s, %s, %s, %s, %s);
                """, (pos_id, symbol, new_layer, fill_price, new_cost, new_units,
                      f"Nhồi lệnh Tầng {new_layer} (+{step_pct}% từ lần trước {last_buy_price:,.2f}){real_pyramid_note}"[:100]))
                conn.commit()

                mode_tag = "[LIVE TRADE THẬT]" if real_pyramid else "[DEMO TRADE]"
                msg = (
                    f"{mode_tag} [ĐÃ NHỒI LỆNH TẦNG {new_layer}] {symbol} ({asset_type.upper()}) tại giá {fill_price:,.2f}{currency_symbol} "
                    f"(+{step_pct}% so với lần trước, vốn thêm {new_cost:,.0f}{currency_symbol}, SL mới: {new_stop_loss:,.2f}{currency_symbol}){real_pyramid_note}"
                )
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type, alert_type="executed")
                _radar_notify(ctx, 'pyramid_buy', asset_type, symbol, fill_price, msg, event_type='pyramid_buy', is_real=real_pyramid)

            # 3. Pre-Trade Warning: tiệm cận mốc nhồi tầng tiếp theo (báo khi cách <= 1%, nhắc lại khi vẫn cách <= 2%)
            elif current_layer < max_pyramids and target_pyramid_price > 0 and \
                    current_price >= target_pyramid_price * (1.0 - PRE_TRADE_ZONE_PCT / 100.0):
                next_layer = current_layer + 1
                send, n_remind, waited = (False, 0, 0.0)
                if can_open_orders:
                    send, n_remind, waited = _pretrade_due(w_id, f'layer_{next_layer}', current_price, target_pyramid_price,
                                                         max_reminders=PRE_PYRAMID_MAX_REMINDERS)
                if send:
                    dist_pct = ((target_pyramid_price - current_price) / target_pyramid_price) * 100.0
                    next_budget = initial_budget * (pyramid_ratio ** (next_layer - 1))
                    real_next = is_real_pos and should_execute_real
                    mode_tag = "[CHUẨN BỊ NHỒI LIVE TRADE]" if real_next else "[CHUẨN BỊ NHỒI LỆNH]"
                    if n_remind:
                        mode_tag = f"[NHẮC LẠI lần {n_remind}] " + mode_tag
                    waited_txt = f" Đã chờ {waited:.0f} phút." if n_remind else ""
                    msg = (
                        f"{mode_tag} TẦNG {next_layer}: {symbol} ({asset_type.upper()}) đang ở giá {current_price:,.2f}{currency_symbol} "
                        f"(cách mốc nhồi lệnh {target_pyramid_price:,.2f}{currency_symbol} chỉ {dist_pct:.2f}%).{waited_txt} "
                        f"Dự kiến nhồi thêm {next_budget:,.0f}{currency_symbol} khi chạm {target_pyramid_price:,.2f}{currency_symbol}."
                    )
                    print(f"\n{msg}\n")
                    play_alert(symbol, asset_type, alert_type="pre_trade")
                    _radar_notify(ctx, 'pre_pyramid', asset_type, symbol, current_price, msg, event_type='pre_pyramid')

            # 4. Reset Pre-Trade Cache cho tầng nhồi nếu giá lùi sâu (> 2%)
            elif current_layer < max_pyramids and target_pyramid_price > 0:
                _pretrade_reset(w_id, f'layer_{current_layer + 1}')

        cur.close()
    except Exception as e:
        print(f"Lỗi xử lý paper trading breakout cho {symbol}: {e}")
    finally:
        if conn:
            if locked:
                try:
                    conn.rollback()
                    c2 = conn.cursor()
                    c2.execute("SELECT pg_advisory_unlock(%s, %s);", (_ADVISORY_LOCK_NS, int(w_id)))
                    c2.close()
                    conn.commit()
                except Exception:
                    pass
            conn.close()


def auto_trigger_breakout_paper_trade(symbol, asset_type, current_price, ath_price=None, name=None):
    """
    Called by market scanners when a symbol reaches >= 99% of ATH.
    Trả về kết quả của Radar (xem process_breakout_paper_trading) hoặc None.
    - Thêm mã vào breakout_watchlist nếu chưa có (với spread/vốn mặc định theo loại tài sản).
    - KHÔNG bật lại mã người dùng đã tắt (is_active = false).
    - Nâng ath_price lên mốc đỉnh mới nhất của scanner nếu đang không có vị thế (tránh mốc đỉnh cũ quá thấp).
    """
    if not symbol or not current_price or current_price <= 0:
        return
    clean_sym = symbol.split(':')[-1] if ':' in symbol else symbol
    clean_sym = clean_sym.upper().strip()
    ath = float(ath_price) if (ath_price and ath_price > 0) else float(current_price)
    budget = BREAKOUT_DEFAULT_BUDGET_VND if asset_type == 'stock_vn' else BREAKOUT_DEFAULT_BUDGET_USD

    conn = None
    row = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.breakout_watchlist (
                symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct,
                sl_mode, max_pyramids, is_active, is_real_trading, spread_pct
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'TRAILING_PEAK', %s, true, false, %s)
            ON CONFLICT (symbol, asset_type) DO NOTHING;
        """, (clean_sym, asset_type, name or clean_sym, ath, budget,
              BREAKOUT_DEFAULT_STEP_PCT, BREAKOUT_DEFAULT_PYRAMID_RATIO, BREAKOUT_DEFAULT_SL_PCT,
              BREAKOUT_DEFAULT_MAX_PYRAMIDS, default_spread_pct(asset_type, clean_sym)))

        cur.execute("""
            UPDATE public.breakout_watchlist w
            SET ath_price = GREATEST(w.ath_price, %s), updated_at = CURRENT_TIMESTAMP
            WHERE w.symbol = %s AND w.asset_type = %s
              AND w.ath_price < %s
              AND NOT EXISTS (
                  SELECT 1 FROM public.paper_positions p
                  WHERE p.watchlist_id = w.id AND p.status = 'OPEN'
              );
        """, (ath, clean_sym, asset_type, ath))

        cur.execute(f"""
            SELECT {BREAKOUT_ITEM_COLUMNS}
            FROM public.breakout_watchlist
            WHERE symbol = %s AND asset_type = %s AND is_active = true;
        """, (clean_sym, asset_type))
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Lỗi auto_trigger_breakout_paper_trade cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

    if not row:
        return None  # mã không được Radar theo dõi (người dùng đã tắt) → bộ quét tự thông báo
    result = process_breakout_paper_trading(row, current_price)
    result['w_id'] = row[0]
    result['pretrade_active'] = (row[0], 'layer_1') in last_pre_trade_alerts
    return result


def _is_market_open_for(asset_type):
    """Chỉ xử lý giao dịch khi thị trường mở, tránh hành động trên giá cũ."""
    if asset_type == 'stock_vn':
        return is_vn_stock_market_open()
    if asset_type == 'stock_us':
        return is_us_stock_market_open()
    if asset_type in ('forex', 'commodity', 'commodities'):
        return is_fx_market_open()
    return True  # crypto / futures 24/7


def monitor_breakout_paper_trading_step():
    """Polls real-time prices and runs automated Pyramiding trade logic for all active breakout watchlist items"""
    conn = None
    items = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT {BREAKOUT_ITEM_COLUMNS}
            FROM public.breakout_watchlist
            WHERE is_active = true;
        """)
        items = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"Lỗi lấy danh sách breakout_watchlist: {e}")
    finally:
        if conn:
            conn.close()

    # Dọn cache cảnh báo của các mã không còn active
    active_ids = {it[0] for it in items}
    for key in [k for k in last_pre_trade_alerts if k[0] not in active_ids]:
        last_pre_trade_alerts.pop(key, None)

    items = [it for it in items if _is_market_open_for(it[2])]
    if not items:
        return

    print(f"[LIVE TRADE] Đang quét {len(items)} mã theo dõi ATH & Vị thế Paper Trading...")

    def fetch_item_price(item):
        return item, fetch_live_price_for_breakout(item[1], item[2])

    # Fetch independent symbols concurrently so a slow Yahoo/KBS request does not
    # prevent crypto positions later in the list from receiving a fresh price.
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as executor:
        futures = [executor.submit(fetch_item_price, item) for item in items]
        for future in as_completed(futures):
            try:
                item, price = future.result()
                if price is not None and price > 0:
                    process_breakout_paper_trading(item, price)
            except Exception as e:
                print(f"Lỗi cập nhật giá Live Trade: {e}")


def main():
    print("Bắt đầu khởi tạo dịch vụ Báo Động Vượt Đỉnh & Paper/Live Trading (Breakout Radar)...")
    init_breakout_paper_trade_tables()
    init_economic_calendar_table()
    if _holidays_lib is None and not (_VN_EXTRA_HOLIDAYS or _US_EXTRA_HOLIDAYS):
        print("ℹ️  Chưa cài thư viện 'holidays' và chưa khai báo VN_MARKET_HOLIDAYS / US_MARKET_HOLIDAYS "
              "→ chưa lọc được ngày lễ (pip install holidays).")
    print("Mô hình hoạt động:")
    print("  • Stocks VN: T2-T6, 09:00-11:30 & 13:00-14:45 (UTC+7), trừ ngày lễ. Dựa trên symbols_watchlist.")
    print("  • Stocks US: T2-T6 (09:30 - 16:00 ET), trừ ngày lễ. Dựa trên world_symbols_watchlist (Mỹ).")
    print("  • Cryptos Spot: Quét 24/7 hàng ngày. Dựa trên cryptos_watchlist.")
    print("  • Cryptos Futures: Quét 24/7 hàng ngày. Dựa trên futures_watchlist.")
    print("  • Commodities / Forex / Yields: CN 17:00 ET → T6 17:00 ET.")
    print("  • Breakout Radar: Quản lý vị thế nhồi lệnh cho breakout_watchlist (theo giờ của từng thị trường).")

    # State caches in memory to prevent duplicate alarms — TÁCH RIÊNG theo thị trường
    # (trước đây Spot và Futures dùng chung 1 dict nên BTCUSDT bên này chặn cảnh báo bên kia)
    # Lưu vào DB (alert_dedupe_state) → khởi động lại không báo lại các mã đang ở gần đỉnh
    last_alerted_prices_vn = PersistentCache('scan_vn')
    last_alerted_prices_us = PersistentCache('scan_us')
    last_alerted_prices_crypto = PersistentCache('scan_crypto')
    last_alerted_prices_futures = PersistentCache('scan_futures')
    last_alerted_prices_commodities = PersistentCache('scan_commodities')
    last_alerted_prices_forex = PersistentCache('scan_forex')
    last_alerted_yields = PersistentCache('scan_yields')

    while True:
        try:
            # Ping database to let the UI know script is alive
            update_heartbeat()

            # Dọn dẹp bảng triggered_alerts cũ
            cleanup_triggered_alerts()

            # 0. Breakout Radar & Pyramiding Paper Trading Scan Cycle
            monitor_breakout_paper_trading_step()

            # Query real-time system scan toggles from the database
            toggles = get_scan_toggles()

            # 1. Stocks VN
            if toggles['scan_stock_vn']:
                vn_now = get_vn_time()
                if is_vn_stock_market_open(vn_now):
                    stock_watchlist = get_watchlist_symbols()
                    if stock_watchlist:
                        monitor_stocks_step(stock_watchlist, last_alerted_prices_vn)
                    else:
                        print("Không có cổ phiếu VN nào đạt đủ 3 tín hiệu trong symbols_watchlist.")
                else:
                    print(f"Ngoài giờ giao dịch Stock VN. Hiện tại: {vn_now.strftime('%d/%m %H:%M:%S')} UTC+7. Tạm ngưng quét VN.")
            else:
                print("Tắt quét Stock VN (theo cấu hình hệ thống).")

            # 2. US Stocks
            if toggles['scan_stock_us']:
                us_now = get_us_time()
                if is_us_stock_market_open(us_now):
                    us_watchlist = get_us_watchlist_symbols()
                    if us_watchlist:
                        monitor_us_stocks_step(us_watchlist, last_alerted_prices_us)
                    else:
                        print("Không có cổ phiếu Mỹ nào trong world_symbols_watchlist.")
                else:
                    print(f"Ngoài giờ giao dịch Stock US. Hiện tại: {us_now.strftime('%d/%m %H:%M:%S')} ET. Tạm ngưng quét US.")
            else:
                print("Tắt quét Stock US (theo cấu hình hệ thống).")

            # 3. Cryptos Spot (24/7)
            if toggles['scan_crypto']:
                crypto_watchlist = get_watchlist_cryptos()
                if crypto_watchlist:
                    monitor_cryptos_step(crypto_watchlist, last_alerted_prices_crypto)
                else:
                    print("Không có crypto nào trong cryptos_watchlist.")
            else:
                print("Tắt quét Crypto Spot (theo cấu hình hệ thống).")

            # 4. Cryptos Futures (24/7)
            if toggles['scan_futures']:
                futures_watchlist = get_watchlist_futures()
                if futures_watchlist:
                    monitor_futures_step(futures_watchlist, last_alerted_prices_futures)
                else:
                    print("Không có futures nào trong futures_watchlist.")
            else:
                print("Tắt quét Crypto Futures (theo cấu hình hệ thống).")

            fx_open = is_fx_market_open()
            us_now_str = get_us_time().strftime('%d/%m %H:%M:%S')

            # 5. Commodities
            if toggles.get('scan_commodities', True):
                if fx_open:
                    monitor_commodities_step(COMMODITIES_SYMBOLS, last_alerted_prices_commodities)
                else:
                    print(f"Ngoài giờ giao dịch Commodities. Hiện tại: {us_now_str} ET. Tạm ngưng quét Commodities.")
            else:
                print("Tắt quét Commodities (theo cấu hình hệ thống).")

            # 6. Forex
            if toggles.get('scan_forex', True):
                if fx_open:
                    forex_watchlist = get_watchlist_forex()
                    if forex_watchlist:
                        monitor_forex_step(forex_watchlist, last_alerted_prices_forex)
                    else:
                        print("Không có forex nào trong forex_watchlist.")
                else:
                    print(f"Ngoài giờ giao dịch Forex. Hiện tại: {us_now_str} ET. Tạm ngưng quét Forex.")
            else:
                print("Tắt quét Forex (theo cấu hình hệ thống).")

            # 7. Treasury Yields
            if toggles.get('scan_yields', True):
                if fx_open:
                    monitor_yields_step(YIELD_SYMBOLS, last_alerted_yields)
                else:
                    print(f"Ngoài giờ giao dịch Treasury Yields. Hiện tại: {us_now_str} ET. Tạm ngưng quét Yields.")
            else:
                print("Tắt quét Treasury Yields (theo cấu hình hệ thống).")

            # 8. Smart Economic Calendar Poller (Micro-polling when events are active)
            monitor_economic_calendar_step()

            # 9. Print separators and sleep for 15 seconds
            print(f"Lượt quét hoàn thành lúc {datetime.now().strftime('%H:%M:%S')}. Nghỉ 15 giây...\n")
            time.sleep(15)

        except KeyboardInterrupt:
            print("\nDừng dịch vụ Báo Động. Hẹn gặp lại!")
            sys.exit(0)
        except Exception as e:
            print(f"Lỗi hệ thống: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
