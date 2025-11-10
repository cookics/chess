import chess
import chess.pgn
import io
from chess_game.stockfish_manager import StockfishManager

class GameAnalyzer:
    def __init__(self, stockfish_path=None):
        self.stockfish_manager = StockfishManager(stockfish_path)

    def analyze_game(self, game_pgn):
        """
        Analyzes a game and identifies blunders and good moves.
        """
        if not self.stockfish_manager:
            return None

        try:
            game = chess.pgn.read_game(io.StringIO(game_pgn))
        except:
            return None

        board = game.board()
        analysis = []

        for move in game.mainline_moves():
            best_move = self.stockfish_manager.get_best_move(board.fen())
            evaluation = self.stockfish_manager.get_evaluation(board.fen())

            if best_move != move.uci():
                # This is a very simple blunder detection. A more sophisticated
                # system could be used in the future.
                if evaluation and evaluation['type'] == 'cp' and evaluation['value'] > 200:
                    analysis.append(f"Blunder on move {board.fullmove_number}: played {move.uci()}, but {best_move} was better.")
            else:
                analysis.append(f"Good move on move {board.fullmove_number}: {move.uci()}")

            board.push(move)

        return analysis
