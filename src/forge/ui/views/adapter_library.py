"""Adapter library view displaying registered adapters and supported capabilities."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.adapters.registry import get_adapter_registry
from forge.ui.widgets.json_viewer import JsonViewerWidget


class AdapterLibraryView(QWidget):
    """Inspects installed application adapters and their exposed handlers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reg = get_adapter_registry()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Adapter Library")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        splitter = QSplitter()

        # Left side: Adapter list & capabilities
        left_box = QGroupBox("Available Adapters")
        left_l = QVBoxLayout(left_box)

        self.adapter_table = QTableWidget(0, 4)
        self.adapter_table.setHorizontalHeaderLabels(["Adapter ID", "Version", "App", "Status"])
        self.adapter_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.adapter_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.adapter_table.itemSelectionChanged.connect(self._on_adapter_selected)
        left_l.addWidget(self.adapter_table)

        left_l.addWidget(QLabel("<b>Capabilities provided by selected adapter:</b>"))
        self.cap_table = QTableWidget(0, 4)
        self.cap_table.setHorizontalHeaderLabels(["Name", "Risk", "Timeout", "Description"])
        self.cap_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.cap_table.itemSelectionChanged.connect(self._on_cap_selected)
        left_l.addWidget(self.cap_table)

        splitter.addWidget(left_box)

        # Right side: Schema Inspector
        right_box = QGroupBox("Capability Schemas (Draft 2020-12)")
        right_l = QVBoxLayout(right_box)
        self.json_viewer = JsonViewerWidget()
        right_l.addWidget(self.json_viewer)
        splitter.addWidget(right_box)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self):
        adapters = self.reg.list_adapters()
        self.adapter_table.setRowCount(len(adapters))
        for i, a in enumerate(adapters):
            det = a.detect_application()
            self.adapter_table.setItem(i, 0, QTableWidgetItem(a.id))
            self.adapter_table.setItem(i, 1, QTableWidgetItem(a.version))
            self.adapter_table.setItem(i, 2, QTableWidgetItem(a.supported_app_id))
            self.adapter_table.setItem(i, 3, QTableWidgetItem(det.get("status", "unknown")))

        if adapters:
            self.adapter_table.selectRow(0)

    def _on_adapter_selected(self):
        row = self.adapter_table.currentRow()
        if row < 0:
            return
        adapter_id = self.adapter_table.item(row, 0).text()
        adapter = self.reg.get_adapter(adapter_id)
        caps = adapter.list_capabilities()

        self._current_caps = caps
        self.cap_table.setRowCount(len(caps))
        for i, c in enumerate(caps):
            self.cap_table.setItem(i, 0, QTableWidgetItem(c.name))
            self.cap_table.setItem(i, 1, QTableWidgetItem(c.risk.value))
            self.cap_table.setItem(i, 2, QTableWidgetItem(str(c.timeout_seconds)))
            self.cap_table.setItem(i, 3, QTableWidgetItem(c.description))

        if caps:
            self.cap_table.selectRow(0)

    def _on_cap_selected(self):
        row = self.cap_table.currentRow()
        if row < 0 or not hasattr(self, "_current_caps"):
            return
        cap = self._current_caps[row]
        self.json_viewer.set_data(
            {
                "name": cap.name,
                "handler": cap.handler,
                "risk": cap.risk.value,
                "timeout_seconds": cap.timeout_seconds,
                "input_schema": cap.input_schema,
                "output_schema": cap.output_schema,
            }
        )
