import chess
import pygame
import os
from . import gui
from . import cli # Import the cli module to use its helper functions

def main():
    """
    Runs the game in a combined mode where the GUI takes mouse input
    and both the GUI and CLI display the game state.
    """
    board = chess.Board()
    # The ChessGUI class handles pygame.init()
    gui_instance = gui.ChessGUI(board)

    # Keep track of the board state to see when a move is made
    previous_fen = board.fen()

    # Initial CLI display
    cli.print_board(board)
    cli.display_game_info(board)
    print("--- White's turn ---")
    print("Make your move on the GUI.")

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Pass mouse clicks to the GUI handler if the game is not over
            if not board.is_game_over() and event.type == pygame.MOUSEBUTTONDOWN:
                gui_instance.handle_mouse_click(pygame.mouse.get_pos())

        # --- CLI Updates ---
        # If the board state has changed, a move was made.
        current_fen = board.fen()
        if current_fen != previous_fen:
            # The cli.print_board() function clears the console
            cli.print_board(board)
            cli.display_game_info(board)
            if not board.is_game_over():
                turn = "White" if board.turn == chess.WHITE else "Black"
                print(f"--- {turn}'s turn ---")
                print("Make your move on the GUI.")
            else:
                # Print final game result to CLI
                print("\n--- Game Over ---")
                print(f"Result: {board.result()}")

            previous_fen = current_fen

        # --- GUI Drawing ---
        gui_instance.draw_board()
        gui_instance.draw_highlights()
        gui_instance.draw_pieces()

        if board.is_game_over():
            gui_instance.draw_game_over(board.result())

        pygame.display.flip()
        gui_instance.clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()