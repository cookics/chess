import chess
import os
import random
import time
import pickle
from datetime import timedelta
from stockfish import Stockfish
import socket
import threading
import json
import sys

class GameState:
    def __init__(self, vs_ai=False, stockfish_path=None):
        self.board = chess.Board()
        self.timer = ChessTimer(600)
        self.stockfish = None
        self.vs_ai = vs_ai
        try:
            if stockfish_path:
                self.stockfish = Stockfish(path=stockfish_path)
            else:
                self.stockfish = Stockfish()
        except Exception as e:
            print(f"Could not initialize stockfish: {e}")
        if self.stockfish:
            self.stockfish.set_fen_position(self.board.fen())

    def make_move(self, move_uci):
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                if self.timer:
                    self.timer.switch_turn()
                if self.stockfish:
                    self.stockfish.set_fen_position(self.board.fen())

                if self.vs_ai and self.board.turn == chess.BLACK:
                    best_move = self.stockfish.get_best_move()
                    if best_move:
                        self.board.push(chess.Move.from_uci(best_move))
                        if self.timer:
                            self.timer.switch_turn()
                        if self.stockfish:
                            self.stockfish.set_fen_position(self.board.fen())

                return True
        except ValueError:
            return False
        return False

    def get_state_json(self):
        outcome = self.board.outcome()
        state = {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "legal_moves": [m.uci() for m in self.board.legal_moves],
            "is_game_over": self.board.is_game_over(),
            "result": outcome.result() if outcome else None,
            "termination_reason": outcome.termination.name.title().replace("_", " ") if outcome else None,
            "white_time": self.timer.get_time_left(chess.WHITE) if self.timer else None,
            "black_time": self.timer.get_time_left(chess.BLACK) if self.timer else None,
        }
        if self.stockfish:
            eval = self.stockfish.get_evaluation()
            state["evaluation"] = eval
        return json.dumps(state)

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

        elapsed = time.time() - self.last_move_time
        if self.current_turn == color:
            return max(0, (self.white_time if color == chess.WHITE else self.black_time) - elapsed)
        else:
            return max(0, self.white_time if color == chess.WHITE else self.black_time)

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))[2:]

    def is_time_out(self, color):
        return self.get_time_left(color) <= 0

    def get_time_display(self):
        return f"White: {self.format_time(self.white_time)} | Black: {self.format_time(self.black_time)}"

def handle_client(client_socket, game_state):
    """Handle incoming requests from a client."""
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break

            data = json.loads(request)
            command = data.get("command")

            if command == "get_state":
                response = game_state.get_state_json()
                client_socket.sendall(response.encode('utf-8'))
            elif command == "make_move":
                move_uci = data.get("move")
                if game_state.make_move(move_uci):
                    response = game_state.get_state_json()
                else:
                    response = json.dumps({"error": "Invalid move"})
                client_socket.sendall(response.encode('utf-8'))
    finally:
        client_socket.close()

def start_server(host='127.0.0.1', port=65432, vs_ai=False, stockfish_path=None):
    """Start the chess game server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    game_state = GameState(vs_ai=vs_ai, stockfish_path=stockfish_path)

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, game_state))
            client_handler.start()
    finally:
        server.close()

def run_cli():
    """Run the interactive CLI for the chess game."""
    game = GameState()
    board = game.board
    timer = game.timer
    stockfish = game.stockfish

    if timer:
        timer.start_turn()

    while not board.is_game_over():
        print_board(board, stockfish)
        print_game_status(board, timer)

        if timer and timer.is_time_out(board.turn):
            print("Time's up!")
            break

        move_input = input("Enter your move in SAN or UCI format: ").strip()

        try:
            move = board.parse_san(move_input)
        except ValueError:
            try:
                move = chess.Move.from_uci(move_input)
            except ValueError:
                print("Invalid move format.")
                continue

        if move in board.legal_moves:
            game.make_move(move.uci())
        else:
            print("Illegal move.")

    print_board(board, stockfish)
    outcome = board.outcome()
    if outcome:
        print(f"Game over. {outcome.result()} by {outcome.termination.name.title().replace('_', ' ')}")
    else:
        print("Game over.", board.result())

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}

def print_board(board, stockfish):
    """Prints the chess board to the console."""
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    os.system(clear_command)

    if stockfish:
        stockfish.set_fen_position(board.fen())
        evaluation = stockfish.get_evaluation()
        if evaluation['type'] == 'cp':
            print(f"Stockfish Evaluation: {evaluation['value'] / 100.0}")

    print("  a b c d e f g h")
    print(" +-+-+-+-+-+-+-+-+")
    board_str = str(board)
    rows = board_str.split('\n')
    for i, row in enumerate(rows):
        print(f"{8-i}|{row.replace(' ', '|')}|{8-i}")
    print(" +-+-+-+-+-+-+-+-+")
    print("  a b c d e f g h")
    print("\n")

def calculate_material_advantage(board):
    """Calculates the material advantage for white."""
    advantage = 0
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                advantage += value
            else:
                advantage -= value
    return advantage

def print_game_status(board, timer):
    """Print the current game status including timer and move information."""
    if board.turn == chess.WHITE:
        print("White's turn.")
    else:
        print("Black's turn.")

    if timer:
        print(f"Time: {timer.get_time_display()}")

    advantage = calculate_material_advantage(board)
    if advantage == 0:
        print("Material is even.")
    else:
        print(f"Material Advantage: +{abs(advantage)} for {'White' if advantage > 0 else 'Black'}")

    # Display legal moves
    legal_moves_san = [board.san(move) for move in board.legal_moves]
    print("Legal Moves:", ", ".join(legal_moves_san))

import argparse

def main():
    parser = argparse.ArgumentParser(description="Chess game CLI and server.")
    parser.add_argument('mode', nargs='?', default='cli', help="'cli' or 'server'")
    parser.add_argument('--vs-ai', action='store_true', help="Enable AI opponent")
    parser.add_argument('--stockfish-path', help="Path to Stockfish executable")
    args = parser.parse_args()

    stockfish_path = args.stockfish_path
    if not stockfish_path:
        try:
            from .config import STOCKFISH_PATH
            stockfish_path = STOCKFISH_PATH
        except ImportError:
            pass

    if args.mode == 'server':
        start_server(vs_ai=args.vs_ai, stockfish_path=stockfish_path)
    else:
        run_cli()

if __name__ == "__main__":
    main()
