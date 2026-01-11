"""UI模块 - PyQt6 版本"""

# PyQt6 新组件
from .qt_main_window import QtMainWindow
from .qt_config_panel import QtConfigPanel
from .qt_result_preview import QtResultPreview, QtResultTable, SampleDisplay
from .qt_dialogs import (
    LoadingDialog, 
    ProgressDialog,
    SheetSelectDialog,
    InputDialog,
    WorkerThread,
    TemplateManagerDialog,
    run_with_progress
)

# 保留旧组件（供参考，测试通过后删除）
# from .main_window import MainWindow
# from .config_panel import ConfigPanel
# from .result_preview import ResultPreview
# from .template_manager import TemplateManagerDialog as OldTemplateManagerDialog
# from .loading import LoadingDialog as OldLoadingDialog, ProgressWindow, OperationThread, run_with_loading
# from .scroll_utils import disable_combobox_scroll, setup_mousewheel_scroll

__all__ = [
    # PyQt6 组件
    "QtMainWindow",
    "QtConfigPanel",
    "QtResultPreview",
    "QtResultTable",
    "SampleDisplay",
    "LoadingDialog",
    "ProgressDialog",
    "SheetSelectDialog",
    "InputDialog",
    "WorkerThread",
    "TemplateManagerDialog",
    "run_with_progress",
]
