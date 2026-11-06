"""Test module OKX/Bybit (live_trader_ccxt.py) bằng sàn giả — không cần mạng/DB/ccxt thật.

Chạy: python3 -m unittest discover -s scripts/tests -v
"""
import os
import sys
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

for _name in ('ccxt', 'psycopg2', 'psycopg2.pool', 'psycopg2.extras', 'dotenv'):
    try:
        __import__(_name)
    except ImportError:
        m = mock.MagicMock()
        if _name == 'dotenv':
            m.load_dotenv = lambda *a, **k: None
        sys.modules[_name] = m

import live_trader_ccxt as lcx  # noqa: E402


class FakeTriggerExchange:
    """Mô phỏng OKX/Bybit: lệnh trigger (SL độc lập) đặt qua triggerPrice, fetch/cancel cần params riêng."""

    def __init__(self, free=0.0, price=100.0, trigger_param_key='trigger', reject_wrong_params=True):
        self.free = free
        self.price = price
        self.orders = []
        self.calls = []
        self._id = 0
        self.markets = {'BTC/USDT': {}}
        self.trigger_param_key = trigger_param_key  # 'trigger' (OKX) hoặc 'stop' (Bybit)
        self.reject_wrong_params = reject_wrong_params

    def load_markets(self):
        return self.markets

    def market(self, sym):
        return {'limits': {'cost': {'min': 5.0}, 'amount': {'min': 0.0001}}}

    def amount_to_precision(self, sym, v):
        return str(round(float(v), 4))

    def price_to_precision(self, sym, v):
        return str(round(float(v), 2))

    def fetch_ticker(self, sym):
        return {'last': self.price}

    def fetch_balance(self):
        return {'BTC': {'free': self.free, 'used': 0}}

    def set_sandbox_mode(self, v):
        self.calls.append(('sandbox', v))

    def fetch_open_orders(self, sym, since=None, limit=None, params=None):
        params = params or {}
        self.calls.append(('fetch_open_orders', dict(params)))
        if self.reject_wrong_params and params.get(self.trigger_param_key) is not True:
            return []  # sàn không trả lệnh trigger nếu thiếu cờ đúng
        return [dict(o) for o in self.orders]

    def cancel_order(self, oid, sym, params=None):
        params = params or {}
        self.calls.append(('cancel', oid, dict(params)))
        if self.reject_wrong_params and params.get(self.trigger_param_key) is not True:
            raise Exception('order not found (wrong params)')
        for o in list(self.orders):
            if o['id'] == oid:
                self.orders.remove(o)
                self.free += o['amount']
                return
        raise Exception('order not found')

    def create_order(self, symbol, type, side, amount, price=None, params=None):
        params = params or {}
        self.calls.append(('create_order', type, side, amount, price, dict(params)))
        if type == 'market' and side == 'buy':
            self.free += amount
            return {'id': 'buy1', 'average': self.price, 'filled': amount}
        if 'triggerPrice' in params:
            if amount > self.free + 1e-12:
                raise Exception('insufficient balance')
            self.free -= amount
            self._id += 1
            o = {'id': str(self._id), 'type': 'market', 'side': side, 'amount': amount,
                 'info': {'ordType': 'trigger'}}
            self.orders.append(o)
            return o
        # market sell thường (đóng vị thế)
        if amount > self.free + 1e-12:
            raise Exception('insufficient balance')
        self.free -= amount
        return {'id': 'sell1', 'average': self.price, 'filled': amount}


def patched(exchange_id, ex):
    return mock.patch.multiple(
        lcx,
        get_credentials_from_db=lambda eid=None: {
            'api_key': 'k', 'api_secret': 's', 'passphrase': 'p', 'sandbox': False, 'trade_amount_usdt': 20.0
        },
        get_exchange_instance=lambda eid, creds=None: ex,
    )


