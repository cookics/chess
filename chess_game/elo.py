# /chess_game/elo.py

# A standard K-factor. This determines how much ratings can change.
# 32 is a good value for players who haven't played many games.
# For established players, it's often lower (e.g., 24).
K_FACTOR = 32

def expected_score(rating_a, rating_b):
    """
    Calculates the expected score for player A against player B.
    Returns a value between 0 and 1.
    """
    return 1 / (1 + 10**((rating_b - rating_a) / 400))

def update_ratings(rating_a, rating_b, score_a):
    """
    Updates the ratings for two players.
    Args:
        rating_a (int): The current rating of player A.
        rating_b (int): The current rating of player B.
        score_a (float): The actual score of player A (1.0 for win, 0.5 for draw, 0.0 for loss).
    Returns:
        tuple: A tuple containing the new ratings for (player_a, player_b).
    """
    exp_a = expected_score(rating_a, rating_b)
    exp_b = expected_score(rating_b, rating_a) # or simply 1 - exp_a

    new_rating_a = rating_a + K_FACTOR * (score_a - exp_a)
    new_rating_b = rating_b + K_FACTOR * ((1 - score_a) - exp_b)

    # Ensure ratings don't go below a minimum (e.g., 100)
    new_rating_a = max(new_rating_a, 100)
    new_rating_b = max(new_rating_b, 100)

    return round(new_rating_a), round(new_rating_b)

# --- Example Usage ---
if __name__ == '__main__':
    player1_rating = 1500
    player2_rating = 1600

    print(f"Initial Ratings: Player 1: {player1_rating}, Player 2: {player2_rating}")

    # Scenario 1: Player 1 wins (score = 1.0)
    new_p1, new_p2 = update_ratings(player1_rating, player2_rating, 1.0)
    print(f"After Player 1 wins: Player 1: {new_p1}, Player 2: {new_p2}")

    # Scenario 2: Player 1 loses (score = 0.0)
    new_p1, new_p2 = update_ratings(player1_rating, player2_rating, 0.0)
    print(f"After Player 1 loses: Player 1: {new_p1}, Player 2: {new_p2}")

    # Scenario 3: It's a draw (score = 0.5)
    new_p1, new_p2 = update_ratings(player1_rating, player2_rating, 0.5)
    print(f"After a draw: Player 1: {new_p1}, Player 2: {new_p2}")
