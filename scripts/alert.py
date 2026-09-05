#!/usr/bin/env python3
import time
import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import psycopg2
from vnstock import Quote

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

# Setup cross-platform Beep alert sound
try:
    import winsound
    def play_alert(symbol, asset_type):
        winsound.Beep(800, 250)  # Frequency 800Hz, duration 250ms
        print(f">>> CẢNH BÁO: PHÁT HIỆN LỆNH LỚN CHO {symbol} ({asset_type.upper()})! <<<")
except ImportError:
    # Fallback for macOS/Linux using terminal bell
    def play_alert(symbol, asset_type):
        print("\a", end="", flush=True)  # Terminal bell
        print(f">>> CẢNH BÁO: PHÁT HIỆN LỆNH LỚN CHO {symbol} ({asset_type.upper()})! <<<")

def get_db_connection():
    """Create database connection using environment variables"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'trading'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

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
                toggles[key] = (val.lower() == 'true')
        cur.close()
    except Exception as e:
        # Default to True on failure
        pass
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
        pass
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

def monitor_us_stocks_step(us_symbols, last_alerted_prices):
    """Performs one scan cycle on the list of US stock symbols using Yahoo Finance"""
    if not us_symbols:
        return

    print(f"🔍 [US STOCK] Đang quét {list(us_symbols.keys())}...")
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
            check_custom_stock_alerts(symbol, current_price)

            # Check if US stock price is breaking/approaching the 52-week high (within 1%)
            if current_price >= fifty_two_high * 0.99:
                last_price = last_alerted_prices.get(symbol, 0.0)
                # Only alert on first breakout OR when price reaches a new higher high (>= +0.5%)
                if last_price == 0.0 or current_price >= last_price * 1.005:
                    clean_sym = symbol.split(":")[-1] if ":" in symbol else symbol
                    message = f"Cảnh báo Stock US: Cổ phiếu {clean_sym} đã tiệm cận hoặc vượt đỉnh 52 tuần tại ${current_price:,.2f}."
                    print(f"🚨 [US Stock Breakout] {clean_sym} tại giá ${current_price:,.2f} >= 99% Đỉnh 52 tuần ${fifty_two_high:,.2f}")
                    play_alert(clean_sym, "stock")
                    insert_triggered_alert("stock", clean_sym, current_price, message)
                    last_alerted_prices[symbol] = current_price
                    auto_trigger_breakout_paper_trade(clean_sym, "stock_us", current_price, fifty_two_high)

            time.sleep(0.3)  # Avoid rate limiting
        except Exception as e:
            print(f"⚠️ Lỗi quét US stock {symbol}: {e}")


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
            print("🔔 Đã gửi cảnh báo thành công qua Slack!")
        else:
            print(f"⚠️ Lỗi gửi Slack: status={res.status_code}")
    except Exception as e:
        print(f"⚠️ Lỗi kết nối gửi Slack: {e}")

def insert_triggered_alert(asset_type, symbol, price, message):
    """Log the alert to public.triggered_alerts so the web UI reads it in real-time"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete any previous alerts for the same symbol to keep only the single latest message
        cur.execute("DELETE FROM public.triggered_alerts WHERE symbol = %s;", (symbol,))
        
        query = """
        INSERT INTO public.triggered_alerts (asset_type, symbol, price, message, is_read)
        VALUES (%s, %s, %s, %s, false);
        """
        cur.execute(query, (asset_type, symbol, price, message))
        conn.commit()
        cur.close()
        print(f"💾 Đã cập nhật báo động mới nhất cho {symbol} ({asset_type}) vào website database!")
        
        # Send to Slack if enabled
        send_slack_message(message)
    except Exception as e:
        print(f"❌ Lỗi ghi triggered_alert vào DB: {e}")
    finally:
        if conn:
            conn.close()

