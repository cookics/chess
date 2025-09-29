import chess
import pygame
import random
import sys
import os
from . import gui

def main():
    """
    Runs the game in a combined mode where the CLI takes input
    and the GUI displays the output.
    """
    board = chess.Board()

    # Initialize Pygame and the GUI
    pygame.init()
    gui_instance = gui.ChessGUI(board)

    running = True
    while running and not board.is_game_over():
        # Handle Pygame events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update the GUI display
        gui_instance.draw_board()
        gui_instance.draw_pieces()
        pygame.display.flip()

        # Print CLI info
        if board.turn == chess.WHITE:
            print("\n--- White's turn ---")
        else:
            print("\n--- Black's turn ---")

        legal_moves = [board.san(move) for move in board.legal_moves]
        print("Legal moves:", ", ".join(legal_moves))
        print("Enter 'random' for a random move, or 'quit' to exit.")

        # Get user input from the command line
        move_input = input("Enter your move (e.g., e4, Nf3): ")

        if move_input.lower() == 'quit':
            running = False
            continue

        if move_input.lower() == 'random':
            move = random.choice(list(board.legal_moves))
            board.push(move)
            continue

        try:
            # Try to parse the move from SAN notation first
            move = board.parse_san(move_input)
            board.push(move)
        except ValueError:
            try:
                # If SAN fails, try UCI notation
                move = chess.Move.from_uci(move_input)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("\nThat's not a legal move! Try again.")
            except ValueError:
                print(f"\nInvalid move format: '{move_input}'. Please use SAN or UCI notation.")

    # Game over
    gui_instance.draw_board()
    gui_instance.draw_pieces()
    pygame.display.flip()

    print("\n--- Game Over ---")
    result = board.result()
    print(f"Result: {result}")

    # Wait for a moment before closing
    pygame.time.wait(3000)
    pygame.quit()

if __name__ == "__main__":
    main()