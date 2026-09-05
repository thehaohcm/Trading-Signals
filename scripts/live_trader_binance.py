"""
Binance Live Trading Execution Module for Breakout Radar
Supports Spot & USD-M Futures automated market entries and stop-loss placement using ccxt.
"""

import os
import ccxt
import traceback
import psycopg2
from dotenv import load_dotenv

# Load local environment
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)


def get_db_connection():
    """Get Postgres connection using env vars"""
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432)
    )


def get_binance_credentials_from_db():
    """Query Binance credentials from system_settings in PostgreSQL"""
    creds = {
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_API_SECRET', ''),
        'testnet': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
        'trade_amount_usdt': float(os.getenv('BINANCE_TRADE_AMOUNT_USDT', '20.0')),
        'trading_mode': os.getenv('TRADING_MODE', 'demo').lower()
    }
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT key, value FROM public.system_settings 
            WHERE key IN ('binance_api_key', 'binance_api_secret', 'binance_testnet', 'binance_trade_amount_usdt', 'trading_mode');
        """)
        rows = cur.fetchall()
        for k, v in rows:
            if k == 'binance_api_key' and v:
                creds['api_key'] = v
            elif k == 'binance_api_secret' and v:
                creds['api_secret'] = v
            elif k == 'binance_testnet' and v:
                creds['testnet'] = (v.lower() == 'true')
            elif k == 'binance_trade_amount_usdt' and v:
                try:
                    creds['trade_amount_usdt'] = float(v)
                except ValueError:
                    pass
            elif k == 'trading_mode' and v:
                creds['trading_mode'] = v.lower()
        cur.close()
    except Exception as e:
        print(f"⚠️ [Binance Trader] Error reading credentials from DB: {e}")
    finally:
        if conn:
            conn.close()
            
    return creds


def get_exchange_instance(asset_type='crypto', creds=None):
    """Create configured ccxt Binance instance (Spot or Futures)"""
    if creds is None:
        creds = get_binance_credentials_from_db()

    config = {
        'apiKey': creds.get('api_key'),
        'secret': creds.get('api_secret'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future' if asset_type == 'futures' else 'spot',
            'adjustForTimeDifference': True,
        }
    }
    
    exchange = ccxt.binance(config)
    if creds.get('testnet'):
        exchange.set_sandbox_mode(True)
        
    return exchange


def execute_binance_order(symbol, asset_type, amount_usd, sl_pct=5.0, layer=1, reason="Breakout Entry"):
    """
    Executes live Binance order:
    1. Places Market Buy for amount_usd
    2. Places Stop Loss limit/market sell order at -sl_pct%
    Returns dict with status, order_id, entry_price, filled_units, error.
    """
    creds = get_binance_credentials_from_db()
    
    # Format symbol for ccxt (e.g. BTCUSDT -> BTC/USDT or BTC/USDT:USDT)
    clean_sym = symbol.split(':')[-1].upper().replace('-', '').strip()
    if clean_sym.endswith('USDT'):
        base = clean_sym[:-4]
        symbol_ccxt = f"{base}/USDT"
    elif '/' in clean_sym:
        symbol_ccxt = clean_sym
    else:
        symbol_ccxt = f"{clean_sym}/USDT"
        
    if asset_type == 'futures' and ':' not in symbol_ccxt:
        symbol_ccxt = f"{symbol_ccxt}:USDT"

    if not creds.get('api_key') or not creds.get('api_secret'):
        return {
            'success': False,
            'simulated': False,
            'error': "Binance API Key hoặc API Secret chưa được cấu hình trong Database.",
            'symbol': symbol_ccxt
        }

    exchange = None
    try:
        exchange = get_exchange_instance(asset_type, creds)
        exchange.load_markets()

        if symbol_ccxt not in exchange.markets:
            # Fallback to standard symbol
            symbol_ccxt = symbol_ccxt.split(':')[0]
            if symbol_ccxt not in exchange.markets:
                return {
                    'success': False,
                    'error': f"Cặp giao dịch {symbol} không tìm thấy trên Binance {asset_type}.",
                    'symbol': symbol_ccxt
                }

        # 1. Fetch current ticker price
        ticker = exchange.fetch_ticker(symbol_ccxt)
        current_price = float(ticker.get('last') or ticker.get('close', 0))
        if current_price <= 0:
            return {
                'success': False,
                'error': f"Không thể lấy giá trực tiếp từ Binance cho {symbol_ccxt}.",
                'symbol': symbol_ccxt
            }

        # 2. Calculate quantity based on amount_usd
        raw_units = float(amount_usd) / current_price
        units_precision = float(exchange.amount_to_precision(symbol_ccxt, raw_units))

        # Check minimum notional / lot limits
        market = exchange.market(symbol_ccxt)
        min_cost = market.get('limits', {}).get('cost', {}).get('min', 5.0) or 5.0
        if (units_precision * current_price) < min_cost:
            return {
                'success': False,
                'error': f"Giá trị lệnh ({units_precision * current_price:.2f} USDT) nhỏ hơn mức tối thiểu ({min_cost} USDT).",
                'symbol': symbol_ccxt
            }

        print(f"🛒 [Binance Live Trader] Đang gửi lệnh MARKET BUY cho {symbol_ccxt} (Khối lượng: {units_precision} ~ {amount_usd} USDT)...")
        
        # 3. Place Market Buy Order
        order = exchange.create_market_buy_order(symbol_ccxt, units_precision)
        order_id = str(order.get('id', ''))
        entry_price = float(order.get('average') or order.get('price') or current_price)
        filled_units = float(order.get('filled') or units_precision)

        # 4. Calculate and place Stop-Loss order (-sl_pct%)
        stop_loss_price = entry_price * (1.0 - (float(sl_pct) / 100.0))
        stop_price_precision = float(exchange.price_to_precision(symbol_ccxt, stop_loss_price))
        
        sl_order_id = None
        try:
            if asset_type == 'spot' or asset_type == 'crypto':
                # Limit price slightly below stopPrice to guarantee fill
                limit_price_precision = float(exchange.price_to_precision(symbol_ccxt, stop_price_precision * 0.99))
                sl_order = exchange.create_order(
                    symbol=symbol_ccxt,
                    type='STOP_LOSS_LIMIT',
                    side='sell',
                    amount=filled_units,
                    price=limit_price_precision,
                    params={'stopPrice': stop_price_precision}
                )
                sl_order_id = str(sl_order.get('id', ''))
            else:
                # Futures stop market order
                sl_order = exchange.create_order(
                    symbol=symbol_ccxt,
                    type='STOP_MARKET',
                    side='sell',
                    amount=filled_units,
                    params={'stopPrice': stop_price_precision, 'reduceOnly': True}
                )
                sl_order_id = str(sl_order.get('id', ''))
        except Exception as sl_err:
            print(f"⚠️ [Binance Live Trader] Cảnh báo: Khớp lệnh Mua thành công nhưng đặt lệnh Stop Loss tự động gặp lỗi: {sl_err}")

        return {
            'success': True,
            'order_id': order_id,
            'sl_order_id': sl_order_id,
            'symbol': symbol_ccxt,
            'entry_price': entry_price,
            'units': filled_units,
            'total_cost': entry_price * filled_units,
            'stop_loss_price': stop_price_precision,
            'sl_pct': sl_pct,
            'layer': layer,
            'message': f"Đã khớp lệnh Binance thực tế: Mua {filled_units} {symbol_ccxt} tại giá {entry_price:,.4f} USDT (SL -{sl_pct}%: {stop_price_precision:,.4f})"
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol_ccxt
        }
