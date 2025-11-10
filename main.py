from chess_game import cli, gui
import sys
from accountcreation import account_manager

def account_menu():
    """Handle account creation and login."""
    while True:
        print("\n=== Account Management ===")
        if account_manager.current_account:
            account_info = account_manager.get_current_account_info()
            print(f"Currently logged in as: {account_manager.current_account}")
            print(f"ELO: {account_info['elo']} | Games: {account_info['games_played']}")
            print("1. Logout")
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
            elif choice == '3':
                account_manager.list_accounts()
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
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
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cli':
            cli.main()
        elif sys.argv[1] == 'gui':
            gui.main()
        else:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python main.py [cli|gui]")
    else:
        while True:
            print("\n=== Chess Game ===")
            print("1. CLI Mode")
            print("2. GUI Mode")
            print("3. Account Management")
            print("4. Exit")

            choice = input("Choose mode (1-4): ").strip()
            if choice == '1':
                cli.main()
            elif choice == '2':
                gui.main()
            elif choice == '3':
                account_menu()
            elif choice == '4':
                print("Thanks for playing!")
                break
            else:
                print("Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
