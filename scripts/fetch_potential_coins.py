import asyncio
import asyncpg
import time
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

EXCLUDE_KEYWORDS = ["USDC", "USDE", "FDUSD", "USD1", "TUSD", "USDD", "USDP", "DAI"]

# ================================
#  BINANCE + COINGECKO FUNCTIONS
# ================================
async def get_usdt_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(url)
        res.raise_for_status()
        data = res.json()["symbols"]
        return [
            s["symbol"] for s in data
            if s["quoteAsset"] == "USDT"
            and s["status"] == "TRADING"
            and not any(s["baseAsset"].upper().startswith(k) for k in EXCLUDE_KEYWORDS)
        ]


async def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(url, params={
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 100,
            "page": 1
        })
        res.raise_for_status()
        return res.json()


async def get_52week_high(symbol):
    try:
        url = "https://api.binance.com/api/v3/klines"
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(days=365)).timestamp() * 1000)
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000
        }
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return None
            klines = res.json()
            if not klines:
                return None
            highs = [float(k[2]) for k in klines]
            closes = [float(k[4]) for k in klines]
            high_52w = max(highs)
            current = closes[-1]
            if current >= 0.95 * high_52w:
                return {"symbol": symbol, "is_ath": False}
    except Exception:
        return None


# ================================
#  DATABASE UPDATE LOGIC
# ================================
async def update_cryptos_watchlist(conn):
    print("🔹 Fetching USDT pairs...")
    usdt_pairs = set(await get_usdt_pairs())

    print("🔹 Fetching top coins...")
    top_coins = await get_top_coins()

    # --- Giai đoạn lọc coin gần ATH ---
    near_ath = [
        {"symbol": c["symbol"].upper() + "USDT", "is_ath": True}
        for c in top_coins
        if (c["symbol"].upper() + "USDT") in usdt_pairs
        and c.get("ath_change_percentage") is not None
        and c["ath_change_percentage"] > -5
    ]

    # --- Giai đoạn lọc coin gần đỉnh 52 tuần ---
    print("🔹 Checking 52-week highs...")
    near_52w = []
    for c in top_coins:
        symbol = c["symbol"].upper() + "USDT"
        if symbol in usdt_pairs:
            res = await get_52week_high(symbol)
            if res:
                near_52w.append(res)
            await asyncio.sleep(0.5)  # tránh rate-limit

    data_to_insert = near_ath + near_52w

    # --- Transaction-safe upsert ---
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
            print("❌ Database error:", e)
            await transaction.rollback()
        else:
            await transaction.commit()
            print("✅ Database updated successfully.")
    else:
        print("⚠️ No data to insert.")


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
        print("❌ Error:", e)
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
