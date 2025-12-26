"""Theme colors and constants."""

DARK_THEME = {
    'bg_primary': '#1c1c1a',
    'bg_secondary': '#252523',
    'bg_tertiary': '#2e2e2b',
    'bg_hover': '#3a3a36',
    'accent': '#82827d',
    'accent_light': '#9a9a95',
    'text_primary': '#e8e8e6',
    'text_secondary': '#a8a8a4',
    'text_muted': '#6e6e6a',
    'border': '#3a3a36',
    'terminal_bg': '#1c1c1a',
    'terminal_fg': '#e8e8e6',
    'close_hover': '#e55050',
}

LIGHT_THEME = {
    'bg_primary': '#ffffff',
    'bg_secondary': '#f5f5f5',
    'bg_tertiary': '#e8e8e8',
    'bg_hover': '#d0d0d0',
    'accent': '#6b6b6b',
    'accent_light': '#888888',
    'text_primary': '#1a1a1a',
    'text_secondary': '#4a4a4a',
    'text_muted': '#888888',
    'border': '#d0d0d0',
    'terminal_bg': '#ffffff',
    'terminal_fg': '#1a1a1a',
    'close_hover': '#e55050',
}

# Current theme (default: dark)
_current_theme = 'dark'
COLORS = DARK_THEME.copy()


def get_theme() -> str:
    """Get current theme name."""
    return _current_theme


def set_theme(theme: str):
    """Set theme ('dark' or 'light')."""
    global _current_theme, COLORS
    _current_theme = theme
    if theme == 'light':
        COLORS.update(LIGHT_THEME)
    else:
        COLORS.update(DARK_THEME)


def toggle_theme() -> str:
    """Toggle between dark and light theme. Returns new theme name."""
    new_theme = 'light' if _current_theme == 'dark' else 'dark'
    set_theme(new_theme)
    return new_theme


ANSI_COLORS = {
    'black': '#1c1c1a',
    'red': '#cc6666',
    'green': '#b5bd68',
    'yellow': '#f0c674',
    'blue': '#81a2be',
    'magenta': '#b294bb',
    'cyan': '#8abeb7',
    'white': '#c5c8c6',
    'brightblack': '#969896',
    'brightred': '#cc6666',
    'brightgreen': '#b5bd68',
    'brightyellow': '#f0c674',
    'brightblue': '#81a2be',
    'brightmagenta': '#b294bb',
    'brightcyan': '#8abeb7',
    'brightwhite': '#ffffff',
}
