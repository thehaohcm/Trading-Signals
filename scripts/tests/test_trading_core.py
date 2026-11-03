import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import trading_core as tc  # noqa: E402


def old_compute_stop_loss(avg_entry, highest, layer, max_pyramids, sl_pct, spread_pct, sl_mode, prev_sl=0.0):
    """Bản gốc trong alert.py trước khi tách (TRAILING_ACTIVATION_PCT=1.0) — để chứng minh không đổi hành vi."""
    breakeven = avg_entry * (1.0 + spread_pct / 100.0)
    base_sl = avg_entry * (1.0 - sl_pct / 100.0)
    trailing_from_peak = highest * (1.0 - sl_pct / 100.0)
    trailing_active = (highest >= avg_entry * (1.0 + 1.0 / 100.0)) or \
                      (highest >= avg_entry * (1.0 + sl_pct / 100.0)) or \
                      (layer >= max_pyramids)
    if sl_mode == 'BREAKEVEN_HOLD' and layer >= 2:
        trailing_active = True
    sl = max(breakeven, trailing_from_peak) if trailing_active else base_sl
    if prev_sl and prev_sl > sl:
        sl = prev_sl
    return sl, breakeven


class EquivalenceTests(unittest.TestCase):
    def test_stop_loss_same_as_original(self):
        rnd = random.Random(1)
        for _ in range(3000):
            avg = rnd.uniform(1, 500)
            args = (avg, avg * rnd.uniform(0.98, 1.2), rnd.randint(1, 4), rnd.randint(1, 4),
                    rnd.uniform(0.5, 5), rnd.uniform(0, 0.5), rnd.choice(['TRAILING_PEAK', 'BREAKEVEN_HOLD']),
                    rnd.choice([0.0, avg * rnd.uniform(0.9, 1.1)]))
            self.assertEqual(tc.compute_stop_loss(*args), old_compute_stop_loss(*args))

    def test_stop_loss_only_ratchets_up(self):
        sl1, _ = tc.compute_stop_loss(100, 110, 1, 3, 2, 0.1, 'TRAILING_PEAK')
        sl2, _ = tc.compute_stop_loss(100, 105, 1, 3, 2, 0.1, 'TRAILING_PEAK', prev_sl=sl1)
        self.assertGreaterEqual(sl2, sl1)

    def test_size_order(self):
        self.assertEqual(tc.size_order('crypto', 100, 0), (0.0, 0.0))
        u, c = tc.size_order('stock_vn', 10_000_000, 25_300)
        self.assertEqual(u % 100, 0)
        self.assertAlmostEqual(c, u * 25_300)
        u, _ = tc.size_order('crypto', 100, 50)
        self.assertAlmostEqual(u, 2.0)


class BreakoutFilterTests(unittest.TestCase):
    kw = dict(margin_pct=0.1, hold_sec=45, max_chase_pct=2.0, min_vol_ratio=1.2, max_wait_sec=900)

    def ev(self, price, now, since=None, rejected=False, vol=None, **over):
        kw = dict(self.kw, **over)
        return tc.evaluate_breakout_confirmation(price, 100.0, now, since, rejected, vol_ratio=vol, **kw)

    def test_below_trigger_is_idle(self):
        self.assertEqual(self.ev(100.05, 1000)[0], 'idle')   # chưa vượt margin 0.1%

    def test_wick_then_fallback_never_enters(self):
        a, _, since, rej = self.ev(100.5, 1000)
        self.assertEqual(a, 'wait')
        a, _, since, rej = self.ev(100.5, 1020, since)
        self.assertEqual(a, 'wait')
        a, _, since, _ = self.ev(99.0, 1030, since)           # rút râu quay lại → huỷ đợt
        self.assertEqual((a, since), ('idle', None))

    def test_hold_then_enter(self):
        _, _, since, _ = self.ev(100.5, 1000)
        a, why, *_ = self.ev(100.6, 1046, since, vol=1.5)
        self.assertEqual(a, 'enter', why)

    def test_low_volume_waits_then_rejects_after_max_wait(self):
        _, _, since, _ = self.ev(100.5, 1000)
        a, *_ = self.ev(100.5, 1100, since, vol=0.6)
        self.assertEqual(a, 'wait')
        a, why, _, rej = self.ev(100.5, 1000 + 901, since, vol=0.6)
        self.assertEqual(a, 'reject')
        self.assertTrue(rej)
        self.assertIn('khối lượng', why)
        # đợt đã bị loại: im lặng cho tới khi giá về dưới mốc
        self.assertEqual(self.ev(100.5, 2000, since, rejected=True)[0], 'idle')
        a, _, since2, rej2 = self.ev(99, 2100, since, rejected=True)
        self.assertEqual((a, since2, rej2), ('idle', None, False))

    def test_unknown_volume_does_not_block(self):
        _, _, since, _ = self.ev(100.5, 1000)
        self.assertEqual(self.ev(100.5, 1100, since, vol=None)[0], 'enter')

    def test_chase_cap_rejects_gap_up(self):
        a, why, _, rej = self.ev(103.0, 1000)
        self.assertEqual(a, 'reject')
        self.assertTrue(rej)
        self.assertIn('không đuổi giá', why)

    def test_disabled_filters_enter_immediately(self):
        a, *_ = tc.evaluate_breakout_confirmation(100.0, 100.0, 1000, None, False)
        self.assertEqual(a, 'enter')


