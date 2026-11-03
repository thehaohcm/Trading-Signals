"""Test vòng đời lệnh SL phía sàn Binance bằng sàn giả (không cần mạng / DB / ccxt thật).

Chạy:  python3 -m unittest discover -s scripts/tests -v
"""
import os
import sys
import types
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

# Thiếu ccxt / psycopg2 / dotenv (môi trường test) → dùng stub, không ảnh hưởng khi chạy thật.
for _name in ('ccxt', 'psycopg2', 'psycopg2.pool', 'psycopg2.extras', 'dotenv'):
    try:
        __import__(_name)
    except ImportError:
        m = mock.MagicMock()
        if _name == 'dotenv':
            m.load_dotenv = lambda *a, **k: None
        sys.modules[_name] = m

import live_trader_binance as ltb  # noqa: E402


class InsufficientFunds(Exception):
    pass


class FakeExchange:
    """Mô phỏng đủ hành vi Binance cần thiết: SL Spot khoá số dư, reduceOnly, SL bị từ chối..."""

    def __init__(self, kind='spot', free=0.0, locked_orders=(), position=0.0, price=100.0,
                 fail_stop=False):
        self.kind = kind
        self.free = free
        self.orders = []          # lệnh mở
        self.price = price
        self.position = position  # futures
        self.fail_stop = fail_stop
        self.calls = []
        self.markets = {'BTC/USDT': {}, 'BTC/USDT:USDT': {}}
        self._id = 0
        for amt, stop in locked_orders:  # [(amount, stopPrice)] đã đặt từ trước
            self._add_order('STOP_LOSS_LIMIT' if kind == 'spot' else 'STOP_MARKET', 'sell', amt, stop)

    # --- helpers
    def _add_order(self, typ, side, amount, stop):
        if self.kind == 'spot':
            if amount > self.free + 1e-12:
                raise InsufficientFunds('insufficient balance')
            self.free -= amount
        self._id += 1
        o = {'id': str(self._id), 'type': typ.lower(), 'side': side, 'amount': amount, 'stopPrice': stop}
        self.orders.append(o)
        return o

    def locked(self):
        return sum(o['amount'] for o in self.orders) if self.kind == 'spot' else 0.0

    # --- ccxt API
    def load_markets(self):
        return self.markets

    def market(self, sym):
        return {'limits': {'cost': {'min': 5.0}}}

    def amount_to_precision(self, sym, v):
        return str(round(float(v), 3))

    def price_to_precision(self, sym, v):
        return str(round(float(v), 2))

    def fetch_open_orders(self, sym):
        self.calls.append(('fetch_open_orders', sym))
        return [dict(o) for o in self.orders]

    def cancel_order(self, oid, sym):
        self.calls.append(('cancel', oid))
        for o in list(self.orders):
            if o['id'] == oid:
                self.orders.remove(o)
                if self.kind == 'spot':
                    self.free += o['amount']
                return
        raise Exception('order not found')

    def fetch_balance(self):
        return {'BTC': {'free': self.free, 'used': self.locked(), 'total': self.free + self.locked()}}

    def fetch_positions(self, syms):
        return [{'contracts': self.position}]

    def fetch_ticker(self, sym):
        return {'last': self.price}

    def create_order(self, symbol, type, side, amount, price=None, params=None):
        params = params or {}
        self.calls.append(('create_order', type, side, amount, price, dict(params)))
        if self.fail_stop and 'stop' in type.lower():
            raise Exception('Order would immediately trigger')
        return self._add_order(type, side, amount, params.get('stopPrice'))

    def create_market_buy_order(self, sym, amount, params=None):
        self.calls.append(('market_buy', amount))
        if self.kind == 'spot':
            self.free += amount
        else:
            self.position += amount
        return {'id': 'buy1', 'average': self.price, 'filled': amount}

    def create_market_sell_order(self, sym, amount, params=None):
        params = params or {}
        self.calls.append(('market_sell', amount, dict(params)))
        if self.kind == 'spot':
            if amount > self.free + 1e-12:
                raise InsufficientFunds('insufficient balance')
            self.free -= amount
        else:
            if params.get('reduceOnly') and self.position <= 0:
                raise Exception('ReduceOnly Order is rejected')
            self.position -= amount
        return {'id': 'sell1', 'average': self.price, 'filled': amount}


def patched(ex):
    return mock.patch.multiple(
        ltb,
        get_binance_credentials_from_db=lambda: {'api_key': 'k', 'api_secret': 's'},
        get_exchange_instance=lambda asset_type='crypto', creds=None: ex,
    )


