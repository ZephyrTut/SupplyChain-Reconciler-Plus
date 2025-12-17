"""
主窗口 - 应用程序主界面
"""
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import ttk as tk_ttk
# 兼容性处理：如果ttkbootstrap没有LabelFrame，创建带标题的Frame替代
if not hasattr(ttk, "LabelFrame"):
    class CustomLabelFrame(ttk.Frame):
        """自定义LabelFrame，使用Frame + Label模拟"""
        def __init__(self, master=None, **kwargs):
            text = kwargs.pop('text', '')
            padding = kwargs.pop('padding', 5)
            super().__init__(master, padding=padding, **kwargs)
            if text:
                title_label = ttk.Label(self, text=text, font=("", 10, "bold"))
                title_label.pack(anchor="w", pady=(0, 5))
    ttk.LabelFrame = CustomLabelFrame
if not hasattr(ttk, "PanedWindow"):
    ttk.PanedWindow = tk_ttk.PanedWindow
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime

from config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_SIZE,
    UI_THEME,
    UI_THEME_FALLBACKS,
    UI_FONT_BASE,
    UI_FONT_BASE_LARGE,
    UI_FONT_TITLE,
    UI_FONT_SMALL,
    UI_FONT_MONO,
    TREE_ROW_HEIGHT,
    CONTROL_PADDING,
    CARD_PADDING,
)
from core import CompareEngine, ExportEngine
from .config_panel import ConfigPanel
from .result_preview import ResultPreview
from .template_manager import TemplateManagerDialog
from .loading import LoadingDialog, run_with_loading
from utils import load_excel, get_sheet_names, load_config, save_config, load_templates, save_template, delete_template, auto_detect_active_workbook

# 响应式断点（静态判定：以启动窗口宽度为准）
RESPONSIVE_BREAKPOINT = 1280

# 尝试支持拖拽
DND_AVAILABLE = False
DND_FILES = None
TkinterDnD = None

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except Exception:
    # 如果 tkinterdnd2 加载失败，继续使用普通 Window
    DND_AVAILABLE = False