class VolumeRatioTests(unittest.TestCase):
    def test_projection_and_closed(self):
        vols = [10] * 21 + [5]          # trung bình 10; nến đang chạy mới 50% thời gian có 5 → chiếu = 10
        self.assertAlmostEqual(tc.volume_ratio(vols, 0, 300_000, 150_000), 1.0)
        vols = [10] * 21 + [30]         # bùng nổ: 30 trong 50% thời gian → chiếu 60 → 6x
        self.assertAlmostEqual(tc.volume_ratio(vols, 0, 300_000, 150_000), 6.0)

    def test_insufficient_data(self):
        self.assertIsNone(tc.volume_ratio([1, 2], 0, 1, 1))
        self.assertIsNone(tc.volume_ratio([0, 0, 0, 0, 0], 0, 300_000, 1))


class PortfolioGateTests(unittest.TestCase):
    limits = dict(max_open=10, max_open_real=5, max_daily_sl_total=6, daily_loss_cap=100, weekly_loss_cap=300)

    def g(self, kind='open', real=False, **stats):
        base = dict(open_total=0, open_real=0, sl_today_total=0, pnl_today=0, pnl_week=0)
        base.update(stats)
        return tc.portfolio_gate(base, self.limits, kind, real)

    def test_ok(self):
        self.assertEqual(self.g(), (True, None))

    def test_open_limits(self):
        self.assertFalse(self.g(open_total=10)[0])
        self.assertFalse(self.g(open_real=5, real=True)[0])
        self.assertTrue(self.g(open_real=5, real=False)[0])
        self.assertFalse(self.g(sl_today_total=6)[0])

    def test_loss_caps_block_open_and_add(self):
        self.assertFalse(self.g(pnl_today=-100)[0])
        self.assertFalse(self.g(kind='add', pnl_week=-300)[0])

    def test_add_ignores_position_count_limits(self):
        self.assertTrue(self.g(kind='add', open_total=99, open_real=99, sl_today_total=99, real=True)[0])

    def test_zero_means_disabled(self):
        off = dict(max_open=0, max_open_real=0, max_daily_sl_total=0, daily_loss_cap=0, weekly_loss_cap=0)
        self.assertTrue(tc.portfolio_gate(dict(open_total=99, pnl_today=-1e9, pnl_week=-1e9), off)[0])


class AtrTests(unittest.TestCase):
    def test_atr_percent(self):
        highs = [101] * 20
        lows = [99] * 20
        closes = [100] * 20
        self.assertAlmostEqual(tc.atr_percent(highs, lows, closes, 14), 2.0)
        self.assertIsNone(tc.atr_percent([1] * 5, [1] * 5, [1] * 5, 14))

    def test_effective_sl(self):
        self.assertEqual(tc.effective_sl_pct(2.0, 3.0, 0), 2.0)         # tắt
        self.assertEqual(tc.effective_sl_pct(2.0, None, 2), 2.0)        # thiếu ATR
        self.assertEqual(tc.effective_sl_pct(2.0, 0.5, 2), 2.0)         # không chặt hơn mức người dùng đặt
        self.assertEqual(tc.effective_sl_pct(2.0, 3.0, 2), 6.0)
        self.assertEqual(tc.effective_sl_pct(2.0, 9.0, 2), 8.0)         # trần 4x

    def test_risk_sizing(self):
        self.assertAlmostEqual(tc.position_size_for_risk(20, 100, 2), 10.0)   # lỗ 2$ x 10 = 20$
        self.assertEqual(tc.position_size_for_risk(20, 0, 2), 0.0)


class BtcRegimeTests(unittest.TestCase):
    def test_uptrend_ok(self):
        self.assertTrue(tc.btc_regime_ok([100 + i for i in range(80)])[0])

    def test_sharp_drop_blocks(self):
        closes = [100.0] * 75 + [100, 99, 97, 96, 95]
        ok, why = tc.btc_regime_ok(closes)
        self.assertFalse(ok)
        self.assertIn('4 giờ', why)

    def test_downtrend_below_ema_blocks(self):
        closes = [200 - i * 0.5 for i in range(80)]    # giảm đều, mỗi 4h < 3% nên chỉ EMA chặn
        ok, why = tc.btc_regime_ok(closes, max_drop_pct_4h=10)
        self.assertFalse(ok)
        self.assertIn('EMA', why)

    def test_missing_data_fail_open(self):
        self.assertEqual(tc.btc_regime_ok([]), (True, None))


class AiStaleTests(unittest.TestCase):
    def test_rules(self):
        now = 1_000_000.0
        self.assertEqual(tc.effective_ai_status('avoid', 'admin', now - 999999, now), ('avoid', False))
        self.assertEqual(tc.effective_ai_status('avoid', 'ai', now - 3600, now), ('avoid', False))
        self.assertEqual(tc.effective_ai_status('avoid', 'ai', now - 49 * 3600, now), (None, True))
        self.assertEqual(tc.effective_ai_status('buy', 'ai', None, now), ('buy', False))


if __name__ == '__main__':
    unittest.main()
