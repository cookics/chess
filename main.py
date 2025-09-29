from chess_game import cli, gui, demo
import sys

def main():
    """
    Main entry point for the application.
    Allows the user to choose between the CLI, GUI, and demo.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cli':
            cli.main()
        elif sys.argv[1] == 'gui':
            gui.main()
        elif sys.argv[1] == 'demo':
            demo.main()
        else:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python main.py [cli|gui|demo]")
    else:
        while True:
            choice = input("Choose interface: (1) CLI, (2) GUI, or (3) Demo: ")
            if choice == '1':
                cli.main()
                break
            elif choice == '2':
                gui.main()
                break
            elif choice == '3':
                demo.main()
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()