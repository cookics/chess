from stockfish import Stockfish
from chess_game.config import load_settings

try:
    settings = load_settings()
    stockfish_path = settings.get('stockfish_path')
    stockfish = Stockfish(path=stockfish_path)
    print("Stockfish initialized successfully!")
    print(f"Stockfish version: {stockfish.get_stockfish_major_version()}")
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you have downloaded the Stockfish executable from https://stockfishchess.org/download/")
    print("2. If Stockfish is not in your system's PATH, you need to specify the path to the executable.")
    print("   For example: stockfish = Stockfish(path='/path/to/stockfish')")
    print("   On Windows, it might look like: stockfish = Stockfish(path='C:\\\\path\\\\to\\\\stockfish.exe')")
