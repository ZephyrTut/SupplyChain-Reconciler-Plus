"""UI module - PyQt6 version."""

from .qt_main_window import QtMainWindow
from .qt_config_panel import QtConfigPanel, NoScrollComboBox
from .qt_result_preview import QtResultPreview, QtResultTable, SampleDisplay
from .qt_dialogs import (
    LoadingDialog,
    ProgressDialog,
    SheetSelectDialog,
    InputDialog,
    ConfirmDialog,
    WorkerThread,
    TemplateManagerDialog,
    run_with_progress,
    show_info,
    show_warning,
    show_error,
    show_confirm,
)

__all__ = [
    # main window
    "QtMainWindow",
    # config panel
    "QtConfigPanel",
    "NoScrollComboBox",
    # result preview
    "QtResultPreview",
    "QtResultTable",
    "SampleDisplay",
    # dialogs
    "LoadingDialog",
    "ProgressDialog",
    "SheetSelectDialog",
    "InputDialog",
    "ConfirmDialog",
    "WorkerThread",
    "TemplateManagerDialog",
    "run_with_progress",
    # helpers
    "show_info",
    "show_warning",
    "show_error",
    "show_confirm",
]
