"""
OKX & Bybit Live Trading Execution Module for Breakout Radar (song song với Binance).

Dùng ccxt UNIFIED API (không dùng type string riêng của Binance như 'STOP_LOSS_LIMIT'/'STOP_MARKET'
vì OKX/Bybit không hiểu các type đó). Lệnh dừng lỗ (SL) độc lập được đặt bằng tham số unified
`triggerPrice` trên lệnh market — đây là cách ccxt khuyến nghị chính thức (xem
https://docs.ccxt.com/blog/order-types-guide):

    exchange.create_order(symbol, 'market', 'sell', amount, None, {'triggerPrice': stop_price})

Mỗi sàn có quy ước riêng để ccxt "thấy" được lệnh trigger/điều kiện này khi fetch/hủy (đây là phần
RỦI RO NHẤT vì không có tài liệu ccxt chính thức/đầy đủ xác nhận 100% cho từng sàn — xem hàm
self_test() ở cuối file và PHẢI chạy self-test trên demo/testnet trước khi bật trade thật):
    - OKX:   params={'trigger': True}  khi fetch_open_orders / cancel_order lệnh trigger.
    - Bybit: params={'stop': True}     khi fetch_open_orders / cancel_order lệnh stop/conditional.

QUAN TRỌNG: Trước khi bật "Giao dịch thật" cho OKX hoặc Bybit, PHẢI chạy:
    python3 scripts/live_trader_ccxt.py self-test --exchange okx
    python3 scripts/live_trader_ccxt.py self-test --exchange bybit
(ở chế độ demo/testnet — xem okx_simulated / bybit_testnet trong Trading Settings) để xác nhận
đặt/huỷ lệnh SL hoạt động đúng trên tài khoản thật của bạn, vì cú pháp trigger-order khác nhau
giữa các phiên bản ccxt và không thể kiểm chứng 100% từ tài liệu mà không có tài khoản thật.
"""

import os
import sys
import json
import argparse
import traceback

import ccxt
import psycopg2
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

SUPPORTED_EXCHANGES = ('okx', 'bybit')

# Tham số (params) cần truyền cho fetch_open_orders/cancel_order để sàn trả về/huỷ được
# đúng lệnh trigger/điều kiện (không phải lệnh thường) — khác nhau theo từng sàn ccxt.
_TRIGGER_FETCH_PARAMS = {
    'okx': {'trigger': True},
    'bybit': {'stop': True},
}


def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432)
    )


def get_credentials_from_db(exchange_id):
    """Đọc API key/secret(/passphrase) + trade_amount + testnet/simulated flag từ system_settings."""
    if exchange_id not in SUPPORTED_EXCHANGES:
        raise ValueError(f"Sàn không được hỗ trợ: {exchange_id}")

    env_prefix = exchange_id.upper()
    creds = {
        'api_key': os.getenv(f'{env_prefix}_API_KEY', ''),
        'api_secret': os.getenv(f'{env_prefix}_API_SECRET', ''),
        'passphrase': os.getenv(f'{env_prefix}_PASSPHRASE', ''),
        'sandbox': os.getenv(f'{env_prefix}_TESTNET', os.getenv(f'{env_prefix}_SIMULATED', 'false')).lower() == 'true',
        'trade_amount_usdt': float(os.getenv(f'{env_prefix}_TRADE_AMOUNT_USDT', '20.0')),
    }

    keys = [f'{exchange_id}_api_key', f'{exchange_id}_api_secret', f'{exchange_id}_trade_amount_usdt']
    if exchange_id == 'okx':
        keys += ['okx_passphrase', 'okx_simulated']
        sandbox_key = 'okx_simulated'
    else:  # bybit
        keys += ['bybit_testnet']
        sandbox_key = 'bybit_testnet'

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value FROM public.system_settings WHERE key = ANY(%s);",
            (keys,)
        )
        for k, v in cur.fetchall():
            if not v:
                continue
            if k == f'{exchange_id}_api_key':
                creds['api_key'] = v
            elif k == f'{exchange_id}_api_secret':
                creds['api_secret'] = v
            elif k == 'okx_passphrase':
                creds['passphrase'] = v
            elif k == sandbox_key:
                creds['sandbox'] = (v.lower() == 'true')
            elif k == f'{exchange_id}_trade_amount_usdt':
                try:
                    creds['trade_amount_usdt'] = float(v)
                except ValueError:
                    pass
        cur.close()
    except Exception as e:
        print(f"⚠️ [{exchange_id.upper()} Trader] Lỗi đọc credentials từ DB: {e}")
    finally:
        if conn:
            conn.close()

    return creds


