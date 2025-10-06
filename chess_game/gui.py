import pygame
import chess
import os

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
        # Load the font from the bundled assets folder
        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'DejaVuSans.ttf')
        try:
            self.font = pygame.font.Font(font_path, 72)
            self.game_over_font = pygame.font.Font(font_path, 50)
        except pygame.error:
            # Fallback to the default font if the bundled font is missing for some reason
            print(f"Warning: Could not load bundled font at {font_path}. Falling back to default.")
            self.font = pygame.font.SysFont(None, 72)
            self.game_over_font = pygame.font.SysFont(None, 60)

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

    def draw_game_over(self, result_str):
        """Draws a game over message on the screen."""
        # Create a semi-transparent surface
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency

        # Determine the message
        if result_str == "1-0":
            message = "White wins!"
        elif result_str == "0-1":
            message = "Black wins!"
        elif result_str == "1/2-1/2":
            message = "It's a Draw!"
        else:
            message = "Game Over" # Fallback

        text_surface = self.game_over_font.render(message, True, WHITE_COLOR)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))

        # Blit the overlay and the text
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(text_surface, text_rect)

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