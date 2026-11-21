"""Monospaced code/YAML editor with validation highlighting."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget


class CodeEditorWidget(QWidget):
    """Monospaced text editor for manifests, client configs, and schemas."""

    def __init__(self, text: str = "", read_only: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QPlainTextEdit(text)
        font = QFont("Consolas" if font_exists("Consolas") else "Courier New")
        font.setPointSize(10)
        self.editor.setFont(font)
        self.editor.setReadOnly(read_only)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(self.editor)

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def get_text(self) -> str:
        return self.editor.toPlainText()


def font_exists(name: str) -> bool:
    from PySide6.QtGui import QFontDatabase

    return name in QFontDatabase.families()
