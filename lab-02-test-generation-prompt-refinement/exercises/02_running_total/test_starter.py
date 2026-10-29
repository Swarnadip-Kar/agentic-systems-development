import unittest
from starter import get_running_total

class TestGetRunningTotal(unittest.TestCase):
    def test_basic_transactions(self):
        transactions = [
            {'amount': 100, 'type': 'credit'},
            {'amount': 50, 'type': 'debit'},
            {'amount': 25, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [100, 50, 75])

    def test_only_credits(self):
        transactions = [
            {'amount': 100, 'type': 'credit'},
            {'amount': 200, 'type': 'credit'},
            {'amount': 300, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [100, 300, 600])

    def test_only_debits(self):
        transactions = [
            {'amount': 100, 'type': 'debit'},
            {'amount': 200, 'type': 'debit'},
            {'amount': 300, 'type': 'debit'}
        ]
        self.assertEqual(get_running_total(transactions), [-100, -300, -600])

    def test_mixed_transactions(self):
        transactions = [
            {'amount': 100, 'type': 'credit'},
            {'amount': 50, 'type': 'debit'},
            {'amount': 25, 'type': 'credit'},
            {'amount': 75, 'type': 'debit'}
        ]
        self.assertEqual(get_running_total(transactions), [100, 50, 75, 0])

    def test_empty_transactions(self):
        transactions = []
        self.assertEqual(get_running_total(transactions), [])

    def test_single_credit(self):
        transactions = [{'amount': 100, 'type': 'credit'}]
        self.assertEqual(get_running_total(transactions), [100])

    def test_single_debit(self):
        transactions = [{'amount': 100, 'type': 'debit'}]
        self.assertEqual(get_running_total(transactions), [-100])

    def test_large_numbers(self):
        transactions = [
            {'amount': 1000000, 'type': 'credit'},
            {'amount': 500000, 'type': 'debit'},
            {'amount': 250000, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [1000000, 500000, 750000])

    def test_decimal_amounts(self):
        transactions = [
            {'amount': 100.50, 'type': 'credit'},
            {'amount': 50.25, 'type': 'debit'},
            {'amount': 25.75, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [100.50, 50.25, 76.00])

    def test_negative_amounts(self):
        transactions = [
            {'amount': -100, 'type': 'credit'},
            {'amount': -50, 'type': 'debit'},
            {'amount': -25, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [-100, -50, -75])

    def test_zero_amounts(self):
        transactions = [
            {'amount': 0, 'type': 'credit'},
            {'amount': 0, 'type': 'debit'},
            {'amount': 0, 'type': 'credit'}
        ]
        self.assertEqual(get_running_total(transactions), [0, 0, 0])

if __name__ == '__main__':
    unittest.main()
