import unittest
from starter import calculate_gpa

class TestCalculateGPA(unittest.TestCase):
    def test_basic_gpa_calculation(self):
        grades = [
            ("Math", 4.0, 3),
            ("Science", 3.0, 4),
            ("History", 2.0, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.0, places=7)

    def test_empty_grades(self):
        grades = []
        self.assertEqual(calculate_gpa(grades), 0.0)

    def test_no_credit_hours(self):
        grades = [
            ("Math", 4.0, 0),
            ("Science", 3.0, 0)
        ]
        self.assertEqual(calculate_gpa(grades), 0.0)

    def test_single_course(self):
        grades = [("Math", 4.0, 3)]
        self.assertEqual(calculate_gpa(grades), 4.0)

    def test_all_zero_credit_hours(self):
        grades = [
            ("Math", 4.0, 0),
            ("Science", 3.0, 0),
            ("History", 2.0, 0)
        ]
        self.assertEqual(calculate_gpa(grades), 0.0)

    def test_mixed_credit_hours(self):
        grades = [
            ("Math", 4.0, 3),
            ("Science", 3.0, 0),
            ("History", 2.0, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.0, places=7)

    def test_decimal_grade_points(self):
        grades = [
            ("Math", 3.7, 3),
            ("Science", 2.5, 4),
            ("History", 3.2, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.07, places=7)

    def test_large_numbers(self):
        grades = [
            ("Math", 4.0, 1000),
            ("Science", 3.0, 2000),
            ("History", 2.0, 3000)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 2.6666666666666665, places=7)

    def test_negative_credit_hours(self):
        grades = [
            ("Math", 4.0, -3),
            ("Science", 3.0, 4)
        ]
        with self.assertRaises(ValueError):
            calculate_gpa(grades)

    def test_negative_grade_points(self):
        grades = [
            ("Math", -4.0, 3),
            ("Science", 3.0, 4)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 0.0, places=7)

    def test_zero_grade_points(self):
        grades = [
            ("Math", 0.0, 3),
            ("Science", 3.0, 4)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 1.7142857142857142, places=7)

    def test_all_same_grade_points(self):
        grades = [
            ("Math", 3.0, 3),
            ("Science", 3.0, 4),
            ("History", 3.0, 3)
        ]
        self.assertEqual(calculate_gpa(grades), 3.0)

    def test_all_same_credit_hours(self):
        grades = [
            ("Math", 4.0, 3),
            ("Science", 3.0, 3),
            ("History", 2.0, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.0, places=7)

    def test_single_subject_with_zero_credit_hours(self):
        grades = [("Math", 4.0, 0)]
        self.assertEqual(calculate_gpa(grades), 0.0)

    def test_multiple_subjects_with_zero_credit_hours(self):
        grades = [
            ("Math", 4.0, 0),
            ("Science", 3.0, 0),
            ("History", 2.0, 0)
        ]
        self.assertEqual(calculate_gpa(grades), 0.0)

    def test_multiple_subjects_with_nonzero_credit_hours(self):
        grades = [
            ("Math", 4.0, 3),
            ("Science", 3.0, 4),
            ("History", 2.0, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.0, places=7)

    def test_multiple_subjects_with_mixed_credit_hours(self):
        grades = [
            ("Math", 4.0, 3),
            ("Science", 3.0, 0),
            ("History", 2.0, 3)
        ]
        self.assertAlmostEqual(calculate_gpa(grades), 3.0, places=7)

    def test_negative_credit_hours_exception(self):
        grades = [
            ("Math", 4.0, -3),
            ("Science", 3.0, 4)
        ]
        with self.assertRaises(ValueError):
            calculate_gpa(grades)
