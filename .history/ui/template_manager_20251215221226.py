"""
模板管理弹窗 - 显示所有模板并支持删除
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import Callable, List, Dict
from utils import load_templates, delete_template


class TemplateManagerDialog:
    """模板管理弹窗"""
    
    def __init__(self, parent, on_refresh: Callable = None):
        """
        Args:
            parent: 父窗口
            on_refresh: 模板列表变更后的回调函数
        """
        self.parent = parent
        self.on_refresh = on_refresh
        self.dialog = None
        
    def show(self):
        """显示弹窗"""
        self.dialog = ttk.Toplevel(self.parent)
        self.dialog.title("📋 模板管理")
        self.dialog.geometry("400x350")
        self.dialog.resizable(True, True)
        
        # 设置为模态窗口
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 400) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 350) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._load_templates()
        
    def _create_widgets(self):
        """创建控件"""
        # 标题
        header = ttk.Frame(self.dialog, padding=10)
        header.pack(fill="x")
        
        ttk.Label(header, text="管理已保存的模板", font=("", 11, "bold")).pack(side="left")
        
        # 模板列表区域（可滚动）
        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill="both", expand=True)
        
        # Canvas + Scrollbar 实现滚动
        canvas = ttk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.template_frame = ttk.Frame(canvas)
        
        self.template_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.template_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 鼠标滚轮支持
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        self.template_frame.bind("<MouseWheel>", on_mousewheel)
        
        self.canvas = canvas
        
        # 底部按钮
        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="关闭", bootstyle="secondary",
                  command=self._close).pack(side="right")
        
        # 提示
        self.hint_label = ttk.Label(btn_frame, text="", bootstyle="secondary", font=("", 9))
        self.hint_label.pack(side="left")
        
    def _load_templates(self):
        """加载并显示模板列表"""
        # 清空现有内容
        for widget in self.template_frame.winfo_children():
            widget.destroy()
        
        templates = load_templates()
        
        if not templates:
            ttk.Label(self.template_frame, text="暂无保存的模板", 
                     bootstyle="secondary", font=("", 10)).pack(pady=30)
            self.hint_label.config(text="保存配置后会显示在这里")
            return
        
        self.hint_label.config(text=f"共 {len(templates)} 个模板")
        
        for i, template in enumerate(templates):
            self._create_template_row(template, i)
    
    def _create_template_row(self, template: Dict, index: int):
        """创建单个模板行"""
        row_frame = ttk.Frame(self.template_frame, padding=(5, 3))
        row_frame.pack(fill="x", pady=2)
        
        # 背景色交替
        if index % 2 == 0:
            row_frame.configure(bootstyle="light")
        
        # 模板名称
        name = template.get("name", "未命名")
        ttk.Label(row_frame, text=f"📄 {name}", font=("", 10), 
                 anchor="w").pack(side="left", fill="x", expand=True)
        
        # 删除按钮（叉号）
        delete_btn = ttk.Button(
            row_frame, 
            text="✕", 
            width=3,
            bootstyle="danger-outline",
            command=lambda n=name: self._delete_template(n)
        )
        delete_btn.pack(side="right", padx=2)
        
        # 鼠标悬停效果
        def on_enter(e, btn=delete_btn):
            btn.configure(bootstyle="danger")
        def on_leave(e, btn=delete_btn):
            btn.configure(bootstyle="danger-outline")
        
        delete_btn.bind("<Enter>", on_enter)
        delete_btn.bind("<Leave>", on_leave)
    
    def _delete_template(self, name: str):
        """删除指定模板"""
        result = Messagebox.yesno(
            f"确定要删除模板 '{name}' 吗？\n此操作不可恢复！",
            "确认删除",
            parent=self.dialog
        )
        
        if result == "Yes":
            success = delete_template(name)
            if success:
                # 刷新列表
                self._load_templates()
                # 通知主窗口刷新
                if self.on_refresh:
                    self.on_refresh()
            else:
                Messagebox.show_error(f"删除失败", "错误", parent=self.dialog)
    
    def _close(self):
        """关闭弹窗"""
        self.dialog.destroy()