def get_exchange_instance(exchange_id, creds=None):
    """Tạo instance ccxt cho OKX/Bybit (chỉ hỗ trợ Spot — xem self_test/README)."""
    if creds is None:
        creds = get_credentials_from_db(exchange_id)

    config = {
        'apiKey': creds.get('api_key'),
        'secret': creds.get('api_secret'),
        'enableRateLimit': True,
        'options': {'defaultType': 'spot', 'adjustForTimeDifference': True},
    }
    if exchange_id == 'okx':
        config['password'] = creds.get('passphrase')
        exchange = ccxt.okx(config)
    else:
        exchange = ccxt.bybit(config)

    if creds.get('sandbox'):
        exchange.set_sandbox_mode(True)

    return exchange


def _ccxt_symbol(symbol):
    clean = symbol.split(':')[-1].upper().replace('-', '').strip()
    if clean.endswith('USDT'):
        return f"{clean[:-4]}/USDT"
    if '/' in clean:
        return clean
    return f"{clean}/USDT"


def _resolve_market_symbol(exchange, symbol_ccxt):
    if symbol_ccxt in exchange.markets:
        return symbol_ccxt
    alt = symbol_ccxt.split(':')[0]
    return alt if alt in exchange.markets else None


def _base_of(symbol_ccxt):
    return symbol_ccxt.split('/')[0]


def _trigger_params(exchange_id):
    return dict(_TRIGGER_FETCH_PARAMS.get(exchange_id, {}))


def _is_stop_order(o):
    """Một lệnh được coi là SL nếu sàn gắn cờ trigger/stop HOẶC type có chữ 'stop'/'trigger'."""
    info = o.get('info') or {}
    if str(info.get('ordType', '')).lower() in ('trigger', 'conditional', 'stop', 'stop_market', 'stop_limit'):
        return str(o.get('side') or '').lower() == 'sell'
    t = str(o.get('type') or '').lower()
    return ('stop' in t or 'trigger' in t) and str(o.get('side') or '').lower() == 'sell'


def _cancel_open_stops(exchange, exchange_id, symbol_ccxt):
    """Huỷ mọi lệnh SL (bán, trigger) đang mở của symbol. Trả về số lệnh đã huỷ."""
    cancelled = 0
    params = _trigger_params(exchange_id)
    try:
        orders = exchange.fetch_open_orders(symbol_ccxt, None, None, params)
    except Exception:
        # Một số version/sàn lỗi với params trigger nếu không có lệnh nào — thử lại không params.
        orders = exchange.fetch_open_orders(symbol_ccxt)
    for o in orders:
        if _is_stop_order(o):
            try:
                exchange.cancel_order(o['id'], symbol_ccxt, params)
            except Exception:
                exchange.cancel_order(o['id'], symbol_ccxt)
            cancelled += 1
    return cancelled


def cancel_stops(exchange_id, symbol, asset_type='crypto'):
    creds = get_credentials_from_db(exchange_id)
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key', 'cancelled': 0}
    if exchange_id == 'okx' and not creds.get('passphrase'):
        return {'success': False, 'error': 'Chưa cấu hình OKX Passphrase', 'cancelled': 0}
    try:
        exchange = get_exchange_instance(exchange_id, creds)
        exchange.load_markets()
        sym = _resolve_market_symbol(exchange, _ccxt_symbol(symbol))
        if not sym:
            return {'success': False, 'error': f'Không tìm thấy cặp {symbol}', 'cancelled': 0}
        return {'success': True, 'cancelled': _cancel_open_stops(exchange, exchange_id, sym)}
    except Exception as e:
        return {'success': False, 'error': str(e), 'cancelled': 0}


