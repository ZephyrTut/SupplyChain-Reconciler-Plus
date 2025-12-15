"""
滚动条工具模块 - 统一滚动条配置和鼠标滚轮行为
"""


def disable_combobox_scroll(combobox):
    """
    禁用Combobox的鼠标滚轮事件，防止联动主滚动条
    
    Args:
        combobox: ttk.Combobox实例
    """
    def ignore_scroll(event):
        return "break"
    
    # 绑定鼠标滚轮事件并阻止传播
    combobox.bind("<MouseWheel>", ignore_scroll)
    combobox.bind("<Button-4>", ignore_scroll)  # Linux 向上滚动
    combobox.bind("<Button-5>", ignore_scroll)  # Linux 向下滚动


def setup_mousewheel_scroll(canvas, scroll_frame=None, scroll_speed=1):
    """
    为Canvas设置鼠标滚轮滚动支持（仅在鼠标进入时激活）
    
    Args:
        canvas: ttk.Canvas实例
        scroll_frame: 可选的内部Frame，用于额外绑定
        scroll_speed: 滚动速度倍数（默认1）
    
    Usage:
        canvas = ttk.Canvas(parent)
        scroll_frame = ttk.Frame(canvas)
        setup_mousewheel_scroll(canvas, scroll_frame)
    """
    def on_mousewheel(event):
        # Windows/macOS使用event.delta
        canvas.yview_scroll(int(-1 * scroll_speed * (event.delta / 120)), "units")
    
    def on_mousewheel_linux_up(event):
        # Linux向上滚动
        canvas.yview_scroll(-1 * scroll_speed, "units")
    
    def on_mousewheel_linux_down(event):
        # Linux向下滚动
        canvas.yview_scroll(1 * scroll_speed, "units")
    
    def bind_wheel(event):
        """鼠标进入时绑定滚轮事件"""
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel_linux_up)
        canvas.bind("<Button-5>", on_mousewheel_linux_down)
    
    def unbind_wheel(event):
        """鼠标离开时解绑滚轮事件"""
        canvas.unbind("<MouseWheel>")
        canvas.unbind("<Button-4>")
        canvas.unbind("<Button-5>")
    
    # 绑定进入/离开事件
    canvas.bind("<Enter>", bind_wheel)
    canvas.bind("<Leave>", unbind_wheel)
    
    # 如果提供了scroll_frame，也为其绑定（但不使用Enter/Leave）
    if scroll_frame:
        scroll_frame.bind("<MouseWheel>", on_mousewheel)
        scroll_frame.bind("<Button-4>", on_mousewheel_linux_up)
        scroll_frame.bind("<Button-5>", on_mousewheel_linux_down)


def create_scrollable_frame(parent, orient="vertical", **frame_kwargs):
    """
    创建一个可滚动的Frame容器（Canvas + Scrollbar + Frame）
    
    Args:
        parent: 父容器
        orient: 滚动方向 "vertical", "horizontal", "both"
        **frame_kwargs: 传递给内部Frame的参数
    
    Returns:
        (canvas, scroll_frame, scrollbar_v, scrollbar_h)
        - canvas: Canvas容器
        - scroll_frame: 可放置内容的Frame
        - scrollbar_v: 垂直滚动条（如果orient包含vertical）
        - scrollbar_h: 水平滚动条（如果orient包含horizontal）
    """
    import ttkbootstrap as ttk
    
    canvas = ttk.Canvas(parent, highlightthickness=0)
    scroll_frame = ttk.Frame(canvas, **frame_kwargs)
    
    scrollbar_v = None
    scrollbar_h = None
    
    # 创建滚动条
    if orient in ("vertical", "both"):
        scrollbar_v = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar_v.set)
    
    if orient in ("horizontal", "both"):
        scrollbar_h = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar_h.set)
    
    # 配置Canvas窗口
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    
    # 更新滚动区域
    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    scroll_frame.bind("<Configure>", update_scrollregion)
    
    # 设置鼠标滚轮
    setup_mousewheel_scroll(canvas, scroll_frame)
    
    # 布局
    canvas.pack(side="left", fill="both", expand=True)
    if scrollbar_v:
        scrollbar_v.pack(side="right", fill="y")
    if scrollbar_h:
        scrollbar_h.pack(side="bottom", fill="x")
    
    return canvas, scroll_frame, scrollbar_v, scrollbar_h