class ExecuteOrderTests(unittest.TestCase):
    def test_okx_buy_then_places_trigger_stop(self):
        ex = FakeTriggerExchange(trigger_param_key='trigger')
        with patched('okx', ex):
            r = lcx.execute_order('okx', 'BTCUSDT', 500.0, sl_pct=2.0)
        self.assertTrue(r['success'], r)
        self.assertTrue(r['sl_placed'])
        create_calls = [c for c in ex.calls if c[0] == 'create_order']
        sl_call = [c for c in create_calls if 'triggerPrice' in c[5]][0]
        self.assertEqual(sl_call[1], 'market')
        self.assertEqual(sl_call[2], 'sell')

    def test_place_stop_false_skips_sl(self):
        ex = FakeTriggerExchange()
        with patched('bybit', ex):
            r = lcx.execute_order('bybit', 'BTCUSDT', 500.0, sl_pct=2.0, place_stop=False)
        self.assertTrue(r['success'], r)
        self.assertFalse(r['sl_placed'])
        self.assertFalse([c for c in ex.calls if c[0] == 'create_order' and 'triggerPrice' in c[5]])


class CancelAndSyncStopTests(unittest.TestCase):
    def test_cancel_open_stops_uses_exchange_specific_params(self):
        """OKX cần params={'trigger': True} để fetch/cancel lệnh trigger — thiếu sẽ không thấy/huỷ được."""
        ex = FakeTriggerExchange(free=1.0, trigger_param_key='trigger')
        ex.create_order('BTC/USDT', 'market', 'sell', 1.0, None, {'triggerPrice': 95.0})
        with patched('okx', ex):
            r = lcx.cancel_stops('okx', 'BTCUSDT')
        self.assertTrue(r['success'], r)
        self.assertEqual(r['cancelled'], 1)
        fetch_call = [c for c in ex.calls if c[0] == 'fetch_open_orders'][0]
        self.assertTrue(fetch_call[1].get('trigger'))

    def test_bybit_uses_stop_param_not_trigger(self):
        ex = FakeTriggerExchange(free=1.0, trigger_param_key='stop')
        ex.create_order('BTC/USDT', 'market', 'sell', 1.0, None, {'triggerPrice': 95.0})
        with patched('bybit', ex):
            r = lcx.cancel_stops('bybit', 'BTCUSDT')
        self.assertTrue(r['success'], r)
        self.assertEqual(r['cancelled'], 1)

    def test_sync_stop_replaces_existing_with_single_new_one(self):
        ex = FakeTriggerExchange(free=1.5, trigger_param_key='trigger')
        ex.create_order('BTC/USDT', 'market', 'sell', 1.5, None, {'triggerPrice': 90.0})
        with patched('okx', ex):
            r = lcx.sync_stop('okx', 'BTCUSDT', 1.5, 98.0)
        self.assertTrue(r['success'], r)
        self.assertEqual(r['cancelled'], 1)
        self.assertEqual(len(ex.orders), 1)
        self.assertAlmostEqual(ex.orders[0]['amount'], 1.5)


class SellMarketTests(unittest.TestCase):
    def test_sell_market_cancels_stop_then_sells_free_balance(self):
        ex = FakeTriggerExchange(free=2.0, trigger_param_key='trigger')
        ex.create_order('BTC/USDT', 'market', 'sell', 2.0, None, {'triggerPrice': 90.0})
        with patched('okx', ex):
            r = lcx.sell_market('okx', 'BTCUSDT')
        self.assertTrue(r['success'], r)
        self.assertEqual(r['cancelled_stops'], 1)
        self.assertAlmostEqual(ex.free, 0.0)

    def test_already_closed_when_no_balance(self):
        ex = FakeTriggerExchange(free=0.0)
        with patched('bybit', ex):
            r = lcx.sell_market('bybit', 'BTCUSDT')
        self.assertTrue(r['success'])
        self.assertTrue(r['already_closed'])


if __name__ == '__main__':
    unittest.main()
