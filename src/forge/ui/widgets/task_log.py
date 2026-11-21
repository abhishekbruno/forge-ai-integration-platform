"""Task and execution log output widget with auto-scroll and filtering."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class TaskLogWidget(QWidget):
    """Displays append-only chronological execution logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bar = QHBoxLayout()
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear)
        bar.addStretch()
        bar.addWidget(clear_btn)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 11px; background-color: #121216; color: #c0c0d0;"
        )

        layout.addLayout(bar)
        layout.addWidget(self.log_box)

    def append_log(self, text: str, level: str = "INFO") -> None:
        now = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": "#7aa2f7",
            "WARN": "#e0af68",
            "ERROR": "#f7768e",
            "SUCCESS": "#9ece6a",
        }.get(level.upper(), "#a0a0b0")

        msg_html = f"<span style='color: #555566;'>[{now}]</span> <b style='color: {color};'>[{level.upper()}]</b> {text}<br>"
        self.log_box.insertHtml(msg_html)
        self.log_box.ensureCursorVisible()

    def clear(self) -> None:
        self.log_box.clear()
