import chess
import random
import time
from . import cli
from . import gui
import pygame
import os

def run_cli_demo():
    """Runs a 10-move random game in the CLI."""
    print("--- Starting CLI Demo ---")
    board = chess.Board()
    for i in range(10):
        if board.is_game_over():
            print("Game over before 10 moves.")
            break
        cli.print_board(board)
        turn = "White" if board.turn == chess.WHITE else "Black"
        print(f"Move {i+1}: {turn}'s turn.")

        move = random.choice(list(board.legal_moves))
        san_move = board.san(move)
        board.push(move)
        print(f"Played move: {san_move}")
        time.sleep(1) # Pause for a second to make it watchable

    print("\n--- CLI Demo Finished ---")
    cli.print_board(board)
    print(f"Final board state after 10 random moves.")


def run_gui_demo():
    """Runs a 10-move random game in the GUI and saves a screenshot."""
    print("--- Starting GUI Demo ---")
    # Set up dummy driver for headless environment
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

    board = chess.Board()
    for i in range(10):
        if board.is_game_over():
            print("Game over before 10 moves.")
            break
        move = random.choice(list(board.legal_moves))
        board.push(move)

    print("Generating screenshot of the final board state...")

    gui_instance = gui.ChessGUI(board)
    gui_instance.draw_board()
    gui_instance.draw_pieces()
    pygame.display.flip()

    # Create directory if it doesn't exist
    os.makedirs("demo_screenshots", exist_ok=True)
    screenshot_path = "demo_screenshots/gui_demo_final.png"
    pygame.image.save(gui_instance.screen, screenshot_path)
    pygame.quit()

    print(f"--- GUI Demo Finished ---")
    print(f"Screenshot saved to {screenshot_path}")


def main():
    print("Running Chess Game Demos")
    run_cli_demo()
    print("\n" + "="*30 + "\n")
    run_gui_demo()

if __name__ == "__main__":
    main()