class AIOpponentManager:
    def __init__(self, account_manager):
        self.account_manager = account_manager
        self.ai_opponents = self.load_ai_opponents()

    def load_ai_opponents(self):
        """Load predefined AI opponent profiles"""
        return {
            "AI_Beginner": {"elo": 600, "personality": "Beginner"},
            "AI_Casual": {"elo": 800, "personality": "Casual"},
            "AI_Intermediate": {"elo": 1200, "personality": "Intermediate"},
            "AI_Advanced": {"elo": 1600, "personality": "Advanced"},
            "AI_Expert": {"elo": 2000, "personality": "Expert"},
            "AI_Master": {"elo": 2400, "personality": "Master"}
        }

    def get_ai_opponent_by_elo(self, user_elo, tolerance=200):
        # Get AI opponent with similar ELO to user
        # Find the closest AI opponent within tolerance
        closest_opponent = None
        min_difference = float('inf')

        for opponent_name, opponent_data in self.ai_opponents.items():
            difference = abs(opponent_data["elo"] - user_elo)
            if difference <= tolerance and difference < min_difference:
                min_difference = difference
                closest_opponent = opponent_name

        # If no opponent within tolerance, create a dynamic one
        if not closest_opponent:
            # Find the closest overall
            for opponent_name, opponent_data in self.ai_opponents.items():
                difference = abs(opponent_data["elo"] - user_elo)
                if difference < min_difference:
                    min_difference = difference
                    closest_opponent = opponent_name

        return closest_opponent, self.ai_opponents[closest_opponent]

    def update_ai_elo(self, opponent_name, new_elo):
        # Update AI opponent's ELO based on game results
        if opponent_name in self.ai_opponents:
            self.ai_opponents[opponent_name]["elo"] = new_elo
