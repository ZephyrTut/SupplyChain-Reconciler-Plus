"""
PyQt6 结果预览面板 - 数据样例、表格预览
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QSplitter, QScrollArea,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush

from config.settings import (
    MATCH_STATUS, DIFF_STATUS, MISSING_STATUS,
    HEADER_BG, MATCH_BG, DIFF_BG, MISSING_BG,
    HEADER_FG, MATCH_FG, DIFF_FG, MISSING_FG
)


def hex_to_qcolor(hex_color: str) -> QColor:
    """十六进制颜色转QColor"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 8:  # ARGB格式
        return QColor(int(hex_color[2:4], 16), int(hex_color[4:6], 16), 
                     int(hex_color[6:8], 16), int(hex_color[0:2], 16))
    else:  # RGB格式
        return QColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


class SampleDisplay(QFrame):
    """数据样例显示组件"""
    
    def __init__(self, title: str, color: str, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        padding = 6 if compact else 10
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: {padding}px;
            }}
        """)
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        margin = 6 if self.compact else 10
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(4 if self.compact else 5)
        
        # 标题
        title_size = 9 if self.compact else 10
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei", title_size, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # 内容
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        max_height = 90 if self.compact else 120
        font_size = 10 if self.compact else 11
        self.content.setMaximumHeight(max_height)
        self.content.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                font-family: Consolas, monospace;
                font-size: {font_size}px;
            }}
        """)
        layout.addWidget(self.content)
        
    def set_data(self, df: pd.DataFrame, key_cols: List[str], value_col: str, 
                 total_count: int, pivot_info: str = ""):
        """设置数据"""
        lines = []
        for i, row in df.head(5).iterrows():
            # 构建主键部分
            key_parts = [str(row.get(col, ""))[:15] for col in key_cols[:3]]
            key_str = ", ".join(key_parts)
            if len(key_cols) > 3:
                key_str += "..."
            
            # 数值部分
            value = row.get(value_col, "")
            lines.append(f"{len(lines)+1}. {key_str} = {value}")
            
        if total_count > 5:
            lines.append(f"... 共 {total_count} 条数据")
            
        if pivot_info:
            lines.append(f"透视: {pivot_info}")
            
        self.content.setText("\n".join(lines))
        
    def clear(self):
        """清空"""
        self.content.setText("配置后显示数据样例")


