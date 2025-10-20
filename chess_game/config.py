"""
Configuration settings for the chess game.
"""

# Default settings
DEFAULT_SETTINGS = {
    'time_control': 600,  # Default 10 minutes
    'save_auto': False,    # Auto-save after each move
    'save_file': 'chess_save.pkl',
    'show_legal_moves': True,
    'max_display_moves': 10,
}

def load_settings():
    """Load settings from file or return defaults."""
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file."""
    pass
