"""Side-by-side or colored diff viewer for connector regeneration."""

from __future__ import annotations

import difflib

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class DiffViewerWidget(QWidget):
    """Displays colored unified diff between original and regenerated text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.text_edit)

    def show_diff(
        self, old_text: str, new_text: str, from_file: str = "old", to_file: str = "new"
    ) -> None:
        diff_lines = list(
            difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=from_file,
                tofile=to_file,
            )
        )
        if not diff_lines:
            self.text_edit.setHtml("<span style='color: #888899;'>No differences detected.</span>")
            return

        html_parts = []
        for line in diff_lines:
            escaped = (
                line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").rstrip("\n")
            )
            if line.startswith("+"):
                html_parts.append(
                    f"<div style='color: #48bb78; background-color: #102816;'>{escaped}</div>"
                )
            elif line.startswith("-"):
                html_parts.append(
                    f"<div style='color: #f56565; background-color: #301010;'>{escaped}</div>"
                )
            elif line.startswith("@"):
                html_parts.append(
                    f"<div style='color: #63b3ed; background-color: #1a2438;'>{escaped}</div>"
                )
            else:
                html_parts.append(f"<div style='color: #a0a0b0;'>{escaped}</div>")

        self.text_edit.setHtml("".join(html_parts))
