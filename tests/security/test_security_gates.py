"""Security negative tests validating boundary gates and error handling."""

import zipfile
from pathlib import Path

import pytest

from forge.core.execution_gateway import ExecutionGateway
from forge.core.manifest_service import ManifestService
from forge.core.packaging import PackageExporter
from forge.domain.errors import (
    ApprovalRequiredError,
)
from forge.persistence.audit_journal import AuditJournal
from forge.security.paths import PathSecurityError, ensure_within_workspace


def test_path_traversal_blocked(temp_workspace):
    with pytest.raises(PathSecurityError):
        ensure_within_workspace("../../../windows/system32/cmd.exe", temp_workspace)


def test_zip_slip_rejection(temp_workspace):
    bad_zip = temp_workspace / "evil.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../etc/passwd", "malicious payload")

    exporter = PackageExporter()
    ok, msg, _ = exporter.verify_package(bad_zip)
    assert ok is False
    assert "Zip-slip" in msg


def test_unapproved_write_denial(temp_workspace, temp_db):
    ms = ManifestService()
    manifest = ms.load_and_validate(Path("manifests/fixturelab.yaml"))
    gateway = ExecutionGateway(temp_db)

    args = {"item_id": "hack_01", "name": "Unapproved"}
    with pytest.raises(ApprovalRequiredError):
        gateway.execute_tool(
            connector_id=manifest.integration.id,
            manifest=manifest,
            tool_name="fixturelab_create_item",
            args=args,
            workspace=temp_workspace,
        )


def test_tamper_detected_in_audit_journal(temp_db):
    journal = AuditJournal(temp_db)
    journal.record_event("action.1", "target.1", "success", "corr_1")
    journal.record_event("action.2", "target.2", "success", "corr_2")

    # Modify second record
    with journal.mgr.get_connection() as conn:
        conn.execute("UPDATE audit_events SET outcome = 'failed' WHERE id = 2;")

    ok, msg, broken_id = journal.verify_integrity()
    assert ok is False
    assert broken_id == 2
