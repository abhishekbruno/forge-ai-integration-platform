"""Headless UI smoke tests for PySide6 application."""

import pytest
from PySide6.QtWidgets import QApplication

from forge.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["forge_test"])
    return app


def test_ui_instantiation_and_navigation(qapp, temp_workspace):
    win = MainWindow(workspace_path=temp_workspace)
    assert win is not None
    assert win.current_workspace == temp_workspace

    # Switch across all 11 views
    views = [
        "dashboard",
        "projects",
        "manifest_studio",
        "adapters",
        "tool_explorer",
        "builds",
        "test_lab",
        "approvals",
        "audits",
        "packages",
        "settings",
    ]
    for v in views:
        win.switch_view(v)
        assert win.stack.currentWidget() == win.view_map[v]

    # Theme toggle
    win.toggle_theme()
    assert win.current_theme == "light"
    win.toggle_theme()
    assert win.current_theme == "dark"

    win.close()
    win.deleteLater()
    qapp.processEvents()