class QtResultPreview(QWidget):
    """结果预览面板（用于步骤2）"""
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.column_letters = {}  # 存储列字母映射 {列名: 字母}
        self._setup_ui()
        
    def _excel_col_letter(self, index: int) -> str:
        """将 0 基索引转换为 Excel 列字母（支持超过 Z）
        0 -> A, 25 -> Z, 26 -> AA
        """
        result = ""
        i = index + 1
        while i > 0:
            i, rem = divmod(i - 1, 26)
            result = chr(65 + rem) + result
        return result
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        spacing = 6 if self.compact else 10
        layout.setSpacing(spacing)
        
        # 标题
        title_size = 11 if self.compact else 12
        title = QLabel("📋 数据预览")
        title.setFont(QFont("Microsoft YaHei", title_size, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 样例区域
        sample_layout = QHBoxLayout()
        sample_layout.setSpacing(8 if self.compact else 10)
        
        self.manual_sample = SampleDisplay("手工表样例", "#e3f2fd", compact=self.compact)
        self.system_sample = SampleDisplay("系统表样例", "#e8f5e9", compact=self.compact)
        
        sample_layout.addWidget(self.manual_sample)
        sample_layout.addWidget(self.system_sample)
        layout.addLayout(sample_layout)
        
        # 公式说明区域（新增）
        formula_frame = QFrame()
        formula_frame.setStyleSheet("""
            QFrame {
                background-color: #fff9e6;
                border: 1px solid #ffe082;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        formula_layout = QVBoxLayout(formula_frame)
        formula_layout.setContentsMargins(8, 8, 8, 8)
        formula_layout.setSpacing(4)
        
        self.formula_label = QLabel("差值公式: 配置后显示")
        self.formula_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.formula_label.setStyleSheet("color: #f57c00; background: transparent; border: none; padding: 0;")
        formula_layout.addWidget(self.formula_label)
        
        self.column_info_label = QLabel("")
        self.column_info_label.setFont(QFont("Consolas", 10))
        self.column_info_label.setStyleSheet("color: #666; background: transparent; border: none; padding: 0;")
        self.column_info_label.setWordWrap(True)
        formula_layout.addWidget(self.column_info_label)
        
        layout.addWidget(formula_frame)
        
        # 字段映射标签（默认隐藏，列对照已在formula区域显示）
        self.mapping_label = QLabel("")
        self.mapping_label.setVisible(False)
        layout.addWidget(self.mapping_label)
        
        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        padding = "3px" if self.compact else "5px"
        header_padding = "5px" if self.compact else "8px"
        self.preview_table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: {padding};
            }}
            QHeaderView::section {{
                background-color: #e3f2fd;
                color: #1565c0;
                font-weight: bold;
                padding: {header_padding};
                border: none;
                border-right: 1px solid #bbdefb;
                border-bottom: 1px solid #bbdefb;
            }}
        """)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.preview_table, 1)
        
        # 状态栏
        self.status_label = QLabel("配置主键和数值列后显示预览")
        self.status_label.setStyleSheet("color: #999;")
        layout.addWidget(self.status_label)
        
    def update_preview(self, manual_df: pd.DataFrame, system_df: pd.DataFrame, 
                       config: Dict[str, Any]):
        """更新预览"""
        try:
            # 获取配置
            key_mappings = config.get("key_mappings", [])
            value_mapping = config.get("value_mapping", {})
            
            if not key_mappings or not value_mapping.get("manual"):
                self.status_label.setText("请先配置主键和数值列")
                return
                
            manual_keys = [m["manual"] for m in key_mappings]
            system_keys = [m["system"] for m in key_mappings]
            manual_value = value_mapping.get("manual", "")
            system_value = value_mapping.get("system", "")
            
            # 更新样例
            self.manual_sample.set_data(
                manual_df, manual_keys, manual_value, len(manual_df)
            )
            
            pivot_config = config.get("pivot_column", {})
            pivot_col = pivot_config.get("system") if isinstance(pivot_config, dict) else pivot_config
            pivot_info = ""
            pivot_values = config.get("pivot_values", [])
            
            if pivot_col:
                unique_count = len(system_df[pivot_col].unique()) if pivot_col in system_df.columns else 0
                pivot_info = f"{pivot_col} ({unique_count}值)"
                
            self.system_sample.set_data(
                system_df, system_keys, system_value, len(system_df), pivot_info
            )
            
            # 生成列字母映射（所有列都分配字母，与导出Excel一致）
            self.column_letters.clear()
            
            # 构建导出列顺序
            export_columns = []
            if "__KEY__" in manual_df.columns or True:  # KEY总是存在
                export_columns.append("__KEY__")
            for pv in sorted(pivot_values):
                export_columns.append(pv)
            export_columns.extend(["系统总计", "手工数量", "差值", "比对状态"])
            
            # 为所有列分配字母
            for i, col in enumerate(export_columns):
                self.column_letters[col] = self._excel_col_letter(i)
            
            # 更新公式说明
            self._update_formula_display(config, pivot_values)
            
            # 更新列对照说明（简化版，只显示关键列的字母映射）
            col_info_parts = []
            for col, letter in sorted(self.column_letters.items(), key=lambda x: x[1]):
                # 排除 KEY 和 比对状态
                if col not in ["__KEY__", "比对状态"]:
                    col_info_parts.append(f"{letter}={col}")
            
            if col_info_parts:
                self.mapping_label.setText("列对照: " + ", ".join(col_info_parts))
            else:
                self.mapping_label.setText("列对照: -")
            
            # 更新预览表格（显示原始数据前几行）
            preview_df = manual_df.head(10)
            self._fill_table(preview_df)
            
            self.status_label.setText(f"显示前 {min(10, len(manual_df))} 行 / 共 {len(manual_df)} 行")
            
        except Exception as e:
            self.status_label.setText(f"预览更新失败: {str(e)}")
            
    def _update_formula_display(self, config: Dict[str, Any], pivot_values: List[str]):
        """更新公式说明标签（显示实际公式和原始公式）
        
        变量规则（与v1.2.0一致）：
        - M = 手工数量
        - S = 系统总计
        - 透视列名直接作为变量（如 "已完成"、"未完成"）
        
        显示时会将变量替换为对应的列字母
        """
        # 找到手工数量和系统总计的列字母
        manual_letter = self.column_letters.get("手工数量", "?")
        system_letter = self.column_letters.get("系统总计", "?")
        
        formula = config.get("difference_formula", "")
        if formula:
            # 使用正则分别替换独立的 M/S（确保不替换其他文字中的 M/S）
            display_formula = formula
            display_formula = re.sub(r"\bM\b", manual_letter, display_formula)
            display_formula = re.sub(r"\bS\b", system_letter, display_formula)
            
            # 替换透视列变量（按完整列名匹配，按长度降序避免部分匹配）
            for pv in sorted(pivot_values, key=len, reverse=True):
                pv_letter = self.column_letters.get(pv, None)
                if pv_letter:
                    display_formula = re.sub(r"\b" + re.escape(pv) + r"\b", pv_letter, display_formula)
            
            # 显示公式和原始表达式
            self.formula_label.setText(f"差值公式: {display_formula}  (原始: {formula})")
        else:
            # 默认简单差值公式
            self.formula_label.setText(f"简单差值: {manual_letter} - {system_letter}  (M - S)")
        
        # 更新列字母说明（排除 KEY 和 比对状态）
        col_info_parts = []
        for col, letter in sorted(self.column_letters.items(), key=lambda x: x[1]):
            display_name = col if col != "__KEY__" else "KEY"
            if display_name != "KEY" and display_name != "比对状态":
                col_info_parts.append(f"{letter}={display_name}")
        
        if col_info_parts:
            self.column_info_label.setText("列对照: " + ", ".join(col_info_parts))
        else:
            self.column_info_label.setText("")
            
    def _fill_table(self, df: pd.DataFrame):
        """填充表格"""
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels(list(df.columns))
        
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(df.columns):
                value = row[col]
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(i, j, item)
    
    def _get_export_columns(self, df: pd.DataFrame, pivot_values: List[str]) -> List[str]:
        """获取导出列顺序（与导出引擎一致）
        
        列顺序规范（v1.4.1）：
        1. 主键 (__KEY__)
        2. 手工数量
        3. 透视列（按字母排序）
        4. 系统总计
        5. 差值
        6. 比对状态
        """
        cols = []
        
        # 1. 主键
        if "__KEY__" in df.columns:
            cols.append("__KEY__")
        
        # 2. 手工数量（移到透视列之前）
        if "手工数量" in df.columns:
            cols.append("手工数量")
        
        # 3. 透视列（按排序）
        for pv in sorted(pivot_values):
            if pv in df.columns:
                cols.append(pv)
        
        # 4. 系统总计
        if "系统总计" in df.columns:
            cols.append("系统总计")
        
        # 5. 差值
        if "差值" in df.columns:
            cols.append("差值")
        
        # 6. 比对状态
        if "比对状态" in df.columns:
            cols.append("比对状态")
        
        return cols if cols else list(df.columns)
    
    def update_result_preview(self, result_df: pd.DataFrame, pivot_values: List[str], 
                              config: Dict[str, Any], manual_df: pd.DataFrame = None, 
                              system_df: pd.DataFrame = None):
        """
        更新对账结果预览（步骤2使用，显示计算后的结果）
        
        Args:
            result_df: 对账结果DataFrame
            pivot_values: 透视值列表
            config: 配置信息
            manual_df: 手工表原始数据
            system_df: 系统表原始数据
        """
        if result_df is None or result_df.empty:
            self.status_label.setText("请先配置主键和数值列")
            return
            
        try:
            # 更新样例（如果提供了原始数据）
            if manual_df is not None and system_df is not None:
                key_mappings = config.get("key_mappings", [])
                value_mapping = config.get("value_mapping", {})
                manual_keys = [m["manual"] for m in key_mappings]
                system_keys = [m["system"] for m in key_mappings]
                manual_value = value_mapping.get("manual", "")
                system_value = value_mapping.get("system", "")
                
                self.manual_sample.set_data(
                    manual_df, manual_keys, manual_value, len(manual_df)
                )
                
                pivot_config = config.get("pivot_column", {})
                pivot_col = pivot_config.get("system") if isinstance(pivot_config, dict) else pivot_config
                pivot_info = f"{pivot_col} ({len(pivot_values)}值)" if pivot_col and pivot_values else ""
                
                self.system_sample.set_data(
                    system_df, system_keys, system_value, len(system_df), pivot_info
                )
            
            # 获取导出列顺序
            columns = self._get_export_columns(result_df, pivot_values)
            
            # 生成列字母映射（所有列都分配字母，与导出Excel一致）
            self.column_letters.clear()
            for i, col in enumerate(columns):
                self.column_letters[col] = self._excel_col_letter(i)
            
            # 更新公式说明（包含列对照）
            self._update_formula_display(config, pivot_values)
            
            # 隐藏多余的mapping_label（列对照已在_update_formula_display中显示）
            self.mapping_label.setVisible(False)
            
            # 填充预览表格（只显示指定列，前15行）
            display_df = result_df[columns].head(15)
            self._fill_result_table(display_df, pivot_values)
            
            self.status_label.setText(f"预览前 {len(display_df)} 行 / 共 {len(result_df)} 行")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"预览更新失败: {str(e)}")
    
    def _fill_result_table(self, df: pd.DataFrame, pivot_values: List[str]):
        """填充结果表格（带列字母表头和颜色）"""
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        
        # 构建带字母的表头
        headers = []
        for col in df.columns:
            if col == "__KEY__":
                headers.append("KEY")
            elif col in self.column_letters:
                letter = self.column_letters[col]
                headers.append(f"{letter} ({col})")
            else:
                headers.append(col)
        
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        status_col_idx = list(df.columns).index("比对状态") if "比对状态" in df.columns else -1
        
        for i, (_, row) in enumerate(df.iterrows()):
            # 获取状态颜色
            status = row.get("比对状态", "") if status_col_idx >= 0 else ""
            bg_color, fg_color = self._get_status_colors(status)
            
            for j, col in enumerate(df.columns):
                value = row[col]
                # 格式化数值
                if isinstance(value, (float, np.floating)):
                    if pd.isna(value):
                        text = ""
                    elif float(value).is_integer():
                        text = str(int(round(value)))
                    else:
                        text = f"{value:.2f}".rstrip("0").rstrip(".")
                elif isinstance(value, (int, np.integer)):
                    text = str(int(value))
                else:
                    text = str(value) if pd.notna(value) else ""
                
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(fg_color))
                self.preview_table.setItem(i, j, item)
    
    def _get_status_colors(self, status: str) -> Tuple[QColor, QColor]:
        """根据状态获取背景色和前景色"""
        if status == MATCH_STATUS:
            return hex_to_qcolor(MATCH_BG), hex_to_qcolor(MATCH_FG) if MATCH_FG else QColor(0, 0, 0)
        elif status == DIFF_STATUS:
            return hex_to_qcolor(DIFF_BG), hex_to_qcolor(DIFF_FG) if DIFF_FG else QColor(0, 0, 0)
        elif status == MISSING_STATUS:
            return hex_to_qcolor(MISSING_BG), hex_to_qcolor(MISSING_FG) if MISSING_FG else QColor(0, 0, 0)
        return QColor(255, 255, 255), QColor(0, 0, 0)
    
    def get_column_letters(self) -> Dict[str, str]:
        """获取列字母映射"""
        return self.column_letters.copy()
                
    def clear(self):
        """清空预览"""
        self.manual_sample.clear()
        self.system_sample.clear()
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.column_letters.clear()
        self.formula_label.setText("差值公式: 配置后显示")
        self.column_info_label.setText("")
        self.mapping_label.setText("字段映射: -")
        self.status_label.setText("配置主键和数值列后显示预览")


