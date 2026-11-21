"""Dashboard view summarizing workspace status, adapters, builds, and doctor health."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from forge.adapters.registry import get_adapter_registry
from forge.core.application_service import ApplicationService
from forge.ui.widgets.status_badge import StatusBadge


class DashboardView(QWidget):
    """High-level system and workspace overview."""

    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.current_workspace = Path(".").resolve()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Metrics cards layout
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)

        self.ws_card = self._create_metric_card(
            "Current Workspace", str(self.current_workspace.name), str(self.current_workspace)
        )
        self.build_card = self._create_metric_card("Builds", "0", "Generated connectors")
        self.approval_card = self._create_metric_card(
            "Pending Approvals", "0", "Mutations awaiting review"
        )
        self.health_card = self._create_metric_card(
            "Doctor Status", "Checking...", "System diagnostics"
        )

        metrics_layout.addWidget(self.ws_card)
        metrics_layout.addWidget(self.build_card)
        metrics_layout.addWidget(self.approval_card)
        metrics_layout.addWidget(self.health_card)
        layout.addLayout(metrics_layout)

        # Quick Actions
        actions_box = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_box)
        actions_layout.setSpacing(10)

        btn_manifest = QPushButton("Edit Manifest Studio")
        btn_manifest.clicked.connect(lambda: self.navigate_requested.emit("manifest_studio"))
        btn_build = QPushButton("Generate Connector")
        btn_build.clicked.connect(lambda: self.navigate_requested.emit("builds"))
        btn_test = QPushButton("Run Test Lab")
        btn_test.clicked.connect(lambda: self.navigate_requested.emit("test_lab"))
        btn_approvals = QPushButton("Review Approvals")
        btn_approvals.clicked.connect(lambda: self.navigate_requested.emit("approvals"))

        actions_layout.addWidget(btn_manifest)
        actions_layout.addWidget(btn_build)
        actions_layout.addWidget(btn_test)
        actions_layout.addWidget(btn_approvals)
        layout.addWidget(actions_box)

        # Adapters summary
        adapters_box = QGroupBox("Detected Application Adapters")
        self.adapters_layout = QVBoxLayout(adapters_box)
        layout.addWidget(adapters_box)

        layout.addStretch()
        self.refresh()

    def _create_metric_card(self, title: str, value: str, subtext: str) -> QGroupBox:
        box = QGroupBox()
        box.setStyleSheet(
            "background-color: #21212c; border: 1px solid #303042; border-radius: 6px;"
        )
        card_layout = QVBoxLayout(box)
        card_layout.setContentsMargins(14, 12, 14, 12)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(
            "color: #888899; font-size: 11px; text-transform: uppercase; font-weight: bold;"
        )
        v_lbl = QLabel(value)
        v_lbl.setObjectName("metric_val")
        v_lbl.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; margin: 4px 0;")
        s_lbl = QLabel(subtext)
        s_lbl.setObjectName("metric_sub")
        s_lbl.setStyleSheet("color: #666677; font-size: 11px;")

        card_layout.addWidget(t_lbl)
        card_layout.addWidget(v_lbl)
        card_layout.addWidget(s_lbl)
        return box

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()
        self.refresh()

    def refresh(self) -> None:
        # Update workspace card
        val_lbl = self.ws_card.findChild(QLabel, "metric_val")
        sub_lbl = self.ws_card.findChild(QLabel, "metric_sub")
        if val_lbl and sub_lbl:
            val_lbl.setText(self.current_workspace.name)
            sub_lbl.setText(str(self.current_workspace))

        # Update pending approvals
        pending = self.svc.list_pending_approvals()
        app_val = self.approval_card.findChild(QLabel, "metric_val")
        if app_val:
            app_val.setText(str(len(pending)))

        # Update builds
        proj = self.svc.open_project(self.current_workspace)
        builds = self.svc.build_repo.list_by_project(proj.id)
        b_val = self.build_card.findChild(QLabel, "metric_val")
        if b_val:
            b_val.setText(str(len(builds)))

        # Update Doctor
        rep = self.svc.run_diagnostics(self.current_workspace)
        h_val = self.health_card.findChild(QLabel, "metric_val")
        h_sub = self.health_card.findChild(QLabel, "metric_sub")
        if h_val and h_sub:
            h_val.setText(rep.overall_status.value)
            h_sub.setText("All checks operational" if rep.passed else "Attention required")

        # Update Adapters list
        while self.adapters_layout.count():
            item = self.adapters_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        reg = get_adapter_registry()
        for adapter in reg.list_adapters():
            detection = adapter.detect_application()
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 4, 0, 4)

            name_lbl = QLabel(
                f"<b>{adapter.supported_app_id.upper()}</b> ({adapter.id} v{adapter.version})"
            )
            msg_lbl = QLabel(detection.get("message", ""))
            msg_lbl.setStyleSheet("color: #a0a0b0;")
            badge = StatusBadge(
                detection.get("status", "unknown").upper(),
                "passed" if detection.get("available") else "skipped",
            )

            row_l.addWidget(name_lbl)
            row_l.addWidget(msg_lbl)
            row_l.addStretch()
            row_l.addWidget(badge)
            self.adapters_layout.addWidget(row)
