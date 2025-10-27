from stockfish import Stockfish

try:
    # This will work if stockfish is in your PATH
    stockfish = Stockfish()
    print("Stockfish initialized successfully!")
    print(f"Stockfish version: {stockfish.get_stockfish_major_version()}")
    print("Path to executable:", stockfish.get_parameters()['StockfishPath'])
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you have downloaded the Stockfish executable from https://stockfishchess.org/download/")
    print("2. If Stockfish is not in your system's PATH, you need to specify the path to the executable.")
    print("   For example: stockfish = Stockfish(path='/path/to/stockfish')")
    print("   On Windows, it might look like: stockfish = Stockfish(path='C:\\\\path\\\\to\\\\stockfish.exe')")
