import unittest
from starter import merge_customer_records

class TestMergeCustomerRecords(unittest.TestCase):
    def test_basic_merge(self):
        records = [
            {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30},
            {'customer_id': 'C2', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Bob', 'age': 25}
        ]
        expected = {
            'C1': {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30},
            'C2': {'customer_id': 'C2', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Bob', 'age': 25}
        }
        self.assertEqual(merge_customer_records(records), expected)

    def test_overlapping_fields(self):
        records = [
            {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30},
            {'customer_id': 'C1', 'updated_at': '2023-04-02T12:00:00Z', 'name': 'Alicia', 'age': 31}
        ]
        expected = {
            'C1': {'customer_id': 'C1', 'updated_at': '2023-04-02T12:00:00Z', 'name': 'Alicia', 'age': 31}
        }
        self.assertEqual(merge_customer_records(records), expected)

    def test_different_updated_at(self):
        records = [
            {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30},
            {'customer_id': 'C1', 'updated_at': '2023-04-01T11:00:00Z', 'name': 'Alice', 'age': 30}
        ]
        expected = {
            'C1': {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30}
        }
        self.assertEqual(merge_customer_records(records), expected)

    def test_empty_list(self):
        records = []
        expected = {}
        self.assertEqual(merge_customer_records(records), expected)

    def test_single_record(self):
        records = [{'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30}]
        expected = {
            'C1': {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30}
        }
        self.assertEqual(merge_customer_records(records), expected)

    def test_duplicate_customer_ids(self):
        records = [
            {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alice', 'age': 30},
            {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alicia', 'age': 31}
        ]
        expected = {
            'C1': {'customer_id': 'C1', 'updated_at': '2023-04-01T12:00:00Z', 'name': 'Alicia', 'age': 31}
        }
        self.assertEqual(merge_customer_records(records), expected)

if __name__ == '__main__':
    unittest.main()