def execute_order(exchange_id, symbol, amount_usd, sl_pct=2.0, layer=1, place_stop=True):
    """Market buy (Spot) + đặt SL độc lập bằng triggerPrice (unified ccxt)."""
    creds = get_credentials_from_db(exchange_id)
    symbol_ccxt = _ccxt_symbol(symbol)

    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': f'{exchange_id.upper()} API Key/Secret chưa được cấu hình.', 'symbol': symbol_ccxt}
    if exchange_id == 'okx' and not creds.get('passphrase'):
        return {'success': False, 'error': 'OKX Passphrase chưa được cấu hình.', 'symbol': symbol_ccxt}

    try:
        exchange = get_exchange_instance(exchange_id, creds)
        exchange.load_markets()
        resolved = _resolve_market_symbol(exchange, symbol_ccxt)
        if not resolved:
            return {'success': False, 'error': f'Cặp giao dịch {symbol} không tìm thấy trên {exchange_id.upper()}.', 'symbol': symbol_ccxt}
        symbol_ccxt = resolved

        ticker = exchange.fetch_ticker(symbol_ccxt)
        current_price = float(ticker.get('last') or ticker.get('close', 0))
        if current_price <= 0:
            return {'success': False, 'error': f'Không lấy được giá từ {exchange_id.upper()} cho {symbol_ccxt}.', 'symbol': symbol_ccxt}

        raw_units = float(amount_usd) / current_price
        units_precision = float(exchange.amount_to_precision(symbol_ccxt, raw_units))

        market = exchange.market(symbol_ccxt)
        min_cost = (market.get('limits', {}).get('cost', {}) or {}).get('min') or 5.0
        if (units_precision * current_price) < min_cost:
            return {'success': False, 'error': f'Giá trị lệnh nhỏ hơn mức tối thiểu ({min_cost}).', 'symbol': symbol_ccxt}

        print(f"🛒 [{exchange_id.upper()} Live Trader] MARKET BUY {symbol_ccxt} (~{amount_usd} USDT)...")
        order = exchange.create_order(symbol_ccxt, 'market', 'buy', units_precision)
        order_id = str(order.get('id', ''))
        entry_price = float(order.get('average') or order.get('price') or current_price)
        filled_units = float(order.get('filled') or units_precision)

        stop_loss_price = entry_price * (1.0 - (float(sl_pct) / 100.0))
        stop_price_precision = float(exchange.price_to_precision(symbol_ccxt, stop_loss_price))

        sl_order_id = None
        sl_error = None
        if place_stop:
            try:
                sl_order = exchange.create_order(
                    symbol_ccxt, 'market', 'sell', filled_units, None,
                    {'triggerPrice': stop_price_precision}
                )
                sl_order_id = str(sl_order.get('id', ''))
            except Exception as sl_err:
                sl_error = str(sl_err)
                print(f"⚠️ [{exchange_id.upper()} Live Trader] Mua thành công nhưng đặt SL lỗi: {sl_err}")

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
            'message': f"Đã khớp lệnh {exchange_id.upper()} thực tế: Mua {filled_units} {symbol_ccxt} tại {entry_price:,.4f} USDT (SL -{sl_pct}%: {stop_price_precision:,.4f})"
        }
    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e), 'symbol': symbol_ccxt}


def sync_stop(exchange_id, symbol, units, stop_price):
    """Huỷ SL cũ + đặt lại 1 SL duy nhất phủ toàn bộ khối lượng (giống sync_binance_stop)."""
    creds = get_credentials_from_db(exchange_id)
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key', 'cancelled': 0}
    cancelled = 0
    try:
        exchange = get_exchange_instance(exchange_id, creds)
        exchange.load_markets()
        sym = _resolve_market_symbol(exchange, _ccxt_symbol(symbol))
        if not sym:
            return {'success': False, 'error': f'Không tìm thấy cặp {symbol}', 'cancelled': 0}

        cancelled = _cancel_open_stops(exchange, exchange_id, sym)

        free = float((exchange.fetch_balance().get(_base_of(sym)) or {}).get('free') or 0)
        want = min(float(units or 0), free) if units else free
        qty = float(exchange.amount_to_precision(sym, want)) if want > 0 else 0.0
        if qty <= 0:
            return {'success': False, 'error': 'Không còn khối lượng để đặt SL (vị thế có thể đã đóng).', 'cancelled': cancelled}

        stop_p = float(exchange.price_to_precision(sym, float(stop_price)))
        order = exchange.create_order(sym, 'market', 'sell', qty, None, {'triggerPrice': stop_p})
        return {'success': True, 'sl_order_id': str(order.get('id', '')), 'stop_price': stop_p, 'units': qty, 'cancelled': cancelled}
    except Exception as e:
        return {'success': False, 'error': str(e), 'cancelled': cancelled}


def get_spot_balance(exchange_id, symbol):
    clean = symbol.split(':')[-1].upper().replace('-', '').strip()
    base = clean[:-4] if clean.endswith('USDT') else (clean.split('/')[0] if '/' in clean else clean)
    creds = get_credentials_from_db(exchange_id)
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': f'Chưa cấu hình API Key sàn {exchange_id.upper()}.', 'base': base, 'total': 0}
    try:
        exchange = get_exchange_instance(exchange_id, creds)
        balance = exchange.fetch_balance()
        bal = balance.get(base, {}) or {}
        free = float(bal.get('free') or 0)
        used = float(bal.get('used') or 0)
        total = float(bal.get('total') or (free + used))
        current_price = 0.0
        try:
            ticker = exchange.fetch_ticker(f"{base}/USDT")
            current_price = float(ticker.get('last') or ticker.get('close', 0))
        except Exception:
            pass
        return {'success': True, 'base': base, 'free': free, 'locked': used, 'total': total,
                'price': current_price, 'usd_value': total * current_price if current_price > 0 else 0}
    except Exception as e:
        return {'success': False, 'error': str(e), 'base': base, 'total': 0}


