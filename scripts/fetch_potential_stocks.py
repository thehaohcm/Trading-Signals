import asyncio
import httpx
import time
import asyncpg
import os
import json
from price_alert_utils import check_multiple_alerts

async def get_avg_volume_price(ticket, number_of_day):
    current_unix_ts = str(int(time.time()))
    # TODO: Adjust the base URL if your app is not running on localhost:8080
    url = f"https://apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars-long-term?ticker={ticket}&type=stock&resolution=D&to={current_unix_ts}&countBack={number_of_day}"
    # Note: If the frontend (Vue.js app) is making requests to a different domain,
    # you might encounter CORS issues.  If so, you'll need to configure the server
    # hosting the API (where /stock-insight/v2/... is served) to send the appropriate
    # Access-Control-Allow-Origin headers. This Python script runs outside the browser,
    # so CORS doesn't directly affect it.
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            if res.status_code == 200:
                json_body = res.json()
                data_list = json_body.get('data')
                if not data_list:
                    print("No data found for", ticket)
                    return None, None
                sum_vol = 0
                sum_price = 0
                for data in data_list:
                    vol = data.get('volume', 0)  # Provide a default value
                    sum_vol += vol
                    sum_price += data.get('close', 0)  # Provide a default value

                avg_vol = int(sum_vol / len(data_list))
                avg_price = int(sum_price / len(data_list))
                return avg_vol, avg_price
            else:
                print("Error fetching data:", res.status_code)
                return None, None

    except httpx.HTTPError as e:
        print("exception", e)
        return None, None


