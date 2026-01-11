"""
PyQt6 结果预览面板 - 数据样例、表格预览
"""
import re
from typing import List, Dict, Any, Optional
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
        self.column_letters = {}  # 存储列字母映射
        self._setup_ui()
        
    def _excel_col_letter(self, n: int) -> str:
        """生成Excel列字母（A, B, C, ... Z, AA, AB, ...）"""
        result = ""
        while n >= 0:
            result = chr(n % 26 + 65) + result
            n = n // 26 - 1
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
        
        # 字段映射
        self.mapping_label = QLabel("字段映射: -")
        font_size = "11px" if self.compact else "12px"
        self.mapping_label.setStyleSheet(f"color: #666; padding: 4px; font-size: {font_size};")
        self.mapping_label.setWordWrap(True)
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
            if pivot_col:
                unique_count = len(system_df[pivot_col].unique()) if pivot_col in system_df.columns else 0
                pivot_info = f"{pivot_col} ({unique_count}值)"
                
            self.system_sample.set_data(
                system_df, system_keys, system_value, len(system_df), pivot_info
            )
            
            # 更新字段映射说明
            mapping_parts = []
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            idx = 0
            mapping_parts.append(f"KEY = {' + '.join(manual_keys)}")
            
            pivot_values = config.get("pivot_values", [])
            for pv in pivot_values[:5]:
                mapping_parts.append(f"{letters[idx]} = {pv}")
                idx += 1
            mapping_parts.append(f"M = {manual_value}")
            mapping_parts.append(f"S = 系统总计")
            
            self.mapping_label.setText("字段映射: " + " | ".join(mapping_parts))
            
            # 更新预览表格（显示原始数据前几行）
            preview_df = manual_df.head(10)
            self._fill_table(preview_df)
            
            self.status_label.setText(f"显示前 {min(10, len(manual_df))} 行 / 共 {len(manual_df)} 行")
            
        except Exception as e:
            self.status_label.setText(f"预览更新失败: {str(e)}")
            
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
                
    def clear(self):
        """清空预览"""
        self.manual_sample.clear()
        self.system_sample.clear()
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.mapping_label.setText("字段映射: -")
        self.status_label.setText("配置主键和数值列后显示预览")


class QtResultTable(QWidget):
    """结果表格组件（用于步骤3）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.table.clear()
        
        # 显示前100行
        display_df = df.head(100)
        
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        self.table.setHorizontalHeaderLabels(list(display_df.columns))
        
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
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(fg_color))
                self.table.setItem(i, j, item)
                
        self.status_label.setText(f"显示前 {len(display_df)} 行 / 共 {len(df)} 行")
        
    def clear(self):
        """清空"""
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.status_label.setText("")
