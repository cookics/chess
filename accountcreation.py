import json
import os

ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts.json")

class AccountManager:
    def __init__(self):
        self.accounts = self.load_accounts()
        self.current_account = None

    def load_accounts(self):
        """Load accounts from JSON file."""
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_accounts(self):
        """Save accounts to JSON file."""
        try:
            with open(ACCOUNTS_FILE, 'w') as f:
                json.dump(self.accounts, f, indent=2)
            return True
        except IOError:
            return False

    def create_account(self, username):
        """Create a new account with default ELO 800."""
        if username in self.accounts:
            print(f"Account '{username}' already exists!")
            return False
        
        self.accounts[username] = {
            'elo': 800,
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'game_history': []
        }
        
        if self.save_accounts():
            print(f"Account '{username}' created successfully with ELO 800!")
            return True
        else:
            print("Error saving account!")
            return False

    def login(self, username):
        """Login to an existing account."""
        if username in self.accounts:
            self.current_account = username
            print(f"Logged in as '{username}'")
            print(f"Current ELO: {self.accounts[username]['elo']}")
            return True
        else:
            print(f"Account '{username}' not found!")
            return False

    def logout(self):
        """Logout from current account."""
        if self.current_account:
            print(f"Logged out from '{self.current_account}'")
            self.current_account = None
        else:
            print("No account is currently logged in.")

    def get_current_account_info(self):
        """Get information about the currently logged in account."""
        if self.current_account and self.current_account in self.accounts:
            account_info = self.accounts[self.current_account].copy()
            account_info['username'] = self.current_account
            return account_info
        return None

    def record_game_result(self, player1_username, player2_username, result, game_pgn):
        """Record the result of a game and update ELOs."""
        from chess_game import elo
        p1_elo = self.accounts[player1_username]['elo']
        p2_elo = self.accounts[player2_username]['elo']
        if result == 'player1_win': score_p1 = 1.0
        elif result == 'player2_win': score_p1 = 0.0
        elif result == 'draw': score_p1 = 0.5
        else:
            print("Error: Invalid game result provided.")
            return

        new_p1_elo, new_p2_elo = elo.update_ratings(p1_elo, p2_elo, score_p1)

        # Player 1
        self.accounts[player1_username]['elo'] = new_p1_elo
        self.accounts[player1_username]['games_played'] += 1
        if result == 'player1_win': self.accounts[player1_username]['wins'] += 1
        elif result == 'draw': self.accounts[player1_username]['draws'] += 1
        else: self.accounts[player1_username]['losses'] += 1
        if 'game_history' not in self.accounts[player1_username]:
            self.accounts[player1_username]['game_history'] = []
        self.accounts[player1_username]['game_history'].append(game_pgn)

        # Player 2
        self.accounts[player2_username]['elo'] = new_p2_elo
        self.accounts[player2_username]['games_played'] += 1
        if result == 'player2_win': self.accounts[player2_username]['wins'] += 1
        elif result == 'draw': self.accounts[player2_username]['draws'] += 1
        else: self.accounts[player2_username]['losses'] += 1
        if 'game_history' not in self.accounts[player2_username]:
            self.accounts[player2_username]['game_history'] = []
        self.accounts[player2_username]['game_history'].append(game_pgn)

        self.save_accounts()
        print(f"Game recorded. New ELOs: {player1_username}: {new_p1_elo}, {player2_username}: {new_p2_elo}")

    def list_accounts(self):
        """List all existing accounts."""
        if not self.accounts:
            print("No accounts exist yet.")
            return
        
        print("\n=== Existing Accounts ===")
        for username, info in self.accounts.items():
            status = " (CURRENT)" if username == self.current_account else ""
            print(f"{username}{status}: ELO {info['elo']} | Games: {info['games_played']} | W/L/D: {info['wins']}/{info['losses']}/{info['draws']}")

# Global account manager instance
account_manager = AccountManager()
