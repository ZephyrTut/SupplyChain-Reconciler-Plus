"""
PyQt6 配置面板 - 主键映射、筛选、透视、公式配置
"""
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QGroupBox,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


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
        self.manual_combo = QComboBox()
        self.manual_combo.addItem("(选择列)")
        self.manual_combo.addItems(self.manual_columns)
        self.manual_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.manual_combo, 1)
        
        # 映射符号
        arrow = QLabel("↔")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(arrow)
        
        # 系统表列
        self.system_combo = QComboBox()
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
    """筛选条件行"""
    
    OPERATORS = ["等于", "不等于", "包含", "不包含", "大于", "小于"]
    
    def __init__(self, columns: List[str], unique_values: Dict[str, List] = None, parent=None):
        self.columns = columns
        self.unique_values = unique_values or {}
        super().__init__(parent)
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # 列选择
        self.column_combo = QComboBox()
        self.column_combo.addItem("(选择列)")
        self.column_combo.addItems(self.columns)
        self.column_combo.currentIndexChanged.connect(self._on_column_changed)
        layout.addWidget(self.column_combo, 1)
        
        # 操作符
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(self.OPERATORS)
        self.operator_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.operator_combo)
        
        # 值（下拉框，支持唯一值）
        self.value_combo = QComboBox()
        self.value_combo.setEditable(True)
        self.value_combo.setMinimumWidth(120)
        self.value_combo.currentTextChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.value_combo, 1)
        
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
        
    def _on_column_changed(self, index: int):
        """列选择变更，更新唯一值"""
        self.value_combo.clear()
        column = self.column_combo.currentText()
        if column in self.unique_values:
            values = [str(v) for v in self.unique_values[column] if v is not None]
            self.value_combo.addItems(values[:100])  # 限制100个
        self.changed.emit()
        
    def get_value(self) -> Dict:
        column = self.column_combo.currentText()
        operator = self.operator_combo.currentText()
        value = self.value_combo.currentText()
        if column != "(选择列)" and value:
            return {"column": column, "operator": operator, "value": value}
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
            self.value_combo.setCurrentText(str(value["value"]))
            
    def update_unique_values(self, unique_values: Dict[str, List]):
        """更新唯一值字典"""
        self.unique_values = unique_values
        self._on_column_changed(self.column_combo.currentIndex())


class CollapsibleSection(QWidget):
    """可折叠区块"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        self.header = QPushButton(f"▼ {title}")
        self.header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                background-color: #f5f5f5;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.header.clicked.connect(self.toggle)
        layout.addWidget(self.header)
        
        # 内容区
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.content)
        
        self._title = title
        
    def toggle(self):
        """切换展开/折叠"""
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        arrow = "▼" if self._expanded else "▶"
        self.header.setText(f"{arrow} {self._title}")
        
    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        self._expanded = expanded
        self.content.setVisible(expanded)
        arrow = "▼" if expanded else "▶"
        self.header.setText(f"{arrow} {self._title}")
        
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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background-color: #fafafa; }")
        
        # 主容器
        container = QWidget()
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
        """创建主键配置区"""
        group = QGroupBox("🔑 主键映射")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout(group)
        
        # 说明
        hint = QLabel("配置用于匹配的主键字段（支持多字段复合主键）")
        hint.setStyleSheet("color: #666; font-weight: normal;")
        layout.addWidget(hint)
        
        # 行容器
        self.key_container = QWidget()
        self.key_layout = QVBoxLayout(self.key_container)
        self.key_layout.setContentsMargins(0, 0, 0, 0)
        self.key_layout.setSpacing(5)
        layout.addWidget(self.key_container)
        
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
        layout.addWidget(add_btn)
        
        self.main_layout.addWidget(group)
        
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
        """创建数值列配置区"""
        group = QGroupBox("📊 数值列")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # 手工表数值列
        layout.addWidget(QLabel("手工表数值列:"), 0, 0)
        self.manual_value_combo = QComboBox()
        self.manual_value_combo.addItem("(选择列)")
        self.manual_value_combo.currentIndexChanged.connect(self._emit_config_changed)
        layout.addWidget(self.manual_value_combo, 0, 1)
        
        # 系统表数值列
        layout.addWidget(QLabel("系统表数值列:"), 1, 0)
        self.system_value_combo = QComboBox()
        self.system_value_combo.addItem("(选择列)")
        self.system_value_combo.currentIndexChanged.connect(self._emit_config_changed)
        layout.addWidget(self.system_value_combo, 1, 1)
        
        self.main_layout.addWidget(group)
        
    def _create_filter_section(self):
        """创建筛选配置区（可折叠）"""
        self.filter_section = CollapsibleSection("🔍 数据筛选（可选）")
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
        self.pivot_section = CollapsibleSection("📈 透视列（可选）")
        self.pivot_section.set_expanded(False)
        
        # 说明
        hint = QLabel("如果系统表需要按某列进行透视汇总，请配置此项")
        hint.setStyleSheet("color: #666;")
        hint.setWordWrap(True)
        self.pivot_section.add_widget(hint)
        
        # 透视列选择
        pivot_layout = QHBoxLayout()
        pivot_layout.addWidget(QLabel("透视列:"))
        self.pivot_column_combo = QComboBox()
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
        """创建差值公式配置区"""
        group = QGroupBox("🧮 差值公式")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout(group)
        
        # 快速选择
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("快速选择:"))
        self.formula_quick_combo = QComboBox()
        self.formula_quick_combo.addItems([
            "M - S (手工 - 系统总计)",
            "自定义..."
        ])
        self.formula_quick_combo.currentIndexChanged.connect(self._on_formula_quick_selected)
        quick_layout.addWidget(self.formula_quick_combo, 1)
        layout.addLayout(quick_layout)
        
        # 自定义公式
        formula_layout = QHBoxLayout()
        formula_layout.addWidget(QLabel("公式:"))
        self.formula_edit = QLineEdit()
        self.formula_edit.setText("M - S")
        self.formula_edit.setPlaceholderText("例如: M - S, M - (S - A)")
        self.formula_edit.textChanged.connect(self._emit_config_changed)
        formula_layout.addWidget(self.formula_edit, 1)
        layout.addLayout(formula_layout)
        
        # 变量说明
        self.formula_hint = QLabel("M = 手工数量, S = 系统总计")
        self.formula_hint.setStyleSheet("color: #666; font-style: italic;")
        self.formula_hint.setWordWrap(True)
        layout.addWidget(self.formula_hint)
        
        self.main_layout.addWidget(group)
        
    def _on_formula_quick_selected(self, index: int):
        """快速选择公式"""
        text = self.formula_quick_combo.currentText()
        if "自定义" not in text:
            # 提取公式部分
            formula = text.split("(")[0].strip()
            self.formula_edit.setText(formula)
            
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
                manual_filters.append(f)
        config["manual_filters"] = manual_filters
        
        # 系统表筛选
        system_filters = []
        for row in self.system_filter_rows:
            f = row.get_value()
            if f:
                system_filters.append(f)
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
