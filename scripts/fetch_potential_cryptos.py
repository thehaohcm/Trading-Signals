import asyncio
import asyncpg
import time
import httpx
import os
import ccxt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from price_alert_utils import check_multiple_alerts

EXCLUDE_KEYWORDS = ["USDC", "USDE", "FDUSD", "USD1", "TUSD", "USDD", "USDP", "DAI", "BUSD", "GUSD", "USTC", "BFUSD", "XUSD", "EUR"]

# Load environment variables from .env file
load_dotenv() 

async def send_slack_message(cryptos_list):
    """Send potential crypto symbols to Slack"""
    slack_enabled = os.environ.get('SLACK_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    if not slack_enabled:
        print("Slack notifications disabled, skipping")
        return
    
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not slack_webhook_url:
        print("SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return
    
    if not cryptos_list:
        print("No potential cryptos to report")
        return
    
    # Separate ATH and 52-week high coins
    ath_coins = [c["symbol"] for c in cryptos_list if c["is_ath"]]
    week_52_coins = [c["symbol"] for c in cryptos_list if not c["is_ath"]]
    
    message_parts = [f"🚀 *Potential Cryptos Detected ({len(cryptos_list)} symbols)*\n"]
    
    if ath_coins:
        ath_text = "\n".join([f"• {s}" for s in ath_coins])
        message_parts.append(f"\n*Near ATH ({len(ath_coins)}):*\n{ath_text}")
    
    if week_52_coins:
        week_text = "\n".join([f"• {s}" for s in week_52_coins])
        message_parts.append(f"\n*Near 52-Week High ({len(week_52_coins)}):*\n{week_text}")
    
    message = {"text": "".join(message_parts)}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                slack_webhook_url,
                json=message,
                timeout=10.0
            )
            if response.status_code == 200:
                print(f"Slack notification sent successfully ({len(cryptos_list)} cryptos)")
            else:
                print(f"Failed to send Slack notification: {response.status_code}")
    except Exception as e:
        print(f"Error sending Slack message: {e}")

# ================================
#  BINANCE + COINGECKO FUNCTIONS
# ================================
async def get_top_usdt_pairs_by_volume(limit=50):
    """Get top USDT pairs by trading volume from Binance"""
    loop = asyncio.get_event_loop()
    exchange = ccxt.binance()
    
    # Fetch tickers in async way
    tickers = await loop.run_in_executor(None, exchange.fetch_tickers)
    
    # Filter USDT pairs and sort by volume
    usdt_pairs = []
    for symbol, ticker in tickers.items():
        base_currency = symbol.split('/')[0]
        if (symbol.endswith('/USDT') and 
            ticker.get('quoteVolume') and 
            base_currency not in EXCLUDE_KEYWORDS):
            usdt_pairs.append({
                'symbol': symbol.replace('/', ''),  # Convert BTC/USDT -> BTCUSDT
                'volume': ticker['quoteVolume']
            })
    
    # Sort by volume and get top N
    usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
    return [pair['symbol'] for pair in usdt_pairs[:limit]]


async def check_52week_high_async(symbol):
    """Check if a symbol is near its 52-week high using httpx (async)"""
    try:
        # Convert BTCUSDT -> BTC/USDT for display
        symbol_formatted = symbol.replace('USDT', '/USDT')
        
        # Fetch OHLCV data using Binance API directly
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": 365
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return None
            
            klines = res.json()
            if not klines:
                return None
            
            # Extract highs and current close
            highs = [float(k[2]) for k in klines]
            current_price = float(klines[-1][4])  # Last close price
            max_52w = max(highs)
            
            # Check if within 10% of 52-week high
            diff = (max_52w - current_price) / max_52w
            if diff <= 0.1:  # Within 10% of high
                print(f"   ✅ {symbol_formatted}: Price {current_price:.2f} | 52W High: {max_52w:.2f} | Gap: -{diff:.2%}")
                return {"symbol": symbol, "is_ath": False}
            
            return None
    except Exception as e:
        print(f"   ⚠️  Error checking {symbol}: {e}")
        return None

# ================================
#  DATABASE UPDATE LOGIC
# ================================
async def update_cryptos_watchlist(conn):
    print("🔹 Fetching top USDT pairs by volume...")
    top_symbols = await get_top_usdt_pairs_by_volume(limit=50)
    
    print(f"🔹 Found {len(top_symbols)} top trading pairs")
    print(f"   Symbols: {', '.join([s.replace('USDT', '') for s in top_symbols[:10]])}...")

    # --- Giai đoạn lọc coin gần đỉnh 52 tuần (async batch processing) ---
    print("🔹 Checking 52-week highs...")
    near_52w = []
    
    # Process in concurrent batches
    batch_size = 10
    total_batches = (len(top_symbols) + batch_size - 1) // batch_size
    
    for i in range(0, len(top_symbols), batch_size):
        batch = top_symbols[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} symbols)...")
        
        # Execute batch concurrently
        tasks = [check_52week_high_async(symbol) for symbol in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for res in results:
            if res and not isinstance(res, Exception):
                near_52w.append(res)
        
        # Small delay between batches to respect rate limits
        if i + batch_size < len(top_symbols):
            await asyncio.sleep(0.2)
    
    print(f"   Found {len(near_52w)} coins near 52-week high")
    data_to_insert = near_52w
    if data_to_insert:
        print(f"🔹 Updating {len(data_to_insert)} records into DB...")
        transaction = conn.transaction()
        await transaction.start()
        try:
            await conn.execute("DELETE FROM cryptos_watchlist")
            await conn.executemany(
                """
                INSERT INTO cryptos_watchlist (crypto, is_ath)
                VALUES ($1, $2)
                ON CONFLICT (crypto)
                DO UPDATE SET is_ath = EXCLUDED.is_ath, updated_at = CURRENT_TIMESTAMP
                """,
                [(d["symbol"], d["is_ath"]) for d in data_to_insert],
            )
        except asyncpg.PostgresError as e:
            print("Database error:", e)
            await transaction.rollback()
        else:
            await transaction.commit()
            print("Database updated successfully.")
            # Send Slack notification with the inserted data
            await send_slack_message(data_to_insert)
            
            # Check price alerts
            print("🔹 Checking price alerts...")
            price_data = {}
            for item in data_to_insert:
                symbol = item["symbol"]
                try:
                    # Get current price
                    url = f"https://api.binance.com/api/v3/ticker/price"
                    params = {"symbol": symbol}
                    async with httpx.AsyncClient(timeout=5) as client:
                        res = await client.get(url, params=params)
                        if res.status_code == 200:
                            data = res.json()
                            price_data[symbol] = float(data["price"])
                except Exception as e:
                    print(f"   Error getting price for {symbol}: {e}")
            
            if price_data:
                triggered = check_multiple_alerts("crypto", price_data)
                print(f"🔔 Triggered {triggered} price alerts")
    else:
        print("No data to insert.")


# ================================
#  MAIN ENTRY
# ================================
async def main():
    conn = None
    try:
        db_port_str = os.environ.get('DB_PORT')
        if db_port_str is None:
            raise ValueError("Environment variable DB_PORT is not set.")

        conn = await asyncpg.connect(
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME'),
            host=os.environ.get('DB_HOST'),
            port=int(db_port_str)
        )

        await update_cryptos_watchlist(conn)

    except Exception as e:
        print("Error:", e)
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
