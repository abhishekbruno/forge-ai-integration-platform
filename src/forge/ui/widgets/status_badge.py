"""Reusable status badges for risks, test states, and approvals."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    """Visual rounded pill badge."""

    def __init__(self, text: str, badge_type: str = "info", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_badge_type(badge_type)

    def set_badge_type(self, badge_type: str) -> None:
        color_map = {
            "read": ("#103820", "#48bb78", "#1c5b34"),
            "write": ("#3d3000", "#ecc94b", "#685200"),
            "destructive": ("#441515", "#f56565", "#702020"),
            "external": ("#2b1845", "#b794f4", "#4a2b75"),
            "passed": ("#103820", "#48bb78", "#1c5b34"),
            "failed": ("#441515", "#f56565", "#702020"),
            "skipped": ("#3d3000", "#ecc94b", "#685200"),
            "running": ("#1a2a47", "#63b3ed", "#2a4365"),
            "info": ("#1f2430", "#a0aec0", "#2d3748"),
        }
        bg, fg, border = color_map.get(badge_type.lower(), ("#1f2430", "#a0aec0", "#2d3748"))
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {border}; "
            f"border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;"
        )
