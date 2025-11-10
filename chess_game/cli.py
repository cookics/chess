import chess
import chess.pgn
import os
import random
import time
import pickle
from datetime import timedelta
from AiOpponentManager import AIOpponentManager
from chess_game.config import load_settings
from chess_game.stockfish_manager import StockfishManager
from chess_game.elo_calculator import EloCalculator
import socketserver
import json
import threading
import argparse
import sys

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
        if self.last_move_time is None:
            return self.white_time if color == chess.WHITE else self.black_time

        current_time = self.white_time if color == chess.WHITE else self.black_time
        if self.current_turn == color:
            elapsed = time.time() - self.last_move_time
            current_time -= elapsed

        return max(0, current_time)

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))[2:]

    def is_time_out(self, color):
        return self.get_time_left(color) <= 0

    def get_time_display(self):
        return f"White: {self.format_time(self.get_time_left(chess.WHITE))} | Black: {self.format_time(self.get_time_left(chess.BLACK))}"

class GameServer(socketserver.BaseRequestHandler):

    board = chess.Board()
    game = chess.pgn.Game()
    node = game
    timer = ChessTimer(600)
    stockfish_manager = None
    ai_opponent = None
    vs_ai = False
    lock = threading.Lock()

    def handle(self):
        while True:
            try:
                data = self.request.recv(1024).strip()
                if not data:
                    break

                request = json.loads(data.decode('utf-8'))
                command = request.get("command")

                with GameServer.lock:
                    if command == "get_state":
                        response = self.get_state()
                    elif command == "make_move":
                        move = request.get("move")
                        response = self.make_move(move)
                    else:
                        response = {"status": "error", "message": "Invalid command"}

                self.request.sendall(json.dumps(response).encode('utf-8'))
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def get_state(self):
        eval_data = None
        if GameServer.stockfish_manager:
            eval_data = GameServer.stockfish_manager.get_evaluation(GameServer.board.fen())

        termination_reason = ""
        pgn = ""
        if GameServer.board.is_game_over():
            if GameServer.board.is_checkmate():
                termination_reason = "checkmate"
            elif GameServer.board.is_stalemate():
                termination_reason = "stalemate"
            elif GameServer.board.is_insufficient_material():
                termination_reason = "insufficient material"
            elif GameServer.board.is_seventyfive_moves():
                termination_reason = "75-move rule"
            elif GameServer.board.is_fivefold_repetition():
                termination_reason = "fivefold repetition"

            GameServer.game.headers["Result"] = GameServer.board.result()
            pgn = str(GameServer.game)

        return {
            "fen": GameServer.board.fen(),
            "turn": "white" if GameServer.board.turn == chess.WHITE else "black",
            "legal_moves": [move.uci() for move in GameServer.board.legal_moves],
            "is_game_over": GameServer.board.is_game_over(),
            "result": GameServer.board.result(),
            "white_time": GameServer.timer.get_time_left(chess.WHITE),
            "black_time": GameServer.timer.get_time_left(chess.BLACK),
            "evaluation": eval_data,
            "termination_reason": termination_reason,
            "pgn": pgn
        }

    def make_move(self, move_uci):
        try:
            move = chess.Move.from_uci(move_uci)
            if move in GameServer.board.legal_moves:
                GameServer.board.push(move)
                GameServer.node = GameServer.node.add_variation(move)
                GameServer.timer.switch_turn()

                if GameServer.vs_ai and not GameServer.board.is_game_over():
                    self.make_ai_move()

                return {"status": "ok"}
            else:
                return {"status": "error", "message": "Illegal move"}
        except ValueError:
            return {"status": "error", "message": "Invalid move format"}

    def make_ai_move(self):
        if GameServer.ai_opponent:
            ai_move_uci = GameServer.ai_opponent.get_best_move(GameServer.board)
            if ai_move_uci:
                ai_move = chess.Move.from_uci(ai_move_uci)
                if ai_move in GameServer.board.legal_moves:
                    GameServer.board.push(ai_move)
                    GameServer.node = GameServer.node.add_variation(ai_move)
                    GameServer.timer.switch_turn()
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
def get_legal_moves_display(board):
    """Generate enhanced legal moves display with piece names, grouped by piece in logical order."""
    piece_names = {
        'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop',
        'R': 'Rook', 'Q': 'Queen', 'K': 'King',
        'p':'Pawn', 'n': 'Knight', 'b': 'Bishop',
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

def print_game_status(board, timer, stockfish_manager):
    """Print the current game status including timer and move information."""
    if board.turn == chess.WHITE:
        print("White's turn.")
    else:
        print("Black's turn.")

    if timer:
        print(f"Time: {timer.get_time_display()}")

    if stockfish_manager:
        eval = stockfish_manager.get_evaluation(board.fen())
        if eval and eval['type'] == 'cp':
            print(f"Evaluation: {eval['value'] / 100.0}")
        elif eval and eval['type'] == 'mate':
            print(f"Evaluation: Mate in {eval['value']}")
def run_cli_game(account_manager):
    board = None
    timer = None
    vs_ai = False
    ai_opponent = None
    settings = load_settings()
    stockfish_manager = StockfishManager(settings.get('stockfish_path'))

    print("Welcome to Chess CLI!")
    print("1. Human vs Human")
    print("2. Human vs AI")
    print("Enter 'load' to load a saved game.")
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
    elif choice == '2':
        vs_ai = True
        ai_opponent = AIOpponentManager(settings.get('stockfish_path'))
        while True:
            try:
                elo = int(input("Enter AI ELO (1350-2850): ").strip())
                if 1350 <= elo <= 2850:
                    ai_opponent.set_elo(elo)
                    break
                else:
                    print("ELO must be between 1350 and 2850.")
            except ValueError:
                print("Invalid ELO. Please enter a number.")

    if not board:
        board = chess.Board()
        time_control = get_time_control()
        timer = ChessTimer(time_control) if time_control > 0 else None
        if timer:
            timer.start_turn()

    while not board.is_game_over():
        print_board(board)
        print_game_status(board, timer, stockfish_manager)

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

        if vs_ai and board.turn == chess.BLACK:
            print("AI is thinking...")
            time.sleep(1) # Small delay to make AI move visible
            ai_move_uci = ai_opponent.get_best_move(board)
            if ai_move_uci:
                move = chess.Move.from_uci(ai_move_uci)
                board.push(move)
                continue

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

        if account_manager.current_account:
            game = chess.pgn.Game()
            game.headers["Event"] = "CLI Game"
            game.headers["Site"] = "Local"
            game.headers["Date"] = time.strftime("%Y.%m.%d")
            game.headers["Round"] = "1"
            game.headers["White"] = account_manager.current_account
            game.headers["Black"] = "AI" if vs_ai else "Human"
            game.headers["Result"] = result

            # Create PGN from the board's move stack
            if board.move_stack:
                node = game.add_main_variation(board.move_stack[0])
                for move in board.move_stack[1:]:
                    node = node.add_main_variation(move)

            game_pgn = str(game)
            account_manager.add_game_to_history(account_manager.current_account, game_pgn)

            elo_calculator = EloCalculator(settings.get('stockfish_path'))
            current_elo = account_manager.get_current_account_info()['elo']
            new_elo = elo_calculator.calculate_elo(game_pgn, current_elo)
            account_manager.update_elo(account_manager.current_account, new_elo)
            print(f"Your new ELO is: {new_elo}")

        save_final = input("Save final position? (y/n): ").strip().lower()
        if save_final == 'y':
            save_game(board, timer, "final_position.pkl")
def run_server(vs_ai, stockfish_path):
    GameServer.vs_ai = vs_ai
    stockfish_path = stockfish_path or load_settings().get('stockfish_path')
    if stockfish_path:
        GameServer.stockfish_manager = StockfishManager(stockfish_path)
        if GameServer.vs_ai:
            GameServer.ai_opponent = AIOpponentManager(stockfish_path)
            GameServer.ai_opponent.set_elo(1500) # Default ELO

    host, port = "127.0.0.1", 65432
    print(f"Starting server on {host}:{port}, AI={'on' if GameServer.vs_ai else 'off'}")

    server = socketserver.TCPServer((host, port), GameServer)
    server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description="Chess Game CLI and Server")
    parser.add_argument('mode', nargs='?', default='cli', help="Mode to run: 'cli' or 'server'")
    parser.add_argument('--vs-ai', action='store_true', help="Play against AI (server mode only)")
    parser.add_argument('--stockfish-path', help="Path to Stockfish executable")

    # This is a bit of a hack to make this work with the old main.py
    # If the first argument is an AccountManager instance, we are in CLI mode
    args = []
    account_manager = None
    if len(sys.argv) > 1 and not isinstance(sys.argv[1], str):
        account_manager = sys.argv[1]
    else:
        args = sys.argv[1:]

    parsed_args = parser.parse_args(args)

    if parsed_args.mode == 'server':
        run_server(parsed_args.vs_ai, parsed_args.stockfish_path)
    else:
        run_cli_game(account_manager)
def print_board(board):
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    os.system(clear_command)
    print("  a b c d e f g h")
    print(" +-+-+-+-+-+-+-+-+")
    board_str = str(board)
    rows = board_str.split('\n')
    for i, row in enumerate(rows):
        print(f"{8-i}|{row.replace(' ', '|')}|{8-i}")
    print(" +-+-+-+-+-+-+-+-+")
    print("  a b c d e f g h\n")

def get_time_control():
    try:
        minutes = int(input("Enter minutes per player: "))
        return minutes * 60
    except ValueError:
        return 600

if __name__ == "__main__":
    main()
