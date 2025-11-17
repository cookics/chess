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
    def send_command(self, command, **kwargs):
        if not self.socket:
            return None
        try:
            request_data = {"command": command}
            request_data.update(kwargs)
            request = json.dumps(request_data)
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
WIDTH = 1024
BOARD_WIDTH = 512
INFO_PANEL_WIDTH = (WIDTH - BOARD_WIDTH) // 2
SQUARE_SIZE = BOARD_WIDTH // 8
BOARD_HEIGHT = 8 * SQUARE_SIZE
HEIGHT = BOARD_HEIGHT

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

        self.white_resign_button_rect = pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH + 10, HEIGHT - 100, 120, 40)
        self.white_draw_button_rect = pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH + 140, HEIGHT - 100, 120, 40)
        self.black_resign_button_rect = pygame.Rect(10, HEIGHT - 100, 120, 40)
        self.black_draw_button_rect = pygame.Rect(140, HEIGHT - 100, 120, 40)


        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'DejaVuSans.ttf')
        try:
            self.font = pygame.font.Font(font_path, 72)
            self.game_over_font = pygame.font.Font(font_path, 50)
            self.info_font = pygame.font.Font(font_path, 18)
            self.login_font = pygame.font.Font(font_path, 24)
            self.captured_font = pygame.font.Font(font_path, 24)
        except pygame.error:
            print(f"Warning: Could not load bundled font at {font_path}. Falling back to default.")
            self.font = pygame.font.SysFont(None, 72)
            self.game_over_font = pygame.font.SysFont(None, 60)
            self.info_font = pygame.font.SysFont(None, 24)
            self.login_font = pygame.font.SysFont(None, 30)
            self.captured_font = pygame.font.SysFont(None, 30)
    def show_login_screen(self):
        accounts = list(self.account_manager.accounts.keys())
        white_player_rects = []
        black_player_rects = []

        y_offset = 50
        for i, acc in enumerate(accounts):
            white_player_rects.append(pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH + 10, y_offset + i * 30, 120, 25))
            black_player_rects.append(pygame.Rect(10, y_offset + i * 30, 120, 25))

        while self.player1_username is None or self.player2_username is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(white_player_rects):
                        if rect.collidepoint(event.pos):
                            self.player1_username = accounts[i]
                    for i, rect in enumerate(black_player_rects):
                        if rect.collidepoint(event.pos):
                            self.player2_username = accounts[i]

            self.screen.fill((20,20,20))

            # Draw titles
            white_title = self.login_font.render("White", True, WHITE_COLOR)
            black_title = self.login_font.render("Black", True, WHITE_COLOR)
            self.screen.blit(white_title, (INFO_PANEL_WIDTH + BOARD_WIDTH + 10, 10))
            self.screen.blit(black_title, (10, 10))

            for i, acc in enumerate(accounts):
                # White buttons
                color = (0, 150, 0) if self.player1_username == acc else (50, 50, 50)
                pygame.draw.rect(self.screen, color, white_player_rects[i])
                text = self.info_font.render(acc, True, WHITE_COLOR)
                self.screen.blit(text, (white_player_rects[i].x + 5, white_player_rects[i].y + 5))

                # Black buttons
                color = (0, 150, 0) if self.player2_username == acc else (50, 50, 50)
                pygame.draw.rect(self.screen, color, black_player_rects[i])
                text = self.info_font.render(acc, True, WHITE_COLOR)
                self.screen.blit(text, (black_player_rects[i].x + 5, black_player_rects[i].y + 5))

            pygame.display.flip()
            self.clock.tick(30)

        return True

    def update_state(self):
        self.game_state = self.game_client.get_state()
        if self.game_state:
            self.board = chess.Board(self.game_state["fen"])

    def pixel_to_square(self, pos):
        if not (0 <= pos[1] < BOARD_HEIGHT):
            return None
        if not (INFO_PANEL_WIDTH <= pos[0] < INFO_PANEL_WIDTH + BOARD_WIDTH):
            return None
        col = (pos[0] - INFO_PANEL_WIDTH) // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        return chess.square(col, 7 - row)

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (INFO_PANEL_WIDTH + col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (INFO_PANEL_WIDTH + col * SQUARE_SIZE, row * SQUARE_SIZE))

        for move in self.legal_moves_for_selected_piece:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            dot_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, LEGAL_MOVE_DOT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(dot_surface, (INFO_PANEL_WIDTH + col * SQUARE_SIZE, row * SQUARE_SIZE))

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece:
                    piece_symbol = UNICODE_PIECES[piece.symbol()]
                    color = BLACK_COLOR
                    text = self.font.render(piece_symbol, True, color)
                    text_rect = text.get_rect(center=(INFO_PANEL_WIDTH + col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text, text_rect)

    def draw_game_info(self):
        # This will be the new side panel
        white_panel_rect = pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT)
        black_panel_rect = pygame.Rect(0, 0, INFO_PANEL_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, (40, 40, 40), white_panel_rect)
        pygame.draw.rect(self.screen, (40, 40, 40), black_panel_rect)

        if self.player1_username and self.player2_username:
            white_player_info = self.account_manager.accounts[self.player1_username]
            black_player_info = self.account_manager.accounts[self.player2_username]

            white_player_text = f"{self.player1_username} ({white_player_info['elo']})"
            black_player_text = f"{self.player2_username} ({black_player_info['elo']})"

            white_player_surface = self.info_font.render(white_player_text, True, WHITE_COLOR)
            black_player_surface = self.info_font.render(black_player_text, True, WHITE_COLOR)

            self.screen.blit(white_player_surface, (INFO_PANEL_WIDTH + BOARD_WIDTH + 10, 10))
            self.screen.blit(black_player_surface, (10, 10))
        if self.game_state and self.game_state["white_time"] is not None:
            white_time_str = str(timedelta(seconds=int(self.game_state["white_time"])))[2:]
            black_time_str = str(timedelta(seconds=int(self.game_state["black_time"])))[2:]

            white_timer_surface = self.info_font.render(f"Time: {white_time_str}", True, WHITE_COLOR)
            black_timer_surface = self.info_font.render(f"Time: {black_time_str}", True, WHITE_COLOR)

            self.screen.blit(white_timer_surface, (INFO_PANEL_WIDTH + BOARD_WIDTH + 10, 40))
            self.screen.blit(black_timer_surface, (10, 40))


        if self.game_state and "evaluation" in self.game_state:
            evaluation = self.game_state["evaluation"]
            if evaluation and evaluation['type'] == 'cp':
                adv = evaluation['value']
                if adv == 0:
                    adv_text = "Material is even"
                else:
                    adv_text = f"Advantage: +{abs(adv/100.0)} for {'White' if adv > 0 else 'Black'}"
                adv_surface = self.info_font.render(adv_text, True, WHITE_COLOR)
                self.screen.blit(adv_surface, (INFO_PANEL_WIDTH + 10, 10))

        if self.game_state and "captured_pieces" in self.game_state:
            white_captured = self.game_state["captured_pieces"]["white"]
            black_captured = self.game_state["captured_pieces"]["black"]

            white_captured_text = " ".join([UNICODE_PIECES[p] for p in white_captured])
            black_captured_text = " ".join([UNICODE_PIECES[p] for p in black_captured])

            white_captured_surface = self.captured_font.render(white_captured_text, True, WHITE_COLOR)
            black_captured_surface = self.captured_font.render(black_captured_text, True, WHITE_COLOR)

            self.screen.blit(white_captured_surface, (INFO_PANEL_WIDTH + BOARD_WIDTH + 10, 70))
            self.screen.blit(black_captured_surface, (10, 70))

        # Draw Resign and Draw buttons
        pygame.draw.rect(self.screen, (200, 0, 0), self.white_resign_button_rect)
        pygame.draw.rect(self.screen, (0, 200, 0), self.white_draw_button_rect)
        pygame.draw.rect(self.screen, (200, 0, 0), self.black_resign_button_rect)
        pygame.draw.rect(self.screen, (0, 200, 0), self.black_draw_button_rect)

        resign_text = self.info_font.render("Resign", True, WHITE_COLOR)
        draw_text = self.info_font.render("Draw", True, WHITE_COLOR)

        self.screen.blit(resign_text, (self.white_resign_button_rect.x + 30, self.white_resign_button_rect.y + 10))
        self.screen.blit(draw_text, (self.white_draw_button_rect.x + 40, self.white_draw_button_rect.y + 10))
        self.screen.blit(resign_text, (self.black_resign_button_rect.x + 30, self.black_resign_button_rect.y + 10))
        self.screen.blit(draw_text, (self.black_draw_button_rect.x + 40, self.black_draw_button_rect.y + 10))


    def handle_mouse_click(self, pos):
        if self.white_resign_button_rect.collidepoint(pos):
            self.game_client.send_command("resign")
            return
        if self.white_draw_button_rect.collidepoint(pos):
            self.game_client.send_command("draw")
            return
        if self.black_resign_button_rect.collidepoint(pos):
            self.game_client.send_command("resign")
            return
        if self.black_draw_button_rect.collidepoint(pos):
            self.game_client.send_command("draw")
            return

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

    def draw_draw_offer(self):
        if self.game_state["draw_offer"] == chess.WHITE:
            accept_button = pygame.Rect(10, HEIGHT - 150, 120, 40)
            decline_button = pygame.Rect(140, HEIGHT - 150, 120, 40)
        else:
            accept_button = pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH + 10, HEIGHT - 150, 120, 40)
            decline_button = pygame.Rect(INFO_PANEL_WIDTH + BOARD_WIDTH + 140, HEIGHT - 150, 120, 40)

        pygame.draw.rect(self.screen, (0, 150, 0), accept_button)
        pygame.draw.rect(self.screen, (150, 0, 0), decline_button)

        accept_text = self.info_font.render("Accept", True, WHITE_COLOR)
        decline_text = self.info_font.render("Decline", True, WHITE_COLOR)

        self.screen.blit(accept_text, (accept_button.x + 30, accept_button.y + 10))
        self.screen.blit(decline_text, (decline_button.x + 30, decline_button.y + 10))

        return accept_button, decline_button

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

            draw_offer_turn = self.game_state.get("draw_offer")
            is_our_turn_to_respond = draw_offer_turn is not None and draw_offer_turn != self.board.turn

            if self.vs_ai and self.game_state["turn"] == "black" and not self.game_state["is_game_over"]:
                time.sleep(0.5)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state["is_game_over"]:
                        continue
                    if is_our_turn_to_respond:
                        accept_button, decline_button = self.draw_draw_offer()
                        if accept_button.collidepoint(event.pos):
                            self.game_client.send_command("accept_draw")
                        elif decline_button.collidepoint(event.pos):
                            self.game_client.send_command("decline_draw")
                    else:
                        self.handle_mouse_click(pygame.mouse.get_pos())


            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_game_info()

            if is_our_turn_to_respond:
                self.draw_draw_offer()

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

                if not game_over_processed:
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
