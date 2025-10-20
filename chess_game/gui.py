import pygame
import chess
import os
import subprocess
import sys
import time
from stockfish import Stockfish

# --- Constants ---
# Screen dimensions
WIDTH = 600
EVAL_BAR_WIDTH = 40
INFO_PANEL_HEIGHT = 50
BOARD_HEIGHT = 512
HEIGHT = BOARD_HEIGHT + 2 * INFO_PANEL_HEIGHT # Window height
# Board dimensions are the same as screen dimensions
SQUARE_SIZE = (WIDTH - EVAL_BAR_WIDTH) // 8

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
        if self.last_move_time is None:
            return self.white_time if color == chess.WHITE else self.black_time

        elapsed = time.time() - self.last_move_time
        if self.current_turn == color:
            return max(0, (self.white_time if color == chess.WHITE else self.black_time) - elapsed)
        else:
            return max(0, self.white_time if color == chess.WHITE else self.black_time)

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))[2:]

    def get_time_display(self):
        return f"White: {self.format_time(self.get_time_left(chess.WHITE))} | Black: {self.format_time(self.get_time_left(chess.BLACK))}"

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

class ChessGUI:
    def __init__(self, board, stockfish, timer=None):
        pygame.init()
        self.timer = timer
        self.stockfish = stockfish
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = board
        self.selected_square = None
        self.legal_moves_for_selected_piece = []
        self.game_over_message = None
        # A larger font is needed for the unicode characters to be visible
        # Load the font from the bundled assets folder
        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'DejaVuSans.ttf')
        try:
            self.font = pygame.font.Font(font_path, 72)
            self.game_over_font = pygame.font.Font(font_path, 50)
            self.info_font = pygame.font.Font(font_path, 18)
        except pygame.error:
            # Fallback to the default font if the bundled font is missing for some reason
            print(f"Warning: Could not load bundled font at {font_path}. Falling back to default.")
            self.font = pygame.font.SysFont(None, 72)
            self.game_over_font = pygame.font.SysFont(None, 60)
            self.info_font = pygame.font.SysFont(None, 24)

    def pixel_to_square(self, pos):
        """Converts a pixel position to a chess square index."""
        if not (INFO_PANEL_HEIGHT <= pos[1] < HEIGHT - INFO_PANEL_HEIGHT):
            return None
        if not (EVAL_BAR_WIDTH <= pos[0] < WIDTH):
            return None
        col = (pos[0] - EVAL_BAR_WIDTH) // SQUARE_SIZE
        row = (pos[1] - INFO_PANEL_HEIGHT) // SQUARE_SIZE
        return chess.square(col, 7 - row)

    def draw_board(self):
        """Draws the chessboard squares."""
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        """Draws highlights for the selected piece and its legal moves."""
        # Highlight the selected square
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            # Use a separate surface for transparency
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE))

        # Draw dots for legal moves
        for move in self.legal_moves_for_selected_piece:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            # Use a separate surface for transparency
            dot_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, LEGAL_MOVE_DOT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(dot_surface, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE))

    def draw_pieces(self):
        """Draws the pieces on the board using Unicode characters."""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece:
                    piece_symbol = UNICODE_PIECES[piece.symbol()]
                    color = BLACK_COLOR
                    text = self.font.render(piece_symbol, True, color)
                    text_rect = text.get_rect(center=(EVAL_BAR_WIDTH + col * SQUARE_SIZE + SQUARE_SIZE // 2, INFO_PANEL_HEIGHT + row * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text, text_rect)

    def draw_game_info(self):
        """Draws the timer and material advantage in the top and bottom panels."""
        self.screen.fill(BLACK_COLOR, pygame.Rect(0, 0, WIDTH, INFO_PANEL_HEIGHT))
        self.screen.fill(BLACK_COLOR, pygame.Rect(0, HEIGHT - INFO_PANEL_HEIGHT, WIDTH, INFO_PANEL_HEIGHT))

        # Timer display in the top panel
        if self.timer:
            timer_text = self.timer.get_time_display()
            timer_surface = self.info_font.render(timer_text, True, WHITE_COLOR)
            timer_rect = timer_surface.get_rect(center=(WIDTH // 2, INFO_PANEL_HEIGHT // 2))
            self.screen.blit(timer_surface, timer_rect)

        # Material advantage display in the bottom panel
        advantage = calculate_material_advantage(self.board)
        if advantage == 0:
            adv_text = "Material is even"
        else:
            adv_text = f"Advantage: +{abs(advantage)} for {'White' if advantage > 0 else 'Black'}"
        adv_surface = self.info_font.render(adv_text, True, WHITE_COLOR)
        adv_rect = adv_surface.get_rect(center=(WIDTH // 2, HEIGHT - INFO_PANEL_HEIGHT // 2))
        self.screen.blit(adv_surface, adv_rect)

    def handle_mouse_click(self, pos):
        """Handles a mouse click event to select or move a piece."""
        clicked_square = self.pixel_to_square(pos)

        # If a piece was already selected, check if this is a legal move
        if self.selected_square is not None:
            move = chess.Move(self.selected_square, clicked_square)
            # Also check for promotion
            if move in self.board.legal_moves:
                self.board.push(move)
                if self.timer:
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


    def draw_game_over(self, message):
        """Draws a game over message on the screen."""
        # Create a semi-transparent surface to dim the whole window
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))

        # Render the text and center it on the board
        text_surface = self.game_over_font.render(message, True, WHITE_COLOR)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    def update_stockfish_position(self):
        """Update the Stockfish engine with the current board position."""
        if self.stockfish.is_fen_valid(self.board.fen()):
            self.stockfish.set_fen_position(self.board.fen())
        else:
            print("Error: Invalid FEN")

    def draw_evaluation_bar(self):
        """Draws the Stockfish evaluation bar."""
        if self.stockfish:
            evaluation = self.stockfish.get_evaluation()
            if evaluation['type'] == 'cp':
                # Map centipawn advantage to a value between -1000 and 1000 for the bar
                eval_value = max(-1000, min(1000, evaluation['value']))
                # Calculate the height of the white bar. A positive eval is good for white.
                white_height = (BOARD_HEIGHT / 2) * (1 + eval_value / 1000)
                white_rect = pygame.Rect(0, INFO_PANEL_HEIGHT, EVAL_BAR_WIDTH, white_height)
                black_rect = pygame.Rect(0, INFO_PANEL_HEIGHT + white_height, EVAL_BAR_WIDTH, BOARD_HEIGHT - white_height)
                pygame.draw.rect(self.screen, WHITE_COLOR, white_rect)
                pygame.draw.rect(self.screen, BLACK_COLOR, black_rect)

    def run(self):
        """Main loop for the GUI, now with interaction."""
        running = True
        while running:
            # Check for timeout
            if self.timer and not self.board.is_game_over() and self.game_over_message is None:
                if self.timer.get_time_left(self.board.turn) <= 0:
                    winner = "Black" if self.board.turn == chess.WHITE else "White"
                    self.game_over_message = f"{winner} wins by timeout!"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.board.is_game_over() and self.game_over_message is None:
                        self.handle_mouse_click(pygame.mouse.get_pos())
                        self.update_stockfish_position()

            # Drawing order: board, then highlights, then pieces
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_game_info()
            self.draw_evaluation_bar()

            if self.game_over_message:
                self.draw_game_over(self.game_over_message)
            elif self.board.is_game_over():
                result_str = self.board.result()
                if result_str == "1-0":
                    message = "White wins!"
                elif result_str == "0-1":
                    message = "Black wins!"
                elif result_str == "1/2-1/2":
                    message = "It's a Draw!"
                else:
                    message = "Game Over"
                self.draw_game_over(message)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main():
    # Start the CLI in a new terminal window
    cli_process = None
    try:
        if sys.platform.startswith('win'):
            cli_process = subprocess.Popen(['cmd.exe', '/c', 'python -m chess_game.cli'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform.startswith('darwin'):
            cli_process = subprocess.Popen(['open', '-a', 'Terminal', '-n', sys.executable, '-m', 'chess_game.cli'])
        else:
            terminal_emulator = 'x-terminal-emulator'
            try:
                cli_process = subprocess.Popen([terminal_emulator, '-e', f'{sys.executable} -m chess_game.cli'])
            except FileNotFoundError:
                print("Could not find a default terminal emulator. Please run the CLI manually.")
    except Exception as e:
        print(f"Failed to start CLI: {e}")

    # Initialize Stockfish
    stockfish = None
    try:
        stockfish = Stockfish()
    except (FileNotFoundError, OSError):
        print("Stockfish engine not found. Please install it and ensure it's in your PATH,")
        print("or specify the path in the config.py file.")
        # The GUI will run without the evaluation bar
    except Exception as e:
        print(f"An error occurred while initializing Stockfish: {e}")

    board = chess.Board()
    timer = ChessTimer(600)  # 10 minutes per side
    timer.start_turn()
    gui = ChessGUI(board, stockfish, timer)

    try:
        gui.run()
    finally:
        if cli_process:
            cli_process.terminate()
            cli_process.wait()

if __name__ == "__main__":
    main()
