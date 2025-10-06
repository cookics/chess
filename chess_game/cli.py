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

# --- Helper Functions ---
def get_piece_values():
    return {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0,
            'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def get_captured_pieces(board):
    """
    Returns two lists of captured pieces, one for white and one for black.
    This is done by comparing the piece counts of the current board state
    to the starting piece counts.
    """
    initial_piece_counts = {
        'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1,
        'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1, 'k': 1,
    }
    current_piece_counts = {piece.symbol(): len(board.pieces(piece.piece_type, piece.color))
                            for piece in map(chess.Piece.from_symbol, initial_piece_counts.keys())}

    white_captured = []
    black_captured = []

    for symbol, initial_count in initial_piece_counts.items():
        captured_count = initial_count - current_piece_counts.get(symbol, 0)
        if captured_count > 0:
            # If the piece symbol is uppercase, it's a white piece (captured by black)
            if symbol.isupper():
                black_captured.extend([symbol] * captured_count)
            # If the piece symbol is lowercase, it's a black piece (captured by white)
            else:
                white_captured.extend([symbol] * captured_count)
    return white_captured, black_captured

def display_game_info(board):
    """
    Displays captured pieces and material advantage.
    """
    white_captured, black_captured = get_captured_pieces(board)
    piece_values = get_piece_values()

    white_score = sum(piece_values[p] for p in white_captured)
    black_score = sum(piece_values[p] for p in black_captured)

    print(f"Captured by White: {' '.join(white_captured)} (Score: {white_score})")
    print(f"Captured by Black: {' '.join(black_captured)} (Score: {black_score})")

    if white_score > black_score:
        print(f"White has a material advantage of +{white_score - black_score}")
    elif black_score > white_score:
        print(f"Black has a material advantage of +{black_score - white_score}")
    else:
        print("Material is even.")
    print("-" * 20)

def main():
    board = chess.Board()
    while not board.is_game_over():
        print_board(board)
        display_game_info(board)

        if board.turn == chess.WHITE:
            print("White's turn.")
        else:
            print("Black's turn.")

        try:
            legal_moves_by_piece = {}
            piece_names = {
                'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop',
                'R': 'Rook', 'Q': 'Queen', 'K': 'King'
            }

            for move in board.legal_moves:
                piece = board.piece_at(move.from_square)
                if piece:
                    # Use uppercase for dictionary keys to group pieces regardless of color
                    piece_name = piece_names.get(piece.symbol().upper(), 'Piece')
                    san_move = board.san(move)

                    if piece_name not in legal_moves_by_piece:
                        legal_moves_by_piece[piece_name] = []
                    legal_moves_by_piece[piece_name].append(san_move)

            if legal_moves_by_piece:
                print("Legal moves:")
                for piece_name, moves in sorted(legal_moves_by_piece.items()):
                    print(f"  {piece_name}: {', '.join(sorted(moves))}")
            else:
                print("No legal moves available.")

        except Exception as e:
            print(f"Error generating legal moves: {e}")
            # Fallback to original method
            legal_moves = [board.san(move) for move in board.legal_moves]
            print("Legal moves:", ", ".join(legal_moves))

        print("\nEnter 'random' for a random move.")
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
