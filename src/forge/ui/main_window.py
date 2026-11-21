"""Main Application Window for FORGE Desktop GUI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService
from forge.ui.navigation import NavigationSidebar
from forge.ui.theme import DARK_THEME_QSS, LIGHT_THEME_QSS
from forge.ui.views.adapter_library import AdapterLibraryView
from forge.ui.views.approvals import ApprovalsView
from forge.ui.views.audits import AuditsView
from forge.ui.views.dashboard import DashboardView
from forge.ui.views.manifest_studio import ManifestStudioView
from forge.ui.views.packages import PackagesView
from forge.ui.views.projects import ProjectsView
from forge.ui.views.runs import BuildsView
from forge.ui.views.settings import SettingsView
from forge.ui.views.test_lab import TestLabView
from forge.ui.views.tool_explorer import ToolExplorerView
from forge.ui.widgets.status_badge import StatusBadge


class MainWindow(QMainWindow):
    """The central application window connecting all views and services."""

    def __init__(self, workspace_path: Path | None = None):
        super().__init__()
        self.setWindowTitle("FORGE — Integration Development Platform")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)

        self.current_theme = "dark"
        self.setStyleSheet(DARK_THEME_QSS)

        self.svc = ApplicationService()
        self.current_workspace = Path(workspace_path or ".").resolve()

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Toolbar
        top_bar = QWidget()
        top_bar.setStyleSheet(
            "background-color: #17171e; border-bottom: 1px solid #2b2b38; padding: 6px 16px;"
        )
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 6, 10, 6)

        ws_title = QLabel("Workspace:")
        ws_title.setStyleSheet("color: #707088; font-weight: bold;")
        self.ws_label = QLabel(self.current_workspace.name)
        self.ws_label.setStyleSheet("color: #7aa2f7; font-weight: bold; font-size: 14px;")

        switch_btn = QPushButton("Switch...")
        switch_btn.clicked.connect(self._choose_workspace)

        theme_btn = QPushButton("Theme")
        theme_btn.clicked.connect(self.toggle_theme)

        top_layout.addWidget(ws_title)
        top_layout.addWidget(self.ws_label)
        top_layout.addWidget(switch_btn)
        top_layout.addStretch()
        top_layout.addWidget(theme_btn)

        main_layout.addWidget(top_bar)

        # Body: Sidebar + Stacked Widget
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = NavigationSidebar()
        self.sidebar.view_changed.connect(self.switch_view)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()

        # Instantiate Views
        self.dashboard_view = DashboardView()
        self.dashboard_view.navigate_requested.connect(self.switch_view)

        self.projects_view = ProjectsView()
        self.projects_view.project_selected.connect(self.set_workspace)

        self.manifest_view = ManifestStudioView()
        self.adapters_view = AdapterLibraryView()
        self.tools_view = ToolExplorerView()
        self.builds_view = BuildsView()
        self.test_view = TestLabView()
        self.approvals_view = ApprovalsView()
        self.audits_view = AuditsView()
        self.packages_view = PackagesView()
        self.settings_view = SettingsView(theme_toggle_callback=self.toggle_theme)

        self.view_map = {
            "dashboard": self.dashboard_view,
            "projects": self.projects_view,
            "manifest_studio": self.manifest_view,
            "adapters": self.adapters_view,
            "tool_explorer": self.tools_view,
            "builds": self.builds_view,
            "test_lab": self.test_view,
            "approvals": self.approvals_view,
            "audits": self.audits_view,
            "packages": self.packages_view,
            "settings": self.settings_view,
        }

        for v in self.view_map.values():
            self.stack.addWidget(v)

        body_layout.addWidget(self.stack)
        main_layout.addWidget(body_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. System initialized.")

        self.status_badge = StatusBadge("READY", "passed")
        self.status_bar.addPermanentWidget(self.status_badge)

        self.sidebar.select_view("dashboard")
        self.switch_view("dashboard")

    def switch_view(self, view_id: str) -> None:
        if view_id in self.view_map:
            target_widget = self.view_map[view_id]
            self.stack.setCurrentWidget(target_widget)
            self.sidebar.select_view(view_id)
            if hasattr(target_widget, "refresh"):
                target_widget.refresh()

    def set_workspace(self, workspace_path: Path) -> None:
        self.current_workspace = Path(workspace_path).resolve()
        self.ws_label.setText(self.current_workspace.name)

        # Propagate to views
        for v in self.view_map.values():
            if hasattr(v, "set_workspace"):
                v.set_workspace(self.current_workspace)

        self.status_bar.showMessage(f"Active workspace: {self.current_workspace}")

    def _choose_workspace(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Workspace Folder", str(self.current_workspace)
        )
        if chosen:
            self.set_workspace(Path(chosen))

    def toggle_theme(self) -> None:
        if self.current_theme == "dark":
            self.setStyleSheet(LIGHT_THEME_QSS)
            self.current_theme = "light"
        else:
            self.setStyleSheet(DARK_THEME_QSS)
            self.current_theme = "dark"
