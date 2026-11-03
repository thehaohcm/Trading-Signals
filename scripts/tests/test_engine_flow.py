"""Test tích hợp luồng Case A / pyramid của _process_breakout_impl với DB giả (không cần Postgres thật)."""
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

import alert  # noqa: E402


class FakeDB:
    def __init__(self, position=None, stats=(0, 0, 0, 0.0, 0.0), sl_today=0):
        self.position = position          # None hoặc tuple đúng thứ tự SELECT của Case B
        self.stats = stats
        self.sl_today = sl_today
        self.inserts = []
        self.log = []

    # connection API
    def cursor(self):
        return FakeCur(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    @property
    def connection(self):
        return self

    def respond(self, s, params):
        if 'pg_try_advisory_lock' in s or 'pg_advisory_unlock' in s:
            return [(True,)]
        if 'FROM public.system_settings WHERE key = ANY' in s:
            return [('trading_mode', 'demo'), ('is_live_trade_enabled', 'true')]
        if 'FROM public.ai_asset_signals' in s:
            return []
        if 'FROM public.paper_positions WHERE watchlist_id' in s:
            return [self.position] if self.position else []
        if "status = 'CLOSED_SL'" in s and 'COUNT(*) FILTER' not in s:
            return [(self.sl_today,)]
        if 'COUNT(*) FILTER' in s:
            return [self.stats]
        if s.startswith('INSERT INTO public.paper_positions'):
            self.inserts.append(params)
            return [(101,)]
        return []


class FakeCur:
    def __init__(self, db):
        self.db = db
        self.connection = db
        self._rows = []

    def execute(self, sql, params=None):
        s = ' '.join(sql.split())
        self.db.log.append(s)
        self._rows = self.db.respond(s, params)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


ITEM = (1, 'ETHUSDT', 'crypto', 'ETH', 100.0, 100.0, 2.0, 0.66, 2.0, 3, False, 0.1, 'TRAILING_PEAK')


class EngineFlowTests(unittest.TestCase):
    def setUp(self):
        self.clock = [1_000_000.0]
        self.alerts = []
        self.db = FakeDB()
        alert._breakout_state.clear()
        alert._gate_alert_ts.clear()
        alert._fake_alert_ts.clear()
        alert._ai_signal_cache.update(ts=0.0, data={})
        patches = [
            mock.patch('time.time', lambda: self.clock[0]),
            mock.patch.object(alert, 'get_db_connection', lambda: self.db),
            mock.patch.object(alert, 'insert_triggered_alert', lambda *a, **k: self.alerts.append((a, k))),
            mock.patch.object(alert, 'play_alert', lambda *a, **k: None),
            mock.patch.object(alert, 'fetch_volume_ratio', lambda s, t: 2.0),
            mock.patch.object(alert, 'btc_regime', lambda: (True, None)),
            mock.patch.object(alert, 'fetch_atr_pct', lambda s, t: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_at(self, price, dt=0.0, item=ITEM):
        self.clock[0] += dt
        return alert.process_breakout_paper_trading(item, price)

    def texts(self):
        return ' | '.join(a[0][3] for a in self.alerts)

    # --- lọc breakout giả -------------------------------------------------
    def test_no_entry_until_held_long_enough(self):
        self.run_at(100.5)                     # vừa vượt đỉnh
        self.assertEqual(self.db.inserts, [])
        self.run_at(100.6, 20)
        self.assertEqual(self.db.inserts, [])  # mới 20s < 30s
        self.run_at(100.6, 15)                 # đủ 35s
        self.assertEqual(len(self.db.inserts), 1)

    def test_wick_is_filtered_and_reported(self):
        self.run_at(100.5)
        self.run_at(99.0, 10)                  # râu nến: quay lại dưới đỉnh
        self.assertEqual(self.db.inserts, [])
        self.assertIn('BREAKOUT GIẢ', self.texts())
        self.run_at(100.5, 5)                  # vượt lại → đồng hồ giữ bắt đầu lại từ đầu
        self.run_at(100.5, 20)
        self.assertEqual(self.db.inserts, [])

    def test_chase_is_rejected_once(self):
        self.run_at(103.5)
        self.run_at(103.6, 10)
        self.assertEqual(self.db.inserts, [])
        self.assertEqual(self.texts().count('BREAKOUT BỊ LOẠI'), 1)

    def test_low_volume_blocks_then_rejects(self):
        with mock.patch.object(alert, 'fetch_volume_ratio', lambda s, t: 0.5):
            self.run_at(100.5)
            self.run_at(100.5, 40)
            self.assertEqual(self.db.inserts, [])
            self.run_at(100.5, 1000)
        self.assertEqual(self.db.inserts, [])
        self.assertIn('khối lượng', self.texts())

    def test_entry_records_context(self):
        self.run_at(100.5)
        self.run_at(100.6, 40)
        row = self.db.inserts[0]
        self.assertEqual(row[-3], 2.0)                  # sl_pct_used
        self.assertIn('"hold_sec": 30', row[-1])        # entry_filters
        self.assertIn('"vol_ratio": 2.0', row[-1])

    def test_filter_can_be_disabled(self):
        with mock.patch.object(alert, 'BREAKOUT_FILTER_ENABLED', False):
            self.run_at(100.0)
        self.assertEqual(len(self.db.inserts), 1)

    # --- cổng rủi ro ------------------------------------------------------
    def test_portfolio_open_limit_blocks_entry(self):
        self.db.stats = (10, 0, 0, 0.0, 0.0)
        self.run_at(100.5)
        self.run_at(100.5, 40)
        self.assertEqual(self.db.inserts, [])
        self.assertIn('CỔNG RỦI RO', self.texts())

    def test_daily_loss_cap_blocks_entry(self):
        self.db.stats = (0, 0, 0, -150.0, -150.0)
        with mock.patch.object(alert, 'DAILY_LOSS_CAP_USD', 100.0):
            self.run_at(100.5)
            self.run_at(100.5, 40)
        self.assertEqual(self.db.inserts, [])

    def test_btc_risk_off_blocks_altcoin_but_not_btc(self):
        with mock.patch.object(alert, 'btc_regime', lambda: (False, 'BTC giảm 4% trong 4 giờ')):
            self.run_at(100.5)
            self.run_at(100.5, 40)
            self.assertEqual(self.db.inserts, [])
            self.assertIn('BTC RISK-OFF', self.texts())
            btc = (2, 'BTCUSDT', 'crypto', 'BTC', 100.0, 100.0, 2.0, 0.66, 2.0, 3, False, 0.1, 'TRAILING_PEAK')
            self.run_at(100.5, 1, btc)
            self.run_at(100.5, 40, btc)
            self.assertEqual(len(self.db.inserts), 1)

    def test_atr_widens_stop_when_enabled(self):
        with mock.patch.object(alert, 'ATR_SL_MULT', 2.0), mock.patch.object(alert, 'fetch_atr_pct', lambda s, t: 2.5):
            self.run_at(100.5)
            self.run_at(100.5, 40)
        self.assertEqual(self.db.inserts[0][-3], 5.0)   # 2.5% × 2

    # --- nhồi lệnh bị chặn bởi trần lỗ, nhưng không bởi số vị thế ---------
    def pos_row(self):
        # id, layer, invested, units, avg_entry, last_buy, highest, sl, next_pyr, is_real, real_units, sl_pct_used
        return (9, 1, 100.0, 1.0, 100.0, 100.0, 100.0, 98.0, 102.0, False, 0.0, 0)

    def test_pyramid_ignores_open_count_limit(self):
        self.db.position = self.pos_row()
        self.db.stats = (99, 99, 99, 0.0, 0.0)
        self.run_at(103.0)
        updates = [s for s in self.db.log if s.startswith('UPDATE public.paper_positions SET current_layer')]
        self.assertEqual(len(updates), 1)

    def test_pyramid_blocked_by_loss_cap(self):
        self.db.position = self.pos_row()
        self.db.stats = (1, 0, 0, -500.0, -500.0)
        with mock.patch.object(alert, 'DAILY_LOSS_CAP_USD', 100.0):
            self.run_at(103.0)
        updates = [s for s in self.db.log if s.startswith('UPDATE public.paper_positions SET current_layer')]
        self.assertEqual(updates, [])
        self.assertIn('KHÔNG nhồi lệnh', self.texts())

    def test_sl_hit_still_closes_when_all_gates_closed(self):
        self.db.position = self.pos_row()
        self.db.stats = (99, 99, 99, -1e9, -1e9)
        with mock.patch.object(alert, 'DAILY_LOSS_CAP_USD', 1.0):
            self.run_at(90.0)                   # dưới SL 98
        closes = [s for s in self.db.log if "SET status = 'CLOSED_SL'" in s]
        self.assertEqual(len(closes), 1)


if __name__ == '__main__':
    unittest.main()