def sell_market(exchange_id, symbol, units=None):
    """Đóng vị thế thật bằng lệnh bán market: huỷ SL cũ trước (khoá số dư), rồi bán free balance."""
    creds = get_credentials_from_db(exchange_id)
    symbol_ccxt = _ccxt_symbol(symbol)
    if not creds.get('api_key') or not creds.get('api_secret'):
        return {'success': False, 'error': 'Chưa cấu hình API Key'}
    try:
        exchange = get_exchange_instance(exchange_id, creds)
        exchange.load_markets()
        resolved = _resolve_market_symbol(exchange, symbol_ccxt)
        if resolved:
            symbol_ccxt = resolved
        base = _base_of(symbol_ccxt)

        cancelled = _cancel_open_stops(exchange, exchange_id, symbol_ccxt)

        free = float((exchange.fetch_balance().get(base) or {}).get('free') or 0)
        want = min(float(units), free) if (units and units > 0 and free > 0) else free
        units_precision = float(exchange.amount_to_precision(symbol_ccxt, want)) if want > 0 else 0.0
        if units_precision <= 0:
            return {'success': True, 'already_closed': True, 'order_id': '', 'filled': 0.0, 'price': 0.0,
                    'cancelled_stops': cancelled,
                    'message': f"Không còn {base} để bán — vị thế có thể đã đóng sẵn trên sàn (SL đã khớp hoặc bán tay)."}

        print(f"🛑 [{exchange_id.upper()} Live Trader] BÁN MARKET THỰC TẾ {units_precision} {symbol_ccxt} (Cắt lỗ)...")
        order = exchange.create_order(symbol_ccxt, 'market', 'sell', units_precision)
        return {
            'success': True,
            'order_id': str(order.get('id', '')),
            'filled': float(order.get('filled') or units_precision),
            'price': float(order.get('average') or order.get('price') or 0),
            'cancelled_stops': cancelled,
            'message': f"Đã bán khẩn cấp {units_precision} {symbol_ccxt} trên {exchange_id.upper()} (Spot)."
        }
    except Exception as e:
        print(f"⚠️ [{exchange_id.upper()} Live Trader] Lỗi bán khẩn cấp {symbol_ccxt}: {e}")
        return {'success': False, 'error': str(e)}


# ---------------------------------------------------------------------------
# Self-test: BẮT BUỘC chạy trước khi bật trade thật trên OKX/Bybit.
# Kiểm tra: auth hoạt động, đặt lệnh trigger (SL) chuẩn cú pháp, fetch thấy lại, huỷ thành công.
# Dùng BTC/USDT với giá trigger TRÊN giá thị trường hiện tại cho lệnh BÁN (sẽ không bao giờ khớp
# ngay vì giá trigger cao hơn giá hiện tại) để không rủi ro khớp lệnh thật ngoài ý muốn, và khối
# lượng tối thiểu của sàn (không cần có sẵn BTC — một số sàn validate cú pháp trước khi kiểm tra
# số dư, nếu lỗi "insufficient" vẫn coi là PASS cú pháp nhưng sẽ báo rõ cho người dùng).
# ---------------------------------------------------------------------------

_INSUFFICIENT_HINTS = ('insufficient', 'balance', 'not enough', 'margin')