class MainWindow:
    """主窗口"""

    def __init__(self):
        # 根据拖拽支持情况选择基类
        if DND_AVAILABLE:
            # 创建支持拖拽的窗口
            import tkinter as tk
            root = TkinterDnD.Tk()
            self.root = root
        else:
            self.root = ttk.Window()

        # 应用深色主题与全局字体（含可用主题回退）
        self.style = self._init_style()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)

        # 布局模式（静态判定：启动时决定，不随窗口缩放动态切换）
        self.layout_mode = self._get_initial_layout_mode()
        
        # 数据
        self.manual_df: Optional[pd.DataFrame] = None
        self.system_df: Optional[pd.DataFrame] = None
        self.manual_file_path: str = ""
        self.system_file_path: str = ""
        self.result_df: Optional[pd.DataFrame] = None
        self.pivot_values: List[str] = []
        
        # 当前步骤
        self.current_step = 1
        
        self._create_ui()
        self._load_saved_config()

    def _init_style(self):
        """初始化主题和全局字体，优先使用深色方案。"""
        style = ttk.Style()

        chosen = None
        for theme in [UI_THEME] + UI_THEME_FALLBACKS:
            try:
                if theme in style.theme_names():
                    style.theme_use(theme)
                    chosen = theme
                    break
            except Exception:
                # 某些环境可能缺少主题，继续尝试后备主题
                continue

        if chosen is None:
            chosen = style.theme_use()

        self.current_theme = chosen

        # 统一基础字体和控件尺寸，提升暗色主题下的可读性
        style.configure(".", font=UI_FONT_BASE)
        style.configure("TLabel", font=UI_FONT_BASE)
        style.configure("TButton", font=UI_FONT_BASE, padding=6)
        style.configure("TNotebook.Tab", font=UI_FONT_BASE, padding=(10, 6))
        style.configure("TEntry", font=UI_FONT_MONO)
        style.configure("TCombobox", font=UI_FONT_BASE)
        style.configure("Treeview", font=UI_FONT_MONO, rowheight=TREE_ROW_HEIGHT)
        style.configure(
            "Treeview.Heading",
            font=(UI_FONT_BASE[0], UI_FONT_BASE[1] + 1, "bold"),
            background="#2b2d42",
            foreground="#edf2f4",
            bordercolor="#2b2d42",
        )
        style.map("Treeview.Heading", background=[("active", "#3d405b")])
        
        # 配置Treeview行背景（斑马纹效果）
        style.configure("Treeview", background="#1e1e1e", fieldbackground="#1e1e1e", foreground="#edf2f4")
        style.map("Treeview", background=[("selected", "#3d405b")])

        # 拖拽区域样式（虚线感通过边框与暗色背景对比体现）
        style.configure(
            "dropzone.TFrame",
            background="#2b2d30",
            bordercolor="#4a5568",
        )

        return style

    def _get_initial_layout_mode(self) -> str:
        """根据启动窗口宽度做一次性布局判定（wide/narrow）"""
        width = None
        try:
            # 支持 "1400x900" 或 "1400x900+10+10"
            geom = str(WINDOW_SIZE)
            if "x" in geom:
                width_part = geom.split("x", 1)[0]
                width = int(width_part)
        except Exception:
            width = None

        if width is not None and width < RESPONSIVE_BREAKPOINT:
            return "narrow"
        return "wide"

    def _is_narrow_mode(self) -> bool:
        return getattr(self, "layout_mode", "wide") == "narrow"

    def _create_ui(self):
        """创建UI"""
        # 顶部栏
        self._create_header()
        
        # 步骤指示器
        self._create_step_indicator()
        
        # 主内容区
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Step 1: 文件选择
        self._create_step1_frame()
        
        # Step 2: 配置面板
        self._create_step2_frame()
        
        # Step 3: 结果面板
        self._create_step3_frame()
        
        # 显示第一步
        self._show_step(1)

    def _create_header(self):
        """创建顶部栏"""
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")
        
        # Logo
        logo_frame = ttk.Frame(header)
        logo_frame.pack(side="left")
        
        ttk.Label(logo_frame, text="📊", font=(UI_FONT_TITLE[0], UI_FONT_TITLE[1] + 6)).pack(side="left")
        ttk.Label(logo_frame, text=APP_NAME, font=UI_FONT_TITLE).pack(side="left", padx=10)
        
        # 模板下拉框区域
        template_frame = ttk.Frame(header)
        template_frame.pack(side="right")
        
        ttk.Label(template_frame, text="模板:", font=UI_FONT_SMALL).pack(side="left", padx=(0, 5))
        
        self.template_cb = ttk.Combobox(template_frame, values=["(选择模板)"], width=20, state="readonly")
        self.template_cb.set("(选择模板)")
        self.template_cb.pack(side="left", padx=2)
        self.template_cb.bind("<<ComboboxSelected>>", self._on_template_selected)
        
        # 模板管理按钮（打开管理弹窗）
        ttk.Button(template_frame, text="🗑️", width=3, bootstyle="danger-outline",
                  command=self._show_template_manager).pack(side="left", padx=2)
        
        # 刷新模板列表
        self._refresh_template_list()

    def _create_step_indicator(self):
        """创建步骤指示器"""
        indicator = ttk.Frame(self.root, padding=10)
        indicator.pack(fill="x")
        
        self.step_labels = []
        steps = ["1. 导入文件", "2. 配置字段", "3. 查看结果"]
        
        for i, step in enumerate(steps):
            # 使用Label+分隔符的方式，让步骤更像流程指示器
            label = ttk.Label(indicator, text=step, font=UI_FONT_BASE, bootstyle="secondary")
            label.pack(side="left", padx=15)
            self.step_labels.append(label)
            
            # 在非最后一项后添加箭头分隔符
            if i < len(steps) - 1:
                ttk.Label(indicator, text="→", font=UI_FONT_BASE, bootstyle="secondary").pack(side="left", padx=5)

    def _create_step1_frame(self):
        """创建步骤1 - 文件选择"""
        self.step1_frame = ttk.Frame(self.main_container)
        
        # 文件选择区
        files_frame = ttk.Frame(self.step1_frame)
        files_frame.pack(fill="x", pady=20)
        
        # 手工表
        manual_card = ttk.Frame(files_frame, padding=CARD_PADDING, bootstyle="card", borderwidth=1)
        if self._is_narrow_mode():
            manual_card.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
        else:
            manual_card.pack(side="left", fill="both", expand=True, padx=10)
        
        ttk.Label(manual_card, text="📄 手工表", font=UI_FONT_BASE_LARGE).pack(pady=(0, 5))
        
        self.manual_label = ttk.Label(manual_card, text="点击选择文件或拖拽至此...", 
                                      bootstyle="secondary")
        self.manual_label.pack(pady=5)
        
        btn_frame_m = ttk.Frame(manual_card)
        btn_frame_m.pack(pady=5)
        
        ttk.Button(btn_frame_m, text="📁 选择文件", bootstyle="primary",
                  command=lambda: self._select_file("manual")).pack(side="left", padx=2)
        ttk.Button(btn_frame_m, text="📊 活动Excel", bootstyle="info-outline",
                  command=lambda: self._detect_active("manual")).pack(side="left", padx=2)
        
        self.manual_sheet_cb = ttk.Combobox(manual_card, state="disabled", width=30)
        self.manual_sheet_cb.pack(pady=10)
        self.manual_sheet_cb.bind("<<ComboboxSelected>>", 
                                  lambda e: self._on_sheet_selected("manual"))
        
        # 系统表
        system_card = ttk.Frame(files_frame, padding=CARD_PADDING, bootstyle="card", borderwidth=1)
        if self._is_narrow_mode():
            system_card.pack(side="top", fill="both", expand=True, padx=10)
        else:
            system_card.pack(side="left", fill="both", expand=True, padx=10)
        
        ttk.Label(system_card, text="🗂️ 系统表", font=UI_FONT_BASE_LARGE).pack(pady=(0, 5))
        
        self.system_label = ttk.Label(system_card, text="点击选择文件或拖拽至此...", 
                                      bootstyle="secondary")
        self.system_label.pack(pady=5)
        
        btn_frame_s = ttk.Frame(system_card)
        btn_frame_s.pack(pady=5)
        
        ttk.Button(btn_frame_s, text="📁 选择文件", bootstyle="success",
                  command=lambda: self._select_file("system")).pack(side="left", padx=2)
        ttk.Button(btn_frame_s, text="📊 活动Excel", bootstyle="info-outline",
                  command=lambda: self._detect_active("system")).pack(side="left", padx=2)
        
        self.system_sheet_cb = ttk.Combobox(system_card, state="disabled", width=30)
        self.system_sheet_cb.pack(pady=10)
        self.system_sheet_cb.bind("<<ComboboxSelected>>", 
                                  lambda e: self._on_sheet_selected("system"))
        
        # 注册拖拽功能（可选）
        self._apply_dropzone_idle(manual_card)
        self._apply_dropzone_idle(system_card)
        self._setup_drag_drop(manual_card, system_card)
        
        # 下一步按钮
        btn_frame = ttk.Frame(self.step1_frame)
        btn_frame.pack(pady=30)
        
        self.next_btn1 = ttk.Button(btn_frame, text="智能解析 & 进入配置 ➡️", 
                                    bootstyle="primary", state="disabled",
                                    command=self._go_to_step2)
        self.next_btn1.pack()
    
    def _setup_drag_drop(self, manual_card, system_card):
        """设置拖拽功能 - 分别为两个卡片区域设置拖拽"""
        if not DND_AVAILABLE:
            return
        
        try:
            # 为手工表卡片注册拖拽
            manual_card.drop_target_register(DND_FILES)
            manual_card.dnd_bind('<<Drop>>', lambda e: self._on_drop(e, "manual"))
            
            # 为系统表卡片注册拖拽
            system_card.drop_target_register(DND_FILES)
            system_card.dnd_bind('<<Drop>>', lambda e: self._on_drop(e, "system"))
            
            # 保存卡片引用用于视觉反馈
            self.manual_card = manual_card
            self.system_card = system_card
            
            # 添加拖拽进入/离开的视觉反馈
            manual_card.dnd_bind('<<DropEnter>>', lambda e: self._on_drag_enter(manual_card))
            manual_card.dnd_bind('<<DropLeave>>', lambda e: self._on_drag_leave(manual_card))
            system_card.dnd_bind('<<DropEnter>>', lambda e: self._on_drag_enter(system_card))
            system_card.dnd_bind('<<DropLeave>>', lambda e: self._on_drag_leave(system_card))
            
        except Exception as e:
            print(f"拖拽初始化失败: {e}")

    def _apply_dropzone_idle(self, widget):
        """设置拖拽区域的基础视觉样式"""
        try:
            widget.configure(borderwidth=2, relief="ridge", padding=CARD_PADDING)
            widget.configure(style="dropzone.TFrame")
        except Exception:
            pass

    def _apply_dropzone_active(self, widget):
        """拖拽进入时的高亮样式"""
        try:
            widget.configure(borderwidth=3, relief="solid")
        except Exception:
            pass
    
    def _on_drop(self, event, file_type: str):
        """处理拖拽文件事件 - 根据拖拽区域自动识别目标"""
        try:
            files = self.root.tk.splitlist(event.data)
            if not files:
                return
            
            filepath = files[0].strip('{}')
            
            # 检查是否为Excel文件
            if not filepath.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                Messagebox.show_warning(
                    "文件类型错误", 
                    "请拖入 Excel 文件\n\n支持格式：.xlsx, .xls, .xlsm"
                )
                return
            
            # 根据拖拽目标区域直接导入
            target_name = "手工表" if file_type == "manual" else "系统表"
            print(f"拖拽文件到 {target_name}: {os.path.basename(filepath)}")
            
            self._load_file_from_path(filepath, file_type)
            
        except Exception as e:
            Messagebox.show_error(f"拖拽文件失败: {e}", "错误")
    
    def _on_drag_enter(self, widget):
        """拖拽进入时的视觉反馈"""
        self._apply_dropzone_active(widget)
    
    def _on_drag_leave(self, widget):
        """拖拽离开时恢复样式"""
        self._apply_dropzone_idle(widget)
    
    def _detect_active(self, file_type: str):
        """检测活动 Excel 工作簿并导入"""
        try:
            result = auto_detect_active_workbook()
            
            if result is None:
                Messagebox.show_info(
                    "未检测到活动Excel",
                    "未检测到打开的 Excel 文件。\n\n" +
                    "请确保：\n" +
                    "  • Excel 已打开文件\n" +
                    "  • 文件已保存\n" +
                    "  • 已安装 pywin32 库 (pip install pywin32)"
                )
                return
            
            path = result.get("path")
            name = result.get("name", "未知文件")
            sheet_name = result.get("sheet_name", "")
            
            if not path:
                Messagebox.show_warning(
                    "文件未保存",
                    f"检测到活动工作簿：{name}\n" +
                    f"当前工作表：{sheet_name}\n\n" +
                    "但文件尚未保存到磁盘。\n\n" +
                    "请先保存文件 (Ctrl+S) 后重试。"
                )
                return
            
            # 显示检测到的信息
            target_name = "手工表" if file_type == "manual" else "系统表"
            print(f"检测到活动Excel - 导入到{target_name}: {name} [{sheet_name}]")
            
            # 加载文件
            self._load_file_from_path(path, file_type)
            
        except RuntimeError as e:
            # WPS 检测提示
            Messagebox.show_warning(
                "WPS Office 提示", 
                f"检测到 WPS Office 环境\n\n{str(e)}\n\n" +
                "建议：请使用 Microsoft Excel 或手动选择文件。"
            )
        except Exception as e:
            Messagebox.show_error(
                "检测失败", 
                f"活动Excel检测失败\n\n错误信息：{str(e)}\n\n" +
                "请尝试手动选择文件。"
            )
    
    def _load_file_from_path(self, filepath: str, file_type: str):
        """从路径加载文件（统一处理函数）"""
        try:
            sheets = get_sheet_names(filepath)
            if not sheets:
                Messagebox.show_error("错误", "文件不包含任何工作表")
                return
            
            if file_type == "manual":
                self.manual_file_path = filepath
                self.manual_label.config(text=os.path.basename(filepath))
                self.manual_sheet_cb.config(state="readonly", values=sheets)
                if len(sheets) == 1:
                    self.manual_sheet_cb.set(sheets[0])
                    self._on_sheet_selected("manual")
                else:
                    self.manual_sheet_cb.set("")
                    Messagebox.show_info("选择工作表", f"文件包含 {len(sheets)} 个工作表，请选择一个")
            else:
                self.system_file_path = filepath
                self.system_label.config(text=os.path.basename(filepath))
                self.system_sheet_cb.config(state="readonly", values=sheets)
                if len(sheets) == 1:
                    self.system_sheet_cb.set(sheets[0])
                    self._on_sheet_selected("system")
                else:
                    self.system_sheet_cb.set("")
                    Messagebox.show_info("选择工作表", f"文件包含 {len(sheets)} 个工作表，请选择一个")
            
            self._check_ready()
            
        except Exception as e:
            Messagebox.show_error("加载文件失败", str(e))

    def _create_step2_frame(self):
        """创建步骤2 - 配置"""
        self.step2_frame = ttk.Frame(self.main_container)

        # 使用 grid 固定底部按钮条（避免主内容区把按钮条挤出可视范围）
        self.step2_frame.columnconfigure(0, weight=1)
        self.step2_frame.rowconfigure(0, weight=1)
        self.step2_frame.rowconfigure(1, weight=0)
        self.step2_frame.rowconfigure(2, weight=0)

        content_frame = ttk.Frame(self.step2_frame)
        content_frame.grid(row=0, column=0, sticky="nsew")

        if self._is_narrow_mode():
            # 窄屏：Tabs（配置 / 预览）
            notebook = ttk.Notebook(content_frame)
            notebook.pack(fill="both", expand=True)

            config_tab = ttk.Frame(notebook, padding=10)
            preview_tab = ttk.Frame(notebook, padding=10)
            notebook.add(config_tab, text="配置")
            notebook.add(preview_tab, text="预览")

            self.config_panel = ConfigPanel(config_tab, on_config_change=self._on_config_change)
            self.config_panel.pack(fill="both", expand=True)

            self.result_preview = ResultPreview(preview_tab)
            self.result_preview.pack(fill="both", expand=True)
        else:
            # 宽屏：两列布局：配置 | 结果预览
            paned = ttk.PanedWindow(content_frame, orient="horizontal")
            paned.pack(fill="both", expand=True)

            # 左侧配置
            left_frame = ttk.Frame(paned, padding=CONTROL_PADDING)
            paned.add(left_frame, weight=1)

            self.config_panel = ConfigPanel(left_frame, on_config_change=self._on_config_change)
            self.config_panel.pack(fill="both", expand=True)

            # 右侧结果预览（模拟导出Excel样式）
            right_frame = ttk.Frame(paned, padding=CONTROL_PADDING)
            paned.add(right_frame, weight=2)

            self.result_preview = ResultPreview(right_frame)
            self.result_preview.pack(fill="both", expand=True)
        
        # 按钮区
        ttk.Separator(self.step2_frame, orient="horizontal").grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(self.step2_frame, padding=10)
        btn_frame.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(btn_frame, text="⬅️ 上一步", bootstyle="secondary",
                  command=lambda: self._show_step(1)).pack(side="left")
        
        ttk.Button(btn_frame, text="💾 保存模板", bootstyle="outline",
                  command=self._save_template).pack(side="left", padx=10)
        
        ttk.Button(btn_frame, text="执行对账 ➡️", bootstyle="success",
                  command=self._run_comparison).pack(side="right")

    def _create_step3_frame(self):
        """创建步骤3 - 结果"""
        self.step3_frame = ttk.Frame(self.main_container)
        
        # 统计卡片
        stats_frame = ttk.Frame(self.step3_frame)
        stats_frame.pack(fill="x", pady=10)
        
        self.stat_cards = {}
        card_defs = [
            ("match", "✓", "success"),
            ("diff", "↕", "warning"),
            ("manual_only", "✗系统缺", "danger"),
            ("system_only", "✗手工缺", "info"),
        ]
        cols = 2 if self._is_narrow_mode() else 4
        for idx, (name, icon, style) in enumerate(card_defs):
            # 统计卡片做成统一“卡片感”（ttk 不支持真正圆角，这里用 card 样式 + 边框提升观感）
            card = ttk.Frame(stats_frame, padding=12, bootstyle="card", borderwidth=1)
            card.grid(row=idx // cols, column=idx % cols, sticky="nsew", padx=5, pady=5)
            
            ttk.Label(card, text=icon, font=(UI_FONT_TITLE[0], UI_FONT_TITLE[1] + 4)).pack()
            count_label = ttk.Label(card, text="0", font=(UI_FONT_TITLE[0], 20, "bold"), bootstyle=style)
            count_label.pack()
            
            self.stat_cards[name] = count_label

        for c in range(cols):
            stats_frame.columnconfigure(c, weight=1)
        
        # 结果表格
        table_frame = ttk.Frame(self.step3_frame)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview
        columns = ("key", "manual", "system", "diff", "status")
        self.result_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        self.result_tree.heading("key", text="主键")
        self.result_tree.heading("manual", text="手工数量")
        self.result_tree.heading("system", text="系统总计")
        self.result_tree.heading("diff", text="差值")
        self.result_tree.heading("status", text="状态")
        
        self.result_tree.column("key", width=250)
        self.result_tree.column("manual", width=100)
        self.result_tree.column("system", width=100)
        self.result_tree.column("diff", width=100)
        self.result_tree.column("status", width=120)
        
        # 滚动条（先底部 x，再右侧 y，再 tree）
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.result_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # 关闭列自动拉伸，确保横向滚动条生效
        for col in columns:
            self.result_tree.column(col, stretch=False)

        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right", fill="y")
        self.result_tree.pack(side="left", fill="both", expand=True)
        
        # 按钮区
        btn_frame = ttk.Frame(self.step3_frame, padding=10)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="⬅️ 返回配置", bootstyle="secondary",
                  command=lambda: self._show_step(2)).pack(side="left")
        
        ttk.Button(btn_frame, text="📥 导出Excel", bootstyle="success",
                  command=self._export_results).pack(side="right")
        
        ttk.Button(btn_frame, text="🔄 新任务", bootstyle="outline",
                  command=self._new_task).pack(side="right", padx=10)

    def _show_step(self, step: int):
        """显示指定步骤"""
        self.current_step = step
        
        # 隐藏所有
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()
        
        # 显示当前
        if step == 1:
            self.step1_frame.pack(fill="both", expand=True)
        elif step == 2:
            self.step2_frame.pack(fill="both", expand=True)
        elif step == 3:
            self.step3_frame.pack(fill="both", expand=True)
        
        # 更新步骤指示器
        for i, label in enumerate(self.step_labels):
            if i < step:
                label.configure(bootstyle="success")
            elif i == step - 1:
                label.configure(bootstyle="primary")
            else:
                label.configure(bootstyle="secondary")

    def _select_file(self, file_type: str):
        """选择文件"""
        filepath = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[
                ("Excel 文件 (推荐)", "*.xlsx;*.xls;*.xlsm"),
                ("新版Excel", "*.xlsx"),
                ("旧版Excel", "*.xls"),
                ("所有文件", "*.*")
            ],
            initialdir=os.path.expanduser("~")
        )
        if not filepath:
            return
        
        try:
            sheets = get_sheet_names(filepath)
            
            if file_type == "manual":
                self.manual_file_path = filepath
                self.manual_label.config(text=os.path.basename(filepath))
                self.manual_sheet_cb.config(state="readonly", values=sheets)
                if len(sheets) == 1:
                    self.manual_sheet_cb.set(sheets[0])
                    self._on_sheet_selected("manual")
                else:
                    self.manual_sheet_cb.set("")
            else:
                self.system_file_path = filepath
                self.system_label.config(text=os.path.basename(filepath))
                self.system_sheet_cb.config(state="readonly", values=sheets)
                if len(sheets) == 1:
                    self.system_sheet_cb.set(sheets[0])
                    self._on_sheet_selected("system")
                else:
                    self.system_sheet_cb.set("")
            
            self._check_ready()
            
        except Exception as e:
            Messagebox.show_error(f"读取文件失败: {e}", "错误")

    def _on_sheet_selected(self, file_type: str):
        """Sheet选择后加载数据"""
        try:
            if file_type == "manual":
                sheet = self.manual_sheet_cb.get()
                if sheet:
                    self.manual_df = load_excel(self.manual_file_path, sheet)
            else:
                sheet = self.system_sheet_cb.get()
                if sheet:
                    self.system_df = load_excel(self.system_file_path, sheet)
            
            self._check_ready()
            
        except Exception as e:
            Messagebox.show_error(f"加载数据失败: {e}", "错误")

    def _check_ready(self):
        """检查是否可以进入下一步"""
        ready = (self.manual_df is not None and 
                self.system_df is not None and 
                len(self.manual_df) > 0 and 
                len(self.system_df) > 0)
        
        self.next_btn1.config(state="normal" if ready else "disabled")

    def _go_to_step2(self):
        """进入步骤2"""
        if self.manual_df is None or self.system_df is None:
            return
        
        # 数据样例预览已移除，样例信息现在显示在结果预览的顶部
        
        # 设置可用列
        self.config_panel.set_headers(
            list(self.manual_df.columns),
            list(self.system_df.columns)
        )
        
        # 传递手工表引用（用于筛选值下拉框）
        self.config_panel.set_manual_df(self.manual_df)
        # 传递系统表引用
        self.config_panel.set_system_df(self.system_df)
        
        # 智能识别字段
        self._auto_detect_fields()
        
        self._show_step(2)

    def _auto_detect_fields(self):
        """智能识别字段"""
        from config import DEFAULT_ALIASES
        
        manual_cols = list(self.manual_df.columns)
        system_cols = list(self.system_df.columns)
        
        # 寻找共同列作为主键候选
        common = set(manual_cols) & set(system_cols)
        
        key_keywords = ['order', 'no', 'id', 'sku', 'code', '单号', '料号', '编码', '订单']
        val_keywords = ['qty', 'amount', '数量', '金额', 'quantity']
        
        suggested_keys = []
        suggested_vals = []
        
        for col in common:
            col_lower = col.lower()
            if any(kw in col_lower for kw in key_keywords):
                suggested_keys.append({"manual": col, "system": col})
            elif any(kw in col_lower for kw in val_keywords):
                suggested_vals.append({"manual": col, "system": col})
        
        # 应用建议
        if suggested_keys:
            for sk in suggested_keys[:2]:
                self.config_panel._add_key_row(sk["manual"], sk["system"])
        
        if suggested_vals:
            for sv in suggested_vals[:1]:
                self.config_panel._add_value_row(sv["manual"], sv["system"])

    def _on_config_change(self, config: Dict[str, Any]):
        """配置变更回调"""
        # 只在透视列发生变化时更新透视值
        pivot_col = config.get("pivot_column")
        current_pivot = getattr(self, '_current_pivot_col', None)
        
        if pivot_col != current_pivot:
            # 透视列变化了，重新计算透视值
            self._current_pivot_col = pivot_col
            if pivot_col and self.system_df is not None and pivot_col in self.system_df.columns:
                self.pivot_values = sorted(self.system_df[pivot_col].dropna().astype(str).unique().tolist())
                self.config_panel.set_pivot_values(self.pivot_values)
            else:
                self.pivot_values = []
                self.config_panel.set_pivot_values([])
        
        # 实时更新结果预览
        self._update_result_preview()
    
    def _update_result_preview(self):
        """更新结果预览"""
        if self.manual_df is None or self.system_df is None:
            self.result_preview.clear()
            self.config_panel.update_column_letters({})  # 清空列字母映射
            return
        
        config = self.config_panel.get_config()
        key_columns = config.get("key_columns", [])
        
        if not key_columns:
            self.result_preview.clear()
            self.config_panel.update_column_letters({})  # 清空列字母映射
            return
        
        try:
            # 快速计算预览数据
            preview_df = self._compute_preview_result(config)
            if preview_df is not None:
                self.result_preview.update_preview(preview_df, self.pivot_values, config, self.manual_df, self.system_df)
                # 同步列字母映射到配置面板
                column_letters = self.result_preview.get_column_letters()
                self.config_panel.update_column_letters(column_letters)
        except Exception as e:
            import traceback
            print(f"预览更新失败: {e}")
            print(traceback.format_exc())
            self.result_preview.clear()
    
    def _compute_preview_result(self, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """计算预览结果（简化版，只取前几行）"""
        manual_key_cols = [k["manual"] for k in config["key_columns"]]
        system_key_cols = [k["system"] for k in config["key_columns"]]
        
        manual_val_cols = [v["manual"] for v in config.get("value_columns", [])]
        system_val_cols = [v["system"] for v in config.get("value_columns", [])]
        
        # 生成主键
        manual_with_key = CompareEngine.make_key(self.manual_df, manual_key_cols)
        system_with_key = CompareEngine.make_key(self.system_df, system_key_cols)
        
        # 准备筛选条件
        filters = []
        for f in config.get("system_filters", []):
            filters.append((f["column"], f["operator"], f["value"]))
        
        # 手工表筛选
        manual_filters = []
        for f in config.get("manual_filters", []):
            filters.append((f["column"], f["operator"], f["value"]))
        
        # 聚合数据
        manual_agg, _ = CompareEngine.aggregate_data(
            manual_with_key, "__KEY__", manual_val_cols,
            filters=manual_filters
        )
        
        system_agg, pivot_values = CompareEngine.aggregate_data(
            system_with_key, "__KEY__", system_val_cols,
            pivot_col=config.get("pivot_column"),
            filters=filters
        )
        
        # 更新透视值
        self.pivot_values = pivot_values
        
        # 合并比对
        manual_val = manual_val_cols[0] if manual_val_cols else ""
        system_val = "系统总计" if config.get("pivot_column") else (system_val_cols[0] if system_val_cols else "")
        
        result_df = CompareEngine.merge_and_compare(
            manual_agg, system_agg, "__KEY__",
            manual_val, system_val,
            diff_formula=config.get("diff_formula"),
            pivot_values=pivot_values
        )
        
        return result_df

    def _run_comparison(self):
        """执行对账"""
        if self.manual_df is None or self.system_df is None:
            Messagebox.show_warning("请先选择文件", "提示")
            return
        
        config = self.config_panel.get_config()
        
        if not config.get("key_columns"):
            Messagebox.show_warning("请配置主键字段", "提示")
            return
        
        # 定义操作函数
        def do_comparison():
            # 准备数据
            manual_key_cols = [k["manual"] for k in config["key_columns"]]
            system_key_cols = [k["system"] for k in config["key_columns"]]
            
            manual_val_cols = [v["manual"] for v in config.get("value_columns", [])]
            system_val_cols = [v["system"] for v in config.get("value_columns", [])]
            
            # 生成主键
            manual_with_key = CompareEngine.make_key(self.manual_df, manual_key_cols)
            system_with_key = CompareEngine.make_key(self.system_df, system_key_cols)
            
            # 准备筛选条件
            filters = []
            for f in config.get("system_filters", []):
                filters.append((f["column"], f["operator"], f["value"]))
            
            # 聚合数据
            manual_agg, _ = CompareEngine.aggregate_data(
                manual_with_key, "__KEY__", manual_val_cols
            )
            
            system_agg, pivot_values = CompareEngine.aggregate_data(
                system_with_key, "__KEY__", system_val_cols,
                pivot_col=config.get("pivot_column"),
                filters=filters
            )
            
            # 合并比对
            manual_val = manual_val_cols[0] if manual_val_cols else ""
            system_val = "系统总计" if config.get("pivot_column") else (system_val_cols[0] if system_val_cols else "")
            
            result_df = CompareEngine.merge_and_compare(
                manual_agg, system_agg, "__KEY__",
                manual_val, system_val,
                diff_formula=config.get("diff_formula"),
                pivot_values=pivot_values
            )
            
            return result_df, pivot_values
        
        try:
            # 使用加载动画运行对比
            dialog = LoadingDialog(self.root, "智能对账中...", "正在处理数据，请稍候...")
            self.root.update()
            
            self.result_df, self.pivot_values = do_comparison()
            
            dialog.close()
            
            # 显示结果
            self._display_results()
            self._show_step(3)
            
        except Exception as e:
            Messagebox.show_error(f"对账失败: {e}", "错误")
            import traceback
            traceback.print_exc()

    def _display_results(self):
        """显示结果"""
        if self.result_df is None:
            return
        
        from config import COMPARE_STATUS
        
        # 更新统计
        status_counts = self.result_df["比对状态"].value_counts()
        
        self.stat_cards["match"].config(text=str(status_counts.get(COMPARE_STATUS["match"], 0)))
        self.stat_cards["diff"].config(text=str(status_counts.get(COMPARE_STATUS["diff"], 0)))
        self.stat_cards["manual_only"].config(text=str(status_counts.get(COMPARE_STATUS["manual_only"], 0)))
        self.stat_cards["system_only"].config(text=str(status_counts.get(COMPARE_STATUS["system_only"], 0)))
        
        # 更新表格
        self.result_tree.delete(*self.result_tree.get_children())
        
        for _, row in self.result_df.head(500).iterrows():
            key = row.get("__KEY__", "")
            manual = row.get("手工数量", 0)
            system = row.get("系统总计", 0)
            diff = row.get("差值", 0)
            status = row.get("比对状态", "")
            
            # 格式化数值
            try:
                manual = f"{float(manual):.0f}"
            except:
                pass
            try:
                system = f"{float(system):.0f}"
            except:
                pass
            try:
                diff = f"{float(diff):.0f}"
            except:
                pass
            
            self.result_tree.insert("", "end", values=(key, manual, system, diff, status))

    def _export_results(self):
        """导出结果"""
        if self.result_df is None:
            Messagebox.show_warning("没有可导出的结果", "提示")
            return
        
        # 选择保存路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"对账结果_{timestamp}.xlsx"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not filepath:
            return
        
        try:
            config = self.config_panel.get_config()
            config_info = {
                "key_columns": ", ".join([f"{k['manual']}={k['system']}" for k in config.get("key_columns", [])]),
                "value_columns": ", ".join([f"{v['manual']} vs {v['system']}" for v in config.get("value_columns", [])]),
                "pivot_column": config.get("pivot_column") or "未使用",
                "diff_formula": config.get("diff_formula") or "手工数量 - 系统总计",
            }
            
            ExportEngine.export_results(
                filepath,
                self.result_df,
                self.pivot_values,
                config_info
            )
            
            Messagebox.show_info(f"导出成功!\n{filepath}", "完成")
            
        except Exception as e:
            Messagebox.show_error(f"导出失败: {e}", "错误")

    def _new_task(self):
        """新任务"""
        self.manual_df = None
        self.system_df = None
        self.result_df = None
        self.pivot_values = []
        
        self.manual_label.config(text="点击选择文件...")
        self.system_label.config(text="点击选择文件...")
        self.manual_sheet_cb.set("")
        self.system_sheet_cb.set("")
        self.manual_sheet_cb.config(state="disabled")
        self.system_sheet_cb.config(state="disabled")
        
        self._show_step(1)

    def _save_template(self):
        """保存模板"""
        from ttkbootstrap.dialogs import Querybox
        
        name = Querybox.get_string(prompt="请输入模板名称:", title="保存模板")
        if not name:
            return
        
        config = self.config_panel.get_config()
        save_template(name, config)
        
        # 刷新模板下拉框并选中新保存的模板
        self._refresh_template_list()
        self.template_cb.set(name)

    def _show_template_manager(self):
        """显示模板管理弹窗"""
        dialog = TemplateManagerDialog(self.root, on_refresh=self._refresh_template_list)
        dialog.show()
    
    def _load_template_from_dialog(self, template: dict):
        """从模板管理弹窗加载模板"""
        config = template.get("config", {})
        if config:
            self.config_panel.set_config(config)
            # 同步更新下拉框显示
            template_name = template.get("name", "")
            if template_name:
                self.template_cb.set(template_name)

    def _refresh_template_list(self):
        """刷新模板下拉框列表"""
        templates = load_templates()
        names = ["(选择模板)"] + [t["name"] for t in templates]
        self.template_cb['values'] = names
        self.template_cb.set("(选择模板)")
    
    def _on_template_selected(self, event):
        """模板选择事件"""
        selected = self.template_cb.get()
        if selected == "(选择模板)":
            return
        
        templates = load_templates()
        for t in templates:
            if t["name"] == selected:
                self.config_panel.set_config(t["config"])
                # 触发配置变更以刷新预览
                self._on_config_change(t["config"])
                # 保持显示模板名（不重置）
                # self.template_cb.set("(选择模板)")
                return

    def _load_saved_config(self):
        """加载保存的配置"""
        config = load_config()
        if config:
            self.config_panel.set_config(config)

    def run(self):
        """运行应用"""
        self.root.mainloop()
