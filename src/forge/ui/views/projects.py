"""Projects view allowing opening, creating, and switching workspace folders."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService


class ProjectsView(QWidget):
    """Manages workspace projects."""

    project_selected = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Project Workspaces")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Create/Open Bar
        form_box = QGroupBox("Register / Create Workspace")
        form_l = QHBoxLayout(form_box)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Project Name (e.g. My Blender Integration)")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Workspace Directory Path")

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)

        create_btn = QPushButton("Create / Open")
        create_btn.setObjectName("PrimaryButton")
        create_btn.clicked.connect(self._create_or_open)

        form_l.addWidget(QLabel("Name:"))
        form_l.addWidget(self.name_edit)
        form_l.addWidget(QLabel("Path:"))
        form_l.addWidget(self.path_edit)
        form_l.addWidget(browse_btn)
        form_l.addWidget(create_btn)
        layout.addWidget(form_box)

        # Projects Table
        table_box = QGroupBox("Registered Projects")
        table_l = QVBoxLayout(table_box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Project ID", "Name", "Workspace Path", "Updated At"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        table_l.addWidget(self.table)

        btn_bar = QHBoxLayout()
        select_btn = QPushButton("Open Selected Project")
        select_btn.clicked.connect(self._open_selected)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        btn_bar.addWidget(select_btn)
        btn_bar.addWidget(refresh_btn)
        btn_bar.addStretch()
        table_l.addLayout(btn_bar)

        layout.addWidget(table_box)
        self.refresh()

    def _browse_directory(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Workspace Directory")
        if chosen:
            self.path_edit.setText(chosen)
            if not self.name_edit.text():
                self.name_edit.setText(Path(chosen).name)

    def _create_or_open(self):
        raw_path = self.path_edit.text().strip()
        raw_name = self.name_edit.text().strip() or "Untitled Project"
        if not raw_path:
            QMessageBox.warning(
                self, "Invalid Input", "Please provide a valid workspace directory path."
            )
            return

        try:
            proj = self.svc.create_project(raw_path, raw_name)
            self.refresh()
            self.project_selected.emit(Path(proj.workspace_path))
            QMessageBox.information(self, "Success", f"Project '{proj.name}' is now active.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to initialize project: {exc}")

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Notice", "Please select a project from the table.")
            return
        path_item = self.table.item(row, 2)
        if path_item:
            self.project_selected.emit(Path(path_item.text()))

    def _on_row_double_clicked(self, row: int, col: int):
        path_item = self.table.item(row, 2)
        if path_item:
            self.project_selected.emit(Path(path_item.text()))

    def refresh(self):
        projects = self.svc.list_projects()
        self.table.setRowCount(len(projects))
        for i, p in enumerate(projects):
            self.table.setItem(i, 0, QTableWidgetItem(p.id[:8]))
            self.table.setItem(i, 1, QTableWidgetItem(p.name))
            self.table.setItem(i, 2, QTableWidgetItem(p.workspace_path))
            self.table.setItem(i, 3, QTableWidgetItem(p.updated_at[:19]))
