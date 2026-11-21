"""Integration tests for project service."""

from pathlib import Path

from forge.core.project_service import ProjectService


def test_project_create_and_list(temp_workspace, temp_db):
    svc = ProjectService(temp_db)
    proj = svc.create_project(temp_workspace, "Integration Test Project")
    assert proj.name == "Integration Test Project"
    assert Path(proj.workspace_path) == temp_workspace

    all_projs = svc.list_projects()
    assert len(all_projs) == 1
    assert all_projs[0].id == proj.id
