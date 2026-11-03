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


def execute_binance_order(symbol, asset_type, amount_usd, sl_pct=2.0, layer=1, reason="Breakout Entry", place_stop=True):
    """
    Executes live Binance order:
    1. Places Market Buy for amount_usd
    2. Places Stop Loss limit/market sell order at -sl_pct% (bỏ qua nếu place_stop=False — khi đó người gọi
       tự quản lý SL trên sàn bằng sync_binance_stop() theo TỔNG khối lượng vị thế).
    Returns dict with status, order_id, entry_price, filled_units, error, sl_placed, sl_error.
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
        sl_error = None
        try:
            if not place_stop:
                pass
            elif asset_type == 'spot' or asset_type == 'crypto':
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
            sl_error = str(sl_err)
            print(f"⚠️ [Binance Live Trader] Cảnh báo: Khớp lệnh Mua thành công nhưng đặt lệnh Stop Loss tự động gặp lỗi: {sl_err}")

        return {
            'success': True,
            'order_id': order_id,
            'sl_order_id': sl_order_id,
            'sl_placed': bool(sl_order_id),
            'sl_error': sl_error,
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


# ---------------------------------------------------------------------------
# Quản lý vòng đời lệnh dừng lỗ (SL) trên sàn
# ---------------------------------------------------------------------------

def _ccxt_symbol(symbol, asset_type):
    clean_sym = symbol.split(':')[-1].upper().replace('-', '').strip()
    if clean_sym.endswith('USDT'):
        sym = f"{clean_sym[:-4]}/USDT"
    elif '/' in clean_sym:
        sym = clean_sym
    else:
        sym = f"{clean_sym}/USDT"
    if asset_type == 'futures' and ':' not in sym:
        sym = f"{sym}:USDT"
    return sym


def _resolve_market_symbol(exchange, symbol_ccxt):
    if symbol_ccxt in exchange.markets:
        return symbol_ccxt
    alt = symbol_ccxt.split(':')[0]
    return alt if alt in exchange.markets else None


def _is_stop_order(o):
    return 'stop' in str(o.get('type') or '').lower() and str(o.get('side') or '').lower() == 'sell'


def _cancel_open_stops(exchange, symbol_ccxt):
    """Huỷ mọi lệnh SL (bán, loại stop*) đang mở của symbol. Trả về số lệnh đã huỷ. Lỗi huỷ → raise."""
    cancelled = 0
    for o in exchange.fetch_open_orders(symbol_ccxt):
        if _is_stop_order(o):
            exchange.cancel_order(o['id'], symbol_ccxt)
            cancelled += 1
    return cancelled


def _base_of(symbol_ccxt):
    return symbol_ccxt.split('/')[0]


def _futures_position_size(exchange, symbol_ccxt):
    try:
        for p in exchange.fetch_positions([symbol_ccxt]):
            c = abs(float(p.get('contracts') or 0))
            if c > 0:
                return c
    except Exception:
        return None
    return 0.0


def cancel_binance_stops(symbol, asset_type='crypto'):
    """Huỷ tất cả lệnh SL đang mở của symbol (giải phóng số dư bị khoá trên Spot)."""
    creds = get_binance_credentials_from_db()
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key', 'cancelled': 0}
    try:
        exchange = get_exchange_instance(asset_type, creds)
        exchange.load_markets()
        sym = _resolve_market_symbol(exchange, _ccxt_symbol(symbol, asset_type))
        if not sym:
            return {'success': False, 'error': f'Không tìm thấy cặp {symbol}', 'cancelled': 0}
        return {'success': True, 'cancelled': _cancel_open_stops(exchange, sym)}
    except Exception as e:
        return {'success': False, 'error': str(e), 'cancelled': 0}


def sync_binance_stop(symbol, asset_type, units, stop_price, limit_buffer_pct=1.0):
    """
    Đặt lại MỘT lệnh SL duy nhất phủ TOÀN BỘ khối lượng vị thế:
      1. huỷ mọi SL cũ của symbol (các tầng nhồi trước đó / SL đã lỗi thời),
      2. (Spot) giới hạn khối lượng theo số dư free thực tế sau khi huỷ,
      3. đặt SL mới tại stop_price (Spot: STOP_LOSS_LIMIT, Futures: STOP_MARKET reduceOnly).
    Lưu ý: trên Spot phải huỷ trước khi đặt mới (SL cũ khoá số dư) nên có khoảng trống ngắn (~1 giây) không có SL.
    Trả về dict: success, sl_order_id, stop_price, units, cancelled, error.
    """
    creds = get_binance_credentials_from_db()
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key', 'cancelled': 0}
    cancelled = 0
    try:
        exchange = get_exchange_instance(asset_type, creds)
        exchange.load_markets()
        sym = _resolve_market_symbol(exchange, _ccxt_symbol(symbol, asset_type))
        if not sym:
            return {'success': False, 'error': f'Không tìm thấy cặp {symbol}', 'cancelled': 0}

        cancelled = _cancel_open_stops(exchange, sym)

        want = float(units or 0)
        if asset_type == 'futures':
            size = _futures_position_size(exchange, sym)
            if size is not None:
                want = size
        else:
            free = float(exchange.fetch_balance().get(_base_of(sym), {}).get('free') or 0)
            want = min(want, free) if want > 0 else free
        qty = float(exchange.amount_to_precision(sym, want)) if want > 0 else 0.0
        if qty <= 0:
            return {'success': False, 'error': 'Không còn khối lượng để đặt SL (vị thế có thể đã được đóng).', 'cancelled': cancelled}

        stop_p = float(exchange.price_to_precision(sym, float(stop_price)))
        if asset_type == 'futures':
            order = exchange.create_order(sym, 'STOP_MARKET', 'sell', qty, None,
                                          {'stopPrice': stop_p, 'reduceOnly': True})
        else:
            limit_p = float(exchange.price_to_precision(sym, stop_p * (1.0 - limit_buffer_pct / 100.0)))
            order = exchange.create_order(sym, 'STOP_LOSS_LIMIT', 'sell', qty, limit_p, {'stopPrice': stop_p})
        return {'success': True, 'sl_order_id': str(order.get('id', '')), 'stop_price': stop_p,
                'units': qty, 'cancelled': cancelled}
    except Exception as e:
        return {'success': False, 'error': str(e), 'cancelled': cancelled}


def get_binance_spot_balance(symbol):
    """
    Fetch Spot balance for a given symbol from Binance using ccxt.
    Returns free, locked, total units, current price, and estimated USD value.
    """
    clean_sym = symbol.split(':')[-1].upper().replace('-', '').strip()
    if clean_sym.endswith('USDT'):
        base = clean_sym[:-4]
    elif '/' in clean_sym:
        base = clean_sym.split('/')[0]
    else:
        base = clean_sym

    creds = get_binance_credentials_from_db()
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key sàn Binance.', 'base': base, 'total': 0}

    try:
        exchange = get_exchange_instance('spot', creds)
        balance = exchange.fetch_balance()
        base_bal = balance.get(base, {})
        free = float(base_bal.get('free') or 0)
        used = float(base_bal.get('used') or 0)
        total = float(base_bal.get('total') or (free + used))

        # Get price
        symbol_ccxt = f"{base}/USDT"
        current_price = 0.0
        try:
            ticker = exchange.fetch_ticker(symbol_ccxt)
            current_price = float(ticker.get('last') or ticker.get('close', 0))
        except Exception:
            pass

        return {
            'success': True,
            'base': base,
            'free': free,
            'locked': used,
            'total': total,
            'price': current_price,
            'usd_value': total * current_price if current_price > 0 else 0
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'base': base, 'total': 0}


def execute_binance_sell_market(symbol, units=None, asset_type='crypto'):
    """
    Đóng vị thế thật trên Binance bằng lệnh bán market.
    - Huỷ trước mọi lệnh SL đang mở của symbol (trên Spot chúng khoá số dư nên bán sẽ lỗi "insufficient balance").
    - Spot: bán tối đa số dư free thực tế. Futures: reduceOnly để không bao giờ mở vị thế ngược.
    - Nếu sàn đã tự đóng vị thế (SL của sàn khớp) → success + already_closed=True.
    """
    creds = get_binance_credentials_from_db()
    symbol_ccxt = _ccxt_symbol(symbol, asset_type)
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key'}

    try:
        exchange = get_exchange_instance(asset_type, creds)
        exchange.load_markets()
        resolved = _resolve_market_symbol(exchange, symbol_ccxt)
        if resolved:
            symbol_ccxt = resolved
        base = _base_of(symbol_ccxt)

        cancelled = _cancel_open_stops(exchange, symbol_ccxt)

        if asset_type == 'futures':
            size = _futures_position_size(exchange, symbol_ccxt)
            if size == 0.0:
                return {'success': True, 'already_closed': True, 'order_id': '', 'filled': 0.0, 'price': 0.0,
                        'cancelled_stops': cancelled,
                        'message': f"Vị thế {symbol_ccxt} đã được đóng sẵn trên sàn (SL của sàn đã khớp)."}
            want = size if size is not None else float(units or 0)
        else:
            free = float(exchange.fetch_balance().get(base, {}).get('free', 0) or 0)
            want = min(float(units), free) if (units and units > 0 and free > 0) else free

        units_precision = float(exchange.amount_to_precision(symbol_ccxt, want)) if want > 0 else 0.0
        if units_precision <= 0:
            return {'success': True, 'already_closed': True, 'order_id': '', 'filled': 0.0, 'price': 0.0,
                    'cancelled_stops': cancelled,
                    'message': f"Không còn {base} để bán — vị thế đã được đóng sẵn trên sàn (SL của sàn đã khớp hoặc bán tay)."}

        print(f"🛑 [Binance Live Trader] Đang gửi lệnh BÁN MARKET THỰC TẾ cho {units_precision} {symbol_ccxt} (Cắt Lỗ)...")
        params = {'reduceOnly': True} if asset_type == 'futures' else {}
        order = exchange.create_market_sell_order(symbol_ccxt, units_precision, params)
        return {
            'success': True,
            'order_id': str(order.get('id', '')),
            'filled': float(order.get('filled') or units_precision),
            'price': float(order.get('average') or order.get('price') or 0),
            'cancelled_stops': cancelled,
            'message': f"Đã bán khẩn cấp {units_precision} {symbol_ccxt} trên Binance ({'Futures' if asset_type == 'futures' else 'Spot'})."
        }
    except Exception as e:
        print(f"⚠️ [Binance Live Trader] Lỗi bán khẩn cấp {symbol_ccxt}: {e}")
        return {'success': False, 'error': str(e)}
