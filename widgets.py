"""UI widgets for title bar and status bar."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

from theme import COLORS, get_theme


class TitleBar(QWidget):
    """Custom title bar with window controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_position = QPoint()
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(36)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)

        # App label "Claude" with dot
        app_label = QLabel("●  Claude")
        app_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 13px;
            padding-right: 12px;
        """)
        layout.addWidget(app_label)

        # Tab bar container
        self.tab_container = QWidget()
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(4)
        layout.addWidget(self.tab_container)

        layout.addStretch()

        # Control buttons
        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 6px 12px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """

        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setToolTip("New Session (Ctrl+T)")
        self.new_tab_btn.setStyleSheet(btn_style)
        self.new_tab_btn.setFixedSize(36, 36)
        layout.addWidget(self.new_tab_btn)

        # Window controls
        win_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 8px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """

        self.min_btn = QPushButton("—")
        self.min_btn.setStyleSheet(win_btn_style)
        self.min_btn.setFixedSize(46, 36)
        self.min_btn.clicked.connect(lambda: self.parent_window.showMinimized())
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setStyleSheet(win_btn_style)
        self.max_btn.setFixedSize(46, 36)
        self.max_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.max_btn)

        close_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 8px 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['close_hover']};
                color: white;
            }}
        """
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet(close_btn_style)
        self.close_btn.setFixedSize(46, 36)
        self.close_btn.clicked.connect(lambda: self.parent_window.close())
        layout.addWidget(self.close_btn)

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        self.toggle_maximize()


class StatusBar(QWidget):
    """Status bar at the bottom."""

    mic_clicked = pyqtSignal()
    theme_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(26)
        self.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Microphone button
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setToolTip("Voice Input (click to record)")
        self.mic_btn.setFixedSize(24, 20)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        self._update_mic_style()
        layout.addWidget(self.mic_btn)

        # Theme toggle button
        self.theme_btn = QPushButton("🌙" if get_theme() == 'dark' else "☀️")
        self.theme_btn.setToolTip("Toggle theme")
        self.theme_btn.setFixedSize(24, 20)
        self.theme_btn.clicked.connect(self._on_theme_clicked)
        self._update_theme_btn_style()
        layout.addWidget(self.theme_btn)

        self.hints = QLabel("Alt+T voice | Ctrl+T new | Ctrl+W close")
        self.hints.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; margin-left: 10px;")
        layout.addWidget(self.hints)

    def _update_mic_style(self):
        """Update microphone button style based on recording state."""
        if self.is_recording:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #cc4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #dd5555;
                }}
            """)
            self.mic_btn.setToolTip("Recording... (click to stop)")
        else:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_muted']};
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)
            self.mic_btn.setToolTip("Voice Input (click to record)")

    def _update_theme_btn_style(self):
        """Update theme button style."""
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """)

    def _on_mic_clicked(self):
        """Handle microphone button click."""
        self.mic_clicked.emit()

    def _on_theme_clicked(self):
        """Handle theme button click."""
        self.theme_clicked.emit()

    def update_theme_icon(self, theme: str):
        """Update theme button icon."""
        self.theme_btn.setText("🌙" if theme == 'dark' else "☀️")

    def set_recording(self, recording: bool):
        """Set recording state and update UI."""
        self.is_recording = recording
        self._update_mic_style()

    def set_status(self, text: str):
        self.status_label.setText(text)
