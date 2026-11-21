"""Approvals broker view for inspecting and granting human authorization."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService
from forge.ui.widgets.json_viewer import JsonViewerWidget


class ApprovalsView(QWidget):
    """Human-in-the-loop approval broker interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_bar = QHBoxLayout()
        header = QLabel("Approvals Broker")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_bar.addWidget(refresh_btn)
        layout.addLayout(header_bar)

        splitter = QSplitter()

        # Left: Pending Requests
        left_box = QGroupBox("Pending Approval Requests")
        left_l = QVBoxLayout(left_box)

        self.pending_table = QTableWidget(0, 4)
        self.pending_table.setHorizontalHeaderLabels(
            ["Request ID", "Tool", "Arg Hash", "Requested At"]
        )
        self.pending_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.pending_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pending_table.itemSelectionChanged.connect(self._on_request_selected)
        left_l.addWidget(self.pending_table)

        btn_bar = QHBoxLayout()
        self.approve_btn = QPushButton("Approve Once")
        self.approve_btn.setObjectName("PrimaryButton")
        self.approve_btn.clicked.connect(self._approve_selected)

        self.deny_btn = QPushButton("Deny")
        self.deny_btn.setObjectName("DangerButton")
        self.deny_btn.clicked.connect(self._deny_selected)

        btn_bar.addWidget(self.approve_btn)
        btn_bar.addWidget(self.deny_btn)
        btn_bar.addStretch()
        left_l.addLayout(btn_bar)

        splitter.addWidget(left_box)

        # Right: Request Details & Recent Grants
        right_box = QGroupBox("Proposed Arguments & Side Effects")
        right_l = QVBoxLayout(right_box)
        self.details_viewer = JsonViewerWidget()
        right_l.addWidget(self.details_viewer)

        right_l.addWidget(QLabel("<b>Recent Grants History:</b>"))
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Tool", "Arg Hash", "Consumed"])
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        right_l.addWidget(self.history_table)

        splitter.addWidget(right_box)
        splitter.setSizes([550, 450])
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self):
        pending = self.svc.list_pending_approvals()
        self._current_pending = pending
        self.pending_table.setRowCount(len(pending))

        for i, req in enumerate(pending):
            self.pending_table.setItem(i, 0, QTableWidgetItem(req["request_id"][:8]))
            self.pending_table.setItem(i, 1, QTableWidgetItem(req["tool_name"]))
            self.pending_table.setItem(i, 2, QTableWidgetItem(req["argument_hash"][:12]))
            self.pending_table.setItem(i, 3, QTableWidgetItem(req["created_at"][:19]))

        if pending:
            self.pending_table.selectRow(0)
        else:
            self.details_viewer.set_data({"message": "No pending approval requests."})

        # History
        recent = self.svc.approval_repo.list_recent(limit=15)
        self.history_table.setRowCount(len(recent))
        for i, g in enumerate(recent):
            self.history_table.setItem(i, 0, QTableWidgetItem(g.tool_name))
            self.history_table.setItem(i, 1, QTableWidgetItem(g.argument_hash[:12]))
            self.history_table.setItem(i, 2, QTableWidgetItem("YES" if g.consumed else "NO"))

    def _on_request_selected(self):
        row = self.pending_table.currentRow()
        if row < 0 or not hasattr(self, "_current_pending") or not self._current_pending:
            return
        req = self._current_pending[row]
        self.details_viewer.set_data(req)

    def _approve_selected(self):
        row = self.pending_table.currentRow()
        if row < 0 or not hasattr(self, "_current_pending") or not self._current_pending:
            return

        req = self._current_pending[row]
        self.svc.grant_approval(
            tool_name=req["tool_name"],
            argument_hash=req["argument_hash"],
            correlation_id=req["correlation_id"],
            ttl_seconds=300,
            actor="gui_operator",
        )
        QMessageBox.information(
            self, "Granted", f"Approval granted for '{req['tool_name']}' (single-use, 300s TTL)."
        )
        self.refresh()

    def _deny_selected(self):
        row = self.pending_table.currentRow()
        if row < 0 or not hasattr(self, "_current_pending") or not self._current_pending:
            return

        req = self._current_pending[row]
        self.svc.approval_broker.deny_request(req["request_id"])
        QMessageBox.information(self, "Denied", f"Request for '{req['tool_name']}' was denied.")
        self.refresh()
