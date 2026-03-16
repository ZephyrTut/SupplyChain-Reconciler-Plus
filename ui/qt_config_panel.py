"""
PyQt6 配置面板 - 主键映射、筛选、透视、公式配置
"""
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QGroupBox,
    QSizePolicy, QSpacerItem, QCheckBox, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
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
class MultiSelectValueDialog(QDialog):
    """多值选择弹窗（用于包含于/不包含于）"""

    def __init__(self, title: str, values: List[str], selected_values: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(420, 520)

        self._all_values = [str(v) for v in values if str(v).strip()]
        self._selected_values = set([str(v).strip() for v in selected_values if str(v).strip()])

        self._setup_ui()
        self._load_items()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键字过滤，如：入库")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)

        quick_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("全选")
        self.btn_clear_all = QPushButton("清空")
        self.btn_select_all.clicked.connect(self._select_all_visible)
        self.btn_clear_all.clicked.connect(self._clear_all_visible)
        quick_layout.addWidget(self.btn_select_all)
        quick_layout.addWidget(self.btn_clear_all)
        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(lambda _: self._refresh_count_label())
        self.list_widget.viewport().installEventFilter(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.list_widget, 1)

        self.count_label = QLabel("已选 0 项")
        self.count_label.setStyleSheet("color: #666;")
        layout.addWidget(self.count_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        ok_btn = QPushButton("确定")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def eventFilter(self, obj, event):
        if obj is self.list_widget.viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            item = self.list_widget.itemAt(event.position().toPoint())
            if item:
                rect = self.list_widget.visualItemRect(item)
                # 左侧约24px保留给默认复选框点击，其他区域点击时手动切换
                if event.position().x() > rect.left() + 24:
                    self._toggle_item_check_state(item)
                    return True
        return super().eventFilter(obj, event)

    def _toggle_item_check_state(self, item: QListWidgetItem):
        new_state = (
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        item.setCheckState(new_state)
        self._refresh_count_label()

    def _load_items(self):
        self.list_widget.clear()
        for value in self._all_values:
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if value in self._selected_values else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)
        self._refresh_count_label()

    def _filter_items(self, text: str):
        keyword = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(keyword not in item.text().lower() if keyword else False)

    def _select_all_visible(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
        self._refresh_count_label()

    def _clear_all_visible(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
        self._refresh_count_label()

    def _refresh_count_label(self):
        self.count_label.setText(f"已选 {len(self.get_selected_values())} 项")

    def get_selected_values(self) -> List[str]:
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected


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
        self._selected_multiselect_values: List[str] = []
        super().__init__(parent)
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(8)
        
        # 列选择
        self.column_combo = NoScrollComboBox()
        self.column_combo.setMinimumWidth(100)
        self.column_combo.setMaximumWidth(150)
        self.column_combo.addItem("(选择列)")
        self.column_combo.addItems(self.columns)
        self.column_combo.currentIndexChanged.connect(self._on_column_changed)
        layout.addWidget(self.column_combo)
        
        # 操作符
        self.operator_combo = NoScrollComboBox()
        self.operator_combo.setMinimumWidth(70)
        self.operator_combo.setMaximumWidth(90)
        self.operator_combo.addItems(self.OPERATORS)
        self.operator_combo.currentIndexChanged.connect(self._on_operator_changed)
        layout.addWidget(self.operator_combo)
        
        # 值输入区域容器
        self.value_container = QWidget()
        self.value_layout = QHBoxLayout(self.value_container)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.value_layout.setSpacing(5)
        layout.addWidget(self.value_container, 1)
        
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
        
        # 输入框
        self.value_edit = QLineEdit()
        self.value_edit.setMinimumWidth(150)
        operator = self.operator_combo.currentText()
        if operator in ["大于", "小于"]:
            self.value_edit.setPlaceholderText("输入数值")
        else:
            self.value_edit.setPlaceholderText("多值用逗号分隔，如: 发货,退仓")
        self.value_edit.textChanged.connect(lambda: self.changed.emit())
        self.value_layout.addWidget(self.value_edit)
        self._current_value_widget = "input"
    
    def _on_input_changed(self):
        """输入框内容变化"""
        self.changed.emit()
    
    def _create_multiselect_widget(self):
        """创建多选复选框控件（包含于）"""
        self._clear_value_widget()

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(6)

        self.multiselect_summary_label = QLabel()
        self.multiselect_summary_label.setMinimumWidth(160)
        self.multiselect_summary_label.setStyleSheet("color: #333;")
        wrapper_layout.addWidget(self.multiselect_summary_label, 1)

        self.multiselect_btn = QPushButton("选择...")
        self.multiselect_btn.setFixedHeight(28)
        self.multiselect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 0 10px;
            }
            QPushButton:hover {
                border-color: #2196F3;
                background-color: #f0f7ff;
            }
        """)
        self.multiselect_btn.clicked.connect(self._open_multiselect_dialog)
        wrapper_layout.addWidget(self.multiselect_btn)

        self.value_layout.addWidget(wrapper)

        # 保留仍存在于当前可选值中的已选项
        current_options = set(self._get_current_column_values())
        self._selected_multiselect_values = [
            v for v in self._selected_multiselect_values if v in current_options
        ]
        self._refresh_multiselect_summary()
        self._current_value_widget = "multiselect"

    def _get_current_column_values(self) -> List[str]:
        """获取当前列的唯一值列表（最多200个）。"""
        column = self.column_combo.currentText()
        if column not in self.unique_values:
            return []
        return [str(v) for v in self.unique_values[column] if v is not None][:200]

    def _open_multiselect_dialog(self):
        """打开多选弹窗。"""
        options = self._get_current_column_values()
        if not options:
            self._refresh_multiselect_summary()
            return

        dialog = MultiSelectValueDialog(
            "选择筛选值",
            options,
            self._selected_multiselect_values,
            self
        )
        if dialog.exec():
            self._selected_multiselect_values = dialog.get_selected_values()
            self._refresh_multiselect_summary()
            self.changed.emit()

    def _refresh_multiselect_summary(self):
        """刷新多选摘要显示。"""
        options_count = len(self._get_current_column_values())
        selected_count = len(self._selected_multiselect_values)

        if options_count == 0:
            self.multiselect_summary_label.setText("当前列暂无可选值")
            if hasattr(self, 'multiselect_btn'):
                self.multiselect_btn.setEnabled(False)
            return

        if hasattr(self, 'multiselect_btn'):
            self.multiselect_btn.setEnabled(True)

        if selected_count == 0:
            self.multiselect_summary_label.setText(f"共 {options_count} 项，未选择")
            return

        preview = "，".join(self._selected_multiselect_values[:2])
        if selected_count > 2:
            preview += f" 等{selected_count}项"
        self.multiselect_summary_label.setText(preview)
    
    def _on_checkbox_changed(self):
        """复选框状态变化"""
        self.changed.emit()
    
    def _update_dropdown_values(self):
        """更新下拉框的唯一值"""
        if not hasattr(self, 'value_combo'):
            return
        self.value_combo.clear()
        column = self.column_combo.currentText()
        if column in self.unique_values:
            values = [str(v) for v in self.unique_values[column] if v is not None]
            self.value_combo.addItems(values[:200])
        
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
            value = ",".join(self._selected_multiselect_values)
        
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
                selected_values = [v.strip() for v in val_str.split(",") if v.strip()]
                current_options = set(self._get_current_column_values())
                self._selected_multiselect_values = [v for v in selected_values if v in current_options]
                self._refresh_multiselect_summary()
            
    def update_unique_values(self, unique_values: Dict[str, List]):
        """更新唯一值字典"""
        self.unique_values = unique_values
        operator = self.operator_combo.currentText()
        if operator in self.DROPDOWN_OPERATORS:
            self._update_dropdown_values()
        elif operator in self.MULTISELECT_OPERATORS:
            self._create_multiselect_widget()


class ColumnCleanRow(DynamicRow):
    """列数据清洗行 - 三行布局"""
    
    # 预设清洗规则
    CLEAN_PRESETS = [
        ("去中文", r"[\u4e00-\u9fa5]+"),
        ("去末尾英文", r"[a-zA-Z]+$"),
        ("去开头英文", r"^[a-zA-Z]+"),
        ("只留数字", r"[^\d]+"),
        ("去特殊符号", r"[^\w\s\u4e00-\u9fa5]+"),
        ("去空格", r"^\s+|\s+$"),
    ]
    
    def __init__(self, columns: List[str], parent=None):
        self.columns = columns
        self._checkboxes: Dict[str, QCheckBox] = {}
        super().__init__(parent)
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)
        main_layout.setSpacing(2)
        
        # 第一行：列选择 + 删除
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        
        col_label = QLabel("列:")
        col_label.setStyleSheet("color: #666; font-size: 10px;")
        row1.addWidget(col_label)
        
        self.column_combo = NoScrollComboBox()
        self.column_combo.addItem("(选择列)")
        self.column_combo.addItems(self.columns)
        self.column_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        self.column_combo.setMinimumWidth(80)
        row1.addWidget(self.column_combo, 1)
        
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(18, 18)
        del_btn.setStyleSheet("""
            QPushButton { background-color: #ffebee; color: #f44336; border: none; border-radius: 9px; font-size: 10px; }
            QPushButton:hover { background-color: #f44336; color: white; }
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self))
        row1.addWidget(del_btn)
        main_layout.addLayout(row1)
        
        # 第二行：预设规则（前3个）
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        for i, (preset_name, _) in enumerate(self.CLEAN_PRESETS[:3]):
            cb = QCheckBox(preset_name)
            cb.setStyleSheet("QCheckBox { color: #333; font-size: 10px; }")
            cb.stateChanged.connect(lambda: self.changed.emit())
            self._checkboxes[preset_name] = cb
            row2.addWidget(cb)
        row2.addStretch()
        main_layout.addLayout(row2)
        
        # 第三行：预设规则（后3个）+ 自定义
        row3 = QHBoxLayout()
        row3.setSpacing(4)
        for i, (preset_name, _) in enumerate(self.CLEAN_PRESETS[3:]):
            cb = QCheckBox(preset_name)
            cb.setStyleSheet("QCheckBox { color: #333; font-size: 10px; }")
            cb.stateChanged.connect(lambda: self.changed.emit())
            self._checkboxes[preset_name] = cb
            row3.addWidget(cb)
        
        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText("自定义")
        self.custom_edit.setMaximumWidth(60)
        self.custom_edit.setStyleSheet("font-size: 10px; padding: 1px 3px;")
        self.custom_edit.textChanged.connect(lambda: self.changed.emit())
        row3.addWidget(self.custom_edit)
        row3.addStretch()
        main_layout.addLayout(row3)
        
    def get_value(self) -> Dict:
        column = self.column_combo.currentText()
        if column == "(选择列)":
            return {}
        
        # 收集选中的规则
        selected_presets = []
        regexes = []
        
        for preset_name, preset_regex in self.CLEAN_PRESETS:
            if self._checkboxes[preset_name].isChecked():
                selected_presets.append(preset_name)
                regexes.append(preset_regex)
        
        # 自定义符号
        custom_text = self.custom_edit.text().strip()
        if custom_text:
            selected_presets.append(f"去除'{custom_text}'")
            # 转义特殊正则字符
            import re
            escaped = re.escape(custom_text)
            regexes.append(escaped)
        
        if not regexes:
            return {}
        
        return {
            "column": column,
            "mode": "删除匹配",
            "preset": " + ".join(selected_presets),
            "regexes": regexes,
        }
        
    def set_value(self, value: Dict):
        if "column" in value:
            idx = self.column_combo.findText(value["column"])
            if idx >= 0:
                self.column_combo.setCurrentIndex(idx)
        
        # 恢复选中的预设
        preset_str = value.get("preset", "")
        for preset_name, _ in self.CLEAN_PRESETS:
            self._checkboxes[preset_name].setChecked(preset_name in preset_str)
        
        # 恢复自定义符号（从preset中提取）
        import re
        match = re.search(r"去除'([^']+)'", preset_str)
        if match:
            self.custom_edit.setText(match.group(1))


class CollapsibleSection(QWidget):
    """可折叠区块"""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._expanded = True
        self._icon = icon
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 3)
        layout.setSpacing(0)
        
        # 标题栏
        display_title = f"{self._icon} {title}" if self._icon else title
        self.header = QPushButton(f"▼ {display_title}")
        self.header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 10px;
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
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
                border-radius: 0 0 4px 4px;
            }
            QLabel {
                color: #333333;
                background-color: transparent;
                border: none;
            }
        """)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 8, 10, 8)
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
    export_preview_requested = pyqtSignal()  # 导出手工表预处理预览信号
    export_system_requested = pyqtSignal()   # 导出系统表预处理预览信号
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        
        self.compact = compact
        self.manual_columns: List[str] = []
        self.system_columns: List[str] = []
        self.manual_unique_values: Dict[str, List] = {}  # 手工表唯一值
        self.system_unique_values: Dict[str, List] = {}  # 系统表唯一值
        
        self.key_rows: List[KeyMappingRow] = []
        self.manual_filter_rows: List[FilterRow] = []
        self.system_filter_rows: List[FilterRow] = []
        self.manual_exception_rows: List[FilterRow] = []
        self.system_exception_rows: List[FilterRow] = []
        self.clean_rows: List[ColumnCleanRow] = []  # 列清洗行
        self._updating_formula_options = False
        
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
        
        # 3. 筛选配置（可折叠）- 包含列清洗和手工表透视
        self._create_filter_section()
        
        # 4. 系统表透视配置（可折叠）
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
        """创建筛选配置区（可折叠）- 包含列清洗和手工表透视"""
        self.filter_section = CollapsibleSection("数据筛选与预处理（可选）", "🔍")
        self.filter_section.set_expanded(False)
        
        # === 手工表数据预处理 ===
        preprocess_label = QLabel("🧹 手工表数据预处理:")
        preprocess_label.setStyleSheet("font-weight: bold; color: #c2185b;")
        self.filter_section.add_widget(preprocess_label)
        
        preprocess_hint = QLabel("使用正则清洗列数据（如去除中文）")
        preprocess_hint.setStyleSheet("color: #999; font-size: 11px;")
        self.filter_section.add_widget(preprocess_hint)
        
        # 清洗行容器
        self.clean_container = QWidget()
        self.clean_layout = QVBoxLayout(self.clean_container)
        self.clean_layout.setContentsMargins(0, 0, 0, 0)
        self.clean_layout.setSpacing(5)
        self.filter_section.add_widget(self.clean_container)
        
        add_clean_btn = QPushButton("➕ 添加清洗规则")
        add_clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #fce4ec;
                color: #c2185b;
                border: 1px dashed #c2185b;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #f8bbd0; }
        """)
        add_clean_btn.clicked.connect(self._add_clean_row)
        self.filter_section.add_widget(add_clean_btn)
        
        # 分隔线
        separator1 = QWidget()
        separator1.setFixedHeight(1)
        separator1.setStyleSheet("background-color: #ddd; margin: 10px 0;")
        self.filter_section.add_widget(separator1)
        
        # === 手工表筛选 ===
        manual_label = QLabel("📋 手工表筛选:")
        manual_label.setStyleSheet("font-weight: bold; color: #e65100;")
        self.filter_section.add_widget(manual_label)
        
        manual_hint = QLabel("💡 使用【包含于】或【包含】筛选多值时，可配置透视计算（出库-入库）")
        manual_hint.setStyleSheet("color: #1565c0; font-size: 11px;")
        manual_hint.setWordWrap(True)
        self.filter_section.add_widget(manual_hint)
        
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

        # 手工表例外保留
        manual_exception_hint = QLabel("🛟 例外保留（满足任一即可保留）：主筛选 OR 例外保留")
        manual_exception_hint.setStyleSheet("color: #8e24aa; font-size: 11px;")
        manual_exception_hint.setWordWrap(True)
        self.filter_section.add_widget(manual_exception_hint)

        self.manual_exception_container = QWidget()
        self.manual_exception_layout = QVBoxLayout(self.manual_exception_container)
        self.manual_exception_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_section.add_widget(self.manual_exception_container)

        add_manual_exception_btn = QPushButton("➕ 添加例外保留")
        add_manual_exception_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3e5f5;
                color: #6a1b9a;
                border: 1px dashed #8e24aa;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #e1bee7; }
        """)
        add_manual_exception_btn.clicked.connect(lambda: self._add_exception_row("manual"))
        self.filter_section.add_widget(add_manual_exception_btn)
        
        # === 手工表透视配置区域（独立区域，在筛选下方）===
        self.manual_pivot_container = QWidget()
        self.manual_pivot_container.setVisible(False)  # 默认隐藏
        self.manual_pivot_container.setStyleSheet("""
            QWidget {
                background-color: #f0f7ff;
                border: 1px solid #bbdefb;
                border-radius: 4px;
            }
        """)
        pivot_layout = QVBoxLayout(self.manual_pivot_container)
        pivot_layout.setContentsMargins(8, 8, 8, 8)
        pivot_layout.setSpacing(5)
        
        # 透视标题
        pivot_title = QLabel("📊 透视计算（基于筛选值）")
        pivot_title.setStyleSheet("color: #1565c0; font-weight: bold; border: none; background: transparent;")
        pivot_layout.addWidget(pivot_title)
        
        # 出库行
        out_row = QHBoxLayout()
        out_label = QLabel("📤 出库:")
        out_label.setStyleSheet("color: #1976D2; border: none; background: transparent;")
        out_label.setFixedWidth(50)
        out_row.addWidget(out_label)
        
        self.pivot_out_container = QWidget()
        self.pivot_out_container.setStyleSheet("border: none; background: transparent;")
        self.pivot_out_layout = QHBoxLayout(self.pivot_out_container)
        self.pivot_out_layout.setContentsMargins(0, 0, 0, 0)
        self.pivot_out_layout.setSpacing(10)
        out_row.addWidget(self.pivot_out_container, 1)
        pivot_layout.addLayout(out_row)
        
        # 入库行
        in_row = QHBoxLayout()
        in_label = QLabel("📥 入库:")
        in_label.setStyleSheet("color: #388E3C; border: none; background: transparent;")
        in_label.setFixedWidth(50)
        in_row.addWidget(in_label)
        
        self.pivot_in_container = QWidget()
        self.pivot_in_container.setStyleSheet("border: none; background: transparent;")
        self.pivot_in_layout = QHBoxLayout(self.pivot_in_container)
        self.pivot_in_layout.setContentsMargins(0, 0, 0, 0)
        self.pivot_in_layout.setSpacing(10)
        in_row.addWidget(self.pivot_in_container, 1)
        pivot_layout.addLayout(in_row)
        
        # 说明
        pivot_hint = QLabel("💡 手工数量 = Σ出库 - Σ入库")
        pivot_hint.setStyleSheet("color: #666; font-style: italic; border: none; background: transparent;")
        pivot_layout.addWidget(pivot_hint)
        
        self.filter_section.add_widget(self.manual_pivot_container)
        
        # 存储透视复选框
        self._pivot_out_checkboxes: List[QCheckBox] = []
        self._pivot_in_checkboxes: List[QCheckBox] = []
        
        # 分隔线
        separator2 = QWidget()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #ddd; margin: 10px 0;")
        self.filter_section.add_widget(separator2)
        
        # === 系统表筛选 ===
        system_label = QLabel("📋 系统表筛选:")
        system_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
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

        # 系统表例外保留
        system_exception_hint = QLabel("🛟 例外保留（满足任一即可保留）：主筛选 OR 例外保留")
        system_exception_hint.setStyleSheet("color: #8e24aa; font-size: 11px;")
        system_exception_hint.setWordWrap(True)
        self.filter_section.add_widget(system_exception_hint)

        self.system_exception_container = QWidget()
        self.system_exception_layout = QVBoxLayout(self.system_exception_container)
        self.system_exception_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_section.add_widget(self.system_exception_container)

        add_system_exception_btn = QPushButton("➕ 添加例外保留")
        add_system_exception_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3e5f5;
                color: #6a1b9a;
                border: 1px dashed #8e24aa;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #e1bee7; }
        """)
        add_system_exception_btn.clicked.connect(lambda: self._add_exception_row("system"))
        self.filter_section.add_widget(add_system_exception_btn)
        
        # 分隔线
        separator3 = QWidget()
        separator3.setFixedHeight(1)
        separator3.setStyleSheet("background-color: #ddd; margin: 10px 0;")
        self.filter_section.add_widget(separator3)
        
        # 导出手工表预览按钮
        export_preview_btn = QPushButton("📋 导出手工表预处理 (Excel)")
        export_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8eaf6;
                color: #3f51b5;
                border: 1px solid #3f51b5;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c5cae9; }
        """)
        export_preview_btn.clicked.connect(self._request_export_preview)
        self.filter_section.add_widget(export_preview_btn)
        
        # 导出系统表预览按钮
        export_system_btn = QPushButton("📋 导出系统表预处理 (Excel)")
        export_system_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 1px solid #2e7d32;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c8e6c9; }
        """)
        export_system_btn.clicked.connect(self._request_export_system)
        self.filter_section.add_widget(export_system_btn)
        
        self.main_layout.addWidget(self.filter_section)
    
    def _request_export_preview(self):
        """请求导出手工表预处理预览"""
        self.export_preview_requested.emit()
    
    def _request_export_system(self):
        """请求导出系统表预处理预览"""
        self.export_system_requested.emit()
    
    def _add_clean_row(self):
        """添加清洗行"""
        row = ColumnCleanRow(self.manual_columns)
        row.deleted.connect(self._remove_clean_row)
        row.changed.connect(self._emit_config_changed)
        self.clean_rows.append(row)
        self.clean_layout.addWidget(row)
        
    def _remove_clean_row(self, row: ColumnCleanRow):
        """删除清洗行"""
        self.clean_rows.remove(row)
        row.deleteLater()
        self._emit_config_changed()
        
    def _add_filter_row(self, table_type: str):
        """添加筛选行"""
        if table_type == "manual":
            columns = self.manual_columns
            row = FilterRow(columns, self.manual_unique_values)  # 传入手工表唯一值
            row.deleted.connect(lambda r: self._remove_filter_row(r, "manual"))
            row.changed.connect(self._update_manual_pivot_config)  # 连接更新透视配置
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
            self._update_manual_pivot_config()  # 删除后更新透视配置
        else:
            self.system_filter_rows.remove(row)
        row.deleteLater()
        self._emit_config_changed()

    def _add_exception_row(self, table_type: str):
        """添加例外保留行"""
        if table_type == "manual":
            row = FilterRow(self.manual_columns, self.manual_unique_values)
            row.deleted.connect(lambda r: self._remove_exception_row(r, "manual"))
            self.manual_exception_rows.append(row)
            self.manual_exception_layout.addWidget(row)
        else:
            row = FilterRow(self.system_columns, self.system_unique_values)
            row.deleted.connect(lambda r: self._remove_exception_row(r, "system"))
            self.system_exception_rows.append(row)
            self.system_exception_layout.addWidget(row)
        row.changed.connect(self._emit_config_changed)

    def _remove_exception_row(self, row: FilterRow, table_type: str):
        """删除例外保留行"""
        if table_type == "manual":
            if row in self.manual_exception_rows:
                self.manual_exception_rows.remove(row)
        else:
            if row in self.system_exception_rows:
                self.system_exception_rows.remove(row)
        row.deleteLater()
        self._emit_config_changed()
    
    def _update_manual_pivot_config(self):
        """更新手工表透视配置（独立区域）"""
        # 收集所有手工表筛选行的多值
        all_values = []
        for row in self.manual_filter_rows:
            operator = row.operator_combo.currentText()
            # 只有"包含"或"包含于"操作符才支持透视
            if operator in ["包含", "包含于"]:
                # 从 get_value 获取值
                filter_data = row.get_value()
                if filter_data and "value" in filter_data:
                    value_str = str(filter_data["value"])
                    # 解析多值
                    values = [v.strip() for v in value_str.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    if len(values) >= 2:
                        all_values.extend(values)
        
        # 去重
        all_values = list(dict.fromkeys(all_values))
        
        # 显示或隐藏透视配置区域
        show_pivot = len(all_values) >= 2
        self.manual_pivot_container.setVisible(show_pivot)
        
        if show_pivot:
            # 清空现有复选框
            for cb in self._pivot_out_checkboxes + self._pivot_in_checkboxes:
                cb.deleteLater()
            self._pivot_out_checkboxes.clear()
            self._pivot_in_checkboxes.clear()
            
            # 为每个值创建出库/入库复选框
            for val in all_values:
                # 出库复选框
                out_cb = QCheckBox(val)
                out_cb.setStyleSheet("color: #1976D2; border: none; background: transparent;")
                out_cb.stateChanged.connect(self._emit_config_changed)
                self.pivot_out_layout.addWidget(out_cb)
                self._pivot_out_checkboxes.append(out_cb)
                
                # 入库复选框
                in_cb = QCheckBox(val)
                in_cb.setStyleSheet("color: #388E3C; border: none; background: transparent;")
                in_cb.stateChanged.connect(self._emit_config_changed)
                self.pivot_in_layout.addWidget(in_cb)
                self._pivot_in_checkboxes.append(in_cb)
        
    def _create_pivot_section(self):
        """创建系统表透视配置区（可折叠）"""
        self.pivot_section = CollapsibleSection("系统表透视（可选）", "📈")
        self.pivot_section.set_expanded(False)
        
        # 说明
        hint = QLabel("如果系统表需要按某列进行透视汇总（如订单状态、月份等），请配置此项")
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
        # 处理“重复选择同一项”场景（模板加载后常见）
        self.formula_quick_combo.activated.connect(self._on_formula_quick_selected)
        self.formula_quick_combo.currentTextChanged.connect(lambda _: self._on_formula_quick_selected(self.formula_quick_combo.currentIndex()))
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
        self.formula_edit.setText("C - B")  # 默认：手工数量(C) - 系统总计(B)（无透视列时）
        self.formula_edit.setPlaceholderText("例如: E - D, F - (D - B)")
        self.formula_edit.textChanged.connect(self._emit_config_changed)
        formula_layout.addWidget(self.formula_edit, 1)
        
        formula_widget = QWidget()
        formula_widget.setLayout(formula_layout)
        self.formula_section.add_widget(formula_widget)
        
        # 变量说明
        self.formula_hint = QLabel("B=系统总计, C=手工数量")
        self.formula_hint.setStyleSheet("color: #666; font-style: italic;")
        self.formula_hint.setWordWrap(True)
        self.formula_section.add_widget(self.formula_hint)
        
        self.main_layout.addWidget(self.formula_section)
        
    def _on_formula_quick_selected(self, index: int):
        """快速选择公式"""
        if self._updating_formula_options:
            return

        if index < 0 or index >= self.formula_quick_combo.count():
            return

        text = self.formula_quick_combo.itemText(index)
        if "自定义" not in text and text:
            # 提取公式部分 - 格式如 "B - F (手工 - 系统总计)" 或 "B - (F - C) (排除XX)"
            # 找到最后一个括号说明，取其前面的公式部分
            import re
            # 移除末尾的中文说明括号
            match = re.match(r'^(.+?)\s*\([^()]*[\u4e00-\u9fa5][^()]*\)\s*$', text)
            if match:
                formula = match.group(1).strip()
            else:
                formula = text.strip()
            self.formula_edit.setText(formula)
            
    def update_formula_options(self, column_letters: Dict[str, str]):
        """根据字母映射动态更新公式快速选择选项
        
        Args:
            column_letters: 列名到字母的映射，如 {"__KEY__": "A", "手工数量": "B", ...}
        """
        # 保存当前状态
        current_formula = self.formula_edit.text()
        selected_quick_text = self.formula_quick_combo.currentText()

        # 更新选项时避免触发公式重置
        self._updating_formula_options = True
        self.formula_quick_combo.blockSignals(True)
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
        
        # 构建公式选项（直接使用实际列字母）
        formula_options = []
        
        # 基本选项：手工 - 系统总计
        formula_options.append(f"{manual_letter} - {system_letter} (手工 - 系统总计)")
        
        # 如果有透视列，添加更多选项
        if pivot_letters:
            first_letter, first_name = pivot_letters[0]
            
            # 排除某透视列
            formula_options.append(
                f"{manual_letter} - ({system_letter} - {first_letter}) (排除{first_name})"
            )
            
            # 如果有多个透视列
            if len(pivot_letters) >= 2:
                second_letter, second_name = pivot_letters[1]
                formula_options.append(
                    f"{manual_letter} - ({first_letter} + {second_letter}) (只对比{first_name}+{second_name})"
                )
            
            # 如果有3个及以上透视列，添加透视汇总选项
            if len(pivot_letters) >= 3:
                pivot_sum = " + ".join([p[0] for p in pivot_letters[:5]])  # 使用字母
                if len(pivot_letters) > 5:
                    pivot_sum += " + ..."
                formula_options.append(
                    f"{manual_letter} - ({pivot_sum}) (对比所有透视列)"
                )
        
        # 自定义选项
        formula_options.append("自定义...")
        
        # 更新下拉框
        self.formula_quick_combo.addItems(formula_options)

        # 尽量恢复用户之前选中的快速选项
        restore_idx = self.formula_quick_combo.findText(selected_quick_text)
        if restore_idx >= 0:
            self.formula_quick_combo.setCurrentIndex(restore_idx)
        else:
            custom_idx = self.formula_quick_combo.findText("自定义...")
            if custom_idx >= 0:
                self.formula_quick_combo.setCurrentIndex(custom_idx)

        self.formula_quick_combo.blockSignals(False)
        self._updating_formula_options = False
        
        # 同时更新公式输入框为默认公式（如果当前是旧格式或为空）
        current = self.formula_edit.text().strip()
        if not current or current in ("M - S", "B - C", "C - B"):
            self.formula_edit.setText(f"{manual_letter} - {system_letter}")
        
        # 更新变量说明（显示列字母对照）
        hint_parts = [f"{system_letter}=系统总计", f"{manual_letter}=手工数量"]
        if pivot_letters:
            pivot_hints = [f"{letter}={name}" for letter, name in pivot_letters[:5]]
            if len(pivot_letters) > 5:
                pivot_hints.append("...")
            hint_parts = pivot_hints + hint_parts  # 透视列在前
        hint_text = " | ".join(hint_parts)
        self.formula_hint.setText(hint_text)
            
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
        
        # 更新系统表透视列下拉框
        self.pivot_column_combo.clear()
        self.pivot_column_combo.addItem("(不透视)")
        self.pivot_column_combo.addItems(system_columns)
        
        # 更新清洗行的列选项
        for row in self.clean_rows:
            current_col = row.column_combo.currentText()
            row.column_combo.clear()
            row.column_combo.addItem("(选择列)")
            row.column_combo.addItems(manual_columns)
            if current_col in manual_columns:
                row.column_combo.setCurrentText(current_col)
        
    def set_system_unique_values(self, unique_values: Dict[str, List]):
        """设置系统表唯一值（用于筛选和透视）"""
        self.system_unique_values = unique_values
        for row in self.system_filter_rows:
            row.update_unique_values(unique_values)
        for row in self.system_exception_rows:
            row.update_unique_values(unique_values)
    
    def set_manual_unique_values(self, unique_values: Dict[str, List]):
        """设置手工表唯一值（用于筛选）"""
        self.manual_unique_values = unique_values
        for row in self.manual_filter_rows:
            row.update_unique_values(unique_values)
        for row in self.manual_exception_rows:
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

        # 手工表例外保留
        manual_filter_exceptions = []
        for row in self.manual_exception_rows:
            f = row.get_value()
            if f:
                from core.compare_engine import CompareEngine
                f_converted = {
                    "column": f["column"],
                    "operator": CompareEngine.convert_operator(f["operator"]),
                    "value": f["value"]
                }
                manual_filter_exceptions.append(f_converted)
        config["manual_filter_exceptions"] = manual_filter_exceptions
        
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

        # 系统表例外保留
        system_filter_exceptions = []
        for row in self.system_exception_rows:
            f = row.get_value()
            if f:
                from core.compare_engine import CompareEngine
                f_converted = {
                    "column": f["column"],
                    "operator": CompareEngine.convert_operator(f["operator"]),
                    "value": f["value"]
                }
                system_filter_exceptions.append(f_converted)
        config["system_filter_exceptions"] = system_filter_exceptions
        
        # 列清洗规则
        clean_rules = []
        for row in self.clean_rows:
            rule = row.get_value()
            if rule:
                clean_rules.append(rule)
        config["clean_rules"] = clean_rules
        
        # 手工表透视 - 从独立透视配置区域获取
        if hasattr(self, '_pivot_out_checkboxes'):
            out_values = [cb.text() for cb in self._pivot_out_checkboxes if cb.isChecked()]
            in_values = [cb.text() for cb in self._pivot_in_checkboxes if cb.isChecked()]
            if out_values or in_values:
                # 获取筛选列
                pivot_column = ""
                for row in self.manual_filter_rows:
                    operator = row.operator_combo.currentText()
                    if operator in ["包含", "包含于"]:
                        pivot_column = row.column_combo.currentText()
                        break
                config["manual_pivot"] = {
                    "pivot_column": pivot_column,
                    "out_values": out_values,
                    "in_values": in_values
                }
        
        # 系统表透视列
        pivot_col = self.pivot_column_combo.currentText()
        if pivot_col != "(不透视)":
            config["pivot_column"] = {"system": pivot_col}
            if pivot_col in self.system_unique_values:
                config["pivot_values"] = self.system_unique_values[pivot_col]
        
        # 差值公式（使用动态字母，默认C - B：手工数量-系统总计）
        config["difference_formula"] = self.formula_edit.text().strip() or "C - B"
        
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

        # 模板加载后，快速选择下拉重置为“自定义”，避免首项重复点击不触发
        custom_idx = self.formula_quick_combo.findText("自定义...")
        if custom_idx >= 0:
            # 先置为无选择，再置为自定义，确保后续选择首项能触发
            self.formula_quick_combo.setCurrentIndex(-1)
            self.formula_quick_combo.setCurrentIndex(custom_idx)
        
        # 手工表筛选 - 先清空现有行
        for row in self.manual_filter_rows[:]:
            row.deleteLater()
        self.manual_filter_rows.clear()
        
        # 加载手工表筛选条件
        manual_filters = config.get("manual_filters", [])
        for f in manual_filters:
            self._add_filter_row("manual")
            # 反向映射操作符
            op_reverse = {v: k for k, v in FilterRow.OPERATOR_MAP.items()}
            f_display = {
                "column": f.get("column", ""),
                "operator": op_reverse.get(f.get("operator", ""), f.get("operator", "")),
                "value": f.get("value", "")
            }
            self.manual_filter_rows[-1].set_value(f_display)
        
        # 系统表筛选 - 先清空现有行
        for row in self.system_filter_rows[:]:
            row.deleteLater()
        self.system_filter_rows.clear()
        
        # 加载系统表筛选条件
        system_filters = config.get("system_filters", [])
        for f in system_filters:
            self._add_filter_row("system")
            # 反向映射操作符
            op_reverse = {v: k for k, v in FilterRow.OPERATOR_MAP.items()}
            f_display = {
                "column": f.get("column", ""),
                "operator": op_reverse.get(f.get("operator", ""), f.get("operator", "")),
                "value": f.get("value", "")
            }
            self.system_filter_rows[-1].set_value(f_display)

        # 手工表例外保留 - 先清空现有行
        for row in self.manual_exception_rows[:]:
            row.deleteLater()
        self.manual_exception_rows.clear()

        manual_filter_exceptions = config.get("manual_filter_exceptions", [])
        for f in manual_filter_exceptions:
            self._add_exception_row("manual")
            op_reverse = {v: k for k, v in FilterRow.OPERATOR_MAP.items()}
            f_display = {
                "column": f.get("column", ""),
                "operator": op_reverse.get(f.get("operator", ""), f.get("operator", "")),
                "value": f.get("value", "")
            }
            self.manual_exception_rows[-1].set_value(f_display)

        # 系统表例外保留 - 先清空现有行
        for row in self.system_exception_rows[:]:
            row.deleteLater()
        self.system_exception_rows.clear()

        system_filter_exceptions = config.get("system_filter_exceptions", [])
        for f in system_filter_exceptions:
            self._add_exception_row("system")
            op_reverse = {v: k for k, v in FilterRow.OPERATOR_MAP.items()}
            f_display = {
                "column": f.get("column", ""),
                "operator": op_reverse.get(f.get("operator", ""), f.get("operator", "")),
                "value": f.get("value", "")
            }
            self.system_exception_rows[-1].set_value(f_display)
        
        # 列清洗规则 - 先清空现有行
        for row in self.clean_rows[:]:
            row.deleteLater()
        self.clean_rows.clear()
        
        # 加载清洗规则
        clean_rules = config.get("clean_rules", [])
        for rule in clean_rules:
            self._add_clean_row()
            self.clean_rows[-1].set_value(rule)
        
        # 手工表透视配置 - 应用到独立透视区域
        manual_pivot = config.get("manual_pivot", {})
        if manual_pivot and hasattr(self, '_pivot_out_checkboxes'):
            out_values = manual_pivot.get("out_values", [])
            in_values = manual_pivot.get("in_values", [])
            for cb in self._pivot_out_checkboxes:
                cb.setChecked(cb.text() in out_values)
            for cb in self._pivot_in_checkboxes:
                cb.setChecked(cb.text() in in_values)
