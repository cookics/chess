import chess
import os
import random

def print_board(board):
    """
    Prints the chess board to the console.
    Uses platform-specific clear screen commands.
    """
    # Use 'cls' for Windows, 'clear' for Linux/macOS
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    os.system(clear_command)
    print("  a b c d e f g h")
    print(" +-+-+-+-+-+-+-+-+")
    # Get the board as a string and add row numbers
    board_str = str(board)
    rows = board_str.split('\n')
    for i, row in enumerate(rows):
        print(f"{8-i}|{row.replace(' ', '|')}|{8-i}")
    print(" +-+-+-+-+-+-+-+-+")
    print("  a b c d e f g h")
    print("\n")

def main():
    board = chess.Board()
    while not board.is_game_over():
        print_board(board)
        if board.turn == chess.WHITE:
            print("White's turn.")
        else:
            print("Black's turn.")

        try:
            legal_moves_with_pieces = []
            piece_names = {
                'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop',
                'R': 'Rook', 'Q': 'Queen', 'K': 'King',
                'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop',
                'r': 'Rook', 'q': 'Queen', 'k': 'King'
            }

            for move in board.legal_moves:
                piece = board.piece_at(move.from_square)
                if piece:
                    piece_symbol = piece.symbol()
                    piece_name = piece_names.get(piece_symbol, 'Piece')

                    #San notation
                    san_move = board.san(move)

                    # Create enchanced display string
                    move_display = f"{piece_name} {san_move}"
                    legal_moves_with_pieces.append(move_display)

            if legal_moves_with_pieces:
                print("Legal moves:", ", ".join(legal_moves_with_pieces))
            else:
                print("No legal moves available.")

        except Exception as e:
            print(f"Error generating legal moves: {e}")
            # Fallback to original method
            legal_moves = [board.san(move) for move in board.legal_moves]
            print("Legal moves:", ", ".join(legal_moves))

        print("Enter 'random' for a random move.")
        move_input = input("Enter your move in SAN format (e.g., e4, Nf3) or UCI format (e.g., e2e4): ")

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
                    input("Press Enter to continue...") # Pause for user to read
            except ValueError:
                print(f"\nInvalid move format: '{move_input}'. Please use SAN or UCI notation.")
                input("Press Enter to continue...") # Pause for user to read

    # Game over
    print_board(board)
    result = board.result()
    print("Game over!")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
