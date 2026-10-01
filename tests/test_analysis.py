"""Checks for failures that could materially change the reported results."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analysis", ROOT / "python/analysis.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class AnalysisTests(unittest.TestCase):
    def test_official_city_figures_and_annual_coverage(self):
        source = ROOT / "data/raw/mbie_monthly_ta_2026-09.csv"
        frame, quality = analysis.clean_data(source)
        self.assertEqual(quality["excluded_aggregate_or_unallocated_rows"], 804)
        with analysis.make_database(frame, ":memory:") as con:
            row = con.execute("SELECT median_rent, prior_year_median, rent_yoy_pct FROM latest_snapshot WHERE location = 'Christchurch City'").fetchone()
            self.assertEqual(row, (550, 530, 3.77))
            incomplete = con.execute("SELECT months_present, full_year_lodged_bonds FROM annual_activity WHERE location = 'Christchurch City' AND year = '2026'").fetchone()
            self.assertEqual(incomplete, (7, None))
            total = con.execute("SELECT full_year_lodged_bonds FROM annual_activity WHERE location = 'Christchurch City' AND year = '2025'").fetchone()[0]
            raw = pd.read_csv(source)
            independent = raw[(raw.location == 'Christchurch City') & raw.TimeFrame.str.endswith('/2025')].LodgedBonds.sum()
            self.assertEqual(total, independent)

    def test_missing_calendar_month_is_not_replaced_by_previous_row(self):
        frame = pd.DataFrame({"month": ["2024-06-01", "2025-07-01"],
                              "location_id": [1, 1], "location": ["Test", "Test"],
                              "median_rent": [100, 200], "lodged_bonds": [30, 60]})
        with analysis.make_database(frame, ":memory:") as con:
            result = con.execute("SELECT prior_year_median, rent_yoy_pct FROM latest_snapshot").fetchone()
            self.assertEqual(result, (None, None))

    def test_duplicate_keys_fail_and_missing_values_stay_missing(self):
        raw = pd.read_csv(ROOT / 'data/raw/mbie_monthly_ta_2026-09.csv').head(3)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.csv'
            pd.concat([raw, raw.tail(1)]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                analysis.clean_data(path)
            raw.loc[2, 'MedianRent'] = 0
            raw.to_csv(path, index=False)
            cleaned, _ = analysis.clean_data(path)
            self.assertTrue(pd.isna(cleaned.loc[cleaned.location.eq('Auckland'), 'median_rent'].iloc[0]))


if __name__ == '__main__':
    unittest.main()
