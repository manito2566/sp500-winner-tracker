import unittest
import numpy as np
import pandas as pd
from tracker import analyze, normalize_ticker, period_return

class TrackerTests(unittest.TestCase):
    def setUp(self):
        index = pd.bdate_range("2024-01-01", periods=300)
        self.prices = pd.DataFrame({"SPY": np.linspace(100,125,300), "FAST": np.linspace(100,190,300), "WEAK": np.linspace(100,90,300)}, index=index)
    def test_period_return(self):
        expected = self.prices["SPY"].iloc[-1] / self.prices["SPY"].iloc[-22] - 1
        self.assertAlmostEqual(period_return(self.prices["SPY"], 21), expected)
    def test_strong_stock_is_leader(self):
        result = analyze(self.prices, "FAST")
        self.assertEqual(result["Status"], "Leader")
        self.assertGreater(result["RS 3M"], 0)
    def test_weak_stock_requires_review(self):
        result = analyze(self.prices, "WEAK")
        self.assertEqual(result["Status"], "Review/Exit")
        self.assertLess(result["RS 3M"], 0)
    def test_normalizes_tradingview_symbols(self):
        self.assertEqual(normalize_ticker("NASDAQ:NVDA"), "NVDA")
        self.assertEqual(normalize_ticker(" AMEX:SPY "), "SPY")
        self.assertEqual(normalize_ticker("BRK.B"), "BRK-B")

if __name__ == "__main__": unittest.main()
