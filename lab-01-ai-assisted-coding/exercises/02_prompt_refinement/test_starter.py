from starter import sort_names


def test_sorts_lowercase_names():
    assert sort_names(["charlie", "alice", "bob"]) == ["alice", "bob", "charlie"]


def test_case_insensitive_order():
    # A naive `sorted(names)` (a common response to a vague "sort
    # alphabetically" prompt) sorts by ASCII order, which puts every
    # uppercase letter before any lowercase letter -- that's the point
    # of this test.
    assert sort_names(["banana", "Cherry", "apple"]) == ["apple", "banana", "Cherry"]


def test_empty_list():
    assert sort_names([]) == []


def test_single_name():
    assert sort_names(["Solo"]) == ["Solo"]


def test_already_sorted_same_case():
    assert sort_names(["ann", "bob", "cara"]) == ["ann", "bob", "cara"]
