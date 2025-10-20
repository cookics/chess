import chess
import os
import random
import time
import pickle
from datetime import timedelta

class ChessTimer:
    def __init__(self, time_control_seconds=600):
        self.time_control = time_control_seconds
        self.white_time = time_control_seconds
        self.black_time = time_control_seconds
        self.last_move_time = None
        self.current_turn = chess.WHITE


    def start_turn(self):
        self.last_move_time = time.time()

    def end_turn(self):
        if self.last_move_time is not None:
            elapsed = time.time() - self.last_move_time
            if self.current_turn == chess.WHITE:
                self.white_time -= elapsed
            else:
                self.black_time -= elapsed

    def switch_turn(self):
        self.end_turn()
        self.current_turn = not self.current_turn
        self.start_turn()

    def get_time_left(self, color):
        if color == chess.WHITE:
            return max(0, self.white_time)
        else:
            return max(0, self.black_time)
        # Calculate current time if timer is running
        if self.running and self.last_move_time is not None:
            elapsed = time.time() - self.last_move_time
            current_time = max(0, current_time - elapsed)
        return current_time

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))[2:]

    def is_time_out(self, color):
        return self.get_time_left(color) <= 0

    def get_time_display(self):
        return f"White: {self.format_time(self.white_time)} | Black: {self.format_time(self.black_time)}"

def save_game(board, timer, filename="chess_save.pkl"):
    """Save the current game state to a file."""
    game_state = {
        'board': board,
        'timer': timer,
        'save_time': time.time()
    }

    try:
        with open(filename, 'wb') as f:
            pickle.dump(game_state, f)
        print(f"Game saved successfully to {filename}!")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def load_game(filename="chess_save.pkl"):
    """Load a game state from a file."""
    try:
        with open(filename, 'rb') as f:
            game_state = pickle.load(f)

        print(f"Game loaded successfully from {filename}!")
        print(f"Save was created on: {time.ctime(game_state['save_time'])}")
        return game_state['board'], game_state['timer']
    except FileNotFoundError:
        print(f"No saved game found at {filename}")
        return None, None
    except Exception as e:
        print(f"Error loading game: {e}")
        return None, None

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}

def calculate_material_advantage(board):
    """Calculates the material advantage for each side."""
    white_material = sum(len(board.pieces(pt, chess.WHITE)) * val for pt, val in PIECE_VALUES.items())
    black_material = sum(len(board.pieces(pt, chess.BLACK)) * val for pt, val in PIECE_VALUES.items())
    return white_material - black_material

def get_captured_pieces_display(board):
    """Returns two strings representing captured pieces for each color."""
    initial_piece_count = {
        chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
        chess.ROOK: 2, chess.QUEEN: 1
    }

    captured_by_white = []
    for piece_type, count in initial_piece_count.items():
        captured_count = count - len(board.pieces(piece_type, chess.BLACK))
        for _ in range(captured_count):
            captured_by_white.append(UNICODE_PIECES[chess.Piece(piece_type, chess.BLACK).symbol()])

    captured_by_black = []
    for piece_type, count in initial_piece_count.items():
        captured_count = count - len(board.pieces(piece_type, chess.WHITE))
        for _ in range(captured_count):
            captured_by_black.append(UNICODE_PIECES[chess.Piece(piece_type, chess.WHITE).symbol()])

    return "".join(sorted(captured_by_white)), "".join(sorted(captured_by_black))

def print_board(board):
    """Prints the chess board to the console."""
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    os.system(clear_command)

    captured_w, captured_b = get_captured_pieces_display(board)
    print(f"Captured by White: {captured_w}")
    print(f"Captured by Black: {captured_b}")

    advantage = calculate_material_advantage(board)
    if advantage > 0:
        print(f"White has a material advantage of +{advantage}")
    elif advantage < 0:
        print(f"Black has a material advantage of +{-advantage}")
    print("  a b c d e f g h")
    print(" +-+-+-+-+-+-+-+-+")
    board_str = str(board)
    rows = board_str.split('\n')
    for i, row in enumerate(rows):
        print(f"{8-i}|{row.replace(' ', '|')}|{8-i}")
    print(" +-+-+-+-+-+-+-+-+")
    print("  a b c d e f g h")
    print("\n")

def print_game_status(board, timer):
    """Print the current game status including timer and move information."""
    if board.turn == chess.WHITE:
        print("White's turn.")
    else:
        print("Black's turn.")

    if timer:
        print(f"Time: {timer.get_time_display()}")
    else:
        print()

def get_legal_moves_display(board):
    """Generate enhanced legal moves display with piece names, grouped by piece in logical order."""
    piece_names = {
        'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop',
        'R': 'Rook', 'Q': 'Queen', 'K': 'King',
        'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop',
        'r': 'Rook', 'q': 'Queen', 'k': 'King'
    }

    # Define the order we want pieces to appear
    piece_order = ['King', 'Queen', 'Rook', 'Bishop', 'Knight', 'Pawn']

    # Group moves by piece type
    moves_by_piece = {}

    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)
        if piece:
            piece_symbol = piece.symbol()
            piece_name = piece_names.get(piece_symbol, 'Piece')
            san_move = board.san(move)

            if piece_name not in moves_by_piece:
                moves_by_piece[piece_name] = []
            moves_by_piece[piece_name].append(san_move)

    # Format the grouped moves in the specified order
    formatted_moves = []
    for piece_name in piece_order:
        if piece_name in moves_by_piece:
            moves_list = moves_by_piece[piece_name]
            moves_list.sort()
            formatted_moves.append(f"{piece_name}: {', '.join(moves_list)}")

    # Add any pieces that weren't in our predefined order (shouldn't happen in chess)
    for piece_name in sorted(moves_by_piece.keys()):
        if piece_name not in piece_order:
            moves_list = moves_by_piece[piece_name]
            moves_list.sort()
            formatted_moves.append(f"{piece_name}: {', '.join(moves_list)}")

    return formatted_moves

