import unittest
from starter import batch_pack_quantities

class TestBatchPackQuantities(unittest.TestCase):
    def test_zero_order_quantity(self):
        self.assertEqual(batch_pack_quantities(0, 5), 0)

    def test_zero_pack_size(self):
        with self.assertRaises(ValueError):
            batch_pack_quantities(10, 0)

    def test_negative_order_quantity(self):
        with self.assertRaises(ValueError):
            batch_pack_quantities(-10, 5)

    def test_negative_pack_size(self):
        with self.assertRaises(ValueError):
            batch_pack_quantities(10, -5)

    def test_full_packs(self):
        self.assertEqual(batch_pack_quantities(10, 5), 2)
        self.assertEqual(batch_pack_quantities(20, 10), 2)

    def test_partial_pack(self):
        self.assertEqual(batch_pack_quantities(11, 5), 3)
        self.assertEqual(batch_pack_quantities(21, 10), 3)

    def test_single_unit(self):
        self.assertEqual(batch_pack_quantities(1, 1), 1)

    def test_large_order_and_small_pack(self):
        self.assertEqual(batch_pack_quantities(100, 1), 100)

    def test_large_order_and_large_pack(self):
        self.assertEqual(batch_pack_quantities(100, 100), 1)

    def test_decimal_order_quantity(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities(10.5, 5)

    def test_decimal_pack_size(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities(10, 5.5)

    def test_empty_string_order_quantity(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities("", 5)

    def test_empty_string_pack_size(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities(10, "")

    def test_non_integer_order_quantity(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities(10.0, 5)

    def test_non_integer_pack_size(self):
        with self.assertRaises(TypeError):
            batch_pack_quantities(10, 5.0)

    def test_large_order_and_large_pack(self):
        self.assertEqual(batch_pack_quantities(10**10, 10**5), 10**5)

if __name__ == '__main__':
    unittest.main()
