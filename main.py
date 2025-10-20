from chess_game import cli, gui, demo, combined
import sys

def show_settings():
    """Display and modify game settings."""
    print("\n=== Chess Game Settings ===")
    print("1. Change default time control")
    print("2. Set default save location")
    print("3. Back to main menu")

    choice = input("Choose option: ").strip()
    if choice == '1':
        print("\nTime control options:")
        print("1. Bullet (1 minute)")
        print("2. Blitz (3 minutes)")
        print("3. Rapid (10 minutes)")
        print("4. Classical (30 minutes)")
        print("5. Custom time")
        time_choice = input("Choose: ").strip()
        # You would save this to a config file
        print("Settings updated (configuration saving not implemented)")
    elif choice == '2':
        new_path = input("Enter default save path: ").strip()
        print(f"Save path set to: {new_path}")

def main():
    """
    Main entry point for the application.
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
        elif sys.argv[1] == 'settings':
            show_settings()
        else:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python main.py [cli|gui|demo|combined|settings]")
    else:
        while True:
            print("\n=== Chess Game ===")
            print("1. CLI Mode")
            print("2. GUI Mode")
            print("3. Demo Mode")
            print("4. Combined Mode (CLI input + GUI display)")
            print("5. Settings")
            print("6. Exit")

            choice = input("Choose mode (1-6): ").strip()
            if choice == '1':
                cli.main()
            elif choice == '2':
                gui.main()
            elif choice == '3':
                demo.main()
            elif choice == '4':
                combined.main()
            elif choice == '5':
                show_settings()
            elif choice == '6':
                print("Thanks for playing!")
                break
            else:
                print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()
