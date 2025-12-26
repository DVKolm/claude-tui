"""Terminal widget with PTY support."""

import os
import threading
from typing import Optional

from PyQt6.QtWidgets import QApplication, QPlainTextEdit, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeyEvent

import winpty
import pyte

from theme import COLORS


class TerminalWidget(QPlainTextEdit):
    """Real terminal emulator widget using PTY."""

    data_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pty_process: Optional[winpty.PTY] = None
        self.screen = pyte.HistoryScreen(120, 30, history=10000)
        self.stream = pyte.Stream(self.screen)
        self.read_thread: Optional[threading.Thread] = None
        self.running = False
        self._last_text = ""
        self._user_scrolling = False

        self.setup_ui()
        self.data_ready.connect(self.process_output)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.start_pty()

    def setup_ui(self):
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 11))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS['terminal_bg']};
                color: {COLORS['terminal_fg']};
                border: none;
                padding: 8px;
                selection-background-color: {COLORS['accent']};
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg_primary']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {COLORS['bg_primary']};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: {COLORS['border']};
                border-radius: 5px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {COLORS['text_muted']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)
        self.setCursorWidth(8)

    def start_pty(self):
        """Start PTY with shell."""
        try:
            cols, rows = 120, 30
            self.pty_process = winpty.PTY(cols, rows)
            shell = os.environ.get('COMSPEC', 'cmd.exe')
            self.pty_process.spawn(shell)
            self.running = True

            self.read_thread = threading.Thread(target=self.read_pty, daemon=True)
            self.read_thread.start()

            QTimer.singleShot(500, lambda: self.write_to_pty("claude\r"))
            QTimer.singleShot(1500, self.auto_press_one)

        except Exception as e:
            self.setPlainText(f"Error starting terminal: {e}\n\nMake sure winpty is installed correctly.")

    def auto_press_one(self):
        """Auto-press 1 to select first option in Claude menu."""
        if self.running:
            self.write_to_pty("1")

    def read_pty(self):
        """Read output from PTY in background thread."""
        import time
        while self.running and self.pty_process:
            try:
                data = self.pty_process.read()
                if data:
                    self.data_ready.emit(data)
                time.sleep(0.005)
            except Exception:
                if self.running:
                    self.data_ready.emit("\n[Session ended]\n")
                break

    def process_output(self, data: str):
        self.stream.feed(data)
        self.render_screen()

    def _on_scroll(self, value):
        """Track if user is scrolling manually."""
        scrollbar = self.verticalScrollBar()
        self._user_scrolling = value < scrollbar.maximum() - 10

    def render_screen(self):
        lines = []

        # Add history lines (scrolled up content)
        for hist_line in self.screen.history.top:
            line = "".join(char.data or " " for char in hist_line.values())
            lines.append(line.rstrip())

        # Add current screen lines
        for y in range(self.screen.lines):
            line = "".join(self.screen.buffer[y][x].data or " " for x in range(self.screen.columns))
            lines.append(line.rstrip())

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        new_text = "\n".join(lines)

        # Only update if content changed
        if new_text != self._last_text:
            self._last_text = new_text
            self.blockSignals(True)
            self.setPlainText(new_text)
            self.blockSignals(False)

            # Auto-scroll only if user isn't scrolling up
            if not self._user_scrolling:
                scrollbar = self.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

    def write_to_pty(self, data: str):
        """Write data to PTY."""
        if self.pty_process:
            try:
                self.pty_process.write(data)
            except Exception as e:
                print(f"Write error: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input."""
        key = event.key()
        modifiers = event.modifiers()
        text = event.text()

        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_C:
                self.copy_selection()
                return
            elif key == Qt.Key.Key_V:
                self.paste_clipboard()
                return

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.write_to_pty("\r")
        elif key == Qt.Key.Key_Backspace:
            self.write_to_pty("\x7f")
        elif key == Qt.Key.Key_Tab:
            self.write_to_pty("\t")
        elif key == Qt.Key.Key_Escape:
            self.write_to_pty("\x1b")
        elif key == Qt.Key.Key_Up:
            self.write_to_pty("\x1b[A")
        elif key == Qt.Key.Key_Down:
            self.write_to_pty("\x1b[B")
        elif key == Qt.Key.Key_Right:
            self.write_to_pty("\x1b[C")
        elif key == Qt.Key.Key_Left:
            self.write_to_pty("\x1b[D")
        elif key == Qt.Key.Key_Home:
            self.write_to_pty("\x1b[H")
        elif key == Qt.Key.Key_End:
            self.write_to_pty("\x1b[F")
        elif key == Qt.Key.Key_Delete:
            self.write_to_pty("\x1b[3~")
        elif key == Qt.Key.Key_PageUp:
            self.write_to_pty("\x1b[5~")
        elif key == Qt.Key.Key_PageDown:
            self.write_to_pty("\x1b[6~")
        elif modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_C:
                self.write_to_pty("\x03")
            elif key == Qt.Key.Key_D:
                self.write_to_pty("\x04")
            elif key == Qt.Key.Key_Z:
                self.write_to_pty("\x1a")
            elif key == Qt.Key.Key_L:
                self.write_to_pty("\x0c")
            elif key >= Qt.Key.Key_A and key <= Qt.Key.Key_Z:
                self.write_to_pty(chr(key - Qt.Key.Key_A + 1))
        elif text:
            self.write_to_pty(text)

    def resizeEvent(self, event):
        """Handle resize - update PTY size."""
        super().resizeEvent(event)
        if self.pty_process:
            font_metrics = self.fontMetrics()
            char_width = font_metrics.averageCharWidth()
            char_height = font_metrics.height()

            cols = max(80, self.viewport().width() // char_width)
            rows = max(24, self.viewport().height() // char_height)

            try:
                self.pty_process.set_size(cols, rows)
                self.screen.resize(rows, cols)
            except:
                pass

    def show_context_menu(self, pos):
        """Show context menu with copy/paste options."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['bg_hover']};
            }}
        """)

        copy_action = menu.addAction("Copy (Ctrl+Shift+C)")
        copy_action.triggered.connect(self.copy_selection)

        paste_action = menu.addAction("Paste (Ctrl+Shift+V)")
        paste_action.triggered.connect(self.paste_clipboard)

        menu.addSeparator()

        select_all_action = menu.addAction("Select All (Ctrl+A)")
        select_all_action.triggered.connect(self.selectAll)

        menu.exec(self.mapToGlobal(pos))

    def copy_selection(self):
        """Copy selected text to clipboard."""
        text = self.textCursor().selectedText()
        if text:
            text = text.replace('\u2029', '\n')
            QApplication.clipboard().setText(text)

    def paste_clipboard(self):
        """Paste clipboard content to terminal."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.write_to_pty(text)

    def cleanup(self):
        """Clean up resources."""
        self.running = False
        if self.pty_process:
            try:
                self.pty_process.close()
            except:
                pass
