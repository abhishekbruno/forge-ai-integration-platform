"""Application bootstrap and GUI main entrypoint."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from forge.persistence.migrations import apply_migrations
from forge.ui.main_window import MainWindow


def main():
    """Start the FORGE Desktop application."""
    apply_migrations()
    app = QApplication(sys.argv)
    app.setApplicationName("FORGE")
    app.setOrganizationName("FORGE Platform")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
