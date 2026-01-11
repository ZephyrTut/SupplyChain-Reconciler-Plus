"""
PyQt6 配置面板 - 主键映射、筛选、透视、公式配置
"""
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QGroupBox,
    QSizePolicy, QSpacerItem, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QWheelEvent


class NoScrollComboBox(QComboBox):
    """禁用鼠标滚轮的下拉框，避免干扰外部滚动"""
    
    def wheelEvent(self, event: QWheelEvent):
        # 忽略滚轮事件，让父容器处理滚动
        event.ignore()


class DynamicRow(QWidget):
    """动态行组件基类"""
    
    deleted = pyqtSignal(object)
    changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        raise NotImplementedError
        
    def get_value(self) -> Dict:
        raise NotImplementedError
        
    def set_value(self, value: Dict):
        raise NotImplementedError


class KeyMappingRow(DynamicRow):
    """主键映射行"""
    
    def __init__(self, manual_columns: List[str], system_columns: List[str], parent=None):
        self.manual_columns = manual_columns
        self.system_columns = system_columns
        super().__init__(parent)
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # 手工表列
        self.manual_combo = NoScrollComboBox()
        self.manual_combo.addItem("(选择列)")
        self.manual_combo.addItems(self.manual_columns)
        self.manual_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.manual_combo, 1)
        
        # 映射符号
        arrow = QLabel("↔")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #333333; font-size: 16px; background: transparent; border: none;")
        layout.addWidget(arrow)
        
        # 系统表列
        self.system_combo = NoScrollComboBox()
        self.system_combo.addItem("(选择列)")
        self.system_combo.addItems(self.system_columns)
        self.system_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.system_combo, 1)
        
        # 删除按钮
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                color: #f44336;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self))
        layout.addWidget(del_btn)
        
    def get_value(self) -> Dict:
        manual = self.manual_combo.currentText()
        system = self.system_combo.currentText()
        if manual != "(选择列)" and system != "(选择列)":
            return {"manual": manual, "system": system}
        return {}
        
    def set_value(self, value: Dict):
        if "manual" in value:
            idx = self.manual_combo.findText(value["manual"])
            if idx >= 0:
                self.manual_combo.setCurrentIndex(idx)
        if "system" in value:
            idx = self.system_combo.findText(value["system"])
            if idx >= 0:
                self.system_combo.setCurrentIndex(idx)
                
    def update_columns(self, manual_columns: List[str], system_columns: List[str]):
        """更新列选项"""
        current_manual = self.manual_combo.currentText()
        current_system = self.system_combo.currentText()
        
        self.manual_combo.clear()
        self.manual_combo.addItem("(选择列)")
        self.manual_combo.addItems(manual_columns)
        
        self.system_combo.clear()
        self.system_combo.addItem("(选择列)")
        self.system_combo.addItems(system_columns)
        
        # 恢复选择
        idx = self.manual_combo.findText(current_manual)
        if idx >= 0:
            self.manual_combo.setCurrentIndex(idx)
        idx = self.system_combo.findText(current_system)
        if idx >= 0:
            self.system_combo.setCurrentIndex(idx)


