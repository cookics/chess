from chess_game import cli, gui, demo, combined
import sys

def main():
    """
    Main entry point for the application.
    Allows the user to choose between the CLI, GUI, demo, and combined modes.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cli':
            cli.main()
        elif sys.argv[1] == 'gui':
            gui.main()
        elif sys.argv[1] == 'demo':
            demo.main()
        elif sys.argv[1] == 'combined':
            combined.main()
        else:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python main.py [cli|gui|demo|combined]")
    else:
        while True:
            choice = input("Choose mode: (1) CLI, (2) GUI, (3) Demo, or (4) Combined (CLI input + GUI display): ")
            if choice == '1':
                cli.main()
                break
            elif choice == '2':
                gui.main()
                break
            elif choice == '3':
                demo.main()
                break
            elif choice == '4':
                combined.main()
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()