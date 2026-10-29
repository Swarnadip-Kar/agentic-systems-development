import unittest
from starter import compute_late_fee

class TestComputeLateFee(unittest.TestCase):
    def test_on_time_payment(self):
        self.assertEqual(compute_late_fee("2023-10-01", "2023-10-01", 10.0), 0.0)

    def test_late_payment(self):
        self.assertEqual(compute_late_fee("2023-10-01", "2023-10-05", 10.0), 40.0)

    def test_different_daily_rate(self):
        self.assertEqual(compute_late_fee("2023-10-01", "2023-10-05", 5.0), 20.0)

    def test_invalid_due_date_format(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2023-10-01T", "2023-10-05", 10.0)

    def test_invalid_paid_date_format(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2023-10-01", "2023-10-05T", 10.0)

    def test_paid_before_due(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2023-10-05", "2023-10-01", 10.0)

    def test_zero_daily_rate(self):
        self.assertEqual(compute_late_fee("2023-10-01", "2023-10-05", 0.0), 0.0)

    def test_large_daily_rate(self):
        self.assertEqual(compute_late_fee("2023-10-01", "2023-10-05", 1000.0), 4000.0)

    def test_large_number_of_days(self):
        self.assertEqual(compute_late_fee("2023-01-01", "2023-12-31", 10.0), 3640.0)

    def test_leap_year(self):
        self.assertEqual(compute_late_fee("2024-02-28", "2024-03-01", 10.0), 20.0)  # Updated expected value

    def test_non_existent_date(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2023-02-30", "2023-03-01", 10.0)

    def test_negative_dates(self):
        with self.assertRaises(ValueError):
            compute_late_fee("-2023-10-01", "-2023-10-05", 10.0)

    def test_future_due_date(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2025-10-01", "2023-10-05", 10.0)

    def test_future_paid_date(self):
        with self.assertRaises(ValueError):
            compute_late_fee("2023-10-01", "2077-10-01", 10.0)
