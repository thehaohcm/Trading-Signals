import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtest as bt


def bar(t, o, h, l, c, v=100.0):
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


def flat(n, price=100.0):
    return [bar(i, price, price + 0.5, price - 0.5, price) for i in range(n)]


P = bt.Params(lookback=30, margin_pct=0.05, max_chase_pct=0, min_vol_ratio=0, sl_pct=2.0, fee_pct=0, slippage_pct=0,
              max_pyramids=3, pyramid_step_pct=50.0)  # nhồi lệnh xa → không kích hoạt trong test


class BacktestTests(unittest.TestCase):
    def test_no_breakout_no_trades(self):
        self.assertEqual(bt.simulate(flat(100), P), [])

    def test_breakout_then_stop_out_loses_about_sl(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5)]            # breakout, đóng 102.5
        bars += [bar(41, 102, 102.2, 99, 100)]                         # rơi xuống dưới SL 102.5*0.98=100.45
        tr = bt.simulate(bars, P)
        self.assertEqual(len(tr), 1)
        self.assertEqual(tr[0]['reason'], 'SL')
        self.assertAlmostEqual(tr[0]['pnl_pct'], -2.0, places=1)

    def test_trailing_locks_profit(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5)]
        bars += [bar(41, 102.5, 110, 102.5, 109)]                      # lên đỉnh 110 → SL trailing ≈ 107.8
        bars += [bar(42, 109, 109, 105, 106)]                          # rơi chạm SL
        tr = bt.simulate(bars, P)
        self.assertGreater(tr[0]['pnl_pct'], 4.0)

    def test_gap_down_fills_at_open_not_sl(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5)]
        bars += [bar(41, 95, 96, 94, 95)]                              # gap xuống dưới SL
        tr = bt.simulate(bars, P)
        self.assertLess(tr[0]['pnl_pct'], -5.0)

    def test_volume_filter_blocks_entry(self):
        q = bt.Params(**{**bt.asdict(P), 'min_vol_ratio': 1.5})
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5, v=100.0)]
        self.assertEqual(bt.simulate(bars, q), [])
        bars[-1]['v'] = 300.0
        self.assertEqual(len(bt.simulate(bars, q)), 1)

    def test_chase_filter(self):
        q = bt.Params(**{**bt.asdict(P), 'max_chase_pct': 2.0})
        bars = flat(40) + [bar(40, 100, 106, 100, 105)]                # đóng cao hơn đỉnh 100.5 tới 4.5%
        self.assertEqual(bt.simulate(bars, q), [])

    def test_fees_reduce_pnl(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102, 102.2, 99, 100)]
        free = bt.simulate(bars, P)[0]['pnl_pct']
        paid = bt.simulate(bars, bt.Params(**{**bt.asdict(P), 'fee_pct': 0.1}))[0]['pnl_pct']
        self.assertLess(paid, free)

    def test_pyramid_adds_layer(self):
        q = bt.Params(**{**bt.asdict(P), 'pyramid_step_pct': 2.0})
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102.5, 108, 102.5, 107), bar(42, 107, 107, 100, 101)]
        tr = bt.simulate(bars, q)
        self.assertGreaterEqual(tr[0]['layers'], 2)

    def test_max_pyramids_reached_moves_to_breakeven_like_engine(self):
        q = bt.Params(**{**bt.asdict(P), 'max_pyramids': 1})
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102.5, 103, 101, 102)]
        tr = bt.simulate(bars, q)
        self.assertEqual(tr[0]['reason'], 'SL')            # SL = hoà vốn ngay khi đã đủ tầng (đúng logic engine)
        self.assertGreater(tr[0]['pnl_pct'], -0.6)

    def test_stats(self):
        s = bt.stats([dict(pnl_pct=4, bars_held=3, reason='SL', weight=1), dict(pnl_pct=-2, bars_held=5, reason='SL', weight=1)])
        self.assertEqual((s['trades'], s['win_rate'], s['profit_factor'], s['total_pnl_pct']), (2, 50.0, 2.0, 2.0))
        self.assertEqual(bt.stats([])['trades'], 0)

    def test_open_position_closed_at_end(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102.5, 104, 102.5, 104)]
        self.assertEqual(bt.simulate(bars, P)[0]['reason'], 'OPEN_AT_END')


VN = bt.Params(**{**bt.asdict(P), 'market': 'vn', 'vn_t_plus_bars': 2, 'vn_price_band_pct': 7.0, 'vn_lot_size': 100})


class VnMarketTests(unittest.TestCase):
    def test_t_plus_blocks_sl_for_2_bars(self):
        # breakout rồi rơi mạnh ngay hôm sau (còn trong T+2) → KHÔNG được thoát, chỉ thoát được ở bar thứ 3
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5)]
        bars += [bar(41, 95, 95, 90, 90)]     # T+1: giá sập (nhưng biên độ 7% sẽ kẹp giá này lại)
        bars += [bar(42, 90, 90, 85, 86)]     # T+2: vẫn trong thời gian khoá
        bars += [bar(43, 86, 87, 80, 82)]     # T+3: đủ điều kiện bán, giá vẫn dưới SL
        tr = bt.simulate(bars, VN)
        self.assertEqual(len(tr), 1)
        self.assertEqual(tr[0]['bars_held'], 2)   # i-i0=2 là đủ T+2, thoát được ngay ở bar 42

    def test_price_band_caps_gap(self):
        # T+1 giá đặt lệnh giảm sàn -50% nhưng biên độ HOSE chỉ cho rơi tối đa 7%/phiên
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5)]
        bars += [bar(41, 102.5, 102.5, 50, 50)]
        bars += [bar(42, 50, 90, 50, 80)]
        bars += [bar(43, 80, 90, 70, 75)]
        tr = bt.simulate(bars, VN)
        # giá sau khi kẹp biên độ ở bar 41 tối thiểu là 102.5*0.93 ≈ 95.3, lỗ của lệnh không thể tới -50%
        self.assertGreater(tr[0]['pnl_pct'], -20.0)

    def test_lot_size_100_and_tax_applied(self):
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102.5, 103, 101, 102), bar(42, 102, 102, 99, 100)]
        tr = bt.simulate(bars, VN)
        self.assertEqual(tr[0]['weight'], 1.0)   # 100 cổ / lô 100 = 1.0
        # thuế bán làm lỗ nhiều hơn một chút so với không có thuế
        no_tax = bt.Params(**{**bt.asdict(VN), 'vn_tax_sell_pct': 0.0})
        tr_no_tax = bt.simulate(bars, no_tax)
        self.assertLess(tr[0]['pnl_pct'], tr_no_tax[0]['pnl_pct'])

    def test_crypto_mode_unaffected_by_vn_defaults(self):
        # market='crypto' (mặc định) phải bỏ qua mọi ràng buộc VN, giữ hành vi gốc
        bars = flat(40) + [bar(40, 100, 103, 100, 102.5), bar(41, 102, 102.2, 99, 100)]
        self.assertEqual(bt.simulate(bars, P), bt.simulate(bars, bt.Params(**{**bt.asdict(P), 'market': 'crypto'})))


if __name__ == '__main__':
    unittest.main()
