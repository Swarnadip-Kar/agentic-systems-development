import unittest
from starter import merge_overlapping_intervals

class TestMergeOverlappingIntervals(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(merge_overlapping_intervals([]), [])

    def test_single_interval(self):
        self.assertEqual(merge_overlapping_intervals([(1, 3)]), [(1, 3)])

    def test_no_overlapping_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(1, 2), (4, 5), (8, 10)]), [(1, 2), (4, 5), (8, 10)])

    def test_overlapping_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(1, 3), (2, 4), (5, 7)]), [(1, 4), (5, 7)])

    def test_touching_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(1, 2), (2, 3), (3, 4)]), [(1, 4)])

    def test_intervals_with_negative_values(self):
        self.assertEqual(merge_overlapping_intervals([(-2, -1), (-1, 0), (1, 2)]), [(-2, 0), (1, 2)])

    def test_intervals_with_floating_point_numbers(self):
        self.assertEqual(merge_overlapping_intervals([(1.0, 2.0), (2.5, 3.0), (3.5, 4.0)]), [(1.0, 2.0), (2.5, 3.0), (3.5, 4.0)])

    def test_empty_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(1, 1)]), [(1, 1)])

    def test_single_point_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(1, 1), (2, 2)]), [(1, 1), (2, 2)])

    def test_large_intervals(self):
        self.assertEqual(merge_overlapping_intervals([(10**10, 10**10 + 1), (10**10 + 1, 10**10 + 3)]), [(10**10, 10**10 + 3)])

    def test_intervals_with_non_integer_values(self):
        self.assertEqual(merge_overlapping_intervals([(1.5, 2.5), (2.5, 3.5)]), [(1.5, 3.5)])

    def test_intervals_with_negative_end_values(self):
        self.assertEqual(merge_overlapping_intervals([(1, 0), (2, 3)]), [(2, 3)])

if __name__ == '__main__':
    unittest.main()