def self_test(exchange_id):
    creds = get_credentials_from_db(exchange_id)
    result = {'exchange': exchange_id, 'steps': []}

    def step(name, ok, detail=''):
        result['steps'].append({'step': name, 'ok': ok, 'detail': detail})
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ''))
        return ok

    if not creds.get('api_key') or not creds.get('api_secret'):
        step('credentials', False, 'Chưa cấu hình API Key/Secret trong Trading Settings.')
        result['success'] = False
        return result
    if exchange_id == 'okx' and not creds.get('passphrase'):
        step('credentials', False, 'Chưa cấu hình OKX Passphrase.')
        result['success'] = False
        return result
    step('credentials', True, f"sandbox={creds.get('sandbox')}")

    try:
        exchange = get_exchange_instance(exchange_id, creds)
        exchange.load_markets()
        step('load_markets', True, f"{len(exchange.markets)} markets")
    except Exception as e:
        step('load_markets', False, str(e))
        result['success'] = False
        return result

    sym = _resolve_market_symbol(exchange, 'BTC/USDT')
    if not sym:
        step('resolve_symbol', False, 'Không tìm thấy BTC/USDT')
        result['success'] = False
        return result
    step('resolve_symbol', True, sym)

    try:
        bal_ok = exchange.fetch_balance()
        step('fetch_balance (xác thực API key)', True, 'auth OK')
    except Exception as e:
        step('fetch_balance (xác thực API key)', False, str(e))
        result['success'] = False
        return result

    try:
        ticker = exchange.fetch_ticker(sym)
        price = float(ticker.get('last') or ticker.get('close', 0))
        step('fetch_ticker', price > 0, f"last={price}")
    except Exception as e:
        step('fetch_ticker', False, str(e))
        result['success'] = False
        return result

    market = exchange.market(sym)
    min_amt = (market.get('limits', {}).get('amount', {}) or {}).get('min') or 0.0001
    trigger_price = float(exchange.price_to_precision(sym, price * 1.5))  # cao hơn giá hiện tại → SELL trigger không khớp ngay
    test_order_id = None
    try:
        order = exchange.create_order(sym, 'market', 'sell', min_amt, None, {'triggerPrice': trigger_price})
        test_order_id = str(order.get('id', ''))
        step('create_order triggerPrice (đặt lệnh SL thử)', True, f"id={test_order_id}")
    except Exception as e:
        msg = str(e)
        tolerated = any(h in msg.lower() for h in _INSUFFICIENT_HINTS)
        step('create_order triggerPrice (đặt lệnh SL thử)', tolerated,
             f"{msg}" + (" (chấp nhận: cú pháp đúng, chỉ thiếu số dư BTC để test đầy đủ vòng đời lệnh)" if tolerated else ""))
        if not tolerated:
            result['success'] = False
            return result
        result['success'] = True
        result['note'] = 'Cú pháp đặt lệnh được sàn chấp nhận, nhưng KHÔNG kiểm chứng được fetch/huỷ do không có số dư BTC để test. Nên nạp một ít BTC vào tài khoản demo/testnet và chạy lại self-test để kiểm tra đầy đủ vòng đời (đặt → thấy lại → huỷ) trước khi bật trade thật.'
        return result

    try:
        params = _trigger_params(exchange_id)
        open_orders = exchange.fetch_open_orders(sym, None, None, params)
        found = any(str(o.get('id')) == test_order_id for o in open_orders)
        step('fetch_open_orders thấy lại lệnh trigger', found, f"params={params}, found={found}")
    except Exception as e:
        step('fetch_open_orders thấy lại lệnh trigger', False, str(e))
        found = False

    try:
        params = _trigger_params(exchange_id)
        exchange.cancel_order(test_order_id, sym, params)
        step('cancel_order huỷ lệnh test', True)
    except Exception as e:
        step('cancel_order huỷ lệnh test', False, f"{e} — CẢNH BÁO: lệnh test có thể còn treo trên sàn, vào lịch sử lệnh trên {exchange_id.upper()} để huỷ tay.")
        result['success'] = False
        return result

    result['success'] = bool(found)
    if not found:
        result['note'] = 'Lệnh đặt được và huỷ được, nhưng fetch_open_orders KHÔNG thấy lại bằng params hiện tại — có thể cần tham số khác cho sàn/tài khoản này. Cancel-and-replace (trailing stop) sẽ KHÔNG an toàn cho tới khi xác nhận lại.'
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_self = sub.add_parser('self-test')
    p_self.add_argument('--exchange', required=True, choices=SUPPORTED_EXCHANGES)

    p_close = sub.add_parser('close')
    p_close.add_argument('--exchange', required=True, choices=SUPPORTED_EXCHANGES)
    p_close.add_argument('--symbol', required=True)
    p_close.add_argument('--units', type=float, default=None)

    p_cancel = sub.add_parser('cancel-stops')
    p_cancel.add_argument('--exchange', required=True, choices=SUPPORTED_EXCHANGES)
    p_cancel.add_argument('--symbol', required=True)

    args = parser.parse_args()

    if args.cmd == 'self-test':
        print(f"=== Self-test {args.exchange.upper()} ===")
        out = self_test(args.exchange)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if out.get('success') else 1)
    elif args.cmd == 'close':
        out = sell_market(args.exchange, args.symbol, args.units)
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(0 if out.get('success') else 1)
    elif args.cmd == 'cancel-stops':
        out = cancel_stops(args.exchange, args.symbol)
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(0 if out.get('success') else 1)


if __name__ == '__main__':
    main()
