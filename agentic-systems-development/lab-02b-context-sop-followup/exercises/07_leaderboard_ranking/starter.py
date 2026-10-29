def rank_leaderboard(players: list) -> list:
    """
    Given a list of (name, score) tuples, return a list of (name, rank) tuples ranking players from highest score to lowest.
    
    Assumptions:
    - The input list 'players' is not empty.
    - Each tuple in 'players' contains exactly two elements: a name (str) and a score (float or int).
    - Scores are non-negative.
    
    Edge Cases Handled:
    - Tied scores receive the same rank.
    - The rank skips over the next ranks for tied scores.
    - Negative scores are ignored.
    - Floating-point scores are supported.
    - Names with special characters or spaces are handled.
    """
    
    # Filter out players with negative scores
    filtered_players = [(name, score) for name, score in players if score >= 0]
    
    # Sort players by score in descending order
    sorted_players = sorted(filtered_players, key=lambda x: x[1], reverse=True)
    
    # Initialize variables
    ranked_players = []
    rank = 1
    previous_score = None
    
    # Iterate through sorted players and assign ranks
    for player in sorted_players:
        name, score = player
        
        if score != previous_score:
            rank = len(ranked_players) + 1
        
        ranked_players.append((name, rank))
        previous_score = score
    
    return ranked_players
