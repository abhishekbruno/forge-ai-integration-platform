"""Connector Generator and Build management view."""

from __future__ import annotations

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
from forge.ui.widgets.task_log import TaskLogWidget
from forge.ui.workers import GenerateWorker


class BuildsView(QWidget):
    """Generates and inspects MCP connector builds."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.current_workspace = Path(".").resolve()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_bar = QHBoxLayout()
        header = QLabel("Builds & Connector Generator")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        self.gen_btn = QPushButton("Generate Connector from Manifest")
        self.gen_btn.setObjectName("PrimaryButton")
        self.gen_btn.clicked.connect(self._start_generation)
        header_bar.addWidget(self.gen_btn)
        layout.addLayout(header_bar)

        splitter = QSplitter()

        # Left: Builds Table
        left_box = QGroupBox("Generated Connector Builds")
        left_l = QVBoxLayout(left_box)

        self.build_table = QTableWidget(0, 4)
        self.build_table.setHorizontalHeaderLabels(["Build ID", "Version", "Status", "Created At"])
        self.build_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.build_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.build_table.itemSelectionChanged.connect(self._on_build_selected)
        left_l.addWidget(self.build_table)
        splitter.addWidget(left_box)

        # Right: Build Details & Diff
        right_box = QGroupBox("Build Inspector & Generated Files")
        right_l = QVBoxLayout(right_box)

        self.file_table = QTableWidget(0, 2)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Size"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.itemSelectionChanged.connect(self._on_file_selected)
        right_l.addWidget(self.file_table)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        right_l.addWidget(self.file_preview)

        splitter.addWidget(right_box)
        splitter.setSizes([450, 550])
        layout.addWidget(splitter)

        # Task Log
        self.log_widget = TaskLogWidget()
        self.log_widget.setMaximumHeight(150)
        layout.addWidget(self.log_widget)

        self.refresh()

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()
        self.refresh()

    def refresh(self):
        proj = self.svc.open_project(self.current_workspace)
        builds = self.svc.build_repo.list_by_project(proj.id)
        self.build_table.setRowCount(len(builds))
        self._current_builds = builds

        for i, b in enumerate(builds):
            self.build_table.setItem(i, 0, QTableWidgetItem(b.id))
            self.build_table.setItem(i, 1, QTableWidgetItem(b.version))
            self.build_table.setItem(i, 2, QTableWidgetItem(b.status.value))
            self.build_table.setItem(i, 3, QTableWidgetItem(b.created_at[:19]))

        if builds:
            self.build_table.selectRow(0)

    def _start_generation(self):
        manifest_file = self.current_workspace / "manifest.yaml"
        if not manifest_file.is_file():
            QMessageBox.critical(
                self, "Missing Manifest", f"manifest.yaml not found in {self.current_workspace}"
            )
            return

        proj = self.svc.open_project(self.current_workspace)
        self.gen_btn.setEnabled(False)
        self.log_widget.append_log("Starting deterministic connector generation...", "INFO")

        self.worker = GenerateWorker(proj.id, self.current_workspace, manifest_file)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.failed.connect(self._on_generation_failed)
        self.worker.start()

    def _on_generation_finished(self, build):
        self.gen_btn.setEnabled(True)
        self.log_widget.append_log(
            f"Build {build.id[:8]} generated successfully! Source hash: {build.generated_source_hash[:16]}...",
            "SUCCESS",
        )
        self.refresh()

    def _on_generation_failed(self, error):
        self.gen_btn.setEnabled(True)
        self.log_widget.append_log(f"Generation failed: {error}", "ERROR")
        QMessageBox.critical(self, "Build Error", f"Generation failed:\n{error}")

    def _on_build_selected(self):
        row = self.build_table.currentRow()
        if row < 0 or not hasattr(self, "_current_builds"):
            return

        build = self._current_builds[row]
        b_dir = Path(build.build_dir)
        files = list(b_dir.glob("*")) if b_dir.is_dir() else []
        self._current_files = files

        self.file_table.setRowCount(len(files))
        for i, f in enumerate(files):
            self.file_table.setItem(i, 0, QTableWidgetItem(f.name))
            self.file_table.setItem(i, 1, QTableWidgetItem(f"{f.stat().st_size} B"))

        if files:
            self.file_table.selectRow(0)

    def _on_file_selected(self):
        row = self.file_table.currentRow()
        if row < 0 or not hasattr(self, "_current_files"):
            return
        file_path = self._current_files[row]
        try:
            self.file_preview.setPlainText(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.file_preview.setPlainText(f"<Binary or unreadable file: {exc}>")
