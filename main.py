from chess_game import cli, gui
import sys
from accountcreation import AccountManager
from chess_game.game_analyzer import GameAnalyzer
from chess_game.config import load_settings

def account_menu(account_manager):
    """Handle account creation and login."""
    while True:
        print("\n=== Account Management ===")
        if account_manager.current_account:
            account_info = account_manager.get_current_account_info()
            print(f"Currently logged in as: {account_manager.current_account}")
            print(f"ELO: {account_info['elo']} | Games: {account_info['games_played']}")
            print("1. Logout")
            print("2. Game Analysis")
        else:
            print("No account currently logged in")
            print("1. Create Account")
            print("2. Login")

        print("3. List All Accounts")
        print("4. Back to Main Menu")

        choice = input("Choose option (1-4): ").strip()

        if account_manager.current_account:
            if choice == '1':
                account_manager.logout()
            elif choice == '2':
                account_info = account_manager.get_current_account_info()
                if 'game_history' in account_info and account_info['game_history']:
                    print("\n--- Your Games ---")
                    for i, game_pgn in enumerate(account_info['game_history']):
                        print(f"{i+1}. Game {i+1}")

                    game_choice = input("Choose a game to analyze: ").strip()
                    try:
                        game_index = int(game_choice) - 1
                        if 0 <= game_index < len(account_info['game_history']):
                            settings = load_settings()
                            analyzer = GameAnalyzer(settings.get('stockfish_path'))
                            analysis = analyzer.analyze_game(account_info['game_history'][game_index])
                            if analysis:
                                for line in analysis:
                                    print(line)
                            else:
                                print("Could not analyze game.")
                        else:
                            print("Invalid game number.")
                    except ValueError:
                        print("Invalid input.")
                else:
                    print("No games in your history to analyze.")
            elif choice == '3':
                account_manager.list_accounts()
            elif choice == '4':
                break
            else:
                print("Invalid choice.")
        else:
            if choice == '1':
                username = input("Enter username: ").strip()
                if username:
                    account_manager.create_account(username)
                else:
                    print("Username cannot be empty!")
            elif choice == '2':
                username = input("Enter username: ").strip()
                if username:
                    account_manager.login(username)
                else:
                    print("Username cannot be empty!")
            elif choice == '3':
                account_manager.list_accounts()
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")

def main():
    """
    Main entry point for the application.
    """
    account_manager = AccountManager()

    if len(sys.argv) > 1:
        if sys.argv[1] == 'cli':
            cli.main(account_manager)
        elif sys.argv[1] == 'gui':
            gui.main(account_manager=account_manager)
        elif sys.argv[1] == 'ai':
            gui.main(vs_ai=True, account_manager=account_manager)
        else:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python main.py [cli|gui|ai]")
    else:
        while True:
            print("\n=== Chess Game ===")
            print("1. CLI Mode")
            print("2. GUI Mode (Human vs. Human)")
            print("3. GUI Mode (Human vs. AI)")
            print("4. Account Management")
            print("5. Exit")

            choice = input("Choose mode (1-5): ").strip()
            if choice == '1':
                cli.main(account_manager)
            elif choice == '2':
                gui.main(account_manager=account_manager)
            elif choice == '3':
                gui.main(vs_ai=True, account_manager=account_manager)
            elif choice == '4':
                account_menu(account_manager)
            elif choice == '5':
                print("Thanks for playing!")
                break
            else:
                print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
