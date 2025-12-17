import asyncio
import httpx
import time
import asyncpg
import os
import json
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Configuration constants
MIN_TRADE_VOLUME = 50000  # Minimum trade volume threshold for stock filtering 

async def send_slack_error(error_message):
    """Send error message to Slack"""
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not slack_webhook_url:
        return
    
    message = {
        "text": f"🚨 *Error in fetch_potential_stocks.py*\n\n{error_message}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                slack_webhook_url,
                json=message,
                timeout=10.0
            )
    except Exception:
        pass  # Silently fail if Slack notification fails


async def send_slack_message(symbols_list):
    """Send potential stock symbols to Slack"""
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
                print(f"✅ Slack notification sent successfully ({len(symbols_list)} stocks)")
            else:
                print(f"⚠️ Failed to send Slack notification: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending Slack message: {e}")


async def get_stock_volume(client, stock_code, token):
    """Get trade volume for a stock from stockratio API"""
    try:
        volume_response = await client.get(
            f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/ticker/{stock_code}/stockratio",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10.0
        )
        volume_response.raise_for_status()
        volume_data = volume_response.json()
        return volume_data.get('tradeVolume')
    except Exception as e:
        print(f"⚠️ Error fetching volume for {stock_code}: {e}")
        return None


async def get_tcbs_token():
    """Login to TCBS and get authentication token"""
    login_url = "https://apipub.tcbs.com.vn/authen/v1/login"
    
    # Check if credentials are set
    username = os.environ.get('TCBS_USR')
    password = os.environ.get('TCBS_PWD')
    
    if not username or not password:
        error_msg = "❌ TCBS_USR or TCBS_PWD environment variables are not set"
        print(error_msg)
        await send_slack_error(error_msg)
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://tcinvest.tcbs.com.vn/"
    }
    login_data = {
        "username": username,
        "password": password,
        "device_info": '{"os.name":"macOS","os.version":"10.15","browser.name":"Chrome","browser.version":"120","device.platform":"web","device.name":"Chrome Mac","device.physicalID":"tcbs-bot-001","navigator.userAgent":"Mozilla/5.0","webVersion":"stable"}'
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"🔐 Attempting login with username: {username[:3]}***")
            response = await client.post(login_url, json=login_data, headers=headers, timeout=10.0)
            
            # Check for 400 error and show response body
            if response.status_code == 400:
                try:
                    error_detail = response.json()
                    error_msg = f"❌ TCBS login failed (400 Bad Request): {error_detail}"
                except:
                    error_msg = f"❌ TCBS login failed (400 Bad Request): {response.text}"
                print(error_msg)
                await send_slack_error(error_msg)
                return None
            
            response.raise_for_status()
            result = response.json()
            token = result.get('token')
            if token:
                print("✅ TCBS login successful, token obtained")
                return token
            else:
                error_msg = f"⚠️ No token in response. Response: {result}"
                print(error_msg)
                await send_slack_error(error_msg)
                return None
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ Error getting TCBS token: {e}"
        print(error_msg)
        await send_slack_error(error_msg)
        return None
    except Exception as e:
        error_msg = f"❌ Unexpected error getting TCBS token: {e}"
        print(error_msg)
        await send_slack_error(error_msg)
        return None


async def fetch_potential_stocks(stocks, conn):
    # Get authentication token first
    token = await get_tcbs_token()
    if not token:
        print("❌ Failed to get authentication token, aborting...")
        return
    
    print(f"token: {token}")
    
    # controller is not directly translatable; httpx handles timeouts
    async with httpx.AsyncClient() as client:
        data_to_insert = []  # List to accumulate data for bulk insertion
        
        # Set up headers with Bearer token matching curl format
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        for stock in stocks:
            try:
                # Use timeout to handle potential network issues
                response = await client.get(
                    f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/ticker/{stock['code']}/price-volatility",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                await asyncio.sleep(1)
                data = response.json()

                highest_price_percent = data.get('highestPricePercent')
                if highest_price_percent is not None and highest_price_percent >= -0.05:
                    # Check trade volume from stockratio API
                    trade_volume = await get_stock_volume(client, stock['code'], token)
                    
                    if trade_volume is not None and trade_volume >= MIN_TRADE_VOLUME:
                        print(f"🔹 Potential stock found: {stock['code']} (Volume: {trade_volume:,})")
                        data_to_insert.append((data['ticker'], data['highestPrice'], data['lowestPrice']))
                    else:
                        print(f"⚠️ {stock['code']} skipped - Volume too low: {trade_volume} (min: {MIN_TRADE_VOLUME:,})")
                    
                    await asyncio.sleep(0.5)  # Rate limiting

            except httpx.RequestError as e:
                print(f"Network error for {stock['code']}: {e}")
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for {stock['code']}: {e}")
            except asyncio.TimeoutError:
                print(f"Timeout for {stock['code']}")
            except Exception as e:
                print(f"Error for {stock['code']}: {e}")

            await asyncio.sleep(1)
            
        # Delete all items and add new items in a single transaction to avoid duplicates
        transaction = conn.transaction()
        await transaction.start()
        try:
            # Delete all existing data
            await conn.execute('''
                DELETE FROM symbols_watchlist
            ''')
            # Insert new items
            if data_to_insert:
                await conn.executemany('''
                    INSERT INTO symbols_watchlist (symbol, highest_price, lowest_price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (symbol) DO UPDATE
                    SET highest_price = EXCLUDED.highest_price, lowest_price = EXCLUDED.lowest_price
                ''', data_to_insert)
        except asyncpg.PostgresError as e:
            error_msg = f"❌ Database error during transaction: {e}"
            print(error_msg)
            await transaction.rollback()
            await send_slack_error(error_msg)
        else:
            await transaction.commit()
            print(f"✅ Database updated successfully with {len(data_to_insert)} stocks")
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

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())