async def send_slack_message(symbols_list):
    """Send potential stock symbols to Slack"""
    slack_enabled = os.environ.get('SLACK_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    if not slack_enabled:
        print("Slack notifications disabled, skipping")
        return
    
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not slack_webhook_url:
        print("SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return
    
    if not symbols_list:
        print("No potential stocks to report")
        return
    
    # Format message
    symbols_text = "\n".join([f"• *{s[0]}* - Highest: {s[1]:,}, Lowest: {s[2]:,}" for s in symbols_list])
    message = {
        "text": f"*Potential Stocks Detected ({len(symbols_list)} symbols)*\n\n{symbols_text}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                slack_webhook_url,
                json=message,
                timeout=10.0
            )
            if response.status_code == 200:
                print(f"Slack notification sent successfully ({len(symbols_list)} stocks)")
            else:
                print(f"Failed to send Slack notification: {response.status_code}")
    except Exception as e:
        print(f"Error sending Slack message: {e}")


async def fetch_potential_stocks(stocks, conn):
    # controller is not directly translatable; httpx handles timeouts
    async with httpx.AsyncClient() as client:
        data_to_insert = []  # List to accumulate data for bulk insertion
        for stock in stocks:
            try:
                # Use timeout to handle potential network issues
                response = await client.get(f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/ticker/{stock['code']}/price-volatility", timeout=10.0)
                response.raise_for_status()
                await asyncio.sleep(1)
                data = response.json()

                if data.get('highestPricePercent') >= -0.05:  # Use .get() for safety
                    avg_vol_9, avg_price_9 = await get_avg_volume_price(stock['code'], 9)
                    if avg_vol_9 is not None and avg_vol_9 > 500000:
                        avg_vol_20, avg_price_20 = await get_avg_volume_price(stock['code'], 20)
                        await asyncio.sleep(1)
                        avg_vol_50, avg_price_50 = await get_avg_volume_price(stock['code'], 50)
                        await asyncio.sleep(1)
                        if avg_price_9 is not None and avg_price_20 is not None and avg_price_50 is not None and (avg_price_9 > avg_price_20 or avg_price_20 > avg_price_50):
                            data_to_insert.append((data['ticker'], data['highestPrice'], data['lowestPrice']))

            except httpx.RequestError as e:
                print(f"Network error for {stock['code']}: {e}")
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for {stock['code']}: {e}")
            except asyncio.TimeoutError:
                print(f"Timeout for {stock['code']}")
            except Exception as e:
                print(f"Error for {stock['code']}: {e}")

            await asyncio.sleep(1)
            
        # Delete all items before adding
        transaction = conn.transaction()
        await transaction.start()
        try:
            await conn.execute('''
                DELETE FROM symbols_watchlist
            ''')
        except asyncpg.PostgresError as e:
            print(f"Error deleting existing data: {e}")
            await transaction.rollback()
            return  # Exit if deletion fails
        else:
            await transaction.commit()
            
        # adding new items
        transaction = conn.transaction()
        await transaction.start()
        try:
            if data_to_insert:
                await conn.executemany('''
                    INSERT INTO symbols_watchlist (symbol, highest_price, lowest_price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (symbol) DO UPDATE
                    SET highest_price = EXCLUDED.highest_price, lowest_price = EXCLUDED.lowest_price
                ''', data_to_insert)
        except asyncpg.PostgresError as e:
            print(f"Database error during bulk insert: {e}")
            await transaction.rollback()
        else:
            await transaction.commit()
            # Send Slack notification with the inserted data
            await send_slack_message(data_to_insert)

async def update_current_prices_portfolio(conn):
    try:
        # Get all data from the user_trading_symbols table
        symbols = await conn.fetch('SELECT symbol FROM user_trading_symbols')

        data_to_update = []
        async with httpx.AsyncClient() as client:
            for record in symbols:
                symbol = record['symbol']
                url = f"https://services.entrade.com.vn/dnse-financial-product/securities/{symbol}"
                try:
                    response = await client.get(url, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()
                    basic_price = data.get('basicPrice')  # Use .get() for safety
                    if basic_price is not None:
                        data_to_update.append((basic_price, symbol))  #price, symbol
                    else:
                        data_to_update.append((0, symbol)) # Default to 0 if basic_price is None
                except httpx.RequestError as e:
                    print(f"Network error for {symbol}: {e}")
                except httpx.HTTPStatusError as e:
                    print(f"HTTP error for {symbol}: {e}")
                except asyncio.TimeoutError:
                    print(f"Timeout for {symbol}")
                except Exception as e:
                    print(f"Error for {symbol}: {e}")

                await asyncio.sleep(1) # Comply with rate limit

        # Update the current_price field in the database using a single SQL statement
        if data_to_update:
            transaction = conn.transaction()
            await transaction.start()
            try:
                await conn.executemany('''
                    UPDATE user_trading_symbols
                    SET current_price = $1
                    WHERE symbol = $2
                ''', data_to_update)
            except asyncpg.PostgresError as e:
                print(f"Database error during bulk update: {e}")
                await transaction.rollback()
            else:
                await transaction.commit()


    except Exception as e:
        print(f"An error occurred: {e}")

async def main():
    # Fetch stock data
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            }
            response = await client.get("https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000", headers=headers)
            response.raise_for_status()
            stocks_data = response.json().get('data', [])
    except httpx.HTTPError as e:
        print(f"Error fetching stock data: {e}")
        return

    # Database connection
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

        stocks_data = [item for item in stocks_data if len(item['code']) == 3]

        await fetch_potential_stocks(stocks_data, conn)

        await update_current_prices_portfolio(conn)
        
        # Check price alerts for stocks
        print("🔹 Checking price alerts for stocks...")
        stocks_in_watchlist = await conn.fetch('SELECT symbol, highest_price FROM symbols_watchlist')
        price_data = {}
        for record in stocks_in_watchlist:
            symbol = record['symbol']
            highest_price = record['highest_price']
            if highest_price and highest_price > 0:
                price_data[symbol] = float(highest_price) / 1000.0  # Convert to thousands
        
        if price_data:
            triggered = check_multiple_alerts("stock", price_data)
            print(f"🔔 Triggered {triggered} stock price alerts")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())