"""Claude TUI - Main entry point."""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QPalette

from theme import COLORS
from window import ClaudeWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent']))
    app.setPalette(palette)

    window = ClaudeWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
