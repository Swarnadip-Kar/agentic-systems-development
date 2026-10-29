import unittest
from q1_parse_price import parse_price

class TestParsePrice(unittest.TestCase):
    def test_valid_prices(self):
        self.assertEqual(parse_price("$1,234.56 "), 1234.56)
        self.assertEqual(parse_price("$1234.56"), 1234.56)
        self.assertEqual(parse_price("$1234"), 1234.0)
        self.assertEqual(parse_price("The total comes to $42.50 for your order."), 42.5)
        self.assertEqual(parse_price("Total: $1,234.56 due"), 1234.56)
        self.assertEqual(parse_price("That will be $9.0"), 9.0)

    def test_invalid_prices(self):
        with self.assertRaises(ValueError) as context:
            parse_price("")
        self.assertEqual(str(context.exception), "Input string is empty or contains only whitespace.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("   ")
        self.assertEqual(str(context.exception), "Input string is empty or contains only whitespace.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("$1,234.56.78")
        self.assertEqual(str(context.exception), "Invalid price string: '1234.56.78'. The string should represent a valid number.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("$1,234,56a.78")
        self.assertEqual(str(context.exception), "Invalid price string: '123456a.78'. The string should represent a valid number.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("abc")
        self.assertEqual(str(context.exception), "Input string has no dollar signs.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("$")
        self.assertEqual(str(context.exception), "Invalid price string: ''. The string should represent a valid number.")
        
        with self.assertRaises(ValueError) as context:
            parse_price("$1,234,567.89.00")
        self.assertEqual(str(context.exception), "Invalid price string: '1234567.89.00'. The string should represent a valid number.")

if __name__ == '__main__':
    unittest.main()
