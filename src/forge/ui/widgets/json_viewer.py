"""Formatted JSON viewer widget with copy capabilities."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class JsonViewerWidget(QWidget):
    """Displays formatted, syntax-readable JSON structures."""

    def __init__(self, data: Any = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        copy_btn = QPushButton("Copy JSON")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        top_bar.addWidget(copy_btn)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")

        layout.addLayout(top_bar)
        layout.addWidget(self.text_edit)

        if data is not None:
            self.set_data(data)

    def set_data(self, data: Any) -> None:
        self._raw_data = data
        try:
            formatted = json.dumps(data, indent=2, sort_keys=True)
        except Exception:
            formatted = str(data)
        self.text_edit.setPlainText(formatted)

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self.text_edit.toPlainText())