class QtResultTable(QWidget):
    """结果表格组件（用于步骤3）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.column_letters = {}  # 存储列字母映射 {列名: 字母}
        self._setup_ui()
        
    def _excel_col_letter(self, index: int) -> str:
        """将 0 基索引转换为 Excel 列字母（支持超过 Z）
        0 -> A, 25 -> Z, 26 -> AA
        """
        result = ""
        i = index + 1
        while i > 0:
            i, rem = divmod(i - 1, 26)
            result = chr(65 + rem) + result
        return result
    
    def _get_export_columns(self, df: pd.DataFrame, pivot_values: List[str]) -> List[str]:
        """获取导出列顺序（与导出引擎一致）
        
        列顺序规范（v1.4.1）：
        1. 主键 (__KEY__)
        2. 手工数量
        3. 透视列（按字母排序）
        4. 系统总计
        5. 差值
        6. 比对状态
        """
        cols = []
        
        # 1. 主键
        if "__KEY__" in df.columns:
            cols.append("__KEY__")
        
        # 2. 手工数量（移到透视列之前）
        if "手工数量" in df.columns:
            cols.append("手工数量")
        
        # 3. 透视列（按排序）
        for pv in sorted(pivot_values):
            if pv in df.columns:
                cols.append(pv)
        
        # 4. 系统总计
        if "系统总计" in df.columns:
            cols.append("系统总计")
        
        # 5. 差值
        if "差值" in df.columns:
            cols.append("差值")
        
        # 6. 比对状态
        if "比对状态" in df.columns:
            cols.append("比对状态")
        
        return cols if cols else list(df.columns)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 公式说明区域（新增）
        formula_frame = QFrame()
        formula_frame.setStyleSheet("""
            QFrame {
                background-color: #fff9e6;
                border: 1px solid #ffe082;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 10px;
            }
        """)
        formula_layout = QVBoxLayout(formula_frame)
        formula_layout.setContentsMargins(8, 8, 8, 8)
        formula_layout.setSpacing(4)
        
        self.formula_label = QLabel("差值公式: 等待对账结果...")
        self.formula_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.formula_label.setStyleSheet("color: #f57c00; background: transparent; border: none; padding: 0;")
        formula_layout.addWidget(self.formula_label)
        
        self.column_info_label = QLabel("")
        self.column_info_label.setFont(QFont("Consolas", 10))
        self.column_info_label.setStyleSheet("color: #666; background: transparent; border: none; padding: 0;")
        self.column_info_label.setWordWrap(True)
        formula_layout.addWidget(self.column_info_label)
        
        layout.addWidget(formula_frame)
        
        # 表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                color: #1565c0;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-right: 1px solid #bbdefb;
                border-bottom: 1px solid #bbdefb;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # 状态
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
    def set_data(self, df: pd.DataFrame, config: Dict[str, Any] = None):
        """设置数据（所有列都分配字母，与导出Excel一致）"""
        self.table.clear()
        
        # 获取透视值
        pivot_values = config.get("pivot_values", []) if config else []
        
        # 获取导出列顺序
        columns = self._get_export_columns(df, pivot_values)
        
        # 使用正确列顺序的数据
        display_df = df[columns].head(100) if all(c in df.columns for c in columns) else df.head(100)
        
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        
        # 生成列字母映射和表头（所有列都分配字母）
        self.column_letters.clear()
        headers = []
        
        for i, col in enumerate(display_df.columns):
            letter = self._excel_col_letter(i)
            self.column_letters[col] = letter
            
            # 构建表头显示
            if col == "__KEY__":
                headers.append(f"{letter} (KEY)")
            else:
                headers.append(f"{letter} ({col})")
        
        self.table.setHorizontalHeaderLabels(headers)
        
        # 更新公式显示（如果提供了config）
        if config:
            self._update_formula_display(config, pivot_values)
        
        # 状态列索引
        status_col_idx = list(display_df.columns).index('比对状态') if '比对状态' in display_df.columns else -1
        
        for i, (_, row) in enumerate(display_df.iterrows()):
            # 获取状态
            status = row.get('比对状态', '') if status_col_idx >= 0 else ''
            
            # 根据状态设置行颜色
            if status == MATCH_STATUS:
                bg_color = hex_to_qcolor(MATCH_BG)
                fg_color = hex_to_qcolor(MATCH_FG) if MATCH_FG else QColor(0, 0, 0)
            elif status == DIFF_STATUS:
                bg_color = hex_to_qcolor(DIFF_BG)
                fg_color = hex_to_qcolor(DIFF_FG) if DIFF_FG else QColor(0, 0, 0)
            elif status == MISSING_STATUS:
                bg_color = hex_to_qcolor(MISSING_BG)
                fg_color = hex_to_qcolor(MISSING_FG) if MISSING_FG else QColor(0, 0, 0)
            else:
                bg_color = QColor(255, 255, 255)
                fg_color = QColor(0, 0, 0)
                
            for j, col in enumerate(display_df.columns):
                value = row[col]
                # 格式化数值
                if isinstance(value, (float, np.floating)):
                    if pd.isna(value):
                        text = ""
                    elif float(value).is_integer():
                        text = str(int(round(value)))
                    else:
                        text = f"{value:.2f}".rstrip("0").rstrip(".")
                elif isinstance(value, (int, np.integer)):
                    text = str(int(value))
                else:
                    text = str(value) if pd.notna(value) else ""
                    
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(fg_color))
                self.table.setItem(i, j, item)
                
        self.status_label.setText(f"显示前 {len(display_df)} 行 / 共 {len(df)} 行")
        
    def _update_formula_display(self, config: Dict[str, Any], pivot_values: List[str]):
        """更新公式说明标签（显示实际公式和原始公式）
        
        变量规则（与v1.2.0一致）：
        - M = 手工数量
        - S = 系统总计
        - 透视列名直接作为变量（如 "已完成"、"未完成"）
        
        显示时会将变量替换为对应的列字母
        """
        # 找到手工数量和系统总计的列字母
        manual_letter = self.column_letters.get("手工数量", "?")
        system_letter = self.column_letters.get("系统总计", "?")
        
        formula = config.get("difference_formula", "")
        if formula:
            # 使用正则分别替换独立的 M/S（确保不替换其他文字中的 M/S）
            display_formula = formula
            display_formula = re.sub(r"\bM\b", manual_letter, display_formula)
            display_formula = re.sub(r"\bS\b", system_letter, display_formula)
            
            # 替换透视列变量（按完整列名匹配，按长度降序避免部分匹配）
            for pv in sorted(pivot_values, key=len, reverse=True):
                pv_letter = self.column_letters.get(pv, None)
                if pv_letter:
                    display_formula = re.sub(r"\b" + re.escape(pv) + r"\b", pv_letter, display_formula)
            
            # 显示公式和原始表达式
            self.formula_label.setText(f"差值公式: {display_formula}  (原始: {formula})")
        else:
            # 默认简单差值公式
            self.formula_label.setText(f"简单差值: {manual_letter} - {system_letter}  (M - S)")
        
        # 更新列字母说明（排除 KEY 和 比对状态）
        col_info_parts = []
        for col, letter in sorted(self.column_letters.items(), key=lambda x: x[1]):
            display_name = col if col != "__KEY__" else "KEY"
            if display_name != "KEY" and display_name != "比对状态":
                col_info_parts.append(f"{letter}={display_name}")
        
        if col_info_parts:
            self.column_info_label.setText("列对照: " + ", ".join(col_info_parts))
        else:
            self.column_info_label.setText("")
        
    def clear(self):
        """清空"""
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.column_letters.clear()
        self.formula_label.setText("差值公式: 等待对账结果...")
        self.column_info_label.setText("")
        self.status_label.setText("")
