"""UI Views initialization."""

from forge.ui.views.adapter_library import AdapterLibraryView
from forge.ui.views.approvals import ApprovalsView
from forge.ui.views.audits import AuditsView
from forge.ui.views.dashboard import DashboardView
from forge.ui.views.manifest_studio import ManifestStudioView
from forge.ui.views.packages import PackagesView
from forge.ui.views.projects import ProjectsView
from forge.ui.views.runs import BuildsView
from forge.ui.views.settings import SettingsView
from forge.ui.views.test_lab import TestLabView
from forge.ui.views.tool_explorer import ToolExplorerView

__all__ = [
    "DashboardView",
    "ProjectsView",
    "ManifestStudioView",
    "AdapterLibraryView",
    "ToolExplorerView",
    "BuildsView",
    "TestLabView",
    "ApprovalsView",
    "AuditsView",
    "PackagesView",
    "SettingsView",
]
