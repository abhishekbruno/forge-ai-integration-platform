"""Test Lab view for orchestrating contract, e2e, and live test runs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService
from forge.ui.widgets.task_log import TaskLogWidget
from forge.ui.workers import TestRunnerWorker


class TestLabView(QWidget):
    """Orchestrates and displays automated test runs against generated builds."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.current_workspace = Path(".").resolve()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header & controls
        header_bar = QHBoxLayout()
        header = QLabel("Test Lab")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        self.live_blender_cb = QCheckBox("Enable Live Blender Test (requires installed Blender)")
        header_bar.addWidget(self.live_blender_cb)

        self.run_btn = QPushButton("Run Verification Suites")
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.clicked.connect(self._run_tests)
        header_bar.addWidget(self.run_btn)
        layout.addLayout(header_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        splitter = QSplitter()

        # Left: Results table
        left_box = QGroupBox("Test Results")
        left_l = QVBoxLayout(left_box)

        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(
            ["Test Suite / Case", "Status", "Duration (s)", "Details"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        left_l.addWidget(self.results_table)
        splitter.addWidget(left_box)

        # Right: Log output
        right_box = QGroupBox("Execution Output / STDERR")
        right_l = QVBoxLayout(right_box)
        self.log_widget = TaskLogWidget()
        right_l.addWidget(self.log_widget)
        splitter.addWidget(right_box)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()

    def _run_tests(self):
        proj = self.svc.open_project(self.current_workspace)
        builds = self.svc.build_repo.list_by_project(proj.id)
        if not builds:
            QMessageBox.warning(
                self, "No Builds", "No builds found. Generate a connector build first."
            )
            return

        latest_build = builds[0]
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_widget.clear()
        self.log_widget.append_log(
            f"Starting test suites for build {latest_build.id[:8]}...", "INFO"
        )

        self.worker = TestRunnerWorker(
            latest_build,
            self.current_workspace,
            live_blender=self.live_blender_cb.isChecked(),
        )
        self.worker.finished.connect(self._on_tests_finished)
        self.worker.failed.connect(self._on_tests_failed)
        self.worker.start()

    def _on_tests_finished(self, test_runs: list):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        total_cases = sum(len(r.test_cases) for r in test_runs)
        self.results_table.setRowCount(total_cases)

        row_idx = 0
        all_passed = True
        for run in test_runs:
            for tc in run.test_cases:
                self.results_table.setItem(
                    row_idx, 0, QTableWidgetItem(f"[{run.test_type}] {tc.name}")
                )
                self.results_table.setItem(row_idx, 1, QTableWidgetItem(tc.status.value.upper()))
                self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(tc.duration_seconds)))
                detail = tc.error_message or tc.skip_reason or "OK"
                self.results_table.setItem(row_idx, 3, QTableWidgetItem(detail))

                if tc.status.value == "failed":
                    all_passed = False
                row_idx += 1

            if run.stdout:
                self.log_widget.append_log(run.stdout, "INFO")
            if run.stderr:
                self.log_widget.append_log(run.stderr, "ERROR")

        if all_passed:
            self.log_widget.append_log("All verification suites passed successfully!", "SUCCESS")
        else:
            self.log_widget.append_log("Verification failed with errors.", "ERROR")

    def _on_tests_failed(self, error: str):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log_widget.append_log(f"Test execution crashed: {error}", "ERROR")
        QMessageBox.critical(
            self, "Test Error", f"Test runner encountered an unhandled exception:\n{error}"
        )