def get_time_control():
    """Get time control settings from user."""
    print("\nTime control options:")
    print("1. Bullet (1 minute)")
    print("2. Blitz (3 minutes)")
    print("3. Rapid (10 minutes)")
    print("4. Classical (30 minutes)")
    print("5. Custom time")
    print("6. No timer")

    while True:
        choice = input("Choose time control (1-6): ").strip()
        time_controls = {
            '1': 60,    # 1 minute
            '2': 180,   # 3 minutes
            '3': 600,   # 10 minutes
            '4': 1800,  # 30 minutes
            '6': 0      # No timer
        }

        if choice in time_controls:
            if choice == '5':
                try:
                    minutes = int(input("Enter minutes per player: "))
                    return minutes * 60
                except ValueError:
                    print("Please enter a valid number.")
                    continue
            return time_controls[choice]
        else:
            print("Invalid choice. Please enter 1-6.")

def main():
    board = None
    timer = None

    print("Welcome to Chess CLI!")
    print("Enter 'load' to load a saved game, or press Enter to start a new game.")
    choice = input("Your choice: ").strip().lower()

    if choice == 'load':
        filename = input("Enter save filename (default: chess_save.pkl): ").strip()
        if not filename:
            filename = "chess_save.pkl"
        loaded_board, loaded_timer = load_game(filename)
        if loaded_board and loaded_timer:
            board = loaded_board
            timer = loaded_timer
            timer.start_turn()

    if not board:
        board = chess.Board()
        time_control = get_time_control()
        timer = ChessTimer(time_control) if time_control > 0 else None
        if timer:
            timer.start_turn()

    while not board.is_game_over():
        print_board(board)
        print_game_status(board, timer)

        # Check for timeout
        if timer and timer.is_time_out(board.turn):
            print("Time's up!")
            if board.turn == chess.WHITE:
                print("Black wins by timeout!")
            else:
                print("White wins by timeout!")
            break

        try:
            legal_moves_groups = get_legal_moves_display(board)
            if legal_moves_groups:
                print("Legal moves:")
                for group in legal_moves_groups:
                    print(f"  {group}")
            else:
                print("No legal moves available.")
        except Exception as e:
            print(f"Error generating legal moves: {e}")
            legal_moves = [board.san(move) for move in board.legal_moves]
            if legal_moves:
                print("Legal moves:", ", ".join(legal_moves[:10]))

        print("\nCommands: 'random', 'save', 'resign', 'draw', 'quit'")
        move_input = input("Enter your move in SAN format (e.g., e4, Nf3) or UCI format: ").strip()

        # Handle special commands
        if move_input.lower() == 'save':
            filename = input("Enter filename to save (default: chess_save.pkl): ").strip()
            if not filename:
                filename = "chess_save.pkl"
            save_game(board, timer, filename)
            input("Press Enter to continue...")
            continue

        elif move_input.lower() == 'resign':
            confirm = input("Are you sure you want to resign? (y/n): ").strip().lower()
            if confirm == 'y':
                if board.turn == chess.WHITE:
                    print("White resigns. Black wins!")
                else:
                    print("Black resigns. White wins!")
                break
            continue

        elif move_input.lower() == 'draw':
            confirm = input("Are you sure you want to offer a draw? (y/n): ").strip().lower()
            if confirm == 'y':
                print("Draw accepted. Game ends in a draw.")
                break
            continue

        elif move_input.lower() == 'quit':
            confirm = input("Are you sure you want to quit? (y/n): ").strip().lower()
            if confirm == 'y':
                save_now = input("Save game before quitting? (y/n): ").strip().lower()
                if save_now == 'y':
                    save_game(board, timer)
                print("Thanks for playing!")
                break
            continue

        elif move_input.lower() == 'random':
            move = random.choice(list(board.legal_moves))
            if timer:
                timer.switch_turn()
            board.push(move)
            continue

        # Handle actual moves
        try:
            move = board.parse_san(move_input)
            if timer:
                timer.switch_turn()
            board.push(move)
        except ValueError:
            try:
                move = chess.Move.from_uci(move_input)
                if move in board.legal_moves:
                    if timer:
                        timer.switch_turn()
                    board.push(move)
                else:
                    print("\nThat's not a legal move! Try again.")
                    input("Press Enter to continue...")
            except ValueError:
                print(f"\nInvalid move format: '{move_input}'. Please use SAN or UCI notation.")
                input("Press Enter to continue...")

    # Game over
    if board.is_game_over():
        print_board(board)
        result = board.result()
        print("Game over!")
        print(f"Result: {result}")

        save_final = input("Save final position? (y/n): ").strip().lower()
        if save_final == 'y':
            save_game(board, timer, "final_position.pkl")