class FilterRow(DynamicRow):
    """筛选条件行 - 根据操作符动态切换输入方式"""
    
    OPERATORS = ["等于", "不等于", "包含", "不包含", "包含于", "不包含于", "大于", "小于"]
    # 需要下拉选择的操作符
    DROPDOWN_OPERATORS = ["等于", "不等于"]
    # 需要多选的操作符
    MULTISELECT_OPERATORS = ["包含于", "不包含于"]
    # 需要输入框的操作符（包含/不包含支持多值用逗号分隔）
    INPUT_OPERATORS = ["包含", "不包含", "大于", "小于"]
    
    # 操作符映射到引擎
    OPERATOR_MAP = {
        "等于": "EQUALS",
        "不等于": "NOT_EQUALS",
        "包含": "CONTAINS",
        "不包含": "NOT_CONTAINS",
        "包含于": "IN_LIST",
        "不包含于": "NOT_IN_LIST",
        "大于": "GREATER",
        "小于": "LESS"
    }
    
    def __init__(self, columns: List[str], unique_values: Dict[str, List] = None, parent=None):
        self.columns = columns
        self.unique_values = unique_values or {}
        self._current_value_widget = None
        self._checkboxes = []  # 存储多选复选框
        super().__init__(parent)
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # 列选择
        self.column_combo = NoScrollComboBox()
        self.column_combo.addItem("(选择列)")
        self.column_combo.addItems(self.columns)
        self.column_combo.currentIndexChanged.connect(self._on_column_changed)
        layout.addWidget(self.column_combo, 1)
        
        # 操作符
        self.operator_combo = NoScrollComboBox()
        self.operator_combo.addItems(self.OPERATORS)
        self.operator_combo.currentIndexChanged.connect(self._on_operator_changed)
        layout.addWidget(self.operator_combo)
        
        # 值输入区域容器
        self.value_container = QWidget()
        self.value_layout = QHBoxLayout(self.value_container)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.value_layout.setSpacing(5)
        layout.addWidget(self.value_container, 2)
        
        # 初始化值控件（默认下拉框）
        self._create_dropdown_widget()
        
        # 删除按钮
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                color: #f44336;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self))
        layout.addWidget(del_btn)
    
    def _clear_value_widget(self):
        """清空值输入区域"""
        while self.value_layout.count():
            item = self.value_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checkboxes = []
        self._current_value_widget = None
    
    def _create_dropdown_widget(self):
        """创建下拉框控件（等于、不等于）"""
        self._clear_value_widget()
        self.value_combo = NoScrollComboBox()
        self.value_combo.setMinimumWidth(150)
        self.value_combo.currentTextChanged.connect(lambda: self.changed.emit())
        self.value_layout.addWidget(self.value_combo)
        self._current_value_widget = "dropdown"
        # 更新下拉框值
        self._update_dropdown_values()
    
    def _create_input_widget(self):
        """创建输入框控件（包含、不包含、大于、小于）"""
        self._clear_value_widget()
        self.value_edit = QLineEdit()
        self.value_edit.setMinimumWidth(150)
        operator = self.operator_combo.currentText()
        if operator in ["大于", "小于"]:
            self.value_edit.setPlaceholderText("输入数值")
        else:
            # 包含/不包含支持多值
            self.value_edit.setPlaceholderText("多值用逗号分隔，如: 发货,退仓")
        self.value_edit.textChanged.connect(lambda: self.changed.emit())
        self.value_layout.addWidget(self.value_edit)
        self._current_value_widget = "input"
    
    def _create_multiselect_widget(self):
        """创建多选复选框控件（包含于）"""
        self._clear_value_widget()
        
        # 创建滚动区域容纳复选框
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(80)
        scroll.setMinimumWidth(200)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
        """)
        
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(5, 5, 5, 5)
        checkbox_layout.setSpacing(2)
        
        # 获取当前列的唯一值
        column = self.column_combo.currentText()
        values = []
        if column in self.unique_values:
            values = [str(v) for v in self.unique_values[column] if v is not None][:50]
        
        if values:
            for val in values:
                cb = QCheckBox(val)
                cb.setStyleSheet("color: #333;")
                cb.stateChanged.connect(lambda: self.changed.emit())
                checkbox_layout.addWidget(cb)
                self._checkboxes.append(cb)
        else:
            # 没有唯一值时显示提示
            hint = QLabel("请先选择列")
            hint.setStyleSheet("color: #999; font-style: italic;")
            checkbox_layout.addWidget(hint)
        
        checkbox_layout.addStretch()
        scroll.setWidget(checkbox_container)
        self.value_layout.addWidget(scroll)
        self._current_value_widget = "multiselect"
    
    def _update_dropdown_values(self):
        """更新下拉框的唯一值"""
        if not hasattr(self, 'value_combo'):
            return
        self.value_combo.clear()
        column = self.column_combo.currentText()
        if column in self.unique_values:
            values = [str(v) for v in self.unique_values[column] if v is not None]
            self.value_combo.addItems(values[:100])
        
    def _on_column_changed(self, index: int):
        """列选择变更"""
        operator = self.operator_combo.currentText()
        if operator in self.DROPDOWN_OPERATORS:
            self._update_dropdown_values()
        elif operator in self.MULTISELECT_OPERATORS:
            self._create_multiselect_widget()
        self.changed.emit()
    
    def _on_operator_changed(self):
        """操作符变更，切换输入控件"""
        operator = self.operator_combo.currentText()
        
        if operator in self.DROPDOWN_OPERATORS:
            if self._current_value_widget != "dropdown":
                self._create_dropdown_widget()
        elif operator in self.MULTISELECT_OPERATORS:
            if self._current_value_widget != "multiselect":
                self._create_multiselect_widget()
        elif operator in self.INPUT_OPERATORS:
            if self._current_value_widget != "input":
                self._create_input_widget()
        
        self.changed.emit()
        
    def get_value(self) -> Dict:
        column = self.column_combo.currentText()
        operator = self.operator_combo.currentText()
        
        if column == "(选择列)":
            return {}
        
        # 根据当前控件类型获取值
        value = ""
        if self._current_value_widget == "dropdown" and hasattr(self, 'value_combo'):
            value = self.value_combo.currentText()
        elif self._current_value_widget == "input" and hasattr(self, 'value_edit'):
            value = self.value_edit.text()
        elif self._current_value_widget == "multiselect":
            selected = [cb.text() for cb in self._checkboxes if cb.isChecked()]
            value = ",".join(selected)
        
        if value:
            # 映射操作符到引擎格式
            engine_op = self.OPERATOR_MAP.get(operator, operator)
            return {"column": column, "operator": engine_op, "value": value}
        return {}
        
    def set_value(self, value: Dict):
        if "column" in value:
            idx = self.column_combo.findText(value["column"])
            if idx >= 0:
                self.column_combo.setCurrentIndex(idx)
        if "operator" in value:
            idx = self.operator_combo.findText(value["operator"])
            if idx >= 0:
                self.operator_combo.setCurrentIndex(idx)
        if "value" in value:
            val_str = str(value["value"])
            if self._current_value_widget == "dropdown" and hasattr(self, 'value_combo'):
                self.value_combo.setCurrentText(val_str)
            elif self._current_value_widget == "input" and hasattr(self, 'value_edit'):
                self.value_edit.setText(val_str)
            elif self._current_value_widget == "multiselect":
                selected_values = val_str.split(",")
                for cb in self._checkboxes:
                    cb.setChecked(cb.text() in selected_values)
            
    def update_unique_values(self, unique_values: Dict[str, List]):
        """更新唯一值字典"""
        self.unique_values = unique_values
        operator = self.operator_combo.currentText()
        if operator in self.DROPDOWN_OPERATORS:
            self._update_dropdown_values()
        elif operator in self.MULTISELECT_OPERATORS:
            self._create_multiselect_widget()


class CollapsibleSection(QWidget):
    """可折叠区块"""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._expanded = True
        self._icon = icon
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(0)
        
        # 标题栏
        display_title = f"{self._icon} {title}" if self._icon else title
        self.header = QPushButton(f"▼ {display_title}")
        self.header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
                border-color: #c0c0c0;
            }
        """)
        self.header.clicked.connect(self.toggle)
        layout.addWidget(self.header)
        
        # 内容区
        self.content = QWidget()
        self.content.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-top: none;
                border-radius: 0 0 6px 6px;
            }
            QLabel {
                color: #333333;
                background-color: transparent;
                border: none;
            }
        """)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(self.content)
        
        self._title = title
        self._display_title = display_title
        
    def toggle(self):
        """切换展开/折叠"""
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        arrow = "▼" if self._expanded else "▶"
        self.header.setText(f"{arrow} {self._display_title}")
        
    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        self._expanded = expanded
        self.content.setVisible(expanded)
        arrow = "▼" if expanded else "▶"
        self.header.setText(f"{arrow} {self._display_title}")
        
    def add_widget(self, widget: QWidget):
        """添加内容"""
        self.content_layout.addWidget(widget)


class QtConfigPanel(QScrollArea):
    """配置面板"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        
        self.compact = compact
        self.manual_columns: List[str] = []
        self.system_columns: List[str] = []
        self.system_unique_values: Dict[str, List] = {}
        
        self.key_rows: List[KeyMappingRow] = []
        self.manual_filter_rows: List[FilterRow] = []
        self.system_filter_rows: List[FilterRow] = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        # 滚动区域设置
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #f5f5f5;
            }
        """)
        
        # 主容器
        container = QWidget()
        container.setStyleSheet("background-color: #f5f5f5;")
        self.main_layout = QVBoxLayout(container)
        margin = 10 if self.compact else 15
        spacing = 10 if self.compact else 15
        self.main_layout.setContentsMargins(margin, margin, margin, margin)
        self.main_layout.setSpacing(spacing)
        
        # 1. 主键配置
        self._create_key_section()
        
        # 2. 数值列配置
        self._create_value_section()
        
        # 3. 筛选配置（可折叠）
        self._create_filter_section()
        
        # 4. 透视配置（可折叠）
        self._create_pivot_section()
        
        # 5. 差值公式配置
        self._create_formula_section()
        
        # 弹性空间
        self.main_layout.addStretch()
        
        self.setWidget(container)
        
    def _create_key_section(self):
        """创建主键配置区（可折叠）"""
        self.key_section = CollapsibleSection("主键映射", "🔑")
        self.key_section.set_expanded(True)
        
        # 说明
        hint = QLabel("配置用于匹配的主键字段（支持多字段复合主键）")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        self.key_section.add_widget(hint)
        
        # 行容器
        self.key_container = QWidget()
        self.key_layout = QVBoxLayout(self.key_container)
        self.key_layout.setContentsMargins(0, 0, 0, 0)
        self.key_layout.setSpacing(5)
        self.key_section.add_widget(self.key_container)
        
        # 添加默认行
        self._add_key_row()
        
        # 添加按钮
        add_btn = QPushButton("➕ 添加主键")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd;
                color: #1976D2;
                border: 1px dashed #1976D2;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)
        add_btn.clicked.connect(self._add_key_row)
        self.key_section.add_widget(add_btn)
        
        self.main_layout.addWidget(self.key_section)
        
    def _add_key_row(self):
        """添加主键行"""
        row = KeyMappingRow(self.manual_columns, self.system_columns)
        row.deleted.connect(self._remove_key_row)
        row.changed.connect(self._emit_config_changed)
        self.key_rows.append(row)
        self.key_layout.addWidget(row)
        
    def _remove_key_row(self, row: KeyMappingRow):
        """删除主键行"""
        if len(self.key_rows) > 1:
            self.key_rows.remove(row)
            row.deleteLater()
            self._emit_config_changed()
            
    def _create_value_section(self):
        """创建数值列配置区（可折叠）"""
        self.value_section = CollapsibleSection("数值列", "📊")
        self.value_section.set_expanded(True)
        
        # 手工表数值列
        manual_layout = QHBoxLayout()
        manual_label = QLabel("手工表数值列:")
        manual_label.setStyleSheet("color: #333;")
        manual_layout.addWidget(manual_label)
        self.manual_value_combo = NoScrollComboBox()
        self.manual_value_combo.addItem("(选择列)")
        self.manual_value_combo.currentIndexChanged.connect(self._emit_config_changed)
        manual_layout.addWidget(self.manual_value_combo, 1)
        
        manual_widget = QWidget()
        manual_widget.setLayout(manual_layout)
        self.value_section.add_widget(manual_widget)
        
        # 系统表数值列
        system_layout = QHBoxLayout()
        system_label = QLabel("系统表数值列:")
        system_label.setStyleSheet("color: #333;")
        system_layout.addWidget(system_label)
        self.system_value_combo = NoScrollComboBox()
        self.system_value_combo.addItem("(选择列)")
        self.system_value_combo.currentIndexChanged.connect(self._emit_config_changed)
        system_layout.addWidget(self.system_value_combo, 1)
        
        system_widget = QWidget()
        system_widget.setLayout(system_layout)
        self.value_section.add_widget(system_widget)
        
        self.main_layout.addWidget(self.value_section)
        
    def _create_filter_section(self):
        """创建筛选配置区（可折叠）"""
        self.filter_section = CollapsibleSection("数据筛选（可选）", "🔍")
        self.filter_section.set_expanded(False)
        
        # 手工表筛选
        manual_label = QLabel("手工表筛选:")
        manual_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.filter_section.add_widget(manual_label)
        
        self.manual_filter_container = QWidget()
        self.manual_filter_layout = QVBoxLayout(self.manual_filter_container)
        self.manual_filter_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_section.add_widget(self.manual_filter_container)
        
        add_manual_filter_btn = QPushButton("➕ 添加筛选条件")
        add_manual_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #fff3e0;
                color: #e65100;
                border: 1px dashed #e65100;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #ffe0b2; }
        """)
        add_manual_filter_btn.clicked.connect(lambda: self._add_filter_row("manual"))
        self.filter_section.add_widget(add_manual_filter_btn)
        
        # 系统表筛选
        system_label = QLabel("系统表筛选:")
        system_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        self.filter_section.add_widget(system_label)
        
        self.system_filter_container = QWidget()
        self.system_filter_layout = QVBoxLayout(self.system_filter_container)
        self.system_filter_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_section.add_widget(self.system_filter_container)
        
        add_system_filter_btn = QPushButton("➕ 添加筛选条件")
        add_system_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 1px dashed #2e7d32;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c8e6c9; }
        """)
        add_system_filter_btn.clicked.connect(lambda: self._add_filter_row("system"))
        self.filter_section.add_widget(add_system_filter_btn)
        
        self.main_layout.addWidget(self.filter_section)
        
    def _add_filter_row(self, table_type: str):
        """添加筛选行"""
        if table_type == "manual":
            columns = self.manual_columns
            row = FilterRow(columns)
            row.deleted.connect(lambda r: self._remove_filter_row(r, "manual"))
            self.manual_filter_rows.append(row)
            self.manual_filter_layout.addWidget(row)
        else:
            columns = self.system_columns
            row = FilterRow(columns, self.system_unique_values)
            row.deleted.connect(lambda r: self._remove_filter_row(r, "system"))
            self.system_filter_rows.append(row)
            self.system_filter_layout.addWidget(row)
        row.changed.connect(self._emit_config_changed)
        
    def _remove_filter_row(self, row: FilterRow, table_type: str):
        """删除筛选行"""
        if table_type == "manual":
            self.manual_filter_rows.remove(row)
        else:
            self.system_filter_rows.remove(row)
        row.deleteLater()
        self._emit_config_changed()
        
    def _create_pivot_section(self):
        """创建透视配置区（可折叠）"""
        self.pivot_section = CollapsibleSection("透视列（可选）", "📈")
        self.pivot_section.set_expanded(False)
        
        # 说明
        hint = QLabel("如果系统表需要按某列进行透视汇总，请配置此项")
        hint.setStyleSheet("color: #666;")
        hint.setWordWrap(True)
        self.pivot_section.add_widget(hint)
        
        # 透视列选择
        pivot_layout = QHBoxLayout()
        pivot_layout.addWidget(QLabel("透视列:"))
        self.pivot_column_combo = NoScrollComboBox()
        self.pivot_column_combo.addItem("(不透视)")
        self.pivot_column_combo.currentIndexChanged.connect(self._on_pivot_column_changed)
        pivot_layout.addWidget(self.pivot_column_combo, 1)
        
        pivot_widget = QWidget()
        pivot_widget.setLayout(pivot_layout)
        self.pivot_section.add_widget(pivot_widget)
        
        # 透视值显示
        self.pivot_values_label = QLabel("透视值: -")
        self.pivot_values_label.setStyleSheet("color: #666; margin-top: 5px;")
        self.pivot_values_label.setWordWrap(True)
        self.pivot_section.add_widget(self.pivot_values_label)
        
        self.main_layout.addWidget(self.pivot_section)
        
    def _on_pivot_column_changed(self, index: int):
        """透视列变更"""
        column = self.pivot_column_combo.currentText()
        if column != "(不透视)" and column in self.system_unique_values:
            values = self.system_unique_values[column]
            values_str = ", ".join([str(v) for v in values[:10]])
            if len(values) > 10:
                values_str += f" ... 共{len(values)}个"
            self.pivot_values_label.setText(f"透视值: {values_str}")
        else:
            self.pivot_values_label.setText("透视值: -")
        self._emit_config_changed()
        
    def _create_formula_section(self):
        """创建差值公式配置区（可折叠）"""
        self.formula_section = CollapsibleSection("差值公式", "🧮")
        self.formula_section.set_expanded(True)
        
        # 快速选择
        quick_layout = QHBoxLayout()
        quick_label = QLabel("快速选择:")
        quick_label.setStyleSheet("color: #333;")
        quick_layout.addWidget(quick_label)
        self.formula_quick_combo = NoScrollComboBox()
        self.formula_quick_combo.addItems([
            "M - S (手工 - 系统总计)",
            "自定义..."
        ])
        self.formula_quick_combo.currentIndexChanged.connect(self._on_formula_quick_selected)
        quick_layout.addWidget(self.formula_quick_combo, 1)
        
        quick_widget = QWidget()
        quick_widget.setLayout(quick_layout)
        self.formula_section.add_widget(quick_widget)
        
        # 自定义公式
        formula_layout = QHBoxLayout()
        formula_label = QLabel("公式:")
        formula_label.setStyleSheet("color: #333;")
        formula_layout.addWidget(formula_label)
        self.formula_edit = QLineEdit()
        self.formula_edit.setText("M - S")
        self.formula_edit.setPlaceholderText("例如: M - S, M - (S - A)")
        self.formula_edit.textChanged.connect(self._emit_config_changed)
        formula_layout.addWidget(self.formula_edit, 1)
        
        formula_widget = QWidget()
        formula_widget.setLayout(formula_layout)
        self.formula_section.add_widget(formula_widget)
        
        # 变量说明
        self.formula_hint = QLabel("M = 手工数量, S = 系统总计")
        self.formula_hint.setStyleSheet("color: #666; font-style: italic;")
        self.formula_hint.setWordWrap(True)
        self.formula_section.add_widget(self.formula_hint)
        
        self.main_layout.addWidget(self.formula_section)
        
    def _on_formula_quick_selected(self, index: int):
        """快速选择公式"""
        text = self.formula_quick_combo.currentText()
        if "自定义" not in text and text:
            # 提取公式部分 - 格式如 "M - S (手工 - 系统总计)" 或 "排除XX: M - (S - A) (说明)"
            if ":" in text:
                formula = text.split(":", 1)[1].strip().split("(")[0].strip()
            else:
                formula = text.split("(")[0].strip()
            self.formula_edit.setText(formula)
            
    def update_formula_options(self, column_letters: Dict[str, str]):
        """根据字母映射动态更新公式快速选择选项
        
        Args:
            column_letters: 列名到字母的映射，如 {"__KEY__": "A", "手工数量": "B", ...}
        """
        # 保存当前公式
        current_formula = self.formula_edit.text()
        
        # 清空选项
        self.formula_quick_combo.clear()
        
        # 从column_letters获取实际的列字母
        manual_letter = column_letters.get("手工数量", "B")
        system_letter = column_letters.get("系统总计", "F")
        
        # 找出透视列（排除 KEY、手工数量、系统总计、差值、比对状态）
        pivot_letters = []
        exclude_cols = {"__KEY__", "手工数量", "系统总计", "差值", "比对状态"}
        
        for col, letter in sorted(column_letters.items(), key=lambda x: x[1]):
            if col not in exclude_cols:
                pivot_letters.append((letter, col))
        
        # 构建公式选项（使用M-S作为公式变量，显示时会替换为实际字母）
        formula_options = []
        
        # 基本选项：M - S
        formula_options.append(f"M - S (手工 - 系统总计)")
        
        # 如果有透视列，添加更多选项
        if pivot_letters:
            first_letter, first_name = pivot_letters[0]
            
            # 排除某透视列（使用列名作为变量）
            formula_options.append(
                f"排除{first_name}: M - (S - {first_name}) (排除特定透视列)"
            )
            
            # 如果有多个透视列
            if len(pivot_letters) >= 2:
                second_letter, second_name = pivot_letters[1]
                formula_options.append(
                    f"特定透视: M - ({first_name} + {second_name}) (只对比指定列)"
                )
            
            # 如果有3个及以上透视列，添加透视汇总选项
            if len(pivot_letters) >= 3:
                pivot_sum = " + ".join([p[1] for p in pivot_letters[:5]])  # 使用列名
                if len(pivot_letters) > 5:
                    pivot_sum += " + ..."
                formula_options.append(
                    f"透视汇总: M - ({pivot_sum}) (对比所有透视列)"
                )
        
        # 自定义选项
        formula_options.append("自定义...")
        
        # 更新下拉框
        self.formula_quick_combo.addItems(formula_options)
        
        # 更新变量说明（使用实际的列字母）
        hint_parts = [f"{manual_letter} = 手工数量", f"{system_letter} = 系统总计"]
        if pivot_letters:
            pivot_hints = [f"{letter}={name}" for letter, name in pivot_letters[:5]]
            if len(pivot_letters) > 5:
                pivot_hints.append("...")
            hint_parts.append("透视: " + ", ".join(pivot_hints))
        self.formula_hint.setText(" | ".join(hint_parts))
            
    def _emit_config_changed(self):
        """发射配置变更信号"""
        self.config_changed.emit()
        
    def set_columns(self, manual_columns: List[str], system_columns: List[str]):
        """设置列选项"""
        self.manual_columns = manual_columns
        self.system_columns = system_columns
        
        # 更新主键行
        for row in self.key_rows:
            row.update_columns(manual_columns, system_columns)
            
        # 更新数值列下拉框
        self.manual_value_combo.clear()
        self.manual_value_combo.addItem("(选择列)")
        self.manual_value_combo.addItems(manual_columns)
        
        self.system_value_combo.clear()
        self.system_value_combo.addItem("(选择列)")
        self.system_value_combo.addItems(system_columns)
        
        # 更新透视列下拉框
        self.pivot_column_combo.clear()
        self.pivot_column_combo.addItem("(不透视)")
        self.pivot_column_combo.addItems(system_columns)
        
    def set_system_unique_values(self, unique_values: Dict[str, List]):
        """设置系统表唯一值（用于筛选和透视）"""
        self.system_unique_values = unique_values
        for row in self.system_filter_rows:
            row.update_unique_values(unique_values)
            
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        config = {}
        
        # 主键映射
        key_mappings = []
        for row in self.key_rows:
            mapping = row.get_value()
            if mapping:
                key_mappings.append(mapping)
        config["key_mappings"] = key_mappings
        
        # 数值列
        manual_value = self.manual_value_combo.currentText()
        system_value = self.system_value_combo.currentText()
        config["value_mapping"] = {
            "manual": manual_value if manual_value != "(选择列)" else "",
            "system": system_value if system_value != "(选择列)" else ""
        }
        
        # 手工表筛选
        manual_filters = []
        for row in self.manual_filter_rows:
            f = row.get_value()
            if f:
                # 转换操作符为内部代码
                from core.compare_engine import CompareEngine
                f_converted = {
                    "column": f["column"],
                    "operator": CompareEngine.convert_operator(f["operator"]),
                    "value": f["value"]
                }
                manual_filters.append(f_converted)
        config["manual_filters"] = manual_filters
        
        # 系统表筛选
        system_filters = []
        for row in self.system_filter_rows:
            f = row.get_value()
            if f:
                # 转换操作符为内部代码
                from core.compare_engine import CompareEngine
                f_converted = {
                    "column": f["column"],
                    "operator": CompareEngine.convert_operator(f["operator"]),
                    "value": f["value"]
                }
                system_filters.append(f_converted)
        config["system_filters"] = system_filters
        
        # 透视列
        pivot_col = self.pivot_column_combo.currentText()
        if pivot_col != "(不透视)":
            config["pivot_column"] = {"system": pivot_col}
            if pivot_col in self.system_unique_values:
                config["pivot_values"] = self.system_unique_values[pivot_col]
        
        # 差值公式
        config["difference_formula"] = self.formula_edit.text().strip() or "M - S"
        
        return config
        
    def set_config(self, config: Dict[str, Any]):
        """加载配置"""
        # 主键映射
        key_mappings = config.get("key_mappings", [])
        # 清空现有行
        for row in self.key_rows[1:]:  # 保留第一行
            row.deleteLater()
        self.key_rows = self.key_rows[:1]
        
        # 设置第一行并添加其他行
        if key_mappings:
            self.key_rows[0].set_value(key_mappings[0])
            for mapping in key_mappings[1:]:
                self._add_key_row()
                self.key_rows[-1].set_value(mapping)
                
        # 数值列
        value_mapping = config.get("value_mapping", {})
        if value_mapping.get("manual"):
            idx = self.manual_value_combo.findText(value_mapping["manual"])
            if idx >= 0:
                self.manual_value_combo.setCurrentIndex(idx)
        if value_mapping.get("system"):
            idx = self.system_value_combo.findText(value_mapping["system"])
            if idx >= 0:
                self.system_value_combo.setCurrentIndex(idx)
                
        # 透视列
        pivot_config = config.get("pivot_column", {})
        if isinstance(pivot_config, dict):
            pivot_col = pivot_config.get("system", "")
        else:
            pivot_col = pivot_config
        if pivot_col:
            idx = self.pivot_column_combo.findText(pivot_col)
            if idx >= 0:
                self.pivot_column_combo.setCurrentIndex(idx)
                
        # 差值公式
        formula = config.get("difference_formula", "M - S")
        self.formula_edit.setText(formula)
