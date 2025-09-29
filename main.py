from chess_game import cli, gui
import sys

def main():
    """
    Main entry point for the application.
    Allows the user to choose between the CLI and GUI.
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
            choice = input("Choose interface: (1) CLI or (2) GUI: ")
            if choice == '1':
                cli.main()
                break
            elif choice == '2':
                gui.main()
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()