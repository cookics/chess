import json
import os

ACCOUNTS_FILE = "accounts.json"

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
            return self.accounts[self.current_account]
        return None

    def update_elo(self, username, new_elo):
        """Update ELO for an account."""
        if username in self.accounts:
            self.accounts[username]['elo'] = new_elo
            self.save_accounts()
            return True
        return False

    def add_game_to_history(self, username, game_pgn):
        """Add a completed game to the user's game history."""
        if username in self.accounts:
            if 'game_history' not in self.accounts[username]:
                self.accounts[username]['game_history'] = []
            self.accounts[username]['game_history'].append(game_pgn)
            self.accounts[username]['games_played'] += 1
            self.save_accounts()
            return True
        return False

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
