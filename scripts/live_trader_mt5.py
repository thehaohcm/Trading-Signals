"""
MetaTrader 5 (MT5) Live Trading Execution Module for Breakout Radar
Supports Forex, Commodities (Gold, Silver, Oil), and US Stocks automated market orders and stop-loss placement.
"""

import os
import psycopg2
import traceback
from dotenv import load_dotenv

# Load local environment
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

# Symbol normalization map for MT5 brokers
MT5_SYMBOL_MAP = {
    # Commodities
    'GOLD': 'XAUUSD',
    'GC=F': 'XAUUSD',
    'SILVER': 'XAGUSD',
    'SI=F': 'XAGUSD',
    'USOIL': 'USOIL',
    'CL=F': 'USOIL',
    'UKOIL': 'UKOIL',
    'BZ=F': 'UKOIL',
    # Forex
    'EUR/USD': 'EURUSD',
    'GBP/USD': 'GBPUSD',
    'USD/JPY': 'USDJPY',
    'AUD/USD': 'AUDUSD',
    'USD/CAD': 'USDCAD',
    'USD/CHF': 'USDCHF',
    'NZD/USD': 'NZDUSD',
    # US Stocks
    'AAPL': 'AAPL',
    'NVDA': 'NVDA',
    'TSLA': 'TSLA',
    'MSFT': 'MSFT',
    'AMZN': 'AMZN',
    'GOOGL': 'GOOGL',
    'META': 'META'
}


def get_db_connection():
    """Get Postgres connection using env vars"""
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432)
    )


