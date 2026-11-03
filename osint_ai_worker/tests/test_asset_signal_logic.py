import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_signal_logic import decide_ai_status as d  # noqa: E402


class HysteresisTests(unittest.TestCase):
    def test_first_run_accepts_immediately(self):
        self.assertEqual(d(None, None, 0, 'avoid'), ('avoid', None, 0))
        self.assertEqual(d('buy', None, 0, 'avoid', first_run=True), ('avoid', None, 0))

    def test_same_status_clears_pending(self):
        self.assertEqual(d('buy', 'avoid', 1, 'buy'), ('buy', None, 0))

    def test_needs_two_consecutive_runs(self):
        s = d('buy', None, 0, 'avoid')
        self.assertEqual(s, ('buy', 'avoid', 1))
        self.assertEqual(d(*s, 'avoid'), ('avoid', None, 0))

    def test_flapping_never_flips(self):
        status, pend, cnt = 'buy', None, 0
        for rec in ['avoid', 'buy', 'avoid', 'buy', 'avoid']:
            status, pend, cnt = d(status, pend, cnt, rec)
        self.assertEqual(status, 'buy')

    def test_configurable_runs(self):
        self.assertEqual(d('buy', None, 0, 'avoid', confirm_runs=1), ('avoid', None, 0))
        s = ('buy', None, 0)
        for _ in range(2):
            s = d(*s, 'avoid', confirm_runs=3)
        self.assertEqual(s[0], 'buy')
        self.assertEqual(d(*s, 'avoid', confirm_runs=3)[0], 'avoid')


if __name__ == '__main__':
    unittest.main()
