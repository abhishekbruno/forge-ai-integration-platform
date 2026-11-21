"""Tool Explorer view for inspecting and executing tools through the policy gateway."""

from __future__ import annotations

import json
from pathlib import Path

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService
from forge.domain.errors import ApprovalRequiredError
from forge.ui.widgets.json_viewer import JsonViewerWidget


class ToolExplorerView(QWidget):
    """Enables testing tool execution through the secure gateway."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.current_workspace = Path(".").resolve()
        self._current_manifest = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Tool Explorer")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        splitter = QSplitter()

        # Left: Tools Table
        left_box = QGroupBox("Available Tools in Active Manifest")
        left_l = QVBoxLayout(left_box)

        self.tools_table = QTableWidget(0, 3)
        self.tools_table.setHorizontalHeaderLabels(["Tool Name", "Risk", "Description"])
        self.tools_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tools_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tools_table.itemSelectionChanged.connect(self._on_tool_selected)
        left_l.addWidget(self.tools_table)
        splitter.addWidget(left_box)

        # Right: Invocation & Results
        right_box = QGroupBox("Invocation & Results")
        right_l = QVBoxLayout(right_box)

        right_l.addWidget(QLabel("<b>Input Arguments (JSON):</b>"))
        self.args_edit = QTextEdit()
        self.args_edit.setPlainText("{}")
        self.args_edit.setMaximumHeight(150)
        self.args_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        right_l.addWidget(self.args_edit)

        exec_btn_bar = QHBoxLayout()
        self.exec_btn = QPushButton("Execute Tool via Gateway")
        self.exec_btn.setObjectName("PrimaryButton")
        self.exec_btn.clicked.connect(self._execute_tool)
        exec_btn_bar.addWidget(self.exec_btn)
        exec_btn_bar.addStretch()
        right_l.addLayout(exec_btn_bar)

        right_l.addWidget(QLabel("<b>Execution Result / Error:</b>"))
        self.result_viewer = JsonViewerWidget()
        right_l.addWidget(self.result_viewer)

        splitter.addWidget(right_box)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

        self.refresh()

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()
        self.refresh()

    def refresh(self):
        manifest_file = self.current_workspace / "manifest.yaml"
        if not manifest_file.is_file():
            self.tools_table.setRowCount(0)
            return

        try:
            self._current_manifest = self.svc.validate_manifest(manifest_file)
            caps = self._current_manifest.capabilities
            self.tools_table.setRowCount(len(caps))
            for i, c in enumerate(caps):
                self.tools_table.setItem(i, 0, QTableWidgetItem(c.name))
                self.tools_table.setItem(i, 1, QTableWidgetItem(c.risk.value))
                self.tools_table.setItem(i, 2, QTableWidgetItem(c.description))

            if caps:
                self.tools_table.selectRow(0)
        except Exception:
            self.tools_table.setRowCount(0)

    def _on_tool_selected(self):
        row = self.tools_table.currentRow()
        if row < 0 or not self._current_manifest:
            return

        tool_name = self.tools_table.item(row, 0).text()
        cap = self._current_manifest.get_capability(tool_name)
        if cap:
            # Provide sample JSON from input schema properties
            sample_args = {}
            props = cap.input_schema.get("properties", {})
            for p_name, p_def in props.items():
                if "default" in p_def:
                    sample_args[p_name] = p_def["default"]
                elif p_def.get("type") == "string":
                    sample_args[p_name] = "sample"
                elif p_def.get("type") == "integer":
                    sample_args[p_name] = 1
                elif p_def.get("type") == "boolean":
                    sample_args[p_name] = True
                elif p_def.get("type") == "array":
                    sample_args[p_name] = []
                else:
                    sample_args[p_name] = None
            self.args_edit.setPlainText(json.dumps(sample_args, indent=2))

    def _execute_tool(self):
        row = self.tools_table.currentRow()
        if row < 0 or not self._current_manifest:
            return

        tool_name = self.tools_table.item(row, 0).text()
        try:
            args = json.loads(self.args_edit.toPlainText())
        except Exception as exc:
            QMessageBox.critical(self, "Invalid JSON", f"Failed to parse arguments JSON: {exc}")
            return

        try:
            result = self.svc.execution_gateway.execute_tool(
                connector_id=self._current_manifest.integration.id,
                manifest=self._current_manifest,
                tool_name=tool_name,
                args=args,
                workspace=self.current_workspace,
                actor="ui_operator",
            )
            self.result_viewer.set_data({"status": "SUCCESS", "result": result})
        except ApprovalRequiredError as exc:
            self.result_viewer.set_data(
                {
                    "status": "APPROVAL_REQUIRED",
                    "error": str(exc),
                    "tool_name": exc.tool_name,
                    "argument_hash": exc.argument_hash,
                    "hint": "Go to the Approvals view to grant permission for this operation.",
                }
            )
            QMessageBox.warning(
                self,
                "Approval Required",
                f"Operation '{tool_name}' requires human approval.\nA request has been submitted to the Approvals view.",
            )
        except Exception as exc:
            self.result_viewer.set_data({"status": "ERROR", "error": str(exc)})
            QMessageBox.critical(self, "Execution Failed", str(exc))
