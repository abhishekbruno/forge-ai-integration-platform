"""Audit journal viewer with cryptographic verification and event filtering."""

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


class AuditsView(QWidget):
    """Browses append-only audit records and verifies hash-chain integrity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_bar = QHBoxLayout()
        header = QLabel("Audit Journal & Evidence")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        verify_btn = QPushButton("Verify Cryptographic Integrity")
        verify_btn.setObjectName("PrimaryButton")
        verify_btn.clicked.connect(self._verify_chain)
        header_bar.addWidget(verify_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_bar.addWidget(refresh_btn)
        layout.addLayout(header_bar)

        splitter = QSplitter()

        # Left: Events Table
        left_box = QGroupBox("Append-Only Event Stream")
        left_l = QVBoxLayout(left_box)

        self.events_table = QTableWidget(0, 5)
        self.events_table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Action", "Target", "Outcome"]
        )
        self.events_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events_table.itemSelectionChanged.connect(self._on_event_selected)
        left_l.addWidget(self.events_table)
        splitter.addWidget(left_box)

        # Right: Event details & hashes
        right_box = QGroupBox("Event Details & Cryptographic Chain")
        right_l = QVBoxLayout(right_box)
        self.details_viewer = JsonViewerWidget()
        right_l.addWidget(self.details_viewer)
        splitter.addWidget(right_box)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self):
        events = self.svc.audit_journal.list_events(limit=100)
        self._current_events = events
        self.events_table.setRowCount(len(events))

        for i, e in enumerate(events):
            self.events_table.setItem(i, 0, QTableWidgetItem(str(e.id)))
            self.events_table.setItem(i, 1, QTableWidgetItem(e.timestamp[:19]))
            self.events_table.setItem(i, 2, QTableWidgetItem(e.action))
            self.events_table.setItem(i, 3, QTableWidgetItem(e.target))
            self.events_table.setItem(i, 4, QTableWidgetItem(e.outcome))

        if events:
            self.events_table.selectRow(0)

    def _on_event_selected(self):
        row = self.events_table.currentRow()
        if row < 0 or not hasattr(self, "_current_events") or not self._current_events:
            return
        event = self._current_events[row]
        self.details_viewer.set_data(event.model_dump())

    def _verify_chain(self):
        is_valid, msg, broken_id = self.svc.verify_audit_integrity()
        if is_valid:
            QMessageBox.information(
                self, "Integrity Verified", f"Cryptographic audit chain is VALID:\n{msg}"
            )
        else:
            QMessageBox.critical(
                self,
                "Integrity Violation",
                f"TAMPERING DETECTED at event record {broken_id}!\n{msg}",
            )