class SyncStopTests(unittest.TestCase):
    def test_replaces_per_layer_stops_with_one_covering_all_units(self):
        # 2 tầng, mỗi tầng 1 lệnh SL riêng (kiểu cũ) khoá 1.0 + 0.5; không còn free
        ex = FakeExchange(free=1.5, locked_orders=[(1.0, 95.0), (0.5, 96.0)])
        with patched(ex):
            r = ltb.sync_binance_stop('BTCUSDT', 'crypto', 1.5, 98.0)
        self.assertTrue(r['success'], r)
        self.assertEqual(r['cancelled'], 2)
        self.assertEqual(len(ex.orders), 1)
        self.assertAlmostEqual(ex.orders[0]['amount'], 1.5)
        self.assertEqual(ex.orders[0]['stopPrice'], 98.0)
        create = [c for c in ex.calls if c[0] == 'create_order'][0]
        self.assertEqual(create[1], 'STOP_LOSS_LIMIT')
        self.assertLess(create[4], 98.0)  # giá limit thấp hơn giá kích hoạt để chắc khớp

    def test_caps_units_at_actual_free_balance(self):
        ex = FakeExchange(free=1.2)  # sổ sách nói 2.0 nhưng sàn chỉ còn 1.2 (đã bán tay một phần)
        with patched(ex):
            r = ltb.sync_binance_stop('BTCUSDT', 'crypto', 2.0, 98.0)
        self.assertTrue(r['success'])
        self.assertAlmostEqual(ex.orders[0]['amount'], 1.2)

    def test_no_balance_is_reported_not_crash(self):
        ex = FakeExchange(free=0.0)
        with patched(ex):
            r = ltb.sync_binance_stop('BTCUSDT', 'crypto', 1.0, 98.0)
        self.assertFalse(r['success'])
        self.assertIn('đã được đóng', r['error'])

    def test_exchange_rejects_stop_returns_error(self):
        ex = FakeExchange(free=1.0, fail_stop=True)
        with patched(ex):
            r = ltb.sync_binance_stop('BTCUSDT', 'crypto', 1.0, 98.0)
        self.assertFalse(r['success'])
        self.assertIn('immediately', r['error'])

    def test_futures_uses_stop_market_reduce_only_and_real_position_size(self):
        ex = FakeExchange(kind='futures', position=0.7, locked_orders=[(0.3, 90.0)])
        with patched(ex):
            r = ltb.sync_binance_stop('BTCUSDT', 'futures', 5.0, 98.0)
        self.assertTrue(r['success'], r)
        create = [c for c in ex.calls if c[0] == 'create_order'][-1]
        self.assertEqual(create[1], 'STOP_MARKET')
        self.assertTrue(create[5]['reduceOnly'])
        self.assertAlmostEqual(create[3], 0.7)  # theo vị thế thực trên sàn, không theo sổ sách


class SellTests(unittest.TestCase):
    def test_spot_sell_cancels_locking_stop_first(self):
        ex = FakeExchange(free=2.0, locked_orders=[(2.0, 95.0)])  # toàn bộ số dư đang bị SL khoá
        with patched(ex):
            r = ltb.execute_binance_sell_market('BTCUSDT', 2.0, 'crypto')
        self.assertTrue(r['success'], r)
        self.assertFalse(r.get('already_closed'))
        self.assertEqual(r['cancelled_stops'], 1)
        self.assertEqual(ex.orders, [])
        self.assertAlmostEqual(ex.free, 0.0)

    def test_spot_already_closed_by_exchange_stop(self):
        ex = FakeExchange(free=0.0)  # SL của sàn đã khớp → không còn BTC
        with patched(ex):
            r = ltb.execute_binance_sell_market('BTCUSDT', 2.0, 'crypto')
        self.assertTrue(r['success'])
        self.assertTrue(r['already_closed'])
        self.assertFalse([c for c in ex.calls if c[0] == 'market_sell'])

    def test_futures_flat_does_not_open_short(self):
        ex = FakeExchange(kind='futures', position=0.0)
        with patched(ex):
            r = ltb.execute_binance_sell_market('BTCUSDT', 1.0, 'futures')
        self.assertTrue(r['success'])
        self.assertTrue(r['already_closed'])
        self.assertFalse([c for c in ex.calls if c[0] == 'market_sell'])

    def test_futures_sell_is_reduce_only(self):
        ex = FakeExchange(kind='futures', position=1.0, locked_orders=[(1.0, 95.0)])
        with patched(ex):
            r = ltb.execute_binance_sell_market('BTCUSDT', 1.0, 'futures')
        self.assertTrue(r['success'])
        sell = [c for c in ex.calls if c[0] == 'market_sell'][0]
        self.assertTrue(sell[2].get('reduceOnly'))
        self.assertEqual(ex.orders, [])


