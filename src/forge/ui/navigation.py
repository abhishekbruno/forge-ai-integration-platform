"""Navigation sidebar widget for switching between application views."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NavigationSidebar(QWidget):
    """Left sidebar containing application view buttons."""

    view_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #17171e; border-right: 1px solid #2b2b38;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(6)

        # Brand header
        brand = QLabel("FORGE")
        brand.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #7aa2f7; padding-bottom: 2px;"
        )
        tagline = QLabel("Integration Platform")
        tagline.setStyleSheet("font-size: 11px; color: #707088; padding-bottom: 14px;")
        layout.addWidget(brand)
        layout.addWidget(tagline)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.nav_items = [
            ("dashboard", "Dashboard"),
            ("projects", "Projects"),
            ("manifest_studio", "Manifest Studio"),
            ("adapters", "Adapter Library"),
            ("tool_explorer", "Tool Explorer"),
            ("builds", "Builds & Generator"),
            ("test_lab", "Test Lab"),
            ("approvals", "Approvals"),
            ("audits", "Audit Viewer"),
            ("packages", "Packages"),
            ("settings", "Settings"),
        ]

        self.buttons: dict[str, QPushButton] = {}

        for view_id, label in self.nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding: 8px 12px; border: none; border-radius: 5px; "
                "background: transparent; color: #a0a0b8; font-weight: 500; } "
                "QPushButton:hover { background: #22222d; color: #ffffff; } "
                "QPushButton:checked { background: #282c3c; color: #7aa2f7; font-weight: bold; border-left: 3px solid #7aa2f7; }"
            )
            btn.clicked.connect(lambda checked, vid=view_id: self.view_changed.emit(vid))
            self.button_group.addButton(btn)
            self.buttons[view_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Version label
        ver_label = QLabel("v0.1.0 • Local Engine")
        ver_label.setStyleSheet("color: #555566; font-size: 10px; padding: 4px;")
        layout.addWidget(ver_label)

    def select_view(self, view_id: str) -> None:
        if view_id in self.buttons:
            self.buttons[view_id].setChecked(True)
