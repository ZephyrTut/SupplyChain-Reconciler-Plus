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
        self.dialog.geometry("450x400")
        self.dialog.resizable(True, True)
        
        # 设置为模态窗口
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 450) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._load_templates()
        
    def _create_widgets(self):
        """创建控件"""
        # 标题栏
        header = ttk.Frame(self.dialog, padding=15, bootstyle="light")
        header.pack(fill="x")
        
        title_frame = ttk.Frame(header)
        title_frame.pack(fill="x")
        
        ttk.Label(title_frame, text="📋 已保存的模板", 
                 font=("", 13, "bold")).pack(side="left")
        
        self.count_label = ttk.Label(title_frame, text="", 
                                     bootstyle="secondary", font=("", 9))
        self.count_label.pack(side="right")
        
        # 说明文字
        ttk.Label(header, text="点击模板名称加载配置，点击 🗑️ 删除模板", 
                 bootstyle="secondary", font=("", 9)).pack(anchor="w", pady=(5, 0))
        
        # 分隔线
        ttk.Separator(self.dialog, orient="horizontal").pack(fill="x", pady=5)
        
        # 模板列表区域（可滚动）
        list_container = ttk.Frame(self.dialog, padding=(15, 5))
        list_container.pack(fill="both", expand=True)
        
        # Canvas + Scrollbar
        canvas = ttk.Canvas(list_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.template_frame = ttk.Frame(canvas)
        
        self.template_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.template_frame, anchor="nw", width=400)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 鼠标滚轮支持
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        self.template_frame.bind("<MouseWheel>", on_mousewheel)
        
        self.canvas = canvas
        
        # 底部按钮栏
        btn_frame = ttk.Frame(self.dialog, padding=15)
        btn_frame.pack(fill="x", side="bottom")
        
        ttk.Button(btn_frame, text="关闭", bootstyle="secondary",
                  command=self._close, width=12).pack(side="right")
        
    def _load_templates(self):
        """加载并显示模板列表"""
        # 清空现有内容
        for widget in self.template_frame.winfo_children():
            widget.destroy()
        
        templates = load_templates()
        
        # 更新计数
        self.count_label.config(text=f"共 {len(templates)} 个模板")
        
        if not templates:
            # 空状态提示
            empty_frame = ttk.Frame(self.template_frame)
            empty_frame.pack(expand=True, fill="both", pady=50)
            
            ttk.Label(empty_frame, text="📭", font=("", 36)).pack()
            ttk.Label(empty_frame, text="暂无保存的模板", 
                     bootstyle="secondary", font=("", 11)).pack(pady=5)
            ttk.Label(empty_frame, text="在配置页面点击 💾 保存模板 来创建模板", 
                     bootstyle="secondary", font=("", 9)).pack()
            return
        
        # 按时间倒序排列（最新的在前）
        templates.sort(key=lambda t: t.get('timestamp', ''), reverse=True)
        
        for i, template in enumerate(templates):
            self._create_template_row(template, i)
    
    def _create_template_row(self, template: Dict, index: int):
        """创建单个模板行（参考React版本设计）"""
        # 外层容器
        row_container = ttk.Frame(self.template_frame)
        row_container.pack(fill="x", pady=3, padx=5)
        
        # 模板卡片
        row_frame = ttk.Frame(row_container, bootstyle="light", padding=10)
        row_frame.pack(fill="x")
        
        # 左侧内容区
        content_frame = ttk.Frame(row_frame)
        content_frame.pack(side="left", fill="both", expand=True)
        
        # 模板名称（可点击加载）
        name = template.get("name", "未命名")
        name_label = ttk.Label(
            content_frame, 
            text=f"📄 {name}", 
            font=("", 10, "bold"),
            cursor="hand2",
            foreground="#1e40af"  # 蓝色
        )
        name_label.pack(anchor="w")
        
        # 鼠标悬停效果
        def on_enter(e):
            name_label.configure(foreground="#1d4ed8")
        def on_leave(e):
            name_label.configure(foreground="#1e40af")
        
        name_label.bind("<Enter>", on_enter)
        name_label.bind("<Leave>", on_leave)
        name_label.bind("<Button-1>", lambda e, t=template: self._load_template(t))
        
        # 配置信息预览
        config = template.get("config", {})
        info_parts = []
        
        key_count = len(config.get("key_columns", []))
        if key_count > 0:
            info_parts.append(f"{key_count}个主键")
        
        val_count = len(config.get("value_columns", []))
        if val_count > 0:
            info_parts.append(f"{val_count}个数值")
        
        pivot = config.get("pivot_column")
        if pivot:
            info_parts.append(f"透视: {pivot}")
        
        if info_parts:
            info_text = " · ".join(info_parts)
            ttk.Label(
                content_frame, 
                text=info_text, 
                bootstyle="secondary",
                font=("", 8)
            ).pack(anchor="w", pady=(2, 0))
        
        # 时间戳
        timestamp = template.get("timestamp", "")
        if timestamp:
            ttk.Label(
                content_frame,
                text=f"保存于: {timestamp}",
                bootstyle="secondary",
                font=("", 7)
            ).pack(anchor="w", pady=(2, 0))
        
        # 右侧删除按钮
        delete_btn = ttk.Button(
            row_frame,
            text="🗑️",
            width=4,
            bootstyle="danger-outline",
            command=lambda: self._delete_template(template)
        )
        delete_btn.pack(side="right")
        
        # 删除按钮悬停效果
        def on_btn_enter(e):
            delete_btn.configure(bootstyle="danger")
        def on_btn_leave(e):
            delete_btn.configure(bootstyle="danger-outline")
        
        delete_btn.bind("<Enter>", on_btn_enter)
        delete_btn.bind("<Leave>", on_btn_leave)
        
        # 分隔线
        if index < len(load_templates()) - 1:
            ttk.Separator(self.template_frame, orient="horizontal").pack(
                fill="x", pady=2, padx=20)
    
    def _load_template(self, template: Dict):
        """加载模板配置"""
        # 关闭弹窗
        self._close()
        
        # 触发加载回调（在main_window中实现）
        if hasattr(self.parent, '_load_template_from_dialog'):
            self.parent._load_template_from_dialog(template)
    
    def _delete_template(self, template: Dict):
        """删除指定模板"""
        name = template.get("name", "未命名")
        
        print(f"\n[UI] 用户点击删除按钮")
        print(f"[UI] 模板数据: {template}")
        
        result = Messagebox.yesno(
            f"确定要删除模板 '{name}' 吗？\n此操作不可恢复！",
            "确认删除",
            parent=self.dialog
        )
        
        print(f"[UI] 用户确认结果: {result}")
        
        if result == "Yes":
            # 优先使用ID，如果没有ID则使用name（兼容旧数据）
            template_id = template.get("id") or template.get("name")
            print(f"[UI] 提取的template_id: {repr(template_id)}")
            print(f"[UI] 来源: {'id字段' if template.get('id') else 'name字段(降级)'}")
            
            if not template_id:
                print(f"[UI] ❌ 模板数据异常：template没有id也没有name")
                Messagebox.show_error(
                    "模板数据异常：缺少ID和名称",
                    "删除失败",
                    parent=self.dialog
                )
                return
            
            print(f"[UI] 调用delete_template函数...")
            success, message = delete_template(template_id)
            print(f"[UI] delete_template返回: success={success}, message={message}")
            
            if success:
                print(f"[UI] ✅ 删除成功，开始后续处理")
                # 刷新列表
                print(f"[UI] 刷新模板列表...")
                self._load_templates()
                # 通知主窗口刷新下拉框
                if self.on_refresh:
                    print(f"[UI] 通知主窗口刷新下拉框...")
                    self.on_refresh()
                
                # 显示成功提示
                print(f"[UI] 显示成功对话框")
                Messagebox.show_info(
                    message,
                    "删除成功",
                    parent=self.dialog
                )
            else:
                print(f"[UI] ❌ 删除失败")
                # 显示失败提示
                Messagebox.show_error(
                    message,
                    "删除失败",
                    parent=self.dialog
                )
    
    def _close(self):
        """关闭弹窗"""
        self.dialog.destroy()
