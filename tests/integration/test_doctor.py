"""Integration tests for doctor diagnostics."""

from forge.core.doctor import Doctor


def test_doctor_diagnostics(temp_workspace):
    doc = Doctor()
    report = doc.run_diagnostics(temp_workspace)
    assert report is not None
    check_names = [c.name for c in report.checks]
    assert "Python Runtime" in check_names
    assert "Core Dependencies" in check_names
    assert "Application Data Directory" in check_names
    assert "SQLite Database" in check_names
    assert "FixtureLab Reference Adapter" in check_names
    assert "Project Workspace" in check_names
