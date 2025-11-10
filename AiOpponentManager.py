from chess_game.stockfish_manager import StockfishManager

class AIOpponentManager:
    def __init__(self, stockfish_path=None):
        self.stockfish_manager = StockfishManager(stockfish_path)
        self.elo = 1350  # Default ELO

    def set_elo(self, elo):
        """Set the ELO rating for the Stockfish engine."""
        if self.stockfish_manager and self.stockfish_manager.stockfish:
            self.elo = elo
            self.stockfish_manager.stockfish.set_elo_rating(elo)

    def get_best_move(self, board):
        """Get the best move from the Stockfish engine."""
        if self.stockfish_manager:
            return self.stockfish_manager.get_best_move(board.fen())
        return None

    def get_evaluation(self, board):
        """Get the evaluation from the Stockfish engine."""
        if self.stockfish_manager:
            return self.stockfish_manager.get_evaluation(board.fen())
        return None