def cleanup_triggered_alerts():
    """Dọn dẹp bảng triggered_alerts:
    - Xóa các bản ghi quá 5 ngày
    - Giữ tối đa 200 bản ghi mới nhất
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Xóa bản ghi quá 5 ngày
        cur.execute("DELETE FROM public.triggered_alerts WHERE created_at < NOW() - INTERVAL '5 days';")
        deleted_old = cur.rowcount

        # Nếu còn hơn 200 bản ghi, xóa các bản ghi cũ nhất, chỉ giữ 200 bản ghi mới nhất
        cur.execute("""
            DELETE FROM public.triggered_alerts
            WHERE id IN (
                SELECT id FROM public.triggered_alerts
                ORDER BY created_at DESC
                OFFSET 200
            );
        """)
        deleted_excess = cur.rowcount

        total_deleted = deleted_old + deleted_excess
        if total_deleted > 0:
            print(f"🧹 Đã dọn dẹp {total_deleted} bản ghi cũ từ triggered_alerts ({deleted_old} quá hạn, {deleted_excess} vượt giới hạn).")

        conn.commit()
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi dọn dẹp triggered_alerts: {e}")
    finally:
        if conn:
            conn.close()

def monitor_stocks_step(symbols, last_processed_time, last_alerted_breakout_prices, threshold=5000):
    """Performs one scan cycle on VN stock symbols for price breakouts (New Higher High)"""
    if not symbols:
        return
    
    print(f"🔍 [STOCK VN] Đang quét {list(symbols.keys())}...")
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
            check_custom_stock_alerts(symbol, current_price_vnd)
            
            # 2. Check for price breakout (Only alert on first breakout OR when price reaches a new higher high >= +0.5%)
            if highest_price > 0 and current_price_vnd >= highest_price * 0.99:
                last_price = last_alerted_breakout_prices.get(symbol, 0.0)
                if last_price == 0.0 or current_price_vnd >= last_price * 1.005:
                    clean_sym = symbol.split(':')[-1] if ':' in symbol else symbol
                    message = f"Cảnh báo Chứng khoán Việt Nam: Cổ phiếu {clean_sym} đã "
                    if current_price_vnd > highest_price:
                        message = message + f"vượt đỉnh ở mức {current_price_vnd:,.0f}đ."
                    else:
                        message = message + f"tiệm cận đỉnh ở mức {current_price_vnd:,.0f}đ."
                    print(f"🚨 [VN Stock Breakout] {clean_sym} tại {current_price_vnd:,.0f}đ (Đỉnh cũ: {highest_price:,.0f}đ)")
                    play_alert(clean_sym, "stock")
                    insert_triggered_alert("stock", clean_sym, current_price_vnd, message)
                    last_alerted_breakout_prices[symbol] = current_price_vnd
                    auto_trigger_breakout_paper_trade(clean_sym, "stock_vn", current_price_vnd, highest_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét stock {symbol}: {e}")

def monitor_cryptos_step(cryptos, last_processed_trade_ids, last_alerted_breakout_prices, threshold_usd=10000.0):
    """Performs one scan cycle on Binance spot cryptos for price breakouts (New Higher High)"""
    if not cryptos:
        return

    print(f"🔍 [CRYPTO] Đang quét {list(cryptos.keys())}...")
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
            if highest_price > 0 and current_price >= highest_price * 0.99:
                last_price = last_alerted_breakout_prices.get(crypto, 0.0)
                if last_price == 0.0 or current_price >= last_price * 1.005:
                    message = f"Cảnh báo tiền điện tử: Coin {crypto} đã "
                    if current_price > highest_price:
                        message = message + f"vượt đỉnh ở mức ${current_price:,.4f}."
                    else:
                        message = message + f"tiệm cận đỉnh ở mức ${current_price:,.4f}."
                    print(f"🚨 [Crypto Breakout] {crypto} tại {current_price} >= 99% Đỉnh cũ {highest_price}")
                    play_alert(crypto, "crypto")
                    insert_triggered_alert("crypto", crypto, current_price, message)
                    last_alerted_breakout_prices[crypto] = current_price
                    auto_trigger_breakout_paper_trade(crypto, "crypto", current_price, highest_price)
            
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét crypto {crypto}: {e}")

def monitor_futures_step(futures, last_processed_trade_ids, last_alerted_breakout_prices, threshold_usd=10000.0):
    """Performs one scan cycle on Binance Futures contracts for price breakouts (New Higher High)"""
    if not futures:
        return

    print(f"🔍 [FUTURES] Đang quét {list(futures.keys())}...")
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
            if highest_price > 0 and current_price >= highest_price * 0.99:
                last_price = last_alerted_breakout_prices.get(symbol, 0.0)
                if last_price == 0.0 or current_price >= last_price * 1.005:
                    message = f"Cảnh báo phái sinh {symbol} đã "
                    if current_price >= highest_price:
                        message = message + f"vượt đỉnh cũ ở mức ${current_price:,.4f}."
                    else:
                        message = message + f"tiệm cận đỉnh cũ ở mức ${current_price:,.4f}."
                    print(f"🚨 [Futures Breakout] {symbol} tại {current_price} tiệm cận hoặc vượt đỉnh cũ {highest_price}")
                    play_alert(symbol, "futures")
                    insert_triggered_alert("futures", symbol, current_price, message)
                    last_alerted_breakout_prices[symbol] = current_price
                    auto_trigger_breakout_paper_trade(symbol, "futures", current_price, highest_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét futures {symbol}: {e}")

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
        print(f"⚠️ Error fetching from TradingView scanner: {e}")
    return results

YIELD_SYMBOLS = {
    # US
    '^IRX': 'US02Y',
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

def check_custom_yield_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this yield"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check alerts with asset_type = 'yield'
        cur.execute("""
            SELECT alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = 'yield' 
            AND symbol = %s 
            AND is_active = true;
        """, (symbol,))
        
        alerts = cur.fetchall()
        for alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    message = f"Cảnh báo Lợi suất: {emoji} Lợi suất trái phiếu {symbol} đã {condition} mức {current_price:.3f}%."
                    print(f"🚨 [Yield Price Alert Triggered] {symbol} tại {current_price:.3f}% kích hoạt {operator} {alert_price:.3f}%")
                    
                    play_alert(symbol, "yield")
                    insert_triggered_alert("yield", symbol, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = 'yield';
                    """, (symbol,))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom yield alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def check_custom_crypto_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this crypto"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check alerts with asset_type = 'crypto'
        clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
        cur.execute("""
            SELECT symbol, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = 'crypto' 
            AND (symbol = %s OR symbol = %s) 
            AND is_active = true;
        """, (symbol, clean_symbol))
        
        alerts = cur.fetchall()
        for alert_symbol, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    message = f"Cảnh báo Crypto: {emoji} Giá {alert_symbol} đã {condition} mức {alert_price} (Giá hiện tại: {current_price})."
                    print(f"🚨 [Crypto Price Alert Triggered] {alert_symbol} tại {current_price} kích hoạt {operator} {alert_price}")
                    
                    play_alert(alert_symbol, "crypto")
                    insert_triggered_alert("crypto", alert_symbol, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = 'crypto';
                    """, (alert_symbol,))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom crypto alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def check_custom_futures_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this futures contract"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check alerts with asset_type = 'futures'
        clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
        cur.execute("""
            SELECT symbol, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = 'futures' 
            AND (symbol = %s OR symbol = %s) 
            AND is_active = true;
        """, (symbol, clean_symbol))
        
        alerts = cur.fetchall()
        for alert_symbol, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    message = f"Cảnh báo Futures: {emoji} Giá hợp đồng {alert_symbol} đã {condition} mức {alert_price} (Giá hiện tại: {current_price})."
                    print(f"🚨 [Futures Price Alert Triggered] {alert_symbol} tại {current_price} kích hoạt {operator} {alert_price}")
                    
                    play_alert(alert_symbol, "futures")
                    insert_triggered_alert("futures", alert_symbol, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = 'futures';
                    """, (alert_symbol,))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom futures alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def check_custom_stock_alerts(symbol, current_price):
    """Check if any user price alerts in the database are triggered for this stock"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check alerts with asset_type = 'stock'
        clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
        cur.execute("""
            SELECT symbol, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = 'stock' 
            AND (symbol = %s OR symbol = %s) 
            AND is_active = true;
        """, (symbol, clean_symbol))
        
        alerts = cur.fetchall()
        for alert_symbol, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    message = f"Cảnh báo Cổ phiếu: {emoji} Giá {alert_symbol} đã {condition} mức {alert_price} (Giá hiện tại: {current_price})."
                    print(f"🚨 [Stock Price Alert Triggered] {alert_symbol} tại {current_price} kích hoạt {operator} {alert_price}")
                    
                    play_alert(alert_symbol, "stock")
                    insert_triggered_alert("stock", alert_symbol, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = 'stock';
                    """, (alert_symbol,))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom stock alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def monitor_yields_step(yield_symbols, last_alerted_yields):
    """Performs one scan cycle on Treasury Yields using yfinance (with HTTP fallback) or TradingView scanner"""
    if not yield_symbols:
        return

    print(f"🔍 [YIELDS] Đang quét {list(yield_symbols.values())}...")
    
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
                        print(f"⚠️ yfinance library error for {symbol}: {yfe}. Trying HTTP fallback...")
                
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
            if current_price >= fifty_two_high * 0.99:
                last_price = last_alerted_yields.get(symbol, 0.0)
                # Only alert on first breakout OR when yield reaches a new higher high (>= +0.005%)
                if last_price == 0.0 or current_price >= last_price + 0.005:
                    country = "Mỹ"
                    if symbol.startswith("JP"):
                        country = "Nhật Bản"
                    elif symbol.startswith("GB"):
                        country = "Anh"
                    elif symbol.startswith("DE"):
                        country = "Đức (Châu Âu)"
                        
                    message = f"Cảnh báo Lợi suất: Lợi suất trái phiếu Chính phủ {country} {symbol} đã tiệm cận hoặc vượt đỉnh 52 tuần tại mức {current_price:.3f}%."
                    print(f"🚨 [Yield Breakout] {symbol} ({country}) tại lợi suất {current_price:.3f}% >= 99% Đỉnh 52 tuần {fifty_two_high:.3f}%")
                    play_alert(symbol, "yield")
                    insert_triggered_alert("yield", symbol, current_price, message)
                    last_alerted_yields[symbol] = current_price

            # Check custom user-configured alerts
            check_custom_yield_alerts(symbol, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét yield {symbol}: {e}")

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
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        aliases = list(set(COMMODITY_ALIASES.get(symbol, [symbol]) + [symbol]))
        asset_types = ['commodities', 'commodity', 'gold', 'silver', 'oil', 'forex']
        
        cur.execute("""
            SELECT symbol, asset_type, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = ANY(%s) 
            AND symbol = ANY(%s) 
            AND is_active = true;
        """, (asset_types, aliases))
        
        alerts = cur.fetchall()
        for alert_symbol, alert_asset_type, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    display_sym = 'XAUUSD' if symbol == 'GC=F' else ('XAGUSD' if symbol == 'SI=F' else alert_symbol)
                    message = f"Cảnh báo Hàng hóa: {emoji} {name} ({display_sym}) đã {condition} mức giá ${current_price:,.2f}."
                    print(f"🚨 [Commodity Price Alert Triggered] {name} at {current_price} triggers {operator} {alert_price}")
                    
                    play_alert(display_sym, "commodities")
                    insert_triggered_alert("commodities", display_sym, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = %s;
                    """, (alert_symbol, alert_asset_type))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom commodity alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def monitor_commodities_step(commodities_symbols, last_alerted_prices):
    """Performs one scan cycle on global commodities using Yahoo Finance"""
    if not commodities_symbols:
        return

    print(f"🔍 [COMMODITIES] Đang quét {list(commodities_symbols.keys())}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for symbol, name in commodities_symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
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

            if current_price is None:
                continue

            # Calculate 30-day recent high from daily candles (excluding current in-progress candle)
            quotes = results[0].get("indicators", {}).get("quote", [{}])[0]
            highs = [h for h in quotes.get("high", []) if h is not None]
            recent_high = max(highs[:-1]) if len(highs) > 1 else (max(highs) if highs else fifty_two_high)

            display_sym = 'XAUUSD' if symbol == 'GC=F' else ('XAGUSD' if symbol == 'SI=F' else symbol)

            # 1. Check for 30-day Recent High Breakout (check within 1%)
            if recent_high and recent_high > 0 and current_price >= recent_high * 0.99:
                last_price = last_alerted_prices.get(symbol, 0.0)
                # Only alert on first breakout OR when price reaches a new higher high (>= +0.3%)
                if last_price == 0.0 or current_price >= last_price * 1.003:
                    message = f"Cảnh báo Hàng hóa: {name} đã tiệm cận hoặc vượt đỉnh gần nhất ở mức ${current_price:,.2f} (Đỉnh cũ: ${recent_high:,.2f})."
                    print(f"🚨 [Commodity Breakout] {name} tại giá ${current_price:,.2f} >= 99% Đỉnh gần nhất ${recent_high:,.2f}")
                    play_alert(display_sym, "commodities")
                    insert_triggered_alert("commodities", display_sym, current_price, message)
                    last_alerted_prices[symbol] = current_price

            # 2. Check for 52-Week High Breakout (check within 1%)
            elif fifty_two_high and fifty_two_high > 0 and current_price >= fifty_two_high * 0.99:
                last_price = last_alerted_prices.get(symbol, 0.0)
                if last_price == 0.0 or current_price >= last_price * 1.003:
                    message = f"Cảnh báo Hàng hóa: {name} ({display_sym}) đã tiệm cận hoặc vượt đỉnh 52 tuần tại ${current_price:,.2f}."
                    print(f"🚨 [Commodity 52W Breakout] {name} ({display_sym}) tại giá ${current_price:,.2f} >= 99% Đỉnh 52 tuần ${fifty_two_high:,.2f}")
                    play_alert(display_sym, "commodities")
                    insert_triggered_alert("commodities", display_sym, current_price, message)
                    last_alerted_prices[symbol] = current_price

            # 3. Check for custom user-configured alerts
            check_custom_commodity_alerts(symbol, name, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét commodity {symbol}: {e}")

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
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
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
        
        asset_types = ['forex', 'commodities', 'commodity', 'gold', 'silver']
        
        cur.execute("""
            SELECT symbol, asset_type, alert_price, operator, last_notified_at
            FROM public.price_alerts
            WHERE asset_type = ANY(%s) 
            AND symbol = ANY(%s) 
            AND is_active = true;
        """, (asset_types, list(set(aliases))))
        
        alerts = cur.fetchall()
        for alert_symbol, alert_asset_type, alert_price, operator, last_notified_at in alerts:
            alert_price = float(alert_price)
            alert_triggered = False
            
            if operator == '<=':
                alert_triggered = current_price <= (alert_price * 1.01)
                condition = "giảm xuống dưới hoặc bằng"
                emoji = "🔻"
            elif operator == '>=':
                alert_triggered = current_price >= (alert_price * 0.99)
                condition = "tăng lên trên hoặc bằng"
                emoji = "🚀"

            if alert_triggered:
                should_notify = True
                if last_notified_at:
                    now = datetime.now(timezone.utc)
                    last_notified = last_notified_at.astimezone(timezone.utc) if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=timezone.utc)
                    if now - last_notified < timedelta(hours=1):
                        should_notify = False

                if should_notify:
                    price_diff = ((current_price - alert_price) / alert_price) * 100
                    message = f"Cảnh báo Forex: {emoji} Cặp tiền {pair_name} ({symbol}) đã {condition} mức giá {current_price:,.4f}."
                    print(f"🚨 [Forex Price Alert Triggered] {pair_name} tại {current_price} kích hoạt {operator} {alert_price}")
                    
                    play_alert(pair_name, "forex")
                    insert_triggered_alert("forex", pair_name, current_price, message)
                    
                    cur.execute("""
                        UPDATE public.price_alerts
                        SET last_notified_at = CURRENT_TIMESTAMP
                        WHERE symbol = %s AND asset_type = %s;
                    """, (alert_symbol, alert_asset_type))
                    conn.commit()
                    
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi check custom forex alerts cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def monitor_forex_step(forex_pairs, last_alerted_prices):
    """Performs one scan cycle on forex pairs using Yahoo Finance"""
    if not forex_pairs:
        return

    # Skip commodity pairs already handled in monitor_commodities_step to avoid duplicate alerts
    commodity_pairs = {'XAUUSD', 'XAGUSD', 'WTI', 'USOIL', 'UKOIL', 'BRENT'}
    filtered_pairs = {k: v for k, v in forex_pairs.items() if k.upper() not in commodity_pairs}
    if not filtered_pairs:
        return

    print(f"🔍 [FOREX] Đang quét {list(filtered_pairs.keys())}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for pair in filtered_pairs:
        try:
            # Map standard pair to Yahoo Finance symbol
            symbol = map_forex_symbol_to_yahoo(pair)
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
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

            if current_price is None:
                continue

            # Calculate 30-day recent high from daily candles (excluding current in-progress candle)
            quotes = results[0].get("indicators", {}).get("quote", [{}])[0]
            highs = [h for h in quotes.get("high", []) if h is not None]
            recent_high = max(highs[:-1]) if len(highs) > 1 else (max(highs) if highs else fifty_two_high)

            # 1. Check for 30-day Recent High Breakout (check within 1%)
            if recent_high and recent_high > 0 and current_price >= recent_high * 0.99:
                last_price = last_alerted_prices.get(pair, 0.0)
                # Only alert on first breakout OR when price reaches a new higher high (>= +0.2%)
                if last_price == 0.0 or current_price >= last_price * 1.002:
                    message = f"Cảnh báo Forex: Cặp tiền {pair} ({symbol}) đã tiệm cận hoặc vượt đỉnh gần nhất ở mức {current_price:,.4f} (Đỉnh cũ: {recent_high:,.4f})."
                    print(f"🚨 [Forex Breakout] {pair} tại giá {current_price:,.4f} >= 99% Đỉnh gần nhất {recent_high:,.4f}")
                    play_alert(pair, "forex")
                    insert_triggered_alert("forex", pair, current_price, message)
                    last_alerted_prices[pair] = current_price

            # 2. Check for 52-Week High Breakout (check within 1%)
            elif fifty_two_high and fifty_two_high > 0 and current_price >= fifty_two_high * 0.99:
                last_price = last_alerted_prices.get(pair, 0.0)
                if last_price == 0.0 or current_price >= last_price * 1.002:
                    message = f"Cảnh báo Forex: Cặp tiền {pair} ({symbol}) đã tiệm cận hoặc vượt đỉnh 52 tuần tại {current_price:,.4f}."
                    print(f"🚨 [Forex 52W Breakout] {pair} tại giá {current_price:,.4f} >= 99% Đỉnh 52 tuần {fifty_two_high:,.4f}")
                    play_alert(pair, "forex")
                    insert_triggered_alert("forex", pair, current_price, message)
                    last_alerted_prices[pair] = current_price
                    auto_trigger_breakout_paper_trade(pair, "forex", current_price, fifty_two_high)

            # 3. Check for custom user-configured alerts
            check_custom_forex_alerts(symbol, pair, current_price)

            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Lỗi quét forex {pair}: {e}")

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
                step_pct NUMERIC(5, 2) DEFAULT 5.00 NOT NULL,
                pyramid_ratio NUMERIC(5, 2) DEFAULT 0.67 NOT NULL,
                sl_pct NUMERIC(5, 2) DEFAULT 2.00 NOT NULL,
                max_pyramids INT DEFAULT 3 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT uq_breakout_symbol_asset UNIQUE(symbol, asset_type)
            );

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
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi khởi tạo bảng breakout_watchlist / paper trading: {e}")
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
            # Try KBS Quote
            q = Quote(symbol=clean_sym, source='kbs')
            df = q.intraday(page_size=5, show_log=False)
            if df is not None and not df.empty:
                return float(df.iloc[-1]['price']) * 1000.0
        elif asset_type in ('stock_us', 'commodity', 'forex'):
            # Map ticker if needed for Yahoo Finance
            ticker = clean_sym
            if asset_type == 'forex':
                ticker = map_forex_symbol_to_yahoo(clean_sym)
            elif asset_type == 'commodity':
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
        print(f"⚠️ Lỗi lấy giá trực tiếp cho {symbol} ({asset_type}): {e}")
    return None

def process_breakout_paper_trading(item, current_price):
    """
    Core Pyramiding Live & Paper Trading Engine:
    - Triggers Initial Buy upon 52W ATH breakout
    - Pyramids orders (+5% step) with 2/3 capital scaling & trailing stop loss
    - Executes automated Stop-Loss (default -3% or custom per item)
    - If system setting trading_mode == 'real', dispatches live trade to Binance API or MT5!
    """
    # Unpack item with optional is_real_trading & spread_pct flags
    w_id, symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct, max_pyramids = item[:10]
    is_real_trading = bool(item[10]) if len(item) > 10 else False
    
    # Calculate default spread_pct if not supplied
    default_spread = 1.45 if (asset_type == 'commodity' or symbol in ('XAUUSD', 'GOLD', 'XAGUSD', 'SILVER')) else (0.25 if asset_type == 'stock_vn' else (0.08 if asset_type in ('futures', 'stock_us') else (0.05 if asset_type == 'forex' else 0.10)))
    spread_pct = float(item[11]) if (len(item) > 11 and item[11] is not None and float(item[11]) > 0) else default_spread

    ath_price = float(ath_price)
    initial_budget = float(initial_budget)
    step_pct = float(step_pct)
    pyramid_ratio = float(pyramid_ratio)
    sl_pct = float(sl_pct) if (sl_pct and float(sl_pct) > 0) else 2.0
    max_pyramids = int(max_pyramids)
    current_price = float(current_price)

    if current_price <= 0:
        return

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query trading mode from system_settings
        cur.execute("SELECT value FROM public.system_settings WHERE key = 'trading_mode';")
        tm_row = cur.fetchone()
        trading_mode = tm_row[0].lower() if tm_row else 'demo'

        # Execute real trade only if global mode is 'real' AND this specific item has is_real_trading enabled
        should_execute_real = (trading_mode == 'real' and is_real_trading)

        # Check existing OPEN position
        cur.execute("""
            SELECT id, current_layer, total_invested, total_units, avg_entry_price,
                   last_buy_price, highest_price, stop_loss_price, next_pyramid_price,
                   COALESCE(spread_pct, %s), COALESCE(breakeven_price, 0)
            FROM public.paper_positions
            WHERE watchlist_id = %s AND status = 'OPEN'
            ORDER BY id DESC LIMIT 1;
        """, (spread_pct, w_id))
        pos_row = cur.fetchone()

        display_name = name if name else symbol
        currency_symbol = "đ" if asset_type == 'stock_vn' else "$"

        if not pos_row:
            # === CASE A: NO OPEN POSITION -> Check ATH Breakout ===
            if current_price >= ath_price:
                # BREAKOUT OCCURRED! Open Initial Position
                units = initial_budget / current_price
                stop_loss = current_price * (1.0 - sl_pct / 100.0)
                next_pyramid = current_price * (1.0 + step_pct / 100.0)
                breakeven_price = current_price * (1.0 + spread_pct / 100.0)
                
                real_trade_note = ""
                # Execute REAL trade if should_execute_real
                if should_execute_real:
                    try:
                        if asset_type in ('crypto', 'futures'):
                            from live_trader_binance import execute_binance_order
                            b_res = execute_binance_order(symbol, asset_type, initial_budget, sl_pct=sl_pct, layer=1)
                            if b_res.get('success'):
                                real_trade_note = f" [BINANCE REAL ORDER #{b_res.get('order_id')}]"
                                if b_res.get('entry_price'):
                                    current_price = float(b_res.get('entry_price'))
                                    stop_loss = float(b_res.get('stop_loss_price'))
                                    breakeven_price = current_price * (1.0 + spread_pct / 100.0)
                            else:
                                real_trade_note = f" [BINANCE REAL FAILED: {b_res.get('error')}]"
                        elif asset_type in ('forex', 'commodity', 'stock_us'):
                            from live_trader_mt5 import execute_mt5_order
                            m_res = execute_mt5_order(symbol, asset_type, current_price, sl_pct=sl_pct, layer=1)
                            if m_res.get('success'):
                                real_trade_note = f" [MT5 REAL TICKET #{m_res.get('ticket')}]"
                            else:
                                real_trade_note = f" [MT5 REAL FAILED: {m_res.get('error')}]"
                    except Exception as live_err:
                        print(f"⚠️ [Live Trader] Lỗi thực thi lệnh thật: {live_err}")
                        real_trade_note = f" [LIVE ERROR: {live_err}]"

                # Insert paper position
                cur.execute("""
                    INSERT INTO public.paper_positions (
                        watchlist_id, symbol, asset_type, status, current_layer,
                        total_invested, total_units, avg_entry_price, last_buy_price,
                        highest_price, current_price, stop_loss_price, next_pyramid_price,
                        spread_pct, breakeven_price,
                        unrealized_pnl, unrealized_roi_pct, realized_pnl, opened_at, updated_at
                    ) VALUES (
                        %s, %s, %s, 'OPEN', 1,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        0, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    ) RETURNING id;
                """, (w_id, symbol, asset_type, initial_budget, units, current_price, current_price, current_price, current_price, stop_loss, next_pyramid, spread_pct, breakeven_price))
                pos_id = cur.fetchone()[0]

                # Insert paper order
                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'INITIAL_BUY', 1, %s, %s, %s, %s);
                """, (pos_id, symbol, current_price, initial_budget, units, f"Vượt đỉnh 52W ATH ({ath_price:,.2f}){real_trade_note}"))

                # Update ATH price in watchlist
                cur.execute("""
                    UPDATE public.breakout_watchlist
                    SET ath_price = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (current_price, w_id))
                conn.commit()

                # Alerting
                mode_tag = "🔴 [REAL TRADE]" if should_execute_real else "⚡ [DEMO TRADE]"
                msg = (
                    f"[BREAKOUT RADAR] {symbol} ({asset_type.upper()}) ĐÃ VƯỢT ĐỈNH 52W ATH!\n"
                    f"• Giá phá đỉnh: {current_price:,.2f}{currency_symbol} (Đỉnh cũ: {ath_price:,.2f}{currency_symbol})\n"
                    f"• Khớp lệnh Mua Đợt 1: {currency_symbol}{initial_budget:,.0f} ({units:,.4f} units){real_trade_note}"
                )
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type)
                insert_triggered_alert(asset_type, symbol, current_price, msg)

        else:
            # === CASE B: ACTIVE POSITION ALREADY EXISTS ===
            pos_id, current_layer, total_invested, total_units, avg_entry_price, last_buy_price, highest_price, stop_loss_price, next_pyramid_price, cur_spread_pct, breakeven_price = pos_row
            current_layer = int(current_layer)
            total_invested = float(total_invested)
            total_units = float(total_units)
            avg_entry_price = float(avg_entry_price)
            last_buy_price = float(last_buy_price)
            highest_price = float(highest_price)
            stop_loss_price = float(stop_loss_price)
            next_pyramid_price = float(next_pyramid_price)
            cur_spread_pct = float(cur_spread_pct) if cur_spread_pct else spread_pct
            breakeven_price = float(breakeven_price) if breakeven_price and float(breakeven_price) > 0 else avg_entry_price * (1.0 + spread_pct / 100.0)

            # Ensure stop_loss_price & breakeven stay in sync with watchlist sl_pct & spread_pct if user updated it
            expected_sl = avg_entry_price * (1.0 - sl_pct / 100.0) if current_layer == 1 else max(avg_entry_price, last_buy_price * (1.0 - sl_pct / 100.0))
            expected_breakeven = avg_entry_price * (1.0 + spread_pct / 100.0)
            if abs(stop_loss_price - expected_sl) > 1e-4 or abs(breakeven_price - expected_breakeven) > 1e-4 or abs(cur_spread_pct - spread_pct) > 1e-4:
                stop_loss_price = expected_sl
                breakeven_price = expected_breakeven
                cur_spread_pct = spread_pct
                cur.execute("UPDATE public.paper_positions SET stop_loss_price = %s, spread_pct = %s, breakeven_price = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;", (stop_loss_price, spread_pct, breakeven_price, pos_id))
                conn.commit()

            # Update highest price tracked
            new_highest = max(highest_price, current_price)
            if new_highest > ath_price:
                cur.execute("UPDATE public.breakout_watchlist SET ath_price = %s WHERE id = %s;", (new_highest, w_id))

            # Calculate current PnL & ROI
            unrealized_pnl = (current_price - avg_entry_price) * total_units
            unrealized_roi_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100.0 if avg_entry_price > 0 else 0.0

            # 1. Check STOP-LOSS TRIGGER
            if current_price <= stop_loss_price:
                realized_pnl = (current_price - avg_entry_price) * total_units
                cur.execute("""
                    UPDATE public.paper_positions
                    SET status = 'CLOSED_SL',
                        current_price = %s,
                        realized_pnl = %s,
                        unrealized_pnl = 0,
                        closed_at = CURRENT_TIMESTAMP,
                        close_reason = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (current_price, realized_pnl, f"STOP_LOSS_{sl_pct}PCT", pos_id))

                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'STOP_LOSS', %s, %s, %s, %s, %s);
                """, (pos_id, symbol, current_layer, current_price, current_price * total_units, total_units, f"Chạm ngưỡng cắt lỗ {stop_loss_price:,.2f} (-{sl_pct}%)"))
                conn.commit()

                msg = (
                    f"🛑 [BREAKOUT RADAR - CẮT LỖ] {symbol} ({asset_type.upper()}) Đã chạm mức Stop-Loss -{sl_pct}%!\n"
                    f"• Giá cắt lỗ: {current_price:,.2f}{currency_symbol} (Ngưỡng SL: {stop_loss_price:,.2f}{currency_symbol})\n"
                    f"• Đóng toàn bộ {total_units:,.4f} units vị thế (Tầng {current_layer})\n"
                    f"• Realized PnL: {realized_pnl:+,.2f}{currency_symbol} ({unrealized_roi_pct:+.2f}%)"
                )
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type)
                insert_triggered_alert(asset_type, symbol, current_price, msg)

            # 2. Check PYRAMIDING BUY TRIGGER (+step_pct% from last buy & within max_pyramids)
            elif current_price >= next_pyramid_price and current_layer < max_pyramids:
                new_layer = current_layer + 1
                # Calculate next order size: scaled by pyramid_ratio (e.g. 2/3 of previous buy amount)
                next_budget = initial_budget * (pyramid_ratio ** (new_layer - 1))
                new_units = next_budget / current_price
                new_total_units = total_units + new_units
                new_total_invested = total_invested + next_budget
                new_avg_entry = new_total_invested / new_total_units
                new_breakeven = new_avg_entry * (1.0 + spread_pct / 100.0)

                # Trailing / Breakeven Stop-loss protection
                # Trailing SL is at least breakeven OR sl_pct% below current price
                new_stop_loss = max(new_avg_entry, current_price * (1.0 - sl_pct / 100.0))
                new_next_pyramid = current_price * (1.0 + step_pct / 100.0)

                real_pyramid_note = ""
                if should_execute_real:
                    try:
                        if asset_type in ('crypto', 'futures'):
                            from live_trader_binance import execute_binance_order
                            b_res = execute_binance_order(symbol, asset_type, next_budget, sl_pct=sl_pct, layer=new_layer)
                            if b_res.get('success'):
                                real_pyramid_note = f" [BINANCE REAL ORDER #{b_res.get('order_id')}]"
                        elif asset_type in ('forex', 'commodity', 'stock_us'):
                            from live_trader_mt5 import execute_mt5_order
                            m_res = execute_mt5_order(symbol, asset_type, current_price, sl_pct=sl_pct, layer=new_layer)
                            if m_res.get('success'):
                                real_pyramid_note = f" [MT5 REAL TICKET #{m_res.get('ticket')}]"
                    except Exception as live_err:
                        print(f"⚠️ [Live Trader] Lỗi thực thi nhồi lệnh thật: {live_err}")

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
                        unrealized_pnl = %s,
                        unrealized_roi_pct = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (new_layer, new_total_invested, new_total_units, new_avg_entry, current_price,
                      new_highest, current_price, new_stop_loss, new_next_pyramid,
                      spread_pct, new_breakeven,
                      (current_price - new_avg_entry) * new_total_units,
                      ((current_price - new_avg_entry) / new_avg_entry) * 100.0,
                      pos_id))

                cur.execute("""
                    INSERT INTO public.paper_orders (
                        position_id, symbol, order_type, layer, price, amount_usd, units, reason
                    ) VALUES (%s, %s, 'PYRAMID_BUY', %s, %s, %s, %s, %s);
                """, (pos_id, symbol, new_layer, current_price, next_budget, new_units, f"Nhồi lệnh Tầng {new_layer} (+{step_pct}% bước giá){real_pyramid_note}"))
                conn.commit()

                mode_tag = "🔴 [REAL TRADE]" if should_execute_real else "⚡ [DEMO TRADE]"
                msg = (
                    f"📈 {mode_tag} [NHỒI LỆNH TẦNG {new_layer}] {symbol} ({asset_type.upper()}) Tiếp tục tăng vượt đỉnh!\n"
                    f"• Giá mua nhồi: {current_price:,.2f}{currency_symbol}\n"
                    f"• Vốn nhồi thêm: {currency_symbol}{next_budget:,.0f} (Tỷ lệ {pyramid_ratio*100:.0f}%){real_pyramid_note}\n"
                    f"• Giá vốn bình quân mới: {new_avg_entry:,.2f}{currency_symbol}\n"
                    f"• Giá hòa vốn mới (Spread {spread_pct:.2f}%): {new_breakeven:,.2f}{currency_symbol}\n"
                    f"• Dời Stop-Loss bảo toàn vốn (SL -{sl_pct}%): {new_stop_loss:,.2f}{currency_symbol}\n"
                    f"• Ngưỡng nhồi tiếp theo: {new_next_pyramid:,.2f}{currency_symbol} (Tối đa {max_pyramids} tầng)"
                )
                print(f"\n{msg}\n")
                play_alert(symbol, asset_type)
                insert_triggered_alert(asset_type, symbol, current_price, msg)

            else:
                # 3. Normal heartbeat price & PnL update
                cur.execute("""
                    UPDATE public.paper_positions
                    SET current_price = %s,
                        highest_price = %s,
                        unrealized_pnl = %s,
                        unrealized_roi_pct = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (current_price, new_highest, unrealized_pnl, unrealized_roi_pct, pos_id))
                conn.commit()

        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi xử lý paper trading breakout cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()

