# Chess project

This project will be utlizing python-chess libaries to translate them into pygame for a GUI interface.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/chess-project.git
    cd chess-project
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install the Stockfish Engine:**
    The GUI includes a real-time evaluation bar powered by the Stockfish chess engine. You need to install it separately for this feature to work.

    *   **Ubuntu/Debian:**
        ```bash
        sudo apt update
        sudo apt install stockfish
        ```
    *   **macOS (using Homebrew):**
        ```bash
        brew install stockfish
        ```
    *   **Windows:**
        1.  Download the latest Stockfish release from the [official website](https://stockfishchess.org/download/).
        2.  Extract the `.zip` file.
        3.  Add the directory containing `stockfish.exe` to your system's `PATH` environment variable.

    If the application cannot find the Stockfish executable automatically, it will still run, but the evaluation bar will be disabled.

## TODO

Main Sprint deliverables:

- [x] GUI -> cli
- [x] Game/State (Ie. win/ draw) on GUI

Add:
Cli 
- [x] Peices org in avbl. moves
- [x] Current caputres
- [x] Material advantage

GUI:

- [x] time + mat. adv on display
