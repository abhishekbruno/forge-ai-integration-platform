"""Settings view for themes, paths, and system diagnostics."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.config import get_config
from forge.core.application_service import ApplicationService


class SettingsView(QWidget):
    """System preferences and diagnostics inspection."""

    def __init__(self, theme_toggle_callback=None, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.theme_toggle_callback = theme_toggle_callback
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("System Settings & Diagnostics")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Environment & Paths
        env_box = QGroupBox("Configuration & Paths")
        env_l = QVBoxLayout(env_box)

        # Data Dir
        d_row = QHBoxLayout()
        d_row.addWidget(QLabel("Data Directory:"))
        d_edit = QLineEdit(str(get_config().data_dir))
        d_edit.setReadOnly(True)
        d_row.addWidget(d_edit)
        env_l.addLayout(d_row)

        # Blender Path
        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("Blender Executable:"))
        current_blender = str(get_config().blender_executable or "")
        self.blender_edit = QLineEdit(current_blender)
        browse_btn = QPushButton("Select Blender...")
        browse_btn.clicked.connect(self._browse_blender)
        save_blender_btn = QPushButton("Save")
        save_blender_btn.clicked.connect(self._save_blender_path)

        b_row.addWidget(self.blender_edit)
        b_row.addWidget(browse_btn)
        b_row.addWidget(save_blender_btn)
        env_l.addLayout(b_row)

        # Theme Toggle
        t_row = QHBoxLayout()
        t_row.addWidget(QLabel("Appearance Theme:"))
        toggle_theme_btn = QPushButton("Toggle Dark / Light Theme")
        if self.theme_toggle_callback:
            toggle_theme_btn.clicked.connect(self.theme_toggle_callback)
        t_row.addWidget(toggle_theme_btn)
        t_row.addStretch()
        env_l.addLayout(t_row)

        layout.addWidget(env_box)

        # Doctor Diagnostics
        doc_box = QGroupBox("System Doctor Checks")
        doc_l = QVBoxLayout(doc_box)

        self.doc_table = QTableWidget(0, 3)
        self.doc_table.setHorizontalHeaderLabels(["Status", "Diagnostic Check", "Details"])
        self.doc_table.horizontalHeader().setSectionResizeMode(
            2, self.doc_table.horizontalHeader().ResizeMode.Stretch
        )
        doc_l.addWidget(self.doc_table)

        refresh_doc_btn = QPushButton("Re-run Doctor Diagnostics")
        refresh_doc_btn.clicked.connect(self.refresh_doctor)
        doc_l.addWidget(refresh_doc_btn)

        layout.addWidget(doc_box)
        self.refresh_doctor()

    def _browse_blender(self):
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            "Select Blender Executable",
            "",
            "Executable Files (*.exe);;All Files (*)",
        )
        if chosen:
            self.blender_edit.setText(chosen)

    def _save_blender_path(self):
        path_str = self.blender_edit.text().strip()
        if path_str and Path(path_str).is_file():
            os.environ["FORGE_BLENDER_PATH"] = path_str
            get_config().blender_executable = Path(path_str)
            QMessageBox.information(
                self, "Saved", f"Blender executable path updated to:\n{path_str}"
            )
            self.refresh_doctor()
        elif not path_str:
            os.environ.pop("FORGE_BLENDER_PATH", None)
            get_config().blender_executable = None
            QMessageBox.information(self, "Reset", "Blender executable reset to system discovery.")
            self.refresh_doctor()
        else:
            QMessageBox.critical(self, "Invalid Path", f"Path does not exist: {path_str}")

    def refresh_doctor(self):
        report = self.svc.run_diagnostics()
        self.doc_table.setRowCount(len(report.checks))
        for i, c in enumerate(report.checks):
            self.doc_table.setItem(i, 0, QTableWidgetItem(c.status.value))
            self.doc_table.setItem(i, 1, QTableWidgetItem(c.name))
            self.doc_table.setItem(i, 2, QTableWidgetItem(c.message))
