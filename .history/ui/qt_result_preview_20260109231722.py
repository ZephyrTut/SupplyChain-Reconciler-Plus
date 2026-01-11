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
        self.base_color = color
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
        max_height = 150 if self.compact else 180
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
        """设置数据（显示筛选后的数据样例）"""
        lines = []
        for i, row in df.head(5).iterrows():
            # 构建主键部分（完整显示，不截断）
            key_parts = [str(row.get(col, "")) for col in key_cols]
            key_str = ", ".join(key_parts)
            
            # 数值部分
            value = row.get(value_col, "")
            lines.append(f"{len(lines)+1}. {key_str} = {value}")
            
        if total_count > 5:
            lines.append(f"... 共 {total_count} 条数据")
            
        if pivot_info:
            lines.append(f"透视: {pivot_info}")
            
        self.content.setText("\n".join(lines))
    
    def set_pivot_preview(self, pivot_df: pd.DataFrame, manual_pivot: Dict[str, Any], 
                          filter_col: str = None, filter_non_zero: bool = True):
        """设置手工表透视计算预览
        
        Args:
            pivot_df: 透视计算结果 DataFrame
            manual_pivot: 手工表透视配置 {pivot_column, out_values, in_values}
            filter_col: 筛选列名（如 "退仓"）
            filter_non_zero: 是否只显示筛选列不为0的行
        """
        lines = []
        
        # 透视配置描述
        pivot_col = manual_pivot.get("pivot_column", "")
        out_values = manual_pivot.get("out_values", [])
        in_values = manual_pivot.get("in_values", [])
        
        lines.append(f"【手工表透视配置】")
        lines.append(f"透视列: {pivot_col}")
        lines.append(f"📤 出库值: {', '.join(out_values) if out_values else '(无)'}")
        lines.append(f"📥 入库值: {', '.join(in_values) if in_values else '(无)'}")
        lines.append(f"计算公式: 手工数量 = Σ出库 - Σ入库")
        lines.append("")
        
        # 筛选数据
        if pivot_df is not None and not pivot_df.empty:
            display_df = pivot_df.copy()
            
            # 如果指定筛选列且需要非零筛选
            if filter_col and filter_col in display_df.columns and filter_non_zero:
                display_df = display_df[display_df[filter_col] != 0]
                lines.append(f"📋 {filter_col}≠0 的数据 ({len(display_df)}条):")
            else:
                lines.append(f"📋 透视计算结果 ({len(display_df)}条):")
            
            # 显示数据（格式类似Excel截图）
            # 获取要显示的列
            display_cols = ["__KEY__"]
            for col in out_values + in_values:
                if col in display_df.columns:
                    display_cols.append(col)
            if "手工数量" in display_df.columns:
                display_cols.append("手工数量")
            
            # 表头
            header_parts = []
            for col in display_cols:
                col_name = "KEY" if col == "__KEY__" else col
                header_parts.append(col_name)
            lines.append("  " + " | ".join(header_parts))
            lines.append("  " + "-" * 50)
            
            # 数据行（最多显示10行）
            for idx, (_, row) in enumerate(display_df.head(10).iterrows()):
                row_parts = []
                for col in display_cols:
                    val = row.get(col, "")
                    if pd.isna(val):
                        val = ""
                    elif isinstance(val, (float, np.floating)):
                        val = int(val) if float(val).is_integer() else f"{val:.2f}"
                    row_parts.append(str(val))
                lines.append("  " + " | ".join(row_parts))
            
            if len(display_df) > 10:
                lines.append(f"  ... 还有 {len(display_df) - 10} 条数据")
        else:
            lines.append("（请先配置主键和数值列）")
        
        self.content.setText("\n".join(lines))
    
    def set_key_preview(self, system_df: pd.DataFrame, key_col: str = "__KEY__", 
                        total_count: int = 0):
        """设置系统表KEY预览（只显示KEY列用于匹配检查）
        
        Args:
            system_df: 系统表聚合后的 DataFrame
            key_col: KEY列名
            total_count: 总数量
        """
        lines = []
        lines.append("【系统表KEY预览】")
        lines.append("用于检查主键是否匹配正确")
        lines.append("")
        
        if system_df is not None and not system_df.empty and key_col in system_df.columns:
            lines.append(f"📋 系统表KEY ({len(system_df)}条):")
            lines.append("  KEY")
            lines.append("  " + "-" * 40)
            
            for idx, (_, row) in enumerate(system_df.head(15).iterrows()):
                key_val = row.get(key_col, "")
                lines.append(f"  {key_val}")
            
            if len(system_df) > 15:
                lines.append(f"  ... 还有 {len(system_df) - 15} 条数据")
        else:
            lines.append("（请先配置主键）")
        
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
        # 允许横向滚动，不自动拉伸
        self.preview_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self.preview_table, 1)
        
        # 状态栏
        self.status_label = QLabel("配置主键和数值列后显示预览")
        self.status_label.setStyleSheet("color: #999;")
        layout.addWidget(self.status_label)
        
    def update_preview(self, manual_df: pd.DataFrame, system_df: pd.DataFrame, 
                       config: Dict[str, Any]):
        """更新预览 - 实时执行对账并显示结果预览"""
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
            
            pivot_config = config.get("pivot_column", {})
            pivot_col = pivot_config.get("system") if isinstance(pivot_config, dict) else pivot_config
            pivot_info = ""
            pivot_values = config.get("pivot_values", [])
            
            if pivot_col:
                unique_count = len(system_df[pivot_col].unique()) if pivot_col in system_df.columns else 0
                pivot_info = f"{pivot_col} ({unique_count}值)"
            
            # 实时执行对账生成预览结果
            from core.compare_engine import CompareEngine
            
            # 生成主键
            manual_with_key = CompareEngine.make_key(manual_df.copy(), manual_keys)
            system_with_key = CompareEngine.make_key(system_df.copy(), system_keys)
            
            # 准备筛选条件
            manual_filters = [(f["column"], f["operator"], f["value"]) 
                             for f in config.get("manual_filters", [])]
            system_filters = [(f["column"], f["operator"], f["value"]) 
                             for f in config.get("system_filters", [])]
            
            # 聚合数据（包含筛选）
            manual_agg, _ = CompareEngine.aggregate_data(
                manual_with_key, "__KEY__", [manual_value] if manual_value else [],
                filters=manual_filters
            )
            
            system_agg, actual_pivot_values = CompareEngine.aggregate_data(
                system_with_key, "__KEY__", [system_value] if system_value else [],
                pivot_col=pivot_col if pivot_col else None,
                filters=system_filters
            )
            
            # 获取手工表透视配置
            manual_pivot = config.get("manual_pivot", {})
            
            # 更新样例显示
            if manual_pivot and manual_pivot.get("pivot_column"):
                # 如果配置了手工表透视，显示透视计算结果
                in_values = manual_pivot.get("in_values", [])
                # 找到入库值中的第一个作为筛选列（通常是"退仓"或"退货"）
                filter_col = in_values[0] if in_values else None
                
                try:
                    # 执行手工表透视计算
                    pivot_df, out_cols, in_cols = CompareEngine.aggregate_manual_with_pivot(
                        manual_with_key, "__KEY__", manual_value, manual_pivot, manual_filters
                    )
                    self.manual_sample.set_pivot_preview(pivot_df, manual_pivot, filter_col, True)
                except Exception as e:
                    # 如果透视失败，显示普通样例
                    self.manual_sample.set_data(
                        manual_agg, ["__KEY__"], "手工数量", len(manual_agg)
                    )
            else:
                # 普通样例
                self.manual_sample.set_data(
                    manual_agg, ["__KEY__"], "手工数量", len(manual_agg)
                )
            
            # 系统表样例：只显示KEY供检查匹配
            self.system_sample.set_key_preview(system_agg, "__KEY__", len(system_agg))
            
            # 使用实际透视值
            pivot_values = actual_pivot_values if actual_pivot_values else pivot_values
            
            # 确定数值列名
            manual_val_name = manual_value if manual_value else ""
            system_val_name = "系统总计" if pivot_col else (system_value if system_value else "")
            
            # 合并比对
            result_df = CompareEngine.merge_and_compare(
                manual_agg, system_agg, "__KEY__",
                manual_val_name, system_val_name,
                diff_formula=config.get("difference_formula", "M - S"),
                pivot_values=pivot_values
            )
            
            # 构建导出列顺序（与导出一致）
            export_columns = self._get_export_columns(result_df, pivot_values)
            
            # 生成列字母映射
            self.column_letters.clear()
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
                self.column_info_label.setText("列对照: " + ", ".join(col_info_parts))
            else:
                self.column_info_label.setText("列对照: -")
            
            # 更新预览表格（只显示导出列，前10行）
            preview_df = result_df[export_columns].head(10) if len(export_columns) > 0 else result_df.head(10)
            self._fill_preview_table(preview_df, pivot_values)
            
            self.status_label.setText(f"显示前 {min(10, len(result_df))} 行 / 共 {len(result_df)} 行")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
        """填充表格（原始数据，无颜色）"""
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
    
    def _fill_preview_table(self, df: pd.DataFrame, pivot_values: List[str]):
        """填充预览表格（带颜色，与导出格式一致）"""
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        
        # 设置表头（带字母标识）
        headers = []
        for col in df.columns:
            letter = self.column_letters.get(col, "")
            display_name = "KEY" if col == "__KEY__" else col
            headers.append(f"{letter}({display_name})" if letter else display_name)
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据（带状态颜色）
        for i, (_, row) in enumerate(df.iterrows()):
            status = row.get("比对状态", "")
            
            # 根据状态选择颜色
            if "✓" in str(status) or "一致" in str(status):
                bg_color = hex_to_qcolor(MATCH_BG)
                fg_color = hex_to_qcolor(MATCH_FG)
            elif "↕" in str(status) or "差异" in str(status):
                bg_color = hex_to_qcolor(DIFF_BG)
                fg_color = hex_to_qcolor(DIFF_FG)
            elif "✗" in str(status) or "缺" in str(status):
                bg_color = hex_to_qcolor(MISSING_BG)
                fg_color = hex_to_qcolor(MISSING_FG)
            else:
                bg_color = None
                fg_color = None
            
            for j, col in enumerate(df.columns):
                value = row[col]
                # 格式化数值
                if pd.notna(value):
                    if isinstance(value, (float, np.floating)):
                        if float(value).is_integer():
                            text = str(int(value))
                        else:
                            text = f"{value:.2f}".rstrip('0').rstrip('.')
                    else:
                        text = str(value)
                else:
                    text = ""
                
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if bg_color:
                    item.setBackground(QBrush(bg_color))
                if fg_color:
                    item.setForeground(QBrush(fg_color))
                
                self.preview_table.setItem(i, j, item)
        
        # 自动调整列宽
        for j, col in enumerate(df.columns):
            if col == "__KEY__":
                # KEY列设置更宽，确保完整显示
                self.preview_table.setColumnWidth(j, 200)
            elif col == "比对状态":
                self.preview_table.setColumnWidth(j, 100)
            else:
                self.preview_table.setColumnWidth(j, 90)
    
    def _get_export_columns(self, df: pd.DataFrame, pivot_values: List[str]) -> List[str]:
        """获取导出列顺序（与导出引擎一致）
        
        列顺序规范（v1.4.1）：
        1. 主键 (__KEY__)
        2. 透视列（按字母排序）
        3. 系统总计
        4. 手工数量
        5. 差值
        6. 比对状态
        """
        cols = []
        
        # 1. 主键
        if "__KEY__" in df.columns:
            cols.append("__KEY__")
        
        # 2. 透视列（按排序）
        for pv in sorted(pivot_values):
            if pv in df.columns:
                cols.append(pv)
        
        # 3. 系统总计
        if "系统总计" in df.columns:
            cols.append("系统总计")
        
        # 4. 手工数量（移到系统总计之后）
        if "手工数量" in df.columns:
            cols.append("手工数量")
        
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
                
                # 获取手工表透视配置
                manual_pivot = config.get("manual_pivot", {})
                
                # 更新手工表样例
                if manual_pivot and manual_pivot.get("pivot_column"):
                    # 如果配置了手工表透视，显示透视计算结果
                    from core.compare_engine import CompareEngine
                    in_values = manual_pivot.get("in_values", [])
                    filter_col = in_values[0] if in_values else None
                    
                    try:
                        manual_with_key = CompareEngine.make_key(manual_df.copy(), manual_keys)
                        manual_filters = [(f["column"], f["operator"], f["value"]) 
                                         for f in config.get("manual_filters", [])]
                        pivot_df, out_cols, in_cols = CompareEngine.aggregate_manual_with_pivot(
                            manual_with_key, "__KEY__", manual_value, manual_pivot, manual_filters
                        )
                        self.manual_sample.set_pivot_preview(pivot_df, manual_pivot, filter_col, True)
                    except Exception:
                        self.manual_sample.set_data(
                            manual_df, manual_keys, manual_value, len(manual_df)
                        )
                else:
                    self.manual_sample.set_data(
                        manual_df, manual_keys, manual_value, len(manual_df)
                    )
                
                # 系统表样例：只显示KEY供检查匹配
                from core.compare_engine import CompareEngine
                system_with_key = CompareEngine.make_key(system_df.copy(), system_keys)
                system_filters = [(f["column"], f["operator"], f["value"]) 
                                 for f in config.get("system_filters", [])]
                pivot_config = config.get("pivot_column", {})
                pivot_col = pivot_config.get("system") if isinstance(pivot_config, dict) else pivot_config
                
                system_agg, _ = CompareEngine.aggregate_data(
                    system_with_key, "__KEY__", [system_value] if system_value else [],
                    pivot_col=pivot_col if pivot_col else None,
                    filters=system_filters
                )
                self.system_sample.set_key_preview(system_agg, "__KEY__", len(system_agg))
            
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
        status_str = str(status) if status else ""
        if status_str.startswith(MATCH_STATUS):
            return hex_to_qcolor(MATCH_BG), hex_to_qcolor(MATCH_FG) if MATCH_FG else QColor(0, 0, 0)
        elif status_str.startswith(DIFF_STATUS):
            return hex_to_qcolor(DIFF_BG), hex_to_qcolor(DIFF_FG) if DIFF_FG else QColor(0, 0, 0)
        elif status_str.startswith(MISSING_STATUS):
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
        
        列顺序规范（v1.2.0）：
        1. 主键 (__KEY__)
        2. 透视列（按字母排序）
        3. 系统总计
        4. 手工数量
        5. 差值
        6. 比对状态
        """
        cols = []
        
        # 1. 主键
        if "__KEY__" in df.columns:
            cols.append("__KEY__")
        
        # 2. 透视列（按排序）
        for pv in sorted(pivot_values):
            if pv in df.columns:
                cols.append(pv)
        
        # 3. 系统总计
        if "系统总计" in df.columns:
            cols.append("系统总计")
        
        # 4. 手工数量
        if "手工数量" in df.columns:
            cols.append("手工数量")
        
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
            status_str = str(status) if status else ""
            if status_str.startswith(MATCH_STATUS):
                bg_color = hex_to_qcolor(MATCH_BG)
                fg_color = hex_to_qcolor(MATCH_FG) if MATCH_FG else QColor(0, 0, 0)
            elif status_str.startswith(DIFF_STATUS):
                bg_color = hex_to_qcolor(DIFF_BG)
                fg_color = hex_to_qcolor(DIFF_FG) if DIFF_FG else QColor(0, 0, 0)
            elif status_str.startswith(MISSING_STATUS):
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
