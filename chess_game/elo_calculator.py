import chess
import chess.pgn
import io
from chess_game.stockfish_manager import StockfishManager

class EloCalculator:
    def __init__(self, stockfish_path=None):
        self.stockfish_manager = StockfishManager(stockfish_path)

    def calculate_elo(self, game_pgn, current_elo):
        """
        Analyzes a game and calculates a new ELO for the user.
        """
        if not self.stockfish_manager:
            return current_elo

        try:
            game = chess.pgn.read_game(io.StringIO(game_pgn))
        except:
            return current_elo

        board = game.board()
        total_accuracy = 0
        num_moves = 0

        username = game.headers.get("White") if game.headers.get("Black") == "AI" else game.headers.get("Black")
        user_color = chess.WHITE if game.headers.get("White") == username else chess.BLACK

        for move in game.mainline_moves():
            if board.turn == user_color:
                best_move = self.stockfish_manager.get_best_move(board.fen())
                if best_move == move.uci():
                    total_accuracy += 1
            board.push(move)
            num_moves += 1

        if num_moves == 0:
            return current_elo

        accuracy = total_accuracy / num_moves

        # This is a very simple ELO adjustment formula. A more sophisticated
        # formula could be used in the future.
        new_elo = current_elo + (accuracy - 0.5) * 50

        return int(new_elo)
