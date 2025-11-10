from stockfish import Stockfish

class StockfishManager:
    def __init__(self, stockfish_path=None):
        try:
            self.stockfish = Stockfish(path=stockfish_path)
        except Exception as e:
            print(f"Error initializing Stockfish: {e}")
            self.stockfish = None

    def get_best_move(self, board_fen):
        if self.stockfish:
            self.stockfish.set_fen_position(board_fen)
            return self.stockfish.get_best_move()
        return None

    def get_evaluation(self, board_fen):
        if self.stockfish:
            self.stockfish.set_fen_position(board_fen)
            return self.stockfish.get_evaluation()
        return None