def auto_trigger_breakout_paper_trade(symbol, asset_type, current_price, ath_price=None, name=None):
    """
    Automatically enrolls ANY symbol that triggered a 52W ATH breakout into breakout_watchlist
    and immediately enters a paper trade ($1000 buy) with default 3% Stop Loss.
    """
    if current_price is None or current_price <= 0:
        return
    clean_sym = symbol.split(':')[-1] if ':' in symbol else symbol
    clean_sym = clean_sym.upper().strip()
    ath = float(ath_price) if (ath_price and ath_price > 0) else float(current_price)

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Insert if not exists
        cur.execute("""
            INSERT INTO public.breakout_watchlist (
                symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct, max_pyramids, is_active, is_real_trading
            ) VALUES (%s, %s, %s, %s, 1000.0, 5.0, 0.67, 3.0, 3, true, false)
            ON CONFLICT (symbol, asset_type) DO UPDATE SET is_active = true
            RETURNING id, symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct, max_pyramids, is_real_trading;
        """, (clean_sym, asset_type, name or clean_sym, ath))
        row = cur.fetchone()
        conn.commit()
        cur.close()

        if row:
            process_breakout_paper_trading(row, current_price)
    except Exception as e:
        print(f"⚠️ Lỗi auto_trigger_breakout_paper_trade cho {symbol}: {e}")
    finally:
        if conn:
            conn.close()


