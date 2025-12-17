"""
结果预览组件 - 显示类似导出Excel的预览表格
"""
import re
import numpy as np
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from typing import List, Dict, Any, Optional
import pandas as pd
from .scroll_utils import setup_mousewheel_scroll
from config import UI_FONT_BASE, UI_FONT_SMALL, UI_FONT_MONO, TREE_ROW_HEIGHT


class ResultPreview(ttk.Frame):
    """结果预览面板 - 模拟导出Excel的表格样式"""

    def __init__(self, parent):
        super().__init__(parent)

        # 标题区域
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(header_frame, text="📊 结果预览", font=(UI_FONT_BASE[0], UI_FONT_BASE[1] + 1, "bold")).pack(side="left")

        self.status_label = ttk.Label(header_frame, text="", bootstyle="secondary", font=UI_FONT_SMALL)
        self.status_label.pack(side="right")

        # 手工表和系统表样例区域（改为可滚动的5条数据列表）
        samples_frame = ttk.Frame(self)
        samples_frame.pack(fill="x", pady=5)

        # 手工表样例区域
        manual_outer = ttk.Frame(samples_frame, bootstyle="primary", padding=3)
        manual_outer.pack(side="left", fill="both", expand=True, padx=2)
        ttk.Label(manual_outer, text="📄 手工表样例（前5条）", font=(UI_FONT_BASE[0], UI_FONT_BASE[1], "bold")).pack(anchor="w")

        # 创建可滚动容器（限制高度）
        manual_scroll_container = ttk.Frame(manual_outer, height=100)
        manual_scroll_container.pack(fill="both", expand=True, pady=2)
        manual_scroll_container.pack_propagate(False)  # 固定高度

        self.manual_canvas = ttk.Canvas(manual_scroll_container, highlightthickness=0, height=100)
        manual_scrollbar = ttk.Scrollbar(manual_scroll_container, orient="vertical",
                                         command=self.manual_canvas.yview, bootstyle="primary-round")
        self.manual_scroll_frame = ttk.Frame(self.manual_canvas)

        self.manual_scroll_frame.bind(
            "<Configure>",
            lambda e: self.manual_canvas.configure(scrollregion=self.manual_canvas.bbox("all"))
        )

        self.manual_canvas.create_window((0, 0), window=self.manual_scroll_frame, anchor="nw")
        self.manual_canvas.configure(yscrollcommand=manual_scrollbar.set)
        self.manual_canvas.pack(side="left", fill="both", expand=True)
        manual_scrollbar.pack(side="right", fill="y")

        setup_mousewheel_scroll(self.manual_canvas, self.manual_scroll_frame)

        # 系统表样例区域
        system_outer = ttk.Frame(samples_frame, bootstyle="success", padding=3)
        system_outer.pack(side="left", fill="both", expand=True, padx=2)
        ttk.Label(system_outer, text="🗄️ 系统表样例（前5条）", font=(UI_FONT_BASE[0], UI_FONT_BASE[1], "bold")).pack(anchor="w")

        # 创建可滚动容器（限制高度）
        system_scroll_container = ttk.Frame(system_outer, height=100)
        system_scroll_container.pack(fill="both", expand=True, pady=2)
        system_scroll_container.pack_propagate(False)  # 固定高度

        self.system_canvas = ttk.Canvas(system_scroll_container, highlightthickness=0, height=100)
        system_scrollbar = ttk.Scrollbar(system_scroll_container, orient="vertical",
                                         command=self.system_canvas.yview, bootstyle="success-round")
        self.system_scroll_frame = ttk.Frame(self.system_canvas)

        self.system_scroll_frame.bind(
            "<Configure>",
            lambda e: self.system_canvas.configure(scrollregion=self.system_canvas.bbox("all"))
        )

        self.system_canvas.create_window((0, 0), window=self.system_scroll_frame, anchor="nw")
        self.system_canvas.configure(yscrollcommand=system_scrollbar.set)

        self.system_canvas.pack(side="left", fill="both", expand=True)
        system_scrollbar.pack(side="right", fill="y")

        setup_mousewheel_scroll(self.system_canvas, self.system_scroll_frame)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # 公式说明区（简化版）
        self.formula_frame = ttk.Frame(self, padding=5)
        self.formula_frame.pack(fill="x", pady=5)

        self.formula_label = ttk.Label(
            self.formula_frame,
            text="差值公式: 配置后显示",
            font=(UI_FONT_MONO[0], UI_FONT_MONO[1] + 1, "bold"),
            bootstyle="info"
        )
        self.formula_label.pack(anchor="w")

        # 列字母说明
        self.column_info_label = ttk.Label(
            self.formula_frame,
            text="",
            font=UI_FONT_SMALL,
            bootstyle="secondary"
        )
        self.column_info_label.pack(anchor="w", pady=(2, 0))

        # 表格区域（使用Frame包装以正确布局滚动条）
        table_container = ttk.Frame(self)
        table_container.pack(fill="both", expand=True)
        
        # 创建Treeview
        self.tree = ttk.Treeview(table_container, show="headings", height=15)
        
        # 滚动条（注意：先pack x_scroll，再pack y_scroll和tree，确保布局正确）
        y_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # 布局顺序很重要：先bottom，再right，最后tree
        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # 列字母映射
        self.column_letters = {}  # 列名 -> 字母
        
        # 显示默认提示
        self._show_placeholder()

    def _show_placeholder(self):
        """显示占位提示"""
        self.tree["columns"] = ("hint",)
        self.tree.heading("hint", text="配置字段后显示")
        self.tree.column("hint", width=300, anchor="center")
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", values=("请先配置主键和数值字段...",))
        self.formula_label.config(text="差值公式: 配置后显示")
        self.column_info_label.config(text="")
        # 清空样例区域
        for widget in self.manual_scroll_frame.winfo_children():
            widget.destroy()
        for widget in self.system_scroll_frame.winfo_children():
            widget.destroy()
        ttk.Label(self.manual_scroll_frame, text="配置后显示", 
                 font=("", 8), bootstyle="secondary").pack(pady=5)
        ttk.Label(self.system_scroll_frame, text="配置后显示", 
                 font=("", 8), bootstyle="secondary").pack(pady=5)
    
    def _excel_col_letter(self, index: int) -> str:
        """将 0 基索引转换为 Excel 列字母（支持超过 Z）"""
        # 0 -> A, 25 -> Z, 26 -> AA
        result = ""
        i = index + 1
        while i > 0:
            i, rem = divmod(i - 1, 26)
            result = chr(65 + rem) + result
        return result

    def update_preview(
        self, 
        result_df: Optional[pd.DataFrame], 
        pivot_values: List[str],
        config: Dict[str, Any],
        manual_df: Optional[pd.DataFrame] = None,
        system_df: Optional[pd.DataFrame] = None
    ):
        """
        更新预览
        
        Args:
            result_df: 比对结果DataFrame（前几行）
            pivot_values: 透视值列表
            config: 配置信息（可能包含 'diff_formula', 'float_precision' 等）
            manual_df: 手工表原始DataFrame（用于显示样例）
            system_df: 系统表原始DataFrame（用于显示样例）
        """
        if result_df is None or result_df.empty:
            self._show_placeholder()
            return
        
        # 获取导出列顺序（与导出一致）
        columns = self._get_export_columns(result_df, pivot_values)
        
        if not columns:
            self._show_placeholder()
            return
        
        # 生成列字母映射（支持 Excel 风格）
        self.column_letters = {}
        for i, col in enumerate(columns):
            self.column_letters[col] = self._excel_col_letter(i)
        
        # 配置表格列
        self.tree["columns"] = columns
        
        # 配置表头样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("", 9, "bold"), background="#e7f3ff", foreground="#000")
        
        # 预先设置 tag 颜色（在插入前）
        self.tree.tag_configure("match", background="#d4edda", foreground="#155724")
        self.tree.tag_configure("diff", background="#fff3cd", foreground="#856404")
        self.tree.tag_configure("missing", background="#f8d7da", foreground="#721c24")
        
        # 简单读取前几行用于估算列宽
        sample_rows = result_df.head(8)
        
        for col in columns:
            letter = self.column_letters.get(col, "")
            display_name = self._get_display_name(col)
            # 表头显示: 字母 (名称)
            header_text = f"{letter} ({display_name})" if letter else display_name
            self.tree.heading(col, text=header_text)
            
            # 估算列宽：根据列名与示例内容的长度，限定范围
            max_content_len = max(
                [len(str(display_name))] +
                [len(str(x)) for x in sample_rows.get(col, "").astype(str).tolist()[:8]] if col in sample_rows.columns else [len(str(display_name))]
            )
            # 基于字符数估算像素（粗略）
            width = min(max(80, max_content_len * 8 + 20), 400)
            if col == "__KEY__":
                width = max(width, 150)
            elif col == "比对状态":
                width = max(width, 100)
            self.tree.column(col, width=width, anchor="center")
        
        # 清空数据
        self.tree.delete(*self.tree.get_children())
        
        # 数字格式配置
        float_precision = int(config.get("float_precision", 2))
        
        # 填充数据（前15行）
        for _, row in result_df.head(15).iterrows():
            values = []
            for col in columns:
                val = row.get(col, "")
                if pd.isna(val):
                    val = ""
                elif isinstance(val, (np.floating, float)):
                    # 如果是整数值的浮点，显示为整数；否则保留指定小数位并去掉多余0
                    if float(val).is_integer():
                        val = str(int(round(val)))
                    else:
                        fmt = f"{{:.{float_precision}f}}"
                        val = fmt.format(val).rstrip("0").rstrip(".")
                elif isinstance(val, (np.integer, int)):
                    val = str(int(val))
                else:
                    val = str(val)
                values.append(val)
            
            # 根据状态设置标签
            status = row.get("比对状态", "")
            tag = self._get_row_tag(status)
            if tag:
                self.tree.insert("", "end", values=values, tags=(tag,))
            else:
                self.tree.insert("", "end", values=values)
        
        # 更新公式说明
        self._update_formula_label(config, pivot_values)
        
        # 更新手工表和系统表样例
        self._update_sample_labels(config, pivot_values, manual_df, system_df)
        
        # 更新状态
        self.status_label.config(text=f"预览前{min(15, len(result_df))}行 / 共{len(result_df)}行")

    def _get_export_columns(self, df: pd.DataFrame, pivot_values: List[str]) -> List[str]:
        """获取导出列顺序（新顺序：主键 → 透视列 → 系统总计 → 手工数量 → 差值 → 状态）"""
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
        
        # 4. 手工数量（移到系统总计后面）
        if "手工数量" in df.columns:
            cols.append("手工数量")
        
        # 5. 差值
        if "差值" in df.columns:
            cols.append("差值")
        
        # 6. 比对状态
        if "比对状态" in df.columns:
            cols.append("比对状态")
        
        return cols if cols else list(df.columns)
    
    def _get_display_name(self, col: str) -> str:
        """获取列显示名称"""
        name_map = {
            "__KEY__": "KEY",
            "手工数量": "手工数量",
            "系统总计": "系统总计",
            "差值": "差值",
            "比对状态": "比对状态"
        }
        return name_map.get(col, col)
    
    def _get_row_tag(self, status: str) -> str:
        """根据状态获取行标签"""
        if "一致" in status:
            return "match"
        elif "差异" in status or "↕" in status:
            return "diff"
        elif "缺" in status or "✗" in status:
            return "missing"
        return ""
    
    def _update_formula_label(self, config: Dict[str, Any], pivot_values: List[str]):
        """更新公式说明标签（显示实际公式和原始公式）"""
        # 找到手工数量和系统总计的列字母
        manual_letter = self.column_letters.get("手工数量", "?")
        system_letter = self.column_letters.get("系统总计", "?")
        
        formula = config.get("diff_formula", "")
        if formula:
            # 使用正则分别替换独立的 M/S（确保不替换其他文字中的 M/S）
            display_formula = formula
            display_formula = re.sub(r"\bM\b", manual_letter, display_formula)
            display_formula = re.sub(r"\bS\b", system_letter, display_formula)
            
            # 替换透视列变量（按完整列名匹配）
            for pv in pivot_values:
                pv_letter = self.column_letters.get(pv, None)
                if pv_letter:
                    display_formula = re.sub(r"\b" + re.escape(pv) + r"\b", pv_letter, display_formula)
            
            # 显示公式和原始表达式
            self.formula_label.config(text=f"差值公式: {display_formula}  (原始: {formula})")
        else:
            # 默认简单差值公式
            self.formula_label.config(text=f"简单差值: {manual_letter} - {system_letter}  (M - S)")
        
        # 更新列字母说明
        col_info_parts = []
        for col, letter in sorted(self.column_letters.items(), key=lambda x: x[1]):
            display_name = self._get_display_name(col)
            if display_name != "KEY" and display_name != "比对状态":
                col_info_parts.append(f"{letter}={display_name}")
        
        if col_info_parts:
            self.column_info_label.config(text="列对照: " + ", ".join(col_info_parts))
        else:
            self.column_info_label.config(text="")
    
    def _update_sample_labels(self, config: Dict[str, Any], pivot_values: List[str], manual_df: Optional[pd.DataFrame] = None, system_df: Optional[pd.DataFrame] = None):
        """更新手工表和系统表样例显示（前5条数据）"""
        try:
            # 清空旧样例
            for widget in self.manual_scroll_frame.winfo_children():
                widget.destroy()
            for widget in self.system_scroll_frame.winfo_children():
                widget.destroy()
            
            # 手工表样例
            key_cols = config.get("key_columns", [])
            val_cols = config.get("value_columns", [])
            
            if key_cols and val_cols and manual_df is not None and len(manual_df) > 0:
                # 显示前5条数据
                manual_key_names = [k.get("manual", "") for k in key_cols]
                manual_val_name = val_cols[0].get("manual", "")
                
                sample_count = min(5, len(manual_df))
                for idx in range(sample_count):
                    row = manual_df.iloc[idx]
                    
                    # 构建主键文本
                    key_parts = []
                    for col in manual_key_names[:3]:
                        if col in row:
                            val = str(row[col])[:12]
                            key_parts.append(val)
                    
                    key_text = ", ".join(key_parts)
                    if len(manual_key_names) > 3:
                        key_text += "..."
                    
                    # 构建数值文本
                    val_text = ""
                    if manual_val_name and manual_val_name in row:
                        try:
                            val_text = f" = {float(row[manual_val_name]):.0f}"
                        except:
                            val_text = f" = {row[manual_val_name]}"
                    
                    # 创建一行显示
                    row_frame = ttk.Frame(self.manual_scroll_frame)
                    row_frame.pack(fill="x", padx=2, pady=1)
                    
                    ttk.Label(row_frame, text=f"{idx+1}.", font=("", 8), 
                             bootstyle="primary", width=2).pack(side="left")
                    ttk.Label(row_frame, text=key_text, font=("", 8), 
                             anchor="w").pack(side="left", fill="x", expand=True)
                    if val_text:
                        ttk.Label(row_frame, text=val_text, font=("", 8, "bold"), 
                                 bootstyle="primary").pack(side="right")
                
                # 显示总数
                if len(manual_df) > 5:
                    ttk.Label(self.manual_scroll_frame, 
                             text=f"... 共{len(manual_df)}条数据", 
                             font=("", 7), bootstyle="secondary").pack(pady=2)
            else:
                ttk.Label(self.manual_scroll_frame, text="配置后显示", 
                         font=("", 8), bootstyle="secondary").pack(pady=5)
            
            # 系统表样例
            if key_cols and val_cols and system_df is not None and len(system_df) > 0:
                # 显示前5条数据
                system_key_names = [k.get("system", "") for k in key_cols]
                system_val_name = val_cols[0].get("system", "")
                
                sample_count = min(5, len(system_df))
                for idx in range(sample_count):
                    row = system_df.iloc[idx]
                    
                    # 构建主键文本
                    key_parts = []
                    for col in system_key_names[:3]:
                        if col in row:
                            val = str(row[col])[:12]
                            key_parts.append(val)
                    
                    key_text = ", ".join(key_parts)
                    if len(system_key_names) > 3:
                        key_text += "..."
                    
                    # 构建数值文本
                    val_text = ""
                    if system_val_name and system_val_name in row:
                        try:
                            val_text = f" = {float(row[system_val_name]):.0f}"
                        except:
                            val_text = f" = {row[system_val_name]}"
                    
                    # 创建一行显示
                    row_frame = ttk.Frame(self.system_scroll_frame)
                    row_frame.pack(fill="x", padx=2, pady=1)
                    
                    ttk.Label(row_frame, text=f"{idx+1}.", font=("", 8), 
                             bootstyle="success", width=2).pack(side="left")
                    ttk.Label(row_frame, text=key_text, font=("", 8), 
                             anchor="w").pack(side="left", fill="x", expand=True)
                    if val_text:
                        ttk.Label(row_frame, text=val_text, font=("", 8, "bold"), 
                                 bootstyle="success").pack(side="right")
                
                # 修复: pivot_column 可能是字典或字符串
                pivot_col_config = config.get("pivot_column")
                if isinstance(pivot_col_config, dict):
                    pivot_col = pivot_col_config.get("system")
                elif isinstance(pivot_col_config, str):
                    pivot_col = pivot_col_config
                else:
                    pivot_col = None
                
                # 显示总数和透视信息
                info_parts = []
                if len(system_df) > 5:
                    info_parts.append(f"共{len(system_df)}条")
                if pivot_col and pivot_values:
                    info_parts.append(f"透视: {pivot_col}({len(pivot_values)}值)")
                
                if info_parts:
                    ttk.Label(self.system_scroll_frame, 
                             text=" | ".join(info_parts), 
                             font=("", 7), bootstyle="secondary").pack(pady=2)
            else:
                ttk.Label(self.system_scroll_frame, text="配置后显示", 
                         font=("", 8), bootstyle="secondary").pack(pady=5)
                         
        except Exception as e:
            print(f"更新样例标签失败: {e}")
            import traceback
            traceback.print_exc()
            # 显示错误提示
            for widget in self.manual_scroll_frame.winfo_children():
                widget.destroy()
            for widget in self.system_scroll_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.manual_scroll_frame, text="配置后显示", 
                     font=("", 8), bootstyle="secondary").pack(pady=5)
            ttk.Label(self.system_scroll_frame, text="配置后显示", 
                     font=("", 8), bootstyle="secondary").pack(pady=5)

    def clear(self):
        """清空预览"""
        self._show_placeholder()
    
    def get_column_letters(self) -> Dict[str, str]:
        """获取列字母映射"""
        return self.column_letters.copy()

    def refresh(self, result_df: Optional[pd.DataFrame], pivot_values: List[str], config: Dict[str, Any], manual_df: Optional[pd.DataFrame] = None, system_df: Optional[pd.DataFrame] = None):
        """兼容别名，便于外部调用（同 update_preview）"""
        self.update_preview(result_df, pivot_values, config, manual_df, system_df)
