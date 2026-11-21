"""Manifest Studio view for editing, inspecting, and validating integration manifests."""

from __future__ import annotations

from pathlib import Path

import yaml
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from forge.core.application_service import ApplicationService
from forge.ui.widgets.code_editor import CodeEditorWidget


class ManifestStudioView(QWidget):
    """YAML editor and validator for Integration Manifests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = ApplicationService()
        self.current_workspace = Path(".").resolve()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header bar
        header_bar = QHBoxLayout()
        header = QLabel("Manifest Studio")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header_bar.addWidget(header)
        header_bar.addStretch()

        load_fixture_btn = QPushButton("Load FixtureLab Template")
        load_fixture_btn.clicked.connect(self._load_fixturelab_template)
        load_blender_btn = QPushButton("Load Blender Template")
        load_blender_btn.clicked.connect(self._load_blender_template)

        validate_btn = QPushButton("Validate Manifest")
        validate_btn.setObjectName("PrimaryButton")
        validate_btn.clicked.connect(self._validate)

        save_btn = QPushButton("Save to Workspace")
        save_btn.clicked.connect(self._save_to_workspace)

        header_bar.addWidget(load_fixture_btn)
        header_bar.addWidget(load_blender_btn)
        header_bar.addWidget(validate_btn)
        header_bar.addWidget(save_btn)
        layout.addLayout(header_bar)

        # Splitter: Left editor, Right validation diagnostics
        splitter = QSplitter()

        # Left: Editor
        editor_container = QWidget()
        ed_layout = QVBoxLayout(editor_container)
        ed_layout.setContentsMargins(0, 0, 0, 0)
        ed_layout.addWidget(QLabel("<b>manifest.yaml</b>"))
        self.editor = CodeEditorWidget()
        ed_layout.addWidget(self.editor)
        splitter.addWidget(editor_container)

        # Right: Diagnostics
        diag_container = QWidget()
        diag_layout = QVBoxLayout(diag_container)
        diag_layout.setContentsMargins(0, 0, 0, 0)
        diag_layout.addWidget(QLabel("<b>Validation Status & Diagnostics</b>"))

        self.diag_box = QTextEdit()
        self.diag_box.setReadOnly(True)
        self.diag_box.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        diag_layout.addWidget(self.diag_box)
        splitter.addWidget(diag_container)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        self._load_from_workspace()

    def set_workspace(self, workspace: Path) -> None:
        self.current_workspace = Path(workspace).resolve()
        self._load_from_workspace()

    def _load_from_workspace(self) -> None:
        manifest_file = self.current_workspace / "manifest.yaml"
        if manifest_file.is_file():
            self.editor.set_text(manifest_file.read_text(encoding="utf-8"))
            self._validate()
        else:
            self._load_fixturelab_template()

    def _load_fixturelab_template(self) -> None:
        tpl_path = Path(__file__).parent.parent.parent.parent / "manifests" / "fixturelab.yaml"
        if tpl_path.is_file():
            self.editor.set_text(tpl_path.read_text(encoding="utf-8"))
            self._validate()

    def _load_blender_template(self) -> None:
        tpl_path = Path(__file__).parent.parent.parent.parent / "manifests" / "blender.yaml"
        if tpl_path.is_file():
            self.editor.set_text(tpl_path.read_text(encoding="utf-8"))
            self._validate()

    def _validate(self) -> bool:
        text = self.editor.get_text()
        if not text.strip():
            self.diag_box.setHtml("<span style='color: #f7768e;'>Error: Manifest is empty.</span>")
            return False

        try:
            data = yaml.safe_load(text)
        except Exception as exc:
            self.diag_box.setHtml(
                f"<span style='color: #f7768e;'>YAML Syntax Error:</span><br>{exc}"
            )
            return False

        is_valid, errors, manifest = self.svc.manifest_service.validate_manifest_data(data)
        if not is_valid:
            err_html = "<br>".join(f"• {e}" for e in errors)
            self.diag_box.setHtml(
                f"<div style='color: #f7768e;'><b>Validation FAILED ({len(errors)} errors):</b><br>{err_html}</div>"
            )
            return False
        else:
            caps_html = "".join(
                f"<li><b>{c.name}</b> ({c.risk.value}): {c.description}</li>"
                for c in manifest.capabilities
            )
            self.diag_box.setHtml(
                f"<div style='color: #9ece6a;'><b>Manifest Valid!</b></div>"
                f"<p>Integration: <b>{manifest.integration.name}</b> ({manifest.integration.id} v{manifest.integration.version})<br>"
                f"Application: {manifest.application.display_name} ({manifest.application.id})<br>"
                f"Adapter: {manifest.adapter.id} v{manifest.adapter.version}</p>"
                f"<b>Capabilities ({len(manifest.capabilities)}):</b><ul>{caps_html}</ul>"
            )
            return True

    def _save_to_workspace(self) -> None:
        if not self._validate():
            QMessageBox.warning(
                self, "Validation Warning", "Manifest has validation errors. Fix before saving."
            )
            return

        target_file = self.current_workspace / "manifest.yaml"
        target_file.write_text(self.editor.get_text(), encoding="utf-8")
        QMessageBox.information(self, "Saved", f"Manifest successfully saved to {target_file}")
