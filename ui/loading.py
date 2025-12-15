"""
加载动画和进度显示组件
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time


class LoadingDialog(ttk.Toplevel):
    """加载中对话框"""
    
    def __init__(self, parent, title="处理中", message="请稍候..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        
        # 置顶
        self.attributes('-topmost', True)
        
        # 居中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.geometry(f"+{x}+{y}")
        
        # 内容
        content = ttk.Frame(self, padding=20)
        content.pack(fill="both", expand=True)
        
        # 消息
        ttk.Label(content, text=message, font=("", 10)).pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(
            content, mode='indeterminate', bootstyle="info"
        )
        self.progress.pack(fill="x", pady=10)
        self.progress.start()
        
        # 禁止关闭
        self.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def close(self):
        """关闭对话框"""
        try:
            self.progress.stop()
            self.destroy()
        except:
            pass


class ProgressWindow(ttk.Toplevel):
    """进度窗口"""
    
    def __init__(self, parent, title="进度", max_steps=100):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        
        # 置顶
        self.attributes('-topmost', True)
        
        # 居中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")
        
        self.max_steps = max_steps
        self.current_step = 0
        
        # 内容
        content = ttk.Frame(self, padding=20)
        content.pack(fill="both", expand=True)
        
        # 标题标签
        self.title_label = ttk.Label(content, text="开始处理...", font=("", 10, "bold"))
        self.title_label.pack(anchor="w", pady=5)
        
        # 详情标签
        self.detail_label = ttk.Label(
            content, text="", font=("", 9), bootstyle="secondary"
        )
        self.detail_label.pack(anchor="w", pady=2)
        
        # 进度条
        self.progress = ttk.Progressbar(
            content, mode='determinate', bootstyle="info", maximum=max_steps
        )
        self.progress.pack(fill="x", pady=15)
        
        # 百分比标签
        self.percent_label = ttk.Label(content, text="0%", font=("Consolas", 9))
        self.percent_label.pack(anchor="e")
        
        # 禁止关闭
        self.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def update_step(self, step: int, title: str = "", detail: str = ""):
        """更新进度"""
        self.current_step = min(step, self.max_steps)
        self.progress['value'] = self.current_step
        
        percent = int((self.current_step / self.max_steps) * 100)
        self.percent_label.config(text=f"{percent}%")
        
        if title:
            self.title_label.config(text=title)
        
        if detail:
            self.detail_label.config(text=detail)
        
        self.update_idletasks()
    
    def close(self):
        """关闭对话框"""
        try:
            self.destroy()
        except:
            pass


class OperationThread(threading.Thread):
    """后台操作线程"""
    
    def __init__(self, operation_func, on_complete=None, on_error=None):
        super().__init__(daemon=True)
        self.operation_func = operation_func
        self.on_complete = on_complete
        self.on_error = on_error
        self.result = None
        self.error = None
    
    def run(self):
        """运行操作"""
        try:
            self.result = self.operation_func()
            if self.on_complete:
                self.on_complete(self.result)
        except Exception as e:
            self.error = e
            if self.on_error:
                self.on_error(e)


def run_with_loading(parent, operation_func, title="处理中", message="请稍候..."):
    """
    在加载对话框中运行操作
    
    Args:
        parent: 父窗口
        operation_func: 要运行的函数
        title: 对话框标题
        message: 加载消息
    
    Returns:
        操作结果
    """
    result = [None]
    error = [None]
    
    def on_complete(res):
        result[0] = res
        dialog.close()
    
    def on_error(err):
        error[0] = err
        dialog.close()
    
    dialog = LoadingDialog(parent, title, message)
    
    thread = OperationThread(operation_func, on_complete, on_error)
    thread.start()
    
    # 等待完成
    parent.wait_window(dialog)
    
    if error[0]:
        raise error[0]
    
    return result[0]