def monitor_breakout_paper_trading_step():
    """Polls real-time prices and runs automated Pyramiding trade logic for all active breakout watchlist items"""
    conn = None
    items = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, symbol, asset_type, name, ath_price, initial_budget, step_pct, pyramid_ratio, sl_pct, max_pyramids, is_real_trading, COALESCE(spread_pct, 0.10)
            FROM public.breakout_watchlist
            WHERE is_active = true;
        """)
        items = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"⚠️ Lỗi lấy danh sách breakout_watchlist: {e}")
    finally:
        if conn:
            conn.close()


    if not items:
        return

    print(f"🎯 [BREAKOUT RADAR] Đang quét {len(items)} mã theo dõi ATH & Vị thế Paper Trading...")
    for item in items:
        symbol, asset_type = item[1], item[2]
        price = fetch_live_price_for_breakout(symbol, asset_type)
        if price is not None and price > 0:
            process_breakout_paper_trading(item, price)
        time.sleep(0.3)

def main():
    print("🤖 Bắt đầu khởi tạo dịch vụ Báo Động Lệnh Lớn & Vượt Đỉnh (Breakout Radar)...")
    init_breakout_paper_trade_tables()
    init_economic_calendar_table()
    print("Mô hình hoạt động:")
    print("  • Stocks VN: Thứ 2 đến Thứ 6 (09:00 - 14:45 UTC+7). Dựa trên symbols_watchlist.")
    print("  • Stocks US: Thứ 2 đến Thứ 6 (09:30 - 16:00 ET). Dựa trên world_symbols_watchlist (Mỹ).")
    print("  • Cryptos Spot: Quét 24/7 hàng ngày. Dựa trên cryptos_watchlist.")
    print("  • Cryptos Futures: Quét 24/7 hàng ngày. Dựa trên futures_watchlist.")
    print("  • Commodities: Thứ 2 đến Thứ 6 (Quét 24/5 trong tuần). Hỗ trợ Vàng, Bạc, UKOIL, USOIL.")
    print("  • Breakout Radar: Quét tự động & Quản lý vị thế nhồi lệnh 24/7 cho danh sách breakout_watchlist.")
    
    # State caches in memory to prevent duplicate alarms
    last_processed_time_stocks = {}
    last_processed_trade_ids_cryptos = {}
    last_processed_trade_ids_futures = {}
    last_alerted_prices_us = {}
    last_alerted_prices_commodities = {}
    last_alerted_prices_forex = {}
    last_alerted_yields = {}
    last_alerted_breakout_prices = {}
    
    # Read USD threshold for crypto and share count threshold for stock
    crypto_threshold_usd = float(os.getenv('CRYPTO_ALERT_THRESHOLD_USD', 10000.0))
    stock_threshold_shares = int(os.getenv('STOCK_ALERT_THRESHOLD_SHARES', 5000))

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

            # 1. Stocks Watchlist check (Mon to Fri, 09:00 - 14:45 UTC+7)
            if toggles['scan_stock_vn']:
                vn_now = get_vn_time()
                vn_weekday = vn_now.weekday()
                vn_hour = vn_now.hour
                vn_minute = vn_now.minute

                is_vn_market_open = (
                    vn_weekday < 5 and
                    ((vn_hour == 9 and vn_minute >= 0) or (10 <= vn_hour < 14) or (vn_hour == 14 and vn_minute <= 45))
                )

                if is_vn_market_open:
                    stock_watchlist = get_watchlist_symbols()
                    if stock_watchlist:
                        monitor_stocks_step(stock_watchlist, last_processed_time_stocks, last_alerted_breakout_prices, threshold=stock_threshold_shares)
                    else:
                        print("💤 Không có cổ phiếu VN nào đạt đủ 3 tín hiệu trong symbols_watchlist.")
                else:
                    print(f"💤 Ngoài giờ giao dịch Stock VN (T2-T6, 09:00 - 14:45). Hiện tại: {vn_now.strftime('%d/%m %H:%M:%S')} UTC+7. Tạm ngưng quét VN.")
            else:
                print("💤 Tắt quét Stock VN (theo cấu hình hệ thống).")

            # 2. US Stocks Watchlist check (Mon to Fri, 09:30 - 16:00 US/Eastern)
            if toggles['scan_stock_us']:
                us_now = get_us_time()
                us_weekday = us_now.weekday()
                us_hour = us_now.hour
                us_minute = us_now.minute

                is_us_market_open = (
                    us_weekday < 5 and
                    ((us_hour == 9 and us_minute >= 30) or (10 <= us_hour < 16))
                )

                if is_us_market_open:
                    us_watchlist = get_us_watchlist_symbols()
                    if us_watchlist:
                        monitor_us_stocks_step(us_watchlist, last_alerted_prices_us)
                    else:
                        print("💤 Không có cổ phiếu Mỹ nào trong world_symbols_watchlist.")
                else:
                    print(f"💤 Ngoài giờ giao dịch Stock US (T2-T6, 09:30 - 16:00 ET). Hiện tại: {us_now.strftime('%d/%m %H:%M:%S')} ET. Tạm ngưng quét US.")
            else:
                print("💤 Tắt quét Stock US (theo cấu hình hệ thống).")

            # 3. Cryptos Watchlist check (Every day, 24/7)
            if toggles['scan_crypto']:
                crypto_watchlist = get_watchlist_cryptos()
                if crypto_watchlist:
                    monitor_cryptos_step(crypto_watchlist, last_processed_trade_ids_cryptos, last_alerted_breakout_prices, threshold_usd=crypto_threshold_usd)
                else:
                    print("💤 Không có crypto nào trong cryptos_watchlist.")
            else:
                print("💤 Tắt quét Crypto Spot (theo cấu hình hệ thống).")

            # 4. Cryptos Futures Watchlist check (Every day, 24/7)
            if toggles['scan_futures']:
                futures_watchlist = get_watchlist_futures()
                if futures_watchlist:
                    monitor_futures_step(futures_watchlist, last_processed_trade_ids_futures, last_alerted_breakout_prices, threshold_usd=crypto_threshold_usd)
                else:
                    print("💤 Không có futures nào trong futures_watchlist.")
            else:
                print("💤 Tắt quét Crypto Futures (theo cấu hình hệ thống).")

            # 5. Commodities Watchlist check (Mon to Fri, CME/ICE open hours)
            if toggles.get('scan_commodities', True):
                us_now = get_us_time()
                us_weekday = us_now.weekday()
                
                # Commodities trade Monday to Friday (weekday < 5)
                is_commodities_market_open = (us_weekday < 5)

                if is_commodities_market_open:
                    monitor_commodities_step(COMMODITIES_SYMBOLS, last_alerted_prices_commodities)
                else:
                    print(f"💤 Ngoài giờ giao dịch Commodities (T2-T6). Hiện tại: {us_now.strftime('%d/%m %H:%M:%S')} ET. Tạm ngưng quét Commodities.")
            else:
                print("💤 Tắt quét Commodities (theo cấu hình hệ thống).")

            # 6. Forex Watchlist check (Mon to Fri, 24/5)
            if toggles.get('scan_forex', True):
                us_now = get_us_time()
                us_weekday = us_now.weekday()
                is_forex_market_open = (us_weekday < 5)

                if is_forex_market_open:
                    forex_watchlist = get_watchlist_forex()
                    if forex_watchlist:
                        monitor_forex_step(forex_watchlist, last_alerted_prices_forex)
                    else:
                        print("💤 Không có forex nào trong forex_watchlist.")
                else:
                    print(f"💤 Ngoài giờ giao dịch Forex (T2-T6). Hiện tại: {us_now.strftime('%d/%m %H:%M:%S')} ET. Tạm ngưng quét Forex.")
            else:
                print("💤 Tắt quét Forex (theo cấu hình hệ thống).")

            # 7. US Treasury Yields check (Mon to Fri, 24/5)
            if toggles.get('scan_yields', True):
                us_now = get_us_time()
                us_weekday = us_now.weekday()
                is_yields_market_open = (us_weekday < 5)

                if is_yields_market_open:
                    monitor_yields_step(YIELD_SYMBOLS, last_alerted_yields)
                else:
                    print(f"💤 Ngoài giờ giao dịch US Treasury Yields (T2-T6). Hiện tại: {us_now.strftime('%d/%m %H:%M:%S')} ET. Tạm ngưng quét Yields.")
            else:
                print("💤 Tắt quét US Treasury Yields (theo cấu hình hệ thống).")

            # 8. Smart Economic Calendar Poller (Micro-polling when events are active)
            monitor_economic_calendar_step()

            # 9. Print separators and sleep for 15 seconds
            print(f"🕒 Lượt quét hoàn thành lúc {datetime.now().strftime('%H:%M:%S')}. Nghỉ 15 giây...\n")
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n👋 Dừng dịch vụ Báo Động. Hẹn gặp lại!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Lỗi hệ thống: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()

