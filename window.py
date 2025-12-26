"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QRectF, pyqtSlot, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath

from theme import COLORS, toggle_theme, get_theme
from terminal import TerminalWidget
from widgets import TitleBar, StatusBar
from voice import VoiceRecognizer
from translator import get_translator


class ClaudeWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.session_counter = 0
        self.tab_buttons: list[QPushButton] = []
        self.terminals: list[TerminalWidget] = []
        self.current_tab_index = -1

        self.setup_window()
        self.setup_ui()
        self.setup_voice()
        self.create_session()

    def setup_window(self):
        self.setWindowTitle("Claude")
        self.setMinimumSize(700, 500)
        self.resize(1200, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("central")
        central.setStyleSheet(f"#central {{ background-color: {COLORS['bg_primary']}; border-radius: 10px; }}")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self)
        self.title_bar.new_tab_btn.clicked.connect(self.create_session)
        layout.addWidget(self.title_bar)

        # Content area
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout.addWidget(self.stack)

        # Border line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(line)

        # Status bar
        self.status_bar = StatusBar()
        layout.addWidget(self.status_bar)

    def setup_voice(self):
        """Set up voice recognition and translation."""
        self.voice_recognizer = VoiceRecognizer(model_name="v3_ctc")
        self.voice_recognizer.set_callbacks(
            on_result=self._on_voice_result,
            on_status=self._on_voice_status
        )
        self.status_bar.mic_clicked.connect(self._toggle_voice_recording)
        self.status_bar.theme_clicked.connect(self._toggle_theme)

        # Set up translator
        self.translator = get_translator()
        self.translator.set_status_callback(self._on_voice_status)

    @pyqtSlot()
    def _toggle_voice_recording(self):
        """Toggle voice recording on/off."""
        is_recording = self.voice_recognizer.toggle_recording()
        self.status_bar.set_recording(is_recording)

    @pyqtSlot()
    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        new_theme = toggle_theme()
        self.status_bar.update_theme_icon(new_theme)
        self._apply_theme()
        self.status_bar.set_status(f"Theme: {new_theme}")

    def _apply_theme(self):
        """Apply current theme to all widgets."""
        # Central widget
        central = self.centralWidget()
        central.setStyleSheet(f"#central {{ background-color: {COLORS['bg_primary']}; border-radius: 10px; }}")

        # Stack
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        # Title bar
        self.title_bar.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        # Status bar
        self.status_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")
        self.status_bar.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self.status_bar._update_mic_style()
        self.status_bar._update_theme_btn_style()

        # Terminals
        for terminal in self.terminals:
            terminal.setStyleSheet(f"""
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
            """)

        # Tab buttons
        for i, btn in enumerate(self.tab_buttons):
            self.update_tab_style(btn, i == self.current_tab_index)

        # Force repaint
        self.update()

    def _on_voice_result(self, text: str):
        """Handle transcription result - translate, insert into terminal, and send."""
        if text and 0 <= self.current_tab_index < len(self.terminals):
            terminal = self.terminals[self.current_tab_index]
            # Translate Russian to English
            self._on_voice_status("Translating...")
            translated = self.translator.translate(text)
            output = translated if translated else text
            terminal.write_to_pty(output)
            # Auto-press Enter after small delay
            QTimer.singleShot(100, lambda: terminal.write_to_pty("\r"))
            self._on_voice_status(f"Sent: {output[:40]}...")
        self.status_bar.set_recording(False)

    def _on_voice_status(self, status: str):
        """Handle voice status updates."""
        self.status_bar.set_status(status)

    def create_session(self):
        """Create a new terminal session."""
        self.session_counter += 1
        terminal = TerminalWidget()
        self.terminals.append(terminal)
        self.stack.addWidget(terminal)

        # Create tab button
        tab_btn = QPushButton(f"Claude {self.session_counter}")
        tab_btn.setCheckable(True)
        tab_index = len(self.tab_buttons)
        tab_btn.clicked.connect(lambda checked, idx=tab_index: self.switch_tab(idx))
        self.update_tab_style(tab_btn, False)
        self.tab_buttons.append(tab_btn)
        self.title_bar.tab_layout.addWidget(tab_btn)

        self.switch_tab(tab_index)
        self.status_bar.set_status(f"Created: Claude {self.session_counter}")
        terminal.setFocus()

    def switch_tab(self, index: int):
        """Switch to a specific tab."""
        if 0 <= index < len(self.terminals):
            self.current_tab_index = index
            self.stack.setCurrentIndex(index)
            for i, btn in enumerate(self.tab_buttons):
                self.update_tab_style(btn, i == index)
                btn.setChecked(i == index)
            self.terminals[index].setFocus()

    def update_tab_style(self, btn: QPushButton, selected: bool):
        """Update tab button style."""
        if selected:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_muted']};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    color: {COLORS['text_secondary']};
                }}
            """)

    def close_session(self, index: int = None):
        """Close a terminal session."""
        if index is None:
            index = self.current_tab_index
        if len(self.terminals) > 1 and 0 <= index < len(self.terminals):
            terminal = self.terminals[index]
            terminal.cleanup()
            self.stack.removeWidget(terminal)
            self.terminals.pop(index)

            btn = self.tab_buttons.pop(index)
            self.title_bar.tab_layout.removeWidget(btn)
            btn.deleteLater()

            for i, b in enumerate(self.tab_buttons):
                b.clicked.disconnect()
                b.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))

            new_index = min(index, len(self.terminals) - 1)
            self.switch_tab(new_index)
            self.status_bar.set_status("Session closed")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        modifiers = event.modifiers()
        key = event.key()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_T:
                self.create_session()
                return
            elif key == Qt.Key.Key_W:
                self.close_session()
                return
        elif modifiers == Qt.KeyboardModifier.AltModifier:
            if key == Qt.Key.Key_T:
                self._toggle_voice_recording()
                return
        elif modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_Q:
                self.close()
                return

        if 0 <= self.current_tab_index < len(self.terminals):
            self.terminals[self.current_tab_index].keyPressEvent(event)

    def closeEvent(self, event):
        """Clean up on close."""
        for terminal in self.terminals:
            terminal.cleanup()
        event.accept()

    def paintEvent(self, event):
        """Paint rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 10.0, 10.0)
        painter.fillPath(path, QColor(COLORS['bg_primary']))
