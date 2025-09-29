import pygame
import chess

# --- Constants ---
# Screen dimensions
WIDTH = 512
HEIGHT = 512
# Board dimensions are the same as screen dimensions
SQUARE_SIZE = WIDTH // 8

# Colors
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}


class ChessGUI:
    def __init__(self, board):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = board
        # A larger font is needed for the unicode characters to be visible
        # We specify a font that is likely to have the chess characters
        try:
            self.font = pygame.font.SysFont("dejavusans", 72)
        except pygame.error:
            # Fallback to the default font if dejavusans is not available
            self.font = pygame.font.SysFont(None, 72)

    def draw_board(self):
        """Draws the chessboard squares."""
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        """Draws the pieces on the board using Unicode characters."""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)  # chess.square maps col, row to 0-63 index
                piece = self.board.piece_at(square)
                if piece:
                    piece_symbol = UNICODE_PIECES[piece.symbol()]
                    # We'll draw all pieces in black for better visibility on both light and dark squares
                    color = BLACK_COLOR
                    text = self.font.render(piece_symbol, True, color)
                    text_rect = text.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text, text_rect)

    def run(self):
        """Main loop for the GUI."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # The background is the board itself, so no need to fill with a single color
            self.draw_board()
            self.draw_pieces()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main():
    board = chess.Board()
    gui = ChessGUI(board)
    gui.run()

if __name__ == "__main__":
    main()