from bug_a import moving_average


def test_basic_window():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]


def test_window_equals_length():
    assert moving_average([1, 2, 3], 3) == [2.0]


def test_larger_example():
    assert moving_average([2, 4, 6, 8, 10], 3) == [4.0, 6.0, 8.0]
