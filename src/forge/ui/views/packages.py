"""Packages view for exporting and verifying standalone connector ZIP archives."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
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
from forge.mcp.client_config import generate_claude_desktop_config
from forge.ui.workers import PackageWorker


class PackagesView(QWidget):
    """Manages exported connector distribution packages."""

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
        header = QLabel("Connector Packages")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        self.export_btn = QPushButton("Package Latest Build (ZIP)")
        self.export_btn.setObjectName("PrimaryButton")
        self.export_btn.clicked.connect(self._export_latest)
        header_bar.addWidget(self.export_btn)
        layout.addLayout(header_bar)

        splitter = QSplitter()

        # Left: Packages table
        left_box = QGroupBox("Exported Packages")
        left_l = QVBoxLayout(left_box)

        self.pkg_table = QTableWidget(0, 4)
        self.pkg_table.setHorizontalHeaderLabels(["ID", "Version", "Size", "SHA-256"])
        self.pkg_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.pkg_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pkg_table.itemSelectionChanged.connect(self._on_pkg_selected)
        left_l.addWidget(self.pkg_table)

        btn_bar = QHBoxLayout()
        verify_btn = QPushButton("Verify Archive Integrity")
        verify_btn.clicked.connect(self._verify_selected_archive)
        btn_bar.addWidget(verify_btn)
        btn_bar.addStretch()
        left_l.addLayout(btn_bar)

        splitter.addWidget(left_box)

        # Right: MCP Client Config Block
        right_box = QGroupBox("Sample MCP Client Configuration")
        right_l = QVBoxLayout(right_box)

        copy_btn = QPushButton("Copy Config JSON")
        copy_btn.clicked.connect(self._copy_config)
        right_l.addWidget(copy_btn)

        self.config_box = QTextEdit()
        self.config_box.setReadOnly(True)
        self.config_box.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        right_l.addWidget(self.config_box)

        splitter.addWidget(right_box)
        splitter.setSizes([550, 450])
        layout.addWidget(splitter)

        self.refresh()

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()
        self.refresh()

    def refresh(self):
        proj = self.svc.open_project(self.current_workspace)
        builds = self.svc.build_repo.list_by_project(proj.id)
        all_pkgs = []
        for b in builds:
            all_pkgs.extend(self.svc.package_repo.list_by_build(b.id))

        self._current_pkgs = all_pkgs
        self.pkg_table.setRowCount(len(all_pkgs))
        for i, p in enumerate(all_pkgs):
            self.pkg_table.setItem(i, 0, QTableWidgetItem(p.id[:8]))
            self.pkg_table.setItem(i, 1, QTableWidgetItem(p.version))
            self.pkg_table.setItem(i, 2, QTableWidgetItem(f"{p.size_bytes} B"))
            self.pkg_table.setItem(i, 3, QTableWidgetItem(p.sha256[:16] + "..."))

        if all_pkgs:
            self.pkg_table.selectRow(0)

    def _export_latest(self):
        proj = self.svc.open_project(self.current_workspace)
        builds = self.svc.build_repo.list_by_project(proj.id)
        if not builds:
            QMessageBox.warning(
                self, "No Builds", "No builds found. Generate a connector build first."
            )
            return

        latest_build = builds[0]
        self.export_btn.setEnabled(False)

        self.worker = PackageWorker(latest_build.id, self.current_workspace)
        self.worker.finished.connect(self._on_export_finished)
        self.worker.failed.connect(self._on_export_failed)
        self.worker.start()

    def _on_export_finished(self, pkg):
        self.export_btn.setEnabled(True)
        self.refresh()
        QMessageBox.information(
            self,
            "Package Created",
            f"Package exported successfully:\nPath: {pkg.archive_path}\nSHA-256: {pkg.sha256}",
        )

    def _on_export_failed(self, error):
        self.export_btn.setEnabled(True)
        QMessageBox.critical(self, "Packaging Error", f"Packaging failed:\n{error}")

    def _on_pkg_selected(self):
        row = self.pkg_table.currentRow()
        if row < 0 or not hasattr(self, "_current_pkgs") or not self._current_pkgs:
            return

        pkg = self._current_pkgs[row]
        build = self.svc.build_repo.get_by_id(pkg.build_id)
        if not build:
            return

        launcher = Path(build.build_dir) / "launcher.py"
        cfg = generate_claude_desktop_config(
            integration_id=f"connector-{pkg.version}",
            launcher_path=launcher,
            workspace_path=self.current_workspace,
        )
        self.config_box.setPlainText(json.dumps(cfg, indent=2))

    def _verify_selected_archive(self):
        row = self.pkg_table.currentRow()
        if row < 0 or not hasattr(self, "_current_pkgs") or not self._current_pkgs:
            return

        pkg = self._current_pkgs[row]
        ok, msg, contents = self.svc.package_exporter.verify_package(pkg.archive_path)
        if ok:
            QMessageBox.information(
                self,
                "Archive Verified",
                f"Verification successful:\n{msg}\nFiles: {', '.join(contents)}",
            )
        else:
            QMessageBox.critical(
                self, "Verification Failed", f"Archive failed verification:\n{msg}"
            )

    def _copy_config(self):
        QApplication.clipboard().setText(self.config_box.toPlainText())
        QMessageBox.information(self, "Copied", "Client configuration JSON copied to clipboard.")
