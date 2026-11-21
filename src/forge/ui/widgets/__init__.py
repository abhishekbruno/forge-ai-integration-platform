"""UI Widgets initialization."""

from forge.ui.widgets.code_editor import CodeEditorWidget
from forge.ui.widgets.diff_viewer import DiffViewerWidget
from forge.ui.widgets.json_viewer import JsonViewerWidget
from forge.ui.widgets.status_badge import StatusBadge
from forge.ui.widgets.task_log import TaskLogWidget

__all__ = [
    "StatusBadge",
    "CodeEditorWidget",
    "JsonViewerWidget",
    "DiffViewerWidget",
    "TaskLogWidget",
]
