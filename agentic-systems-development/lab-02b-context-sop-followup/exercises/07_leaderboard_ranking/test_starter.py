import unittest
from starter import rank_leaderboard

class TestRankLeaderboard(unittest.TestCase):
    def test_single_player(self):
        players = [("Alice", 100)]
        expected = [("Alice", 1)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_no_ties(self):
        players = [("Alice", 100), ("Bob", 90), ("Charlie", 80)]
        expected = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_with_ties(self):
        players = [("Alice", 100), ("Bob", 100), ("Charlie", 80)]
        expected = [("Alice", 1), ("Bob", 1), ("Charlie", 3)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_multiple_ties(self):
        players = [("Alice", 100), ("Bob", 100), ("Charlie", 90), ("David", 90), ("Eve", 80)]
        expected = [("Alice", 1), ("Bob", 1), ("Charlie", 3), ("David", 3), ("Eve", 5)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_all_same_scores(self):
        players = [("Alice", 100), ("Bob", 100), ("Charlie", 100)]
        expected = [("Alice", 1), ("Bob", 1), ("Charlie", 1)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_empty_list(self):
        players = []
        expected = []
        self.assertEqual(rank_leaderboard(players), expected)

    def test_single_tie_at_top(self):
        players = [("Alice", 100), ("Bob", 100), ("Charlie", 90), ("David", 80)]
        expected = [("Alice", 1), ("Bob", 1), ("Charlie", 3), ("David", 4)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_single_tie_at_bottom(self):
        players = [("Alice", 100), ("Bob", 90), ("Charlie", 90), ("David", 80)]
        expected = [("Alice", 1), ("Bob", 2), ("Charlie", 2), ("David", 4)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_all_different_scores(self):
        players = [("Alice", 100), ("Bob", 95), ("Charlie", 90), ("David", 85), ("Eve", 80)]
        expected = [("Alice", 1), ("Bob", 2), ("Charlie", 3), ("David", 4), ("Eve", 5)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_negative_scores(self):
        players = [("Alice", 100), ("Bob", -10), ("Charlie", 80)]
        expected = [("Alice", 1), ("Charlie", 2)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_float_scores(self):
        players = [("Alice", 100.5), ("Bob", 100), ("Charlie", 90)]
        expected = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_names_with_special_characters(self):
        players = [("Alice!", 100), ("Bob_123", 90), ("Charlie&", 80)]
        expected = [("Alice!", 1), ("Bob_123", 2), ("Charlie&", 3)]
        self.assertEqual(rank_leaderboard(players), expected)

    def test_names_with_spaces(self):
        players = [("Alice Smith", 100), ("Bob Johnson", 90), ("Charlie Brown", 80)]
        expected = [("Alice Smith", 1), ("Bob Johnson", 2), ("Charlie Brown", 3)]
        self.assertEqual(rank_leaderboard(players), expected)

if __name__ == '__main__':
    unittest.main()
