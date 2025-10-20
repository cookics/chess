from chess_game import cli, gui
import sys

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
            print("3. Exit")

            choice = input("Choose mode (1-3): ").strip()
            if choice == '1':
                cli.main()
            elif choice == '2':
                gui.main()
            elif choice == '3':
                print("Thanks for playing!")
                break
            else:
                print("Invalid choice. Please enter 1-3.")

if __name__ == "__main__":
    main()
