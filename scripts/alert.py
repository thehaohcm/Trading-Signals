#!/usr/bin/env python3
import time
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from vnstock import Quote

# Load environment variables
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

def insert_triggered_alert(asset_type, symbol, price, message):
    """Log the alert to public.triggered_alerts so the web UI reads it in real-time"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
        INSERT INTO public.triggered_alerts (asset_type, symbol, price, message, is_read)
        VALUES (%s, %s, %s, %s, false);
        """
        cur.execute(query, (asset_type, symbol, price, message))
        conn.commit()
        cur.close()
        print(f"💾 Đã lưu báo động {symbol} ({asset_type}) vào website database!")
    except Exception as e:
        print(f"❌ Lỗi ghi triggered_alert vào DB: {e}")
    finally:
        if conn:
            conn.close()

def monitor_stocks_step(symbols, last_processed_time, threshold=5000):
    """Performs one scan cycle on the list of stock symbols"""
    if not symbols:
        return
    
    print(f"🔍 [STOCK] Đang quét {list(symbols.keys())} | Ngưỡng lệnh: >={threshold} CP...")
    for symbol in symbols:
        try:
            q = Quote(symbol=symbol, source='kbs')
            df = q.intraday(page_size=30, show_log=False)
            if df is None or df.empty:
                continue

            recent_trades = df.tail(10)  # Check last 10 ticks
            for _, trade in recent_trades.iterrows():
                current_time = trade['time']
                volume = int(trade['volume'])
                price = float(trade['price'])
                side = trade.get('side', 'N/A')

                # Initialize tracking set for new symbols
                if symbol not in last_processed_time:
                    last_processed_time[symbol] = set()

                if current_time not in last_processed_time[symbol] and volume >= threshold:
                    # Stock prices in KBS API are typically in thousands (e.g. 52.5 means 52,500 VND)
                    price_vnd = price * 1000.0
                    message = f"Cảnh báo Stock: Tín hiệu lớn cho cổ phiếu {symbol}. Khớp lệnh {volume:,} cổ phiếu ở mức giá {price_vnd:,.0f} đồng."
                    
                    print(f"🚨 [{current_time}] Cổ phiếu {symbol}: {side} {volume:,} cp tại giá {price}")
                    play_alert(symbol, "stock")
                    insert_triggered_alert("stock", symbol, price_vnd, message)
                    
                    last_processed_time[symbol].add(current_time)
                    if len(last_processed_time[symbol]) > 100:
                        # Pop oldest elements to prevent memory grow
                        last_processed_time[symbol] = set(list(last_processed_time[symbol])[-100:])
            
            # Avoid API rate-limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Lỗi quét stock {symbol}: {e}")

def monitor_cryptos_step(cryptos, last_processed_trade_ids, threshold_usd=10000.0):
    """Performs one scan cycle on the list of Binance cryptos"""
    if not cryptos:
        return

    print(f"🔍 [CRYPTO] Đang quét {list(cryptos.keys())} | Ngưỡng lệnh: >=${threshold_usd:,.0f} USDT...")
    for crypto in cryptos:
        try:
            url = f"https://api.binance.com/api/v3/trades?symbol={crypto}&limit=30"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                continue

            trades = res.json()
            if not trades:
                continue

            # Get current price to compute dynamic coin volume threshold
            current_price = float(trades[-1]["price"])
            if current_price <= 0:
                continue
            
            coin_threshold = threshold_usd / current_price

            for trade in trades:
                trade_id = trade["id"]
                qty = float(trade["qty"])
                price = float(trade["price"])
                trade_time_ms = trade["time"]
                trade_time = datetime.fromtimestamp(trade_time_ms / 1000.0).strftime('%H:%M:%S')
                
                is_buyer_maker = trade["isBuyerMaker"]
                side = "SELL" if is_buyer_maker else "BUY"

                # Initialize tracking set for new cryptos
                if crypto not in last_processed_trade_ids:
                    last_processed_trade_ids[crypto] = set()

                if trade_id not in last_processed_trade_ids[crypto] and qty >= coin_threshold:
                    val_usd = qty * price
                    # Dynamic Voice message for TTS
                    message = f"Cảnh báo Crypto: Phát hiện lệnh lớn cho {crypto}. Khớp lệnh {qty:,.2f} coin trị giá {val_usd:,.2f} đô la tại mức giá {price:,.6f}."
                    
                    print(f"🚨 [{trade_time}] Crypto {crypto}: {side} {qty:,.4f} coins (${val_usd:,.2f}) at price {price}")
                    play_alert(crypto, "crypto")
                    insert_triggered_alert("crypto", crypto, price, message)

                    last_processed_trade_ids[crypto].add(trade_id)
                    if len(last_processed_trade_ids[crypto]) > 100:
                        # Pop oldest elements to prevent memory grow
                        last_processed_trade_ids[crypto] = set(list(last_processed_trade_ids[crypto])[-100:])
            
            # Avoid API rate-limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Lỗi quét crypto {crypto}: {e}")

def main():
    print("🤖 Bắt đầu khởi tạo dịch vụ Báo Động Lệnh Lớn...")
    print("Mô hình hoạt động:")
    print("  • Stocks: Thứ 2 đến Thứ 6. Dựa trên dữ liệu symbols_watchlist.")
    print("  • Cryptos: Quét 24/7 hàng ngày. Dựa trên cryptos_watchlist.")
    
    # State caches in memory to prevent duplicate alarms
    last_processed_time_stocks = {}
    last_processed_trade_ids_cryptos = {}
    
    # Read USD threshold for crypto and share count threshold for stock
    crypto_threshold_usd = float(os.getenv('CRYPTO_ALERT_THRESHOLD_USD', 10000.0))
    stock_threshold_shares = int(os.getenv('STOCK_ALERT_THRESHOLD_SHARES', 5000))

    while True:
        try:
            today = datetime.today()
            weekday = today.weekday()  # 0 = Monday, ..., 4 = Friday, 5 = Saturday, 6 = Sunday
            is_weekend = (weekday >= 5)

            # 1. Stocks Watchlist check (Mon to Fri only)
            if not is_weekend:
                stock_watchlist = get_watchlist_symbols()
                if stock_watchlist:
                    monitor_stocks_step(stock_watchlist, last_processed_time_stocks, threshold=stock_threshold_shares)
                else:
                    print("💤 Không có cổ phiếu nào đạt đủ 3 tín hiệu trong symbols_watchlist.")
            else:
                print("💤 Hôm nay là cuối tuần (T7/CN). Tạm ngưng quét Stock.")

            # 2. Cryptos Watchlist check (Every day, 24/7)
            crypto_watchlist = get_watchlist_cryptos()
            if crypto_watchlist:
                monitor_cryptos_step(crypto_watchlist, last_processed_trade_ids_cryptos, threshold_usd=crypto_threshold_usd)
            else:
                print("💤 Không có crypto nào trong cryptos_watchlist.")

            # 3. Print separators and sleep for 15 seconds
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
