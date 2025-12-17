"""
配置面板 - 字段映射、筛选、透视等配置
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from typing import Dict, List, Any, Callable, Optional
from .scroll_utils import disable_combobox_scroll, setup_mousewheel_scroll
from config import UI_FONT_BASE, UI_FONT_SMALL, UI_FONT_MONO, CONTROL_PADDING


# 兼容性处理：如果ttkbootstrap没有LabelFrame，创建带标题的Frame替代
if not hasattr(ttk, "LabelFrame"):
    class CustomLabelFrame(ttk.Frame):
        """自定义LabelFrame，使用Frame + Label模拟"""
        def __init__(self, master=None, **kwargs):
            # 提取text参数
            text = kwargs.pop('text', '')
            padding = kwargs.pop('padding', 5)
            super().__init__(master, padding=padding, **kwargs)
            
            # 如果有标题，添加Label
            if text:
                title_label = ttk.Label(self, text=text, font=("", 10, "bold"))
                title_label.pack(anchor="w", pady=(0, 5))
    
    ttk.LabelFrame = CustomLabelFrame


class CollapsibleSection(ttk.Frame):
    """可折叠区块（用于高级配置收纳）。"""

    def __init__(self, parent, title: str, bootstyle: str = "secondary", expanded: bool = False):
        super().__init__(parent)
        self._expanded = bool(expanded)

        header = ttk.Frame(self)
        header.pack(fill="x")

        self._toggle_btn = ttk.Button(
            header,
            text="▼" if self._expanded else "▶",
            width=2,
            bootstyle="secondary-link",
            command=self.toggle,
        )
        self._toggle_btn.pack(side="left")

        self._title_label = ttk.Label(header, text=title, font=(UI_FONT_BASE[0], UI_FONT_BASE[1], "bold"), bootstyle=bootstyle)
        self._title_label.pack(side="left", padx=(6, 0))

        self.body = ttk.Frame(self)
        if self._expanded:
            self.body.pack(fill="x", pady=(6, 0))

    def set_expanded(self, expanded: bool):
        expanded = bool(expanded)
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._toggle_btn.configure(text="▼" if self._expanded else "▶")
        if self._expanded:
            self.body.pack(fill="x", pady=(6, 0))
        else:
            self.body.pack_forget()

    def toggle(self):
        self.set_expanded(not self._expanded)


class ConfigPanel(ttk.Frame):
    """配置面板"""

    def __init__(self, parent, on_config_change: Callable = None):
        super().__init__(parent)
        self.on_config_change = on_config_change
        
        # 配置数据
        self.config = {
            "key_columns": [],      # [{"manual": "col1", "system": "col2"}, ...]
            "value_columns": [],    # [{"manual": "col1", "system": "col2"}, ...]
            "manual_filters": [],   # [{"column": "col", "operator": "=", "value": "val"}, ...]
            "system_filters": [],
            "pivot_column": None,
            "diff_formula": "",
        }
        
        # 可用列
        self.manual_headers: List[str] = []
        self.system_headers: List[str] = []
        self.pivot_values: List[str] = []
        
        # 列字母映射（从结果预览同步）
        self.column_letters: Dict[str, str] = {}
        
        self._create_widgets()

    def _create_widgets(self):
        """创建控件：采用 Notebook 收纳各步骤，减少一次性信息量"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # 字段映射 Tab（主键 + 数值比对）
        mapping_tab = ttk.Frame(self.notebook, padding=CONTROL_PADDING)
        self.notebook.add(mapping_tab, text="字段映射")
        _, self.scroll_frame = self._create_scrollable(mapping_tab)
        self._create_key_section()
        self._create_value_section()

        # 高级筛选 Tab（筛选 + 透视）
        filter_tab = ttk.Frame(self.notebook, padding=CONTROL_PADDING)
        self.notebook.add(filter_tab, text="高级筛选")
        _, self.scroll_frame = self._create_scrollable(filter_tab)
        self._create_filter_section()

        # 差值公式 Tab
        formula_tab = ttk.Frame(self.notebook, padding=CONTROL_PADDING)
        self.notebook.add(formula_tab, text="差值公式")
        _, self.scroll_frame = self._create_scrollable(formula_tab)
        self._create_formula_section()

    def _create_scrollable(self, parent):
        """创建带滚动的容器并返回 (canvas, frame)。"""
        canvas = ttk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        setup_mousewheel_scroll(canvas, frame)
        return canvas, frame

    def _create_key_section(self):
        """创建主键配置区"""
        frame = ttk.LabelFrame(self.scroll_frame, text="1. 复合主键 (Group By)", padding=12)
        frame.pack(fill="x", padx=8, pady=10)
        
        self.key_container = ttk.Frame(frame)
        self.key_container.pack(fill="x")
        
        add_btn = ttk.Button(frame, text="+ 添加主键", bootstyle="link", 
                            command=self._add_key_row)
        add_btn.pack(anchor="w", pady=(5, 0))

    def _add_key_row(self, manual_val="", system_val=""):
        """添加主键行"""
        row_frame = ttk.Frame(self.key_container)
        row_frame.pack(fill="x", pady=4)
        
        manual_cb = ttk.Combobox(row_frame, values=self.manual_headers, width=20)
        manual_cb.set(manual_val or "手工表列...")
        manual_cb.pack(side="left", padx=2)
        manual_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(manual_cb)
        
        ttk.Label(row_frame, text="=").pack(side="left", padx=5)
        
        system_cb = ttk.Combobox(row_frame, values=self.system_headers, width=20)
        system_cb.set(system_val or "系统表列...")
        system_cb.pack(side="left", padx=2)
        system_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(system_cb)
        
        del_btn = ttk.Button(row_frame, text="×", bootstyle="danger-link", width=3,
                            command=lambda: self._remove_row(row_frame))
        del_btn.pack(side="left", padx=5)
        
        row_frame.manual_cb = manual_cb
        row_frame.system_cb = system_cb

    def _create_filter_section(self):
        """创建筛选和透视配置区"""
        self.filter_section = CollapsibleSection(
            self.scroll_frame,
            title="2. 高级透视 (Pivot & Filter)",
            bootstyle="info",
            expanded=False,
        )
        self.filter_section.pack(fill="x", padx=5, pady=5)

        frame = ttk.LabelFrame(self.filter_section.body, text="", padding=10)
        frame.pack(fill="x")
        
        # 手工表筛选
        ttk.Label(frame, text="手工表筛选:", font=("", 9, "bold")).pack(anchor="w")
        self.manual_filter_container = ttk.Frame(frame)
        self.manual_filter_container.pack(fill="x")
        
        add_manual_filter_btn = ttk.Button(frame, text="+ 手工表筛选", bootstyle="primary-link",
                                          command=self._add_manual_filter_row)
        add_manual_filter_btn.pack(anchor="w", pady=(2, 10))
        
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)
        
        # 系统表筛选
        ttk.Label(frame, text="系统表筛选:", font=("", 9, "bold")).pack(anchor="w")
        self.filter_container = ttk.Frame(frame)
        self.filter_container.pack(fill="x")
        
        add_filter_btn = ttk.Button(frame, text="+ 系统表筛选", bootstyle="info-link",
                                   command=self._add_filter_row)
        add_filter_btn.pack(anchor="w", pady=(2, 10))
        
        # 透视列
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)
        
        pivot_frame = ttk.Frame(frame)
        pivot_frame.pack(fill="x")
        
        ttk.Label(pivot_frame, text="透视列 (状态):").pack(side="left")
        self.pivot_cb = ttk.Combobox(pivot_frame, values=["(不透视)"], width=25)
        self.pivot_cb.set("(不透视)")
        self.pivot_cb.pack(side="left", padx=10)
        self.pivot_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(self.pivot_cb)
    
    def _add_manual_filter_row(self, col_val="", op_val="EQUALS", val_val=""):
        """添加手工表筛选行"""
        row_frame = ttk.Frame(self.manual_filter_container)
        row_frame.pack(fill="x", pady=2)
        
        col_cb = ttk.Combobox(row_frame, values=self.manual_headers, width=15)
        col_cb.set(col_val or "选择列...")
        col_cb.pack(side="left", padx=2)
        col_cb.bind("<<ComboboxSelected>>", lambda e: self._update_manual_filter_values(row_frame))
        disable_combobox_scroll(col_cb)
        
        op_cb = ttk.Combobox(row_frame, values=["=", "!=", "包含"], width=5)
        op_cb.set({"EQUALS": "=", "NOT_EQUALS": "!=", "CONTAINS": "包含"}.get(op_val, "="))
        op_cb.pack(side="left", padx=2)
        disable_combobox_scroll(op_cb)
        
        # 值选择下拉框（根据选择的列动态更新）
        val_cb = ttk.Combobox(row_frame, values=[], width=15)
        val_cb.set(val_val or "选择值...")
        val_cb.pack(side="left", padx=2)
        val_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(val_cb)
        
        del_btn = ttk.Button(row_frame, text="×", bootstyle="danger-link", width=3,
                            command=lambda: self._remove_row(row_frame))
        del_btn.pack(side="left", padx=5)
        
        row_frame.col_cb = col_cb
        row_frame.op_cb = op_cb
        row_frame.val_cb = val_cb
        row_frame.is_manual = True  # 标记为手工表筛选
    
    def _update_manual_filter_values(self, row_frame):
        """更新手工表筛选的值下拉框"""
        col = row_frame.col_cb.get()
        if col and "..." not in col and hasattr(self, 'manual_df_ref') and self.manual_df_ref is not None:
            try:
                unique_vals = sorted(self.manual_df_ref[col].dropna().astype(str).unique().tolist())
                row_frame.val_cb['values'] = unique_vals
            except:
                pass
        self._on_config_changed()

    def _add_filter_row(self, col_val="", op_val="EQUALS", val_val=""):
        """添加系统表筛选行"""
        row_frame = ttk.Frame(self.filter_container)
        row_frame.pack(fill="x", pady=2)
        
        col_cb = ttk.Combobox(row_frame, values=self.system_headers, width=15)
        col_cb.set(col_val or "选择列...")
        col_cb.pack(side="left", padx=2)
        col_cb.bind("<<ComboboxSelected>>", lambda e: self._update_system_filter_values(row_frame))
        disable_combobox_scroll(col_cb)
        
        op_cb = ttk.Combobox(row_frame, values=["=", "!=", "包含"], width=5)
        op_cb.set({"EQUALS": "=", "NOT_EQUALS": "!=", "CONTAINS": "包含"}.get(op_val, "="))
        op_cb.pack(side="left", padx=2)
        disable_combobox_scroll(op_cb)
        
        # 值选择下拉框（根据选择的列动态更新）
        val_cb = ttk.Combobox(row_frame, values=[], width=15)
        val_cb.set(val_val or "选择值...")
        val_cb.pack(side="left", padx=2)
        val_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(val_cb)
        
        del_btn = ttk.Button(row_frame, text="×", bootstyle="danger-link", width=3,
                            command=lambda: self._remove_row(row_frame))
        del_btn.pack(side="left", padx=5)
        
        row_frame.col_cb = col_cb
        row_frame.op_cb = op_cb
        row_frame.val_cb = val_cb
        row_frame.is_system = True  # 标记为系统表筛选
    
    def _update_system_filter_values(self, row_frame):
        """更新系统表筛选的值下拉框"""
        col = row_frame.col_cb.get()
        if col and "..." not in col and hasattr(self, 'system_df_ref') and self.system_df_ref is not None:
            try:
                unique_vals = sorted(self.system_df_ref[col].dropna().astype(str).unique().tolist())
                row_frame.val_cb['values'] = unique_vals
            except:
                pass
        self._on_config_changed()

    def _create_value_section(self):
        """创建数值比对配置区"""
        frame = ttk.LabelFrame(self.scroll_frame, text="3. 数值比对 (Value)", padding=12)
        frame.pack(fill="x", padx=8, pady=10)
        
        self.value_container = ttk.Frame(frame)
        self.value_container.pack(fill="x")
        
        add_btn = ttk.Button(frame, text="+ 添加比对列", bootstyle="link",
                            command=self._add_value_row)
        add_btn.pack(anchor="w", pady=(5, 0))

    def _add_value_row(self, manual_val="", system_val=""):
        """添加数值比对行"""
        row_frame = ttk.Frame(self.value_container)
        row_frame.pack(fill="x", pady=4)
        
        manual_cb = ttk.Combobox(row_frame, values=self.manual_headers, width=20)
        manual_cb.set(manual_val or "手工表数值...")
        manual_cb.pack(side="left", padx=2)
        manual_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(manual_cb)
        
        ttk.Label(row_frame, text="vs").pack(side="left", padx=5)
        
        # 系统表数值可选透视值
        system_values = self.system_headers.copy()
        if self.pivot_values:
            system_values.extend([f"透视: {pv}" for pv in self.pivot_values])
        
        system_cb = ttk.Combobox(row_frame, values=system_values, width=20)
        system_cb.set(system_val or "系统表数值...")
        system_cb.pack(side="left", padx=2)
        system_cb.bind("<<ComboboxSelected>>", lambda e: self._on_config_changed())
        disable_combobox_scroll(system_cb)
        
        del_btn = ttk.Button(row_frame, text="×", bootstyle="danger-link", width=3,
                            command=lambda: self._remove_row(row_frame))
        del_btn.pack(side="left", padx=5)
        
        row_frame.manual_cb = manual_cb
        row_frame.system_cb = system_cb

    def _create_formula_section(self):
        """创建差值公式配置区"""
        self.formula_section = CollapsibleSection(
            self.scroll_frame,
            title="4. 差值公式 (可选)",
            bootstyle="warning",
            expanded=False,
        )
        self.formula_section.pack(fill="x", padx=5, pady=5)

        frame = ttk.LabelFrame(self.formula_section.body, text="", padding=10)
        frame.pack(fill="x")
        
        # 公式选择下拉框
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", pady=5)
        
        ttk.Label(select_frame, text="快速选择:", font=("", 9, "bold")).pack(side="left", padx=5)
        self.formula_select_cb = ttk.Combobox(select_frame, width=35, state="readonly")
        self.formula_select_cb.pack(side="left", fill="x", expand=True, padx=5)
        self.formula_select_cb.bind("<<ComboboxSelected>>", self._on_formula_selected)
        disable_combobox_scroll(self.formula_select_cb)
        
        # 公式输入
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=5)
        
        ttk.Label(input_frame, text="自定义公式:", font=("", 9, "bold")).pack(side="left", padx=5)
        self.formula_entry = ttk.Entry(input_frame, width=50, font=UI_FONT_MONO)
        self.formula_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.formula_entry.bind("<KeyRelease>", lambda e: self._on_config_changed())
        
        # 可用变量说明（使用代号）
        var_frame = ttk.LabelFrame(frame, text="可用变量（ABC代号与结果预览同步）", padding=5)
        var_frame.pack(fill="x", pady=5)
        
        # 动态变量容器
        self.vars_display_frame = ttk.Frame(var_frame)
        self.vars_display_frame.pack(fill="x", pady=2)
        
        # 初始提示
        self.vars_placeholder = ttk.Label(
            self.vars_display_frame,
            text="配置字段后将显示可用变量...",
            bootstyle="secondary",
            font=("", 9)
        )
        self.vars_placeholder.pack(anchor="w")
        
        # 示例（动态）
        self.example_frame = ttk.LabelFrame(frame, text="公式说明", padding=5, bootstyle="info")
        self.example_frame.pack(fill="x", pady=5)
        
        # 示例容器
        self.examples_display = ttk.Frame(self.example_frame)
        self.examples_display.pack(fill="x")
        
        # 初始提示
        self.examples_placeholder = ttk.Label(
            self.examples_display,
            text="配置字段后将显示公式说明...",
            bootstyle="secondary",
            font=("", 9)
        )
        self.examples_placeholder.pack(anchor="w")
    
    def _on_formula_selected(self, event):
        """公式选择事件"""
        selected = self.formula_select_cb.get()
        if selected and ":" in selected:
            # 提取公式部分
            formula = selected.split(":", 1)[1].strip().split("(")[0].strip()
            self.formula_entry.delete(0, "end")
            self.formula_entry.insert(0, formula)
            self._on_config_changed()

    def _remove_row(self, row_frame):
        """移除行"""
        row_frame.destroy()
        self._on_config_changed()

    def _on_config_changed(self):
        """配置变更回调"""
        self._collect_config()
        if self.on_config_change:
            self.on_config_change(self.config)

    def _collect_config(self):
        """收集配置"""
        # 收集主键
        self.config["key_columns"] = []
        for child in self.key_container.winfo_children():
            if hasattr(child, 'manual_cb'):
                manual = child.manual_cb.get()
                system = child.system_cb.get()
                if manual and system and "..." not in manual and "..." not in system:
                    self.config["key_columns"].append({"manual": manual, "system": system})
        
        # 收集手工表筛选
        self.config["manual_filters"] = []
        for child in self.manual_filter_container.winfo_children():
            if hasattr(child, 'col_cb'):
                col = child.col_cb.get()
                op = child.op_cb.get()
                val = child.val_cb.get() if hasattr(child, 'val_cb') else ""
                if col and "..." not in col and val and "..." not in val:
                    op_map = {"=": "EQUALS", "!=": "NOT_EQUALS", "包含": "CONTAINS"}
                    self.config["manual_filters"].append({
                        "column": col,
                        "operator": op_map.get(op, "EQUALS"),
                        "value": val
                    })
        
        # 收集系统表筛选
        self.config["system_filters"] = []
        for child in self.filter_container.winfo_children():
            if hasattr(child, 'col_cb'):
                col = child.col_cb.get()
                op = child.op_cb.get()
                val = child.val_cb.get() if hasattr(child, 'val_cb') else ""
                if col and "..." not in col and val and "..." not in val:
                    op_map = {"=": "EQUALS", "!=": "NOT_EQUALS", "包含": "CONTAINS"}
                    self.config["system_filters"].append({
                        "column": col,
                        "operator": op_map.get(op, "EQUALS"),
                        "value": val
                    })
        
        # 收集透视列
        pivot = self.pivot_cb.get()
        self.config["pivot_column"] = pivot if pivot != "(不透视)" else None
        
        # 收集数值列
        self.config["value_columns"] = []
        for child in self.value_container.winfo_children():
            if hasattr(child, 'manual_cb'):
                manual = child.manual_cb.get()
                system = child.system_cb.get()
                if manual and system and "..." not in manual and "..." not in system:
                    self.config["value_columns"].append({"manual": manual, "system": system})
        
        # 收集公式
        self.config["diff_formula"] = self.formula_entry.get()

    def set_headers(self, manual_headers: List[str], system_headers: List[str]):
        """设置可用列"""
        self.manual_headers = manual_headers
        self.system_headers = system_headers
        
        # 更新透视列下拉框
        self.pivot_cb['values'] = ["(不透视)"] + system_headers
        
        # 更新现有控件
        for child in self.key_container.winfo_children():
            if hasattr(child, 'manual_cb'):
                child.manual_cb['values'] = manual_headers
                child.system_cb['values'] = system_headers
        
        for child in self.value_container.winfo_children():
            if hasattr(child, 'manual_cb'):
                child.manual_cb['values'] = manual_headers
                child.system_cb['values'] = system_headers
        
        for child in self.filter_container.winfo_children():
            if hasattr(child, 'col_cb'):
                child.col_cb['values'] = system_headers
        
        for child in self.manual_filter_container.winfo_children():
            if hasattr(child, 'col_cb'):
                child.col_cb['values'] = manual_headers

    def set_pivot_values(self, pivot_values: List[str]):
        """设置透视值（更新公式可用变量）"""
        self.pivot_values = pivot_values
    
    def update_column_letters(self, column_letters: Dict[str, str]):
        """
        更新列字母映射（从结果预览同步）
        
        Args:
            column_letters: 列名 -> 字母代号的映射
        """
        self.column_letters = column_letters.copy()
        
        # 清空可用变量显示
        for widget in self.vars_display_frame.winfo_children():
            widget.destroy()
        
        # 清空示例显示
        for widget in self.examples_display.winfo_children():
            widget.destroy()
        
        if not column_letters:
            # 显示占位提示
            self.vars_placeholder = ttk.Label(
                self.vars_display_frame,
                text="配置字段后将显示可用变量...",
                bootstyle="secondary",
                font=("", 9)
            )
            self.vars_placeholder.pack(anchor="w")
            
            self.examples_placeholder = ttk.Label(
                self.examples_display,
                text="配置字段后将显示公式说明...",
                bootstyle="secondary",
                font=("", 9)
            )
            self.examples_placeholder.pack(anchor="w")
            
            # 清空公式下拉框
            self.formula_select_cb['values'] = []
            return
        
        # 显示可用变量
        # 1. 手工数量
        manual_letter = column_letters.get("手工数量", "?")
        var_row1 = ttk.Frame(self.vars_display_frame)
        var_row1.pack(fill="x", pady=1)
        ttk.Label(var_row1, text=manual_letter, font=("Consolas", 9, "bold"),
                 bootstyle="primary", width=5).pack(side="left")
        ttk.Label(var_row1, text="手工数量:", font=("", 9), width=10).pack(side="left")
        ttk.Label(var_row1, text="手工表聚合后的数值", font=("", 8),
                 bootstyle="secondary").pack(side="left", padx=5)
        
        # 2. 系统总计
        system_letter = column_letters.get("系统总计", "?")
        var_row2 = ttk.Frame(self.vars_display_frame)
        var_row2.pack(fill="x", pady=1)
        ttk.Label(var_row2, text=system_letter, font=("Consolas", 9, "bold"),
                 bootstyle="primary", width=5).pack(side="left")
        ttk.Label(var_row2, text="系统总计:", font=("", 9), width=10).pack(side="left")
        ttk.Label(var_row2, text="系统表聚合/透视后的总计", font=("", 8),
                 bootstyle="secondary").pack(side="left", padx=5)
        
        # 3. 透视列（如果有）
        pivot_letters = []
        for col, letter in sorted(column_letters.items(), key=lambda x: x[1]):
            if col not in ["__KEY__", "手工数量", "系统总计", "差值", "比对状态"]:
                pivot_letters.append((letter, col))
        
        if pivot_letters:
            pivot_row = ttk.Frame(self.vars_display_frame)
            pivot_row.pack(fill="x", pady=3)
            ttk.Label(pivot_row, text="透视列:", font=("", 9, "bold"),
                     bootstyle="info").pack(side="left", padx=5)
            
            for letter, col in pivot_letters[:10]:  # 最多显示10个
                var_label = ttk.Label(
                    pivot_row,
                    text=f"{letter}={col}",
                    font=("Consolas", 8),
                    bootstyle="info-inverse"
                )
                var_label.pack(side="left", padx=2)
            
            if len(pivot_letters) > 10:
                ttk.Label(pivot_row, text="...", font=("", 8)).pack(side="left")
        
        # 更新示例（使用实际字母）
        examples = [
            ("简单差值", f"{manual_letter} - {system_letter}", "手工数量 - 系统总计"),
        ]
        
        # 构建公式下拉框选项
        formula_options = [f"简单差值: {manual_letter} - {system_letter} (手工 - 系统总计)"]
        
        # 如果有透视列，添加更多示例
        if pivot_letters:
            first_pivot = pivot_letters[0][0]
            first_pivot_name = pivot_letters[0][1]
            examples.append(
                ("排除某透视列", f"{manual_letter} - ({system_letter} - {first_pivot})", f"不计算{first_pivot_name}的差异")
            )
            formula_options.append(f"排除{first_pivot_name}: {manual_letter} - ({system_letter} - {first_pivot}) (排除特定透视列)")
            
            if len(pivot_letters) >= 2:
                second_pivot = pivot_letters[1][0]
                second_pivot_name = pivot_letters[1][1]
                examples.append(
                    ("只看特定列", f"{manual_letter} - ({first_pivot} + {second_pivot})", f"只比对前两个透视列")
                )
                formula_options.append(f"特定透视: {manual_letter} - ({first_pivot} + {second_pivot}) (只对比指定列)")
            
            # 添加全透视列求和的公式示例
            if len(pivot_letters) >= 3:
                pivot_sum = " + ".join([p[0] for p in pivot_letters[:5]])
                if len(pivot_letters) > 5:
                    pivot_sum += " + ..."
                examples.append(
                    ("手工 vs 透视汇总", f"{manual_letter} - ({pivot_sum})", "手工对比所有透视列之和")
                )
                formula_options.append(f"透视汇总: {manual_letter} - ({pivot_sum}) (对比所有透视列)")
        
        # 更新公式下拉框
        self.formula_select_cb['values'] = formula_options
        
        for title, formula, desc in examples:
            ex_row = ttk.Frame(self.examples_display)
            ex_row.pack(fill="x", pady=2)
            ttk.Label(ex_row, text=f"{title}:", font=("", 8, "bold"), 
                     width=12).pack(side="left")
            ttk.Label(ex_row, text=formula, font=("Consolas", 8),
                     bootstyle="info", width=25).pack(side="left", padx=5)
            ttk.Label(ex_row, text=f"({desc})", font=("", 7),
                     bootstyle="secondary").pack(side="left")

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        self._collect_config()
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        # 清空现有
        for child in self.key_container.winfo_children():
            child.destroy()
        for child in self.value_container.winfo_children():
            child.destroy()
        for child in self.filter_container.winfo_children():
            child.destroy()
        for child in self.manual_filter_container.winfo_children():
            child.destroy()
        
        # 加载主键
        for kc in config.get("key_columns", []):
            self._add_key_row(kc.get("manual", ""), kc.get("system", ""))
        
        # 加载数值列
        for vc in config.get("value_columns", []):
            self._add_value_row(vc.get("manual", ""), vc.get("system", ""))
        
        # 加载系统表筛选
        for fc in config.get("system_filters", []):
            self._add_filter_row(fc.get("column", ""), fc.get("operator", "EQUALS"), fc.get("value", ""))
        
        # 加载手工表筛选
        for fc in config.get("manual_filters", []):
            self._add_manual_filter_row(fc.get("column", ""), fc.get("operator", "EQUALS"), fc.get("value", ""))
        
        # 加载透视列
        pivot = config.get("pivot_column")
        self.pivot_cb.set(pivot if pivot else "(不透视)")
        
        # 加载公式
        self.formula_entry.delete(0, "end")
        self.formula_entry.insert(0, config.get("diff_formula", ""))
        
        self.config = config.copy()

        # 若高级项已有配置，自动展开对应区块
        self._auto_expand_advanced_sections(config)

    def _auto_expand_advanced_sections(self, config: Dict[str, Any]):
        """根据配置内容决定是否自动展开高级区块。"""
        advanced_enabled = bool(config.get("manual_filters") or config.get("system_filters") or config.get("pivot_column"))
        formula_enabled = bool(str(config.get("diff_formula", "")).strip())

        if hasattr(self, "filter_section"):
            self.filter_section.set_expanded(advanced_enabled)
        if hasattr(self, "formula_section"):
            self.formula_section.set_expanded(formula_enabled)
    
    def set_manual_df(self, df):
        """设置手工表DataFrame引用，用于筛选值下拉框"""
        self.manual_df_ref = df
    
    def set_system_df(self, df):
        """设置系统表DataFrame引用，用于筛选值下拉框"""
        self.system_df_ref = df
