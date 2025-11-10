import pygame
import chess
import os
import subprocess
import sys
import time
import socket
import json
from datetime import timedelta
from accountcreation import AccountManager

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BaseClient:
    """A simple client to handle the basic socket connection."""
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
        except (BrokenPipeError, ConnectionResetError, json.JSONDecodeError):
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
        except (BrokenPipeError, ConnectionResetError, json.JSONDecodeError):
            self.socket = None
            return None

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

class GameClient(BaseClient):
    def __init__(self, host='127.0.0.1', port=65432, account_manager=None):
        super().__init__(host, port)
        self.account_manager = account_manager

# --- Constants ---
WIDTH = 600
EVAL_BAR_WIDTH = 40
INFO_PANEL_HEIGHT = 50
SQUARE_SIZE = (WIDTH - EVAL_BAR_WIDTH) // 8
BOARD_HEIGHT = 8 * SQUARE_SIZE
HEIGHT = BOARD_HEIGHT + 2 * INFO_PANEL_HEIGHT

# Colors
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (255, 255, 51, 170)
LEGAL_MOVE_DOT_COLOR = (20, 80, 20, 120)

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}

class ChessGUI:
    def __init__(self, game_client, vs_ai=False, account_manager=None):
        pygame.init()
        self.game_client = game_client
        self.account_manager = account_manager
        self.vs_ai = vs_ai
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves_for_selected_piece = []
        self.game_state = None
        self.player1_username = None
        self.player2_username = None

        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'DejaVuSans.ttf')
        try:
            self.font = pygame.font.Font(font_path, 72)
            self.game_over_font = pygame.font.Font(font_path, 50)
            self.info_font = pygame.font.Font(font_path, 18)
        except pygame.error:
            print(f"Warning: Could not load bundled font at {font_path}. Falling back to default.")
            self.font = pygame.font.SysFont(None, 72)
            self.game_over_font = pygame.font.SysFont(None, 60)
            self.info_font = pygame.font.SysFont(None, 24)

    def show_login_screen(self):
        login_font = pygame.font.SysFont(None, 36)
        input_font = pygame.font.SysFont(None, 28)
        clock = pygame.time.Clock()

        p1_input_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 60, 300, 32)
        p2_input_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 32)

        p1_text = ''
        p2_text = ''
        active_p1 = True

        logging_in = True
        while logging_in:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    active_p1 = p1_input_rect.collidepoint(event.pos)

                if event.type == pygame.KEYDOWN:
                    if active_p1:
                        if event.key == pygame.K_RETURN:
                            active_p1 = False
                        elif event.key == pygame.K_BACKSPACE:
                            p1_text = p1_text[:-1]
                        else:
                            p1_text += event.unicode
                    else:
                        if event.key == pygame.K_RETURN:
                            if p1_text in self.account_manager.accounts and p2_text in self.account_manager.accounts:
                                self.player1_username = p1_text
                                self.player2_username = p2_text
                                print(f"Player 1 logged in as: {self.player1_username}")
                                print(f"Player 2 logged in as: {self.player2_username}")
                                logging_in = False
                            else:
                                print("Invalid username for one or both players. Please try again.")
                                p1_text = ''
                                p2_text = ''
                                active_p1 = True
                        elif event.key == pygame.K_BACKSPACE:
                            p2_text = p2_text[:-1]
                        else:
                            p2_text += event.unicode

            self.screen.fill(WHITE_COLOR)
            title_text = login_font.render("Player Login", True, BLACK_COLOR)
            title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
            self.screen.blit(title_text, title_rect)

            pygame.draw.rect(self.screen, BLACK_COLOR, p1_input_rect, 2)
            pygame.draw.rect(self.screen, BLACK_COLOR, p2_input_rect, 2)

            p1_surface = input_font.render(p1_text, True, BLACK_COLOR)
            p2_surface = input_font.render(p2_text, True, BLACK_COLOR)

            self.screen.blit(p1_surface, (p1_input_rect.x + 5, p1_input_rect.y + 5))
            self.screen.blit(p2_surface, (p2_input_rect.x + 5, p2_input_rect.y + 5))

            if active_p1:
                pygame.draw.rect(self.screen, (0, 0, 200), p1_input_rect, 3)
            else:
                pygame.draw.rect(self.screen, (0, 0, 200), p2_input_rect, 3)

            inst1 = input_font.render("Player 1 (White):", True, BLACK_COLOR)
            inst2 = input_font.render("Player 2 (Black):", True, BLACK_COLOR)
            self.screen.blit(inst1, (p1_input_rect.x, p1_input_rect.y - 25))
            self.screen.blit(inst2, (p2_input_rect.x, p2_input_rect.y - 25))

            pygame.display.flip()
            clock.tick(30)
        return True

    def update_state(self):
        self.game_state = self.game_client.get_state()
        if self.game_state:
            self.board = chess.Board(self.game_state["fen"])

    def pixel_to_square(self, pos):
        if not (INFO_PANEL_HEIGHT <= pos[1] < HEIGHT - INFO_PANEL_HEIGHT):
            return None
        if not (EVAL_BAR_WIDTH <= pos[0] < WIDTH):
            return None
        col = (pos[0] - EVAL_BAR_WIDTH) // SQUARE_SIZE
        row = (pos[1] - INFO_PANEL_HEIGHT) // SQUARE_SIZE
        return chess.square(col, 7 - row)

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE))

        for move in self.legal_moves_for_selected_piece:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            dot_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, LEGAL_MOVE_DOT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(dot_surface, (EVAL_BAR_WIDTH + col * SQUARE_SIZE, INFO_PANEL_HEIGHT + row * SQUARE_SIZE))

    def draw_pieces(self):
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
        self.screen.fill(BLACK_COLOR, pygame.Rect(0, 0, WIDTH, INFO_PANEL_HEIGHT))
        self.screen.fill(BLACK_COLOR, pygame.Rect(0, HEIGHT - INFO_PANEL_HEIGHT, WIDTH, INFO_PANEL_HEIGHT))

        if self.game_state and self.game_state["white_time"] is not None:
            white_time_str = str(timedelta(seconds=int(self.game_state["white_time"])))[2:]
            black_time_str = str(timedelta(seconds=int(self.game_state["black_time"])))[2:]
            timer_text = f"White: {white_time_str} | Black: {black_time_str}"
            timer_surface = self.info_font.render(timer_text, True, WHITE_COLOR)
            timer_rect = timer_surface.get_rect(center=(WIDTH // 2, INFO_PANEL_HEIGHT // 2))
            self.screen.blit(timer_surface, timer_rect)

        if self.game_state and "evaluation" in self.game_state:
            evaluation = self.game_state["evaluation"]
            if evaluation and evaluation['type'] == 'cp':
                adv = evaluation['value']
                if adv == 0:
                    adv_text = "Material is even"
                else:
                    adv_text = f"Advantage: +{abs(adv/100.0)} for {'White' if adv > 0 else 'Black'}"
                adv_surface = self.info_font.render(adv_text, True, WHITE_COLOR)
                adv_rect = adv_surface.get_rect(center=(WIDTH // 2, HEIGHT - INFO_PANEL_HEIGHT // 2))
                self.screen.blit(adv_surface, adv_rect)

    def handle_mouse_click(self, pos):
        clicked_square = self.pixel_to_square(pos)
        if clicked_square is None:
            return

        if self.selected_square is not None:
            move_uci = chess.Move(self.selected_square, clicked_square).uci()
            if self.game_state and move_uci in self.game_state["legal_moves"]:
                self.game_client.make_move(move_uci)
                self.update_state()
            self.selected_square = None
            self.legal_moves_for_selected_piece = []
            return

        piece = self.board.piece_at(clicked_square)
        if piece and piece.color == self.board.turn:
            self.selected_square = clicked_square
            if self.game_state:
                self.legal_moves_for_selected_piece = [
                    chess.Move.from_uci(m) for m in self.game_state["legal_moves"] if chess.Move.from_uci(m).from_square == self.selected_square
                ]
        else:
            self.selected_square = None
            self.legal_moves_for_selected_piece = []

    def draw_game_over(self, message):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        text_surface = self.game_over_font.render(message, True, WHITE_COLOR)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    def draw_evaluation_bar(self):
        if self.game_state and "evaluation" in self.game_state:
            evaluation = self.game_state["evaluation"]
            if evaluation and evaluation['type'] == 'cp':
                eval_value = max(-1000, min(1000, evaluation['value']))
                white_height = (BOARD_HEIGHT / 2) * (1 - eval_value / 1000)
                white_rect = pygame.Rect(0, INFO_PANEL_HEIGHT, EVAL_BAR_WIDTH, white_height)
                black_rect = pygame.Rect(0, INFO_PANEL_HEIGHT + white_height, EVAL_BAR_WIDTH, BOARD_HEIGHT - white_height)
                pygame.draw.rect(self.screen, WHITE_COLOR, white_rect)
                pygame.draw.rect(self.screen, BLACK_COLOR, black_rect)

    def run(self):
        if not self.vs_ai:
            if not self.show_login_screen():
                return

        running = True
        game_over_processed = False

        while running:
            self.update_state()
            if not self.game_state:
                print("Lost connection to the server.")
                break

            if self.vs_ai and self.game_state["turn"] == "black" and not self.game_state["is_game_over"]:
                time.sleep(0.5)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game_state["is_game_over"]:
                        self.handle_mouse_click(pygame.mouse.get_pos())

            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_game_info()
            self.draw_evaluation_bar()

            if self.game_state["is_game_over"]:
                result = self.game_state["result"]
                termination = self.game_state.get("termination_reason", "")
                if result == "1-0":
                    msg = f"White wins by {termination}!"
                elif result == "0-1":
                    msg = f"Black wins by {termination}!"
                elif result == "1/2-1/2":
                    msg = f"Draw by {termination}!"
                else:
                    msg = "Game Over"
                self.draw_game_over(msg)

                if not game_over_processed and not self.vs_ai and self.player1_username and self.player2_username:
                    if result == "1-0":
                        elo_result = 'player1_win'
                    elif result == "0-1":
                        elo_result = 'player2_win'
                    else:
                        elo_result = 'draw'

                    game_pgn = self.game_state.get("pgn", "")
                    self.account_manager.record_game_result(self.player1_username, self.player2_username, elo_result, game_pgn)

                    print("ELO and stats updated.")
                    game_over_processed = True

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main(vs_ai=False, account_manager=None):
    server_process = None
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env = os.environ.copy()
        env["PYTHONPATH"] = root_dir

        server_cmd = [sys.executable, '-m', 'chess_game.cli', 'server']
        if vs_ai:
            server_cmd.append('--vs-ai')

        server_process = subprocess.Popen(server_cmd, env=env)
        time.sleep(2)
    except Exception as e:
        print(f"Failed to start server: {e}")
        return

    game_client = GameClient(account_manager=account_manager)
    if not game_client.connect():
        print("Failed to connect to the game server.")
        if server_process:
            server_process.terminate()
        return

    gui = ChessGUI(game_client, vs_ai=vs_ai, account_manager=account_manager)

    try:
        gui.run()
    finally:
        game_client.close()
        if server_process:
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main()
