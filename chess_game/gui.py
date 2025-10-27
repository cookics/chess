import pygame
import chess
import os
import subprocess
import sys
import time
from stockfish import Stockfish
import socket
import json
from datetime import timedelta

class GameClient:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except ConnectionRefusedError:
            return False

    def get_state(self):
        if not self.socket:
            return None
        try:
            request = json.dumps({"command": "get_state"})
            self.socket.sendall(request.encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return json.loads(response)
        except (BrokenPipeError, ConnectionResetError):
            self.socket = None
            return None

    def make_move(self, move_uci):
        if not self.socket:
            return None
        try:
            request = json.dumps({"command": "make_move", "move": move_uci})
            self.socket.sendall(request.encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return json.loads(response)
        except (BrokenPipeError, ConnectionResetError):
            self.socket = None
            return None

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

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

class ChessGUI:
    def __init__(self, game_client, vs_ai=False):
        pygame.init()
        self.game_client = game_client
        self.vs_ai = vs_ai
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves_for_selected_piece = []
        self.game_state = None
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

    def update_state(self):
        self.game_state = self.game_client.get_state()
        if self.game_state:
            self.board = chess.Board(self.game_state["fen"])

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
        if self.game_state and self.game_state["white_time"] is not None:
            white_time_str = str(timedelta(seconds=int(self.game_state["white_time"])))[2:]
            black_time_str = str(timedelta(seconds=int(self.game_state["black_time"])))[2:]
            timer_text = f"White: {white_time_str} | Black: {black_time_str}"
            timer_surface = self.info_font.render(timer_text, True, WHITE_COLOR)
            timer_rect = timer_surface.get_rect(center=(WIDTH // 2, INFO_PANEL_HEIGHT // 2))
            self.screen.blit(timer_surface, timer_rect)

        # Material advantage display in the bottom panel
        if self.game_state and "evaluation" in self.game_state:
            evaluation = self.game_state["evaluation"]
            if evaluation['type'] == 'cp':
                adv = evaluation['value']
                if adv == 0:
                    adv_text = "Material is even"
                else:
                    adv_text = f"Advantage: +{abs(adv/100.0)} for {'White' if adv > 0 else 'Black'}"
                adv_surface = self.info_font.render(adv_text, True, WHITE_COLOR)
                adv_rect = adv_surface.get_rect(center=(WIDTH // 2, HEIGHT - INFO_PANEL_HEIGHT // 2))
                self.screen.blit(adv_surface, adv_rect)


    def handle_mouse_click(self, pos):
        """Handles a mouse click event to select or move a piece."""
        clicked_square = self.pixel_to_square(pos)

        # If a piece was already selected, check if this is a legal move
        if self.selected_square is not None:
            move_uci = chess.Move(self.selected_square, clicked_square).uci()
            if self.game_state and move_uci in self.game_state["legal_moves"]:
                self.game_client.make_move(move_uci)
                self.update_state()
            self.selected_square = None
            self.legal_moves_for_selected_piece = []
            return

        # Check if the clicked square has a piece of the correct color
        piece = self.board.piece_at(clicked_square)
        if piece and piece.color == self.board.turn:
            self.selected_square = clicked_square
            # Get all legal moves for the selected piece
            if self.game_state:
                self.legal_moves_for_selected_piece = [
                    chess.Move.from_uci(m) for m in self.game_state["legal_moves"] if chess.Move.from_uci(m).from_square == self.selected_square
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

    def draw_evaluation_bar(self):
        """Draws the Stockfish evaluation bar."""
        if self.game_state and "evaluation" in self.game_state:
            evaluation = self.game_state["evaluation"]
            if evaluation['type'] == 'cp':
                # Map centipawn advantage to a value between -1000 and 1000 for the bar
                eval_value = max(-1000, min(1000, evaluation['value']))
                # Calculate the height of the white bar. A positive eval is good for white.
                white_height = (BOARD_HEIGHT / 2) * (1 - eval_value / 1000)
                white_rect = pygame.Rect(0, INFO_PANEL_HEIGHT, EVAL_BAR_WIDTH, white_height)
                black_rect = pygame.Rect(0, INFO_PANEL_HEIGHT + white_height, EVAL_BAR_WIDTH, BOARD_HEIGHT - white_height)
                pygame.draw.rect(self.screen, WHITE_COLOR, white_rect)
                pygame.draw.rect(self.screen, BLACK_COLOR, black_rect)

    def run(self):
        """Main loop for the GUI, now with interaction."""
        running = True
        while running:
            self.update_state()
            if not self.game_state:
                # Handle server connection loss
                print("Lost connection to the server.")
                break

            # AI's turn
            if self.vs_ai and self.game_state["turn"] == "black" and not self.game_state["is_game_over"]:
                # The server should handle AI moves
                time.sleep(0.5) # Prevent spamming server

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game_state["is_game_over"]:
                        self.handle_mouse_click(pygame.mouse.get_pos())

            # Drawing order: board, then highlights, then pieces
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_game_info()
            self.draw_evaluation_bar()

            if self.game_state["is_game_over"]:
                result = self.game_state["result"]
                if result == "1-0":
                    msg = "White wins!"
                elif result == "0-1":
                    msg = "Black wins!"
                elif result == "1/2-1/2":
                    msg = "Draw!"
                else:
                    msg = "Game Over"
                self.draw_game_over(msg)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main(vs_ai=False):
    # Start the CLI server in a new terminal window
    server_process = None
    try:
        server_process = subprocess.Popen([sys.executable, '-m', 'chess_game.cli', 'server'])
        time.sleep(2) # Give server time to start
    except Exception as e:
        print(f"Failed to start server: {e}")
        return

    game_client = GameClient()
    if not game_client.connect():
        print("Failed to connect to the game server.")
        if server_process:
            server_process.terminate()
        return

    gui = ChessGUI(game_client, vs_ai=vs_ai)

    try:
        gui.run()
    finally:
        game_client.close()
        if server_process:
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main()