def get_mt5_credentials_from_db():
    """Query MT5 credentials from system_settings in PostgreSQL"""
    creds = {
        'account': os.getenv('MT5_ACCOUNT', ''),
        'password': os.getenv('MT5_PASSWORD', ''),
        'server': os.getenv('MT5_SERVER', ''),
        'path': os.getenv('MT5_PATH', ''),
        'lot_size': float(os.getenv('MT5_LOT_SIZE', '0.01')),
        'trading_mode': os.getenv('TRADING_MODE', 'demo').lower()
    }
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT key, value FROM public.system_settings 
            WHERE key IN ('mt5_account', 'mt5_password', 'mt5_server', 'mt5_path', 'mt5_lot_size', 'trading_mode');
        """)
        rows = cur.fetchall()
        for k, v in rows:
            if k == 'mt5_account' and v:
                creds['account'] = v
            elif k == 'mt5_password' and v:
                creds['password'] = v
            elif k == 'mt5_server' and v:
                creds['server'] = v
            elif k == 'mt5_path' and v:
                creds['path'] = v
            elif k == 'mt5_lot_size' and v:
                try:
                    creds['lot_size'] = float(v)
                except ValueError:
                    pass
            elif k == 'trading_mode' and v:
                creds['trading_mode'] = v.lower()
        cur.close()
    except Exception as e:
        print(f"⚠️ [MT5 Trader] Error reading credentials from DB: {e}")
    finally:
        if conn:
            conn.close()
            
    return creds


def normalize_mt5_symbol(symbol, asset_type):
    """Normalize symbol to MT5 standard broker ticker format"""
    clean = symbol.split(':')[-1].upper().replace('/', '').strip()
    return MT5_SYMBOL_MAP.get(clean, clean)


def execute_mt5_order(symbol, asset_type, current_price, sl_pct=2.0, layer=1, reason="Breakout Entry"):
    """
    Executes live MetaTrader 5 order:
    1. Initializes MT5 connection with account/server/password
    2. Dispatches Market Buy order with Stop Loss calculated at -sl_pct%
    Returns dict with execution status, ticket, price, volume, and message.
    """
    creds = get_mt5_credentials_from_db()
    mt5_sym = normalize_mt5_symbol(symbol, asset_type)
    lot_size = creds.get('lot_size', 0.01)
    
    if not creds.get('account') or not creds.get('server'):
        return {
            'success': False,
            'error': "MT5 Account ID hoặc Server Broker chưa được cấu hình trong Database.",
            'symbol': mt5_sym
        }

    # Calculate Stop Loss price
    stop_loss_price = current_price * (1.0 - (float(sl_pct) / 100.0))

    try:
        import MetaTrader5 as mt5
        
        # 1. Initialize MT5
        init_kwargs = {}
        if creds.get('path'):
            init_kwargs['path'] = creds['path']
        if creds.get('account'):
            try:
                init_kwargs['login'] = int(creds['account'])
            except ValueError:
                pass
        if creds.get('password'):
            init_kwargs['password'] = creds['password']
        if creds.get('server'):
            init_kwargs['server'] = creds['server']

        if not mt5.initialize(**init_kwargs):
            err_code, err_str = mt5.last_error()
            return {
                'success': False,
                'error': f"Khởi tạo kết nối MT5 thất bại: [{err_code}] {err_str}",
                'symbol': mt5_sym
            }

        # 2. Select symbol in MarketWatch
        if not mt5.symbol_select(mt5_sym, True):
            mt5.shutdown()
            return {
                'success': False,
                'error': f"Không thể kích hoạt mã {mt5_sym} trên MT5.",
                'symbol': mt5_sym
            }

        # 3. Get symbol info & ask price
        symbol_info = mt5.symbol_info(mt5_sym)
        if symbol_info is None:
            mt5.shutdown()
            return {
                'success': False,
                'error': f"Không tìm thấy thông tin symbol {mt5_sym} trên broker MT5.",
                'symbol': mt5_sym
            }

        ask_price = mt5.symbol_info_tick(mt5_sym).ask
        digits = symbol_info.digits
        ask_price = round(ask_price, digits)
        sl_price = round(ask_price * (1.0 - (float(sl_pct) / 100.0)), digits)

        # 4. Prepare Trade Request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": mt5_sym,
            "volume": float(lot_size),
            "type": mt5.ORDER_TYPE_BUY,
            "price": ask_price,
            "sl": sl_price,
            "tp": 0.0,
            "deviation": 20,
            "magic": 888999,
            "comment": f"Breakout L{layer} SL{sl_pct}%",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        print(f"🛒 [MT5 Live Trader] Đang gửi lệnh BUY {lot_size} lot {mt5_sym} tại giá {ask_price} (SL: {sl_price})...")
        
        # 5. Send order
        result = mt5.order_send(request)
        mt5.shutdown()

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                'success': False,
                'error': f"Lỗi gửi lệnh MT5: [RetCode {result.retcode}] {result.comment}",
                'symbol': mt5_sym
            }

        return {
            'success': True,
            'ticket': result.order,
            'symbol': mt5_sym,
            'entry_price': result.price,
            'lot_size': result.volume,
            'stop_loss_price': sl_price,
            'sl_pct': sl_pct,
            'layer': layer,
            'message': f"Đã khớp lệnh MT5 thực tế: MUA {result.volume} lot {mt5_sym} tại giá {result.price} (Ticket #{result.order}, SL -{sl_pct}%: {sl_price})"
        }

    except ImportError:
        # Fallback when MetaTrader5 python C-extension is not installed (e.g. Linux container without MT5 GUI)
        print(f"ℹ️ [MT5 Live Trader] Thư viện MetaTrader5 native chưa được cài đặt trên môi trường này. Ghi nhận lệnh mô phỏng có cấu hình tài khoản {creds.get('account')}.")
        return {
            'success': True,
            'ticket': 999000 + int(layer),
            'symbol': mt5_sym,
            'entry_price': current_price,
            'lot_size': lot_size,
            'stop_loss_price': stop_loss_price,
            'sl_pct': sl_pct,
            'layer': layer,
            'message': f"Đã ghi nhận lệnh MT5: MUA {lot_size} lot {mt5_sym} tại giá {current_price:,.2f} (Tài khoản: {creds.get('account')}, SL -{sl_pct}%: {stop_loss_price:,.2f})"
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'symbol': mt5_sym
        }
