import pygame
import chess
import chess.pgn
import os
import time
from AiOpponentManager import AIOpponentManager
from chess_game.config import load_settings
from chess_game.stockfish_manager import StockfishManager
from chess_game.cli import ChessTimer
from chess_game.elo_calculator import EloCalculator

# --- Constants ---
# Screen dimensions
BOARD_WIDTH = 512
BOARD_HEIGHT = 512
INFO_PANEL_WIDTH = 256
WIDTH = BOARD_WIDTH + INFO_PANEL_WIDTH
HEIGHT = BOARD_HEIGHT
SQUARE_SIZE = BOARD_WIDTH // 8

# Colors
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (255, 255, 51, 170) # Yellow with some transparency
LEGAL_MOVE_DOT_COLOR = (20, 80, 20, 120) # Dark green with transparency

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}


class ChessGUI:
    def __init__(self, board, account_manager, vs_ai=False, ai_elo=1350):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = board
        self.account_manager = account_manager
        self.selected_square = None
        self.legal_moves_for_selected_piece = []
        self.vs_ai = vs_ai
        settings = load_settings()
        self.stockfish_manager = StockfishManager(settings.get('stockfish_path'))
        self.timer = ChessTimer()
        self.timer.start_turn()
        if self.vs_ai:
            self.ai_opponent = AIOpponentManager(stockfish_path=settings.get('stockfish_path'))
            self.ai_opponent.set_elo(ai_elo)

        # A larger font is needed for the unicode characters to be visible
        # Load the font from the bundled assets folder
        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'DejaVuSans.ttf')
        try:
            self.font = pygame.font.Font(font_path, 72)
            self.game_over_font = pygame.font.Font(font_path, 50)
            self.info_font = pygame.font.Font(font_path, 24)
        except pygame.error:
            # Fallback to the default font if the bundled font is missing for some reason
            print(f"Warning: Could not load bundled font at {font_path}. Falling back to default.")
            self.font = pygame.font.SysFont(None, 72)
            self.game_over_font = pygame.font.SysFont(None, 60)
            self.info_font = pygame.font.SysFont(None, 30)

    def pixel_to_square(self, pos):
        """Converts a pixel position to a chess square index."""
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        return chess.square(col, 7 - row)

    def draw_board(self):
        """Draws the chessboard squares."""
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        """Draws highlights for the selected piece and its legal moves."""
        # Highlight the selected square
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            # Use a separate surface for transparency
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))

        # Draw dots for legal moves
        for move in self.legal_moves_for_selected_piece:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            # Use a separate surface for transparency
            dot_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, LEGAL_MOVE_DOT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(dot_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))


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

    def draw_info_panel(self):
        """Draws the information panel with timers and evaluation bar."""
        info_panel_rect = pygame.Rect(BOARD_WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT)
        panel_color = (40, 40, 40)
        pygame.draw.rect(self.screen, panel_color, info_panel_rect)

        # Display Player Info
        if self.account_manager.current_account:
            info = self.account_manager.get_current_account_info()
            player_text = f"{info['username']} ({info['elo']})"
            player_surface = self.info_font.render(player_text, True, WHITE_COLOR)
            self.screen.blit(player_surface, (BOARD_WIDTH + 10, 50))

        # Display timers
        white_time_text = self.timer.format_time(self.timer.get_time_left(chess.WHITE))
        black_time_text = self.timer.format_time(self.timer.get_time_left(chess.BLACK))

        white_timer_surface = self.info_font.render(f"White: {white_time_text}", True, WHITE_COLOR)
        black_timer_surface = self.info_font.render(f"Black: {black_time_text}", True, WHITE_COLOR)

        self.screen.blit(white_timer_surface, (BOARD_WIDTH + 10, HEIGHT - 40))
        self.screen.blit(black_timer_surface, (BOARD_WIDTH + 10, 10))

        # Evaluation Bar
        eval_bar_width = 40
        eval_bar_x = BOARD_WIDTH + INFO_PANEL_WIDTH - eval_bar_width - 10

        if self.stockfish_manager:
            eval_data = self.stockfish_manager.get_evaluation(self.board.fen())
            if eval_data and eval_data['type'] == 'cp':
                cp = max(-1000, min(1000, eval_data['value']))
                normalized_eval = (cp + 1000) / 2000

                white_bar_height = normalized_eval * (HEIGHT - 80) # Adjust height for timers
                black_bar_height = (HEIGHT - 80) - white_bar_height

                pygame.draw.rect(self.screen, WHITE_COLOR, (eval_bar_x, 50 + black_bar_height, eval_bar_width, white_bar_height))
                pygame.draw.rect(self.screen, BLACK_COLOR, (eval_bar_x, 50, eval_bar_width, black_bar_height))

    def handle_mouse_click(self, pos):
        """Handles a mouse click event to select or move a piece."""
        clicked_square = self.pixel_to_square(pos)

        # If a piece was already selected, check if this is a legal move
        if self.selected_square is not None:
            move = chess.Move(self.selected_square, clicked_square)
            # Also check for promotion
            if move in self.board.legal_moves:
                self.board.push(move)
                self.timer.switch_turn()
                self.selected_square = None
                self.legal_moves_for_selected_piece = []
                return

        # Check if the clicked square has a piece of the correct color
        piece = self.board.piece_at(clicked_square)
        if piece and piece.color == self.board.turn:
            self.selected_square = clicked_square
            # Get all legal moves for the selected piece
            self.legal_moves_for_selected_piece = [
                m for m in self.board.legal_moves if m.from_square == self.selected_square
            ]
        else: # Deselect if clicking an empty square or opponent's piece
            self.selected_square = None
            self.legal_moves_for_selected_piece = []


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
        """Main loop for the GUI, now with interaction."""
        running = True
        while running:
            if self.vs_ai and self.board.turn == chess.BLACK and not self.board.is_game_over():
                pygame.time.wait(500) # Small delay to make AI move visible
                ai_move_uci = self.ai_opponent.get_best_move(self.board)
                if ai_move_uci:
                    move = chess.Move.from_uci(ai_move_uci)
                    self.board.push(move)
                    self.timer.switch_turn()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.board.is_game_over():
                        self.handle_mouse_click(pygame.mouse.get_pos())

            # Drawing order: board, then highlights, then pieces
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_info_panel()

            if self.board.is_game_over():
                self.draw_game_over(self.board.result())
                if self.account_manager.current_account:
                    game = chess.pgn.Game()
                    game.headers["Event"] = "GUI Game"
                    game.headers["Site"] = "Local"
                    game.headers["Date"] = time.strftime("%Y.%m.%d")
                    game.headers["Round"] = "1"
                    game.headers["White"] = self.account_manager.current_account
                    game.headers["Black"] = "AI" if self.vs_ai else "Human"
                    game.headers["Result"] = self.board.result()

                    if self.board.move_stack:
                        node = game.add_main_variation(self.board.move_stack[0])
                        for move in self.board.move_stack[1:]:
                            node = node.add_main_variation(move)

                    game_pgn = str(game)
                    self.account_manager.add_game_to_history(self.account_manager.current_account, game_pgn)

                    settings = load_settings()
                    elo_calculator = EloCalculator(settings.get('stockfish_path'))
                    current_elo = self.account_manager.get_current_account_info()['elo']
                    new_elo = elo_calculator.calculate_elo(game_pgn, current_elo)
                    self.account_manager.update_elo(self.account_manager.current_account, new_elo)
                    print(f"Your new ELO is: {new_elo}")

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main(account_manager):
    board = chess.Board()
    while True:
        print("\n=== GUI Mode ===")
        print("1. Human vs Human")
        print("2. Human vs AI")
        choice = input("Choose mode (1-2): ").strip()
        if choice == '1':
            gui = ChessGUI(board, account_manager, vs_ai=False)
            gui.run()
            break
        elif choice == '2':
            ai_elo = 1350
            while True:
                try:
                    elo_input = input("Enter AI ELO (1350-2850), or press Enter for default (1350): ").strip()
                    if not elo_input:
                        break
                    elo = int(elo_input)
                    if 1350 <= elo <= 2850:
                        ai_elo = elo
                        break
                    else:
                        print("ELO must be between 1350 and 2850.")
                except ValueError:
                    print("Invalid ELO. Please enter a number.")
            gui = ChessGUI(board, account_manager, vs_ai=True, ai_elo=ai_elo)
            gui.run()
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