class BuyTests(unittest.TestCase):
    def test_place_stop_false_places_no_stop(self):
        ex = FakeExchange(free=0.0)
        with patched(ex):
            r = ltb.execute_binance_order('BTCUSDT', 'crypto', 500.0, sl_pct=2.0, place_stop=False)
        self.assertTrue(r['success'], r)
        self.assertFalse(r['sl_placed'])
        self.assertEqual(ex.orders, [])

    def test_stop_failure_is_reported_not_swallowed(self):
        ex = FakeExchange(free=0.0, fail_stop=True)
        with patched(ex):
            r = ltb.execute_binance_order('BTCUSDT', 'crypto', 500.0, sl_pct=2.0)
        self.assertTrue(r['success'])          # lệnh mua đã khớp
        self.assertFalse(r['sl_placed'])
        self.assertIn('immediately', r['sl_error'])


class EnsureStopStateMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import alert
        cls.alert = alert

    def setUp(self):
        a = self.alert
        a._exchange_stop_state.clear()
        self.calls = []
        self.alerts = []
        self.result = {'success': True}

        def fake_sync(symbol, asset_type, units, stop_price):
            self.calls.append((units, stop_price))
            if self.result.get('success'):
                return {'success': True, 'stop_price': stop_price, 'units': units}
            return dict(self.result)

        self._p1 = mock.patch.object(a, '_sync_binance_stop', fake_sync)
        self._p2 = mock.patch.object(a, 'insert_triggered_alert',
                                     lambda *args, **kw: self.alerts.append((args, kw)))
        self._p1.start()
        self._p2.start()
        self.ctx = {'events': [], 'has_position': True}

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()

    def ensure(self, units=1.0, stop=98.0, price=105.0, now=1000.0, force=False, asset='crypto'):
        return self.alert._ensure_exchange_stop(self.ctx, 7, 'BTCUSDT', asset, units, stop, price,
                                                force=force, now=now)

    def test_first_call_syncs_then_idempotent(self):
        self.assertIsNotNone(self.ensure(now=1000))
        self.assertIsNone(self.ensure(now=1100))          # không đổi → không gọi lại sàn
        self.assertEqual(len(self.calls), 1)

    def test_trailing_move_resyncs_only_when_significant(self):
        self.ensure(stop=100.0, now=1000)
        self.assertIsNone(self.ensure(stop=100.05, now=1100))   # +0.05% < ngưỡng 0.1%
        self.assertIsNotNone(self.ensure(stop=100.5, now=1200)) # +0.5%
        self.assertEqual([c[1] for c in self.calls], [100.0, 100.5])

    def test_min_interval_throttles(self):
        self.ensure(stop=100.0, now=1000)
        self.assertIsNone(self.ensure(stop=110.0, price=130.0, now=1005))    # < 20s
        self.assertIsNotNone(self.ensure(stop=110.0, price=130.0, now=1030))

    def test_units_growth_after_pyramid_resyncs(self):
        self.ensure(units=1.0, now=1000)
        self.assertIsNotNone(self.ensure(units=1.6, now=1100))
        self.assertEqual(self.calls[-1][0], 1.6)

    def test_force_always_syncs(self):
        self.ensure(now=1000)
        self.assertIsNotNone(self.ensure(now=1001, force=True))

    def test_price_at_or_below_stop_does_nothing(self):
        self.assertIsNone(self.ensure(stop=98.0, price=98.0))
        self.assertEqual(self.calls, [])

    def test_non_binance_asset_ignored(self):
        self.assertIsNone(self.ensure(asset='forex'))
        self.assertEqual(self.calls, [])

    def test_failure_alerts_once_backs_off_then_retries(self):
        self.result = {'success': False, 'error': 'boom'}
        r = self.ensure(now=1000)
        self.assertFalse(r['success'])
        self.assertEqual(len(self.alerts), 1)
        self.assertEqual(self.alerts[0][1]['event_type'], 'manual_action')
        self.assertIn('manual_action', self.ctx['events'])

        self.assertIsNone(self.ensure(now=1100))                 # đang backoff 5 phút
        self.assertEqual(len(self.calls), 1)

        r = self.ensure(now=1000 + 301)                          # thử lại, vẫn lỗi
        self.assertFalse(r['success'])
        self.assertEqual(len(self.alerts), 1)                    # chưa tới 30 phút → không spam

        r = self.ensure(now=1000 + 1801 + 301)                   # quá 30 phút → nhắc lại
        self.assertEqual(len(self.alerts), 2)

    def test_recovers_after_failure(self):
        self.result = {'success': False, 'error': 'boom'}
        self.ensure(now=1000)
        self.result = {'success': True}
        r = self.ensure(now=1000 + 301)
        self.assertTrue(r['success'])
        self.assertNotIn('fail_ts', self.alert._exchange_stop_state[7])
        self.assertIsNone(self.ensure(now=1000 + 400))           # ổn định trở lại


if __name__ == '__main__':
    unittest.main()
