"""
PyQt6 对话框组件 - 加载动画、Sheet选择、输入框等
"""
from typing import List, Optional, Callable, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QListWidget, QListWidgetItem, QLineEdit,
    QMessageBox, QApplication, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class LoadingDialog(QDialog):
    """加载动画对话框"""
    
    def __init__(self, message: str = "正在处理...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("请稍候")
        self.setFixedSize(300, 120)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)
        self._setup_ui(message)
        
    def _setup_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 消息
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.message_label)
        
        # 进度条（不确定模式）
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定模式
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
    def set_message(self, message: str):
        """更新消息"""
        self.message_label.setText(message)
        QApplication.processEvents()


class ProgressDialog(QDialog):
    """进度对话框（确定模式）"""
    
    def __init__(self, title: str, steps: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 180)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)
        self.steps = steps
        self.current_step = 0
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 当前步骤
        self.step_label = QLabel(self.steps[0] if self.steps else "处理中...")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.step_label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, len(self.steps))
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
        # 百分比
        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percent_label.setStyleSheet("color: #666;")
        layout.addWidget(self.percent_label)
        
    def next_step(self):
        """进入下一步"""
        self.current_step += 1
        if self.current_step < len(self.steps):
            self.step_label.setText(self.steps[self.current_step])
        self.progress.setValue(self.current_step)
        percent = int(self.current_step / len(self.steps) * 100)
        self.percent_label.setText(f"{percent}%")
        QApplication.processEvents()
        
    def set_step(self, step: int, message: str = None):
        """设置当前步骤"""
        self.current_step = step
        if message:
            self.step_label.setText(message)
        elif step < len(self.steps):
            self.step_label.setText(self.steps[step])
        self.progress.setValue(step)
        percent = int(step / len(self.steps) * 100)
        self.percent_label.setText(f"{percent}%")
        QApplication.processEvents()


class SheetSelectDialog(QDialog):
    """Sheet选择对话框"""
    
    def __init__(self, sheets: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择工作表")
        self.setFixedSize(350, 400)
        self.setModal(True)
        self.sheets = sheets
        self.selected_sheet = sheets[0] if sheets else ""
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 提示
        hint = QLabel("Excel文件包含多个工作表，请选择要导入的工作表:")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        
        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976D2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        
        for sheet in self.sheets:
            item = QListWidgetItem(f"📋 {sheet}")
            item.setData(Qt.ItemDataRole.UserRole, sheet)
            self.list_widget.addItem(item)
            
        if self.sheets:
            self.list_widget.setCurrentRow(0)
            
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list_widget, 1)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_ok(self):
        """确定选择"""
        current = self.list_widget.currentItem()
        if current:
            self.selected_sheet = current.data(Qt.ItemDataRole.UserRole)
        self.accept()
        
    def _on_double_click(self, item):
        """双击选择"""
        self.selected_sheet = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class InputDialog(QDialog):
    """输入对话框"""
    
    def __init__(self, title: str, prompt: str, default: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setModal(True)
        self._text = default
        self._setup_ui(prompt, default)
        
    def _setup_ui(self, prompt: str, default: str):
        # 对话框背景样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 提示
        prompt_label = QLabel(prompt)
        layout.addWidget(prompt_label)
        
        # 输入框
        self.input_edit = QLineEdit()
        self.input_edit.setText(default)
        self.input_edit.selectAll()
        self.input_edit.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        layout.addWidget(self.input_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_ok(self):
        """确定"""
        self._text = self.input_edit.text().strip()
        if self._text:
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请输入内容")
            
    def get_text(self) -> str:
        """获取输入文本"""
        return self._text


class WorkerThread(QThread):
    """工作线程"""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    
    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def run_with_progress(parent: QWidget, title: str, steps: List[str], 
                     func: Callable, *args, **kwargs) -> Any:
    """带进度条运行函数（阻塞式）"""
    dialog = ProgressDialog(title, steps, parent)
    dialog.show()
    QApplication.processEvents()
    
    result = None
    error = None
    
    def on_finished(r):
        nonlocal result
        result = r
        
    def on_error(e):
        nonlocal error
        error = e
        
    # 创建工作线程
    thread = WorkerThread(func, *args, **kwargs)
    thread.finished.connect(on_finished)
    thread.error.connect(on_error)
    thread.start()
    
    # 等待完成
    while thread.isRunning():
        QApplication.processEvents()
        
    dialog.close()
    
    if error:
        raise Exception(error)
    return result


class TemplateManagerDialog(QDialog):
    """模板管理对话框"""
    
    template_selected = pyqtSignal(dict)
    template_deleted = pyqtSignal(str)
    
    def __init__(self, templates: List[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("模板管理")
        self.setFixedSize(500, 450)
        self.setModal(True)
        self.templates = templates
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("📋 配置模板列表")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 模板列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976D2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        
        for template in self.templates:
            name = template.get("name", "未命名模板")
            item = QListWidgetItem(f"📄 {name}")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self._on_load)
        layout.addWidget(self.list_widget, 1)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📂 加载模板")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        load_btn.clicked.connect(self._on_load)
        btn_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("🗑️ 删除模板")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_load(self):
        """加载模板"""
        current = self.list_widget.currentItem()
        if current:
            template = current.data(Qt.ItemDataRole.UserRole)
            self.template_selected.emit(template)
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请选择一个模板")
            
    def _on_delete(self):
        """删除模板"""
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请选择要删除的模板")
            return
            
        template = current.data(Qt.ItemDataRole.UserRole)
        name = template.get("name", "未命名")
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模板 '{name}' 吗？\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template_id = template.get("id") or template.get("name")
            self.template_deleted.emit(template_id)
            # 从列表移除
            row = self.list_widget.row(current)
            self.list_widget.takeItem(row)
            self.templates = [t for t in self.templates 
                            if (t.get("id") or t.get("name")) != template_id]
