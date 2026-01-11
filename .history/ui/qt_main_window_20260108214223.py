"""
PyQt6 主窗口 - 供应链对账系统
使用 qt-material 主题
"""
import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QFrame, QFileDialog, QMessageBox,
    QSplitter, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon
import pandas as pd

from config.settings import APP_NAME, APP_VERSION
from utils.excel_utils import get_sheet_names, load_excel
from utils.storage import load_templates, save_template, delete_template
from core.compare_engine import CompareEngine
from core.export_engine import ExportEngine


class FileDropCard(QFrame):
    """文件拖拽卡片组件"""
    
    file_dropped = pyqtSignal(str)  # 文件路径信号
    sheet_changed = pyqtSignal(str)  # Sheet变更信号
    
    def __init__(self, title: str, description: str, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.filepath = ""
        self.setAcceptDrops(True)
        self.setObjectName("fileDropCard")
        self._setup_ui(title, description)
        
    def _setup_ui(self, title: str, description: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6 if self.compact else 10)
        
        # 图标（紧凑模式下缩小）
        icon_size = 24 if self.compact else 32
        icon_label = QLabel("📁")
        icon_label.setFont(QFont("Segoe UI Emoji", icon_size))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 标题
        title_size = 11 if self.compact else 12
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", title_size, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_style = "color: #666; font-size: 11px;" if self.compact else "color: #666;"
        desc_label.setStyleSheet(desc_style)
        layout.addWidget(desc_label)
        
        # 文件名显示
        self.file_label = QLabel("未选择文件")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #999; font-style: italic;")
        layout.addWidget(self.file_label)
        
        # Sheet选择下拉框（初始隐藏）
        self.sheet_combo = QComboBox()
        self.sheet_combo.setVisible(False)
        self.sheet_combo.setMinimumWidth(150)
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        layout.addWidget(self.sheet_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 选择按钮
        self.select_btn = QPushButton("选择文件")
        self.select_btn.setObjectName("selectFileBtn")
        layout.addWidget(self.select_btn)
        
        # 样式（紧凑模式下减小最小高度和内边距）
        min_height = 150 if self.compact else 200
        padding = 12 if self.compact else 20
        self.setStyleSheet(f"""
            #fileDropCard {{
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #fafafa;
                min-height: {min_height}px;
                padding: {padding}px;
            }}
            #fileDropCard:hover {{
                border-color: #2196F3;
                background-color: #f0f7ff;
            }}
        """)
        self._default_style = self.styleSheet()
        
    def _on_sheet_changed(self, sheet_name: str):
        """Sheet选择变更"""
        if sheet_name and self.filepath:
            self.sheet_changed.emit(sheet_name)
        
    def set_file(self, filepath: str, sheets: list = None):
        """设置文件路径和可用Sheet"""
        self.filepath = filepath
        filename = os.path.basename(filepath)
        self.file_label.setText(f"✓ {filename}")
        self.file_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # 更新Sheet下拉框
        if sheets and len(sheets) > 1:
            self.sheet_combo.blockSignals(True)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheets)
            self.sheet_combo.blockSignals(False)
            self.sheet_combo.setVisible(True)
        else:
            self.sheet_combo.setVisible(False)
    
    def get_selected_sheet(self) -> str:
        """获取当前选中的Sheet"""
        if self.sheet_combo.isVisible():
            return self.sheet_combo.currentText()
        return ""
        
    def clear(self):
        """清空文件"""
        self.filepath = ""
        self.file_label.setText("未选择文件")
        self.file_label.setStyleSheet("color: #999; font-style: italic;")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(('.xlsx', '.xls', '.xlsm')):
                event.acceptProposedAction()
                min_height = 150 if self.compact else 200
                padding = 12 if self.compact else 20
                self.setStyleSheet(f"""
                    #fileDropCard {{
                        border: 2px dashed #2196F3;
                        border-radius: 10px;
                        background-color: #e3f2fd;
                        min-height: {min_height}px;
                        padding: {padding}px;
                    }}
                """)
                
    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)
        
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                self.file_dropped.emit(filepath)
        self.dragLeaveEvent(event)


class StepIndicator(QWidget):
    """步骤指示器"""
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.current_step = 0
        self.compact = compact
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        v_margin = 6 if self.compact else 10
        layout.setContentsMargins(20, v_margin, 20, v_margin)
        
        self.steps = []
        step_titles = ["导入文件", "配置规则", "执行对账"]
        
        for i, title in enumerate(step_titles):
            step_widget = self._create_step(i + 1, title)
            self.steps.append(step_widget)
            layout.addWidget(step_widget)
            
            # 添加连接线
            if i < len(step_titles) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(2)
                line.setStyleSheet("background-color: #ddd;")
                layout.addWidget(line, 1)
                
    def _create_step(self, num: int, title: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(3 if self.compact else 5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 步骤圆圈（紧凑模式下缩小）
        size = 28 if self.compact else 36
        font_size = 11 if self.compact else 14
        circle = QLabel(str(num))
        circle.setFixedSize(size, size)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        circle.setObjectName(f"stepCircle_{num}")
        layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 步骤标题
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName(f"stepLabel_{num}")
        if self.compact:
            label.setStyleSheet("font-size: 12px;")
        layout.addWidget(label)
        
        return widget
        
    def set_step(self, step: int):
        """设置当前步骤 (1-3)"""
        self.current_step = step
        radius = 14 if self.compact else 18
        for i in range(3):
            circle = self.findChild(QLabel, f"stepCircle_{i+1}")
            label = self.findChild(QLabel, f"stepLabel_{i+1}")
            
            if i + 1 < step:
                # 已完成
                circle.setStyleSheet(f"""
                    background-color: #4CAF50;
                    color: white;
                    border-radius: {radius}px;
                """)
                label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif i + 1 == step:
                # 当前
                circle.setStyleSheet(f"""
                    background-color: #2196F3;
                    color: white;
                    border-radius: {radius}px;
                """)
                label.setStyleSheet("color: #2196F3; font-weight: bold;")
            else:
                # 未完成
                circle.setStyleSheet(f"""
                    background-color: #e0e0e0;
                    color: #666;
                    border-radius: {radius}px;
                """)
                label.setStyleSheet("color: #999;")


class QtMainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 数据
        self.manual_df: Optional[pd.DataFrame] = None
        self.system_df: Optional[pd.DataFrame] = None
        self.manual_path: str = ""
        self.system_path: str = ""
        self.result_df: Optional[pd.DataFrame] = None
        
        # 响应式尺寸计算
        self._calculate_responsive_sizes()
        
        self._setup_window()
        self._create_ui()
        self._connect_signals()
    
    def _calculate_responsive_sizes(self):
        """根据屏幕尺寸计算响应式参数"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 根据屏幕大小设置窗口尺寸（占屏幕80%，但有上下限）
        self.window_width = max(1000, min(1400, int(screen_width * 0.8)))
        self.window_height = max(650, min(900, int(screen_height * 0.85)))
        
        # 根据屏幕尺寸调整间距
        if screen_height < 800:
            self.spacing_scale = 0.6  # 小屏幕
        elif screen_height < 1000:
            self.spacing_scale = 0.8  # 中等屏幕
        else:
            self.spacing_scale = 1.0  # 大屏幕
            
        # 计算响应式间距
        self.content_margin = int(20 * self.spacing_scale)
        self.section_spacing = int(20 * self.spacing_scale)
        self.card_padding = int(15 * self.spacing_scale)
        
    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(960, 600)
        self.resize(self.window_width, self.window_height)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def _create_ui(self):
        """创建UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部栏
        self._create_header(main_layout)
        
        # 步骤指示器（响应式）
        self.step_indicator = StepIndicator(compact=self.spacing_scale < 1.0)
        main_layout.addWidget(self.step_indicator)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(line)
        
        # 内容区域（堆叠窗口）
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)
        
        # 创建三个步骤页面
        self._create_step1_page()
        self._create_step2_page()
        self._create_step3_page()
        
        # 底部按钮栏
        self._create_footer(main_layout)
        
        # 设置初始步骤
        self._show_step(1)
        
    def _create_header(self, parent_layout: QVBoxLayout):
        """创建顶部栏"""
        header = QFrame()
        header.setStyleSheet("background-color: #fff; border-bottom: 1px solid #e0e0e0;")
        header_layout = QHBoxLayout(header)
        v_margin = 6 if self.spacing_scale < 1.0 else 10
        header_layout.setContentsMargins(15, v_margin, 15, v_margin)
        
        # Logo和标题（紧凑模式缩小字体）
        title_size = 13 if self.spacing_scale < 1.0 else 16
        title = QLabel(f"📊 {APP_NAME}")
        title.setFont(QFont("Microsoft YaHei", title_size, QFont.Weight.Bold))
        title.setStyleSheet("color: #1976D2;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 模板选择
        template_label = QLabel("配置模板:")
        header_layout.addWidget(template_label)
        
        self.template_combo = QComboBox()
        combo_width = 160 if self.spacing_scale < 1.0 else 200
        self.template_combo.setMinimumWidth(combo_width)
        self.template_combo.addItem("(选择模板)")
        self._load_templates()
        header_layout.addWidget(self.template_combo)
        
        # 模板操作按钮
        self.save_template_btn = QPushButton("💾 保存")
        self.save_template_btn.setToolTip("保存当前配置为模板")
        header_layout.addWidget(self.save_template_btn)
        
        self.delete_template_btn = QPushButton("🗑️ 删除")
        self.delete_template_btn.setToolTip("删除选中的模板")
        header_layout.addWidget(self.delete_template_btn)
        
        parent_layout.addWidget(header)
        
    def _create_step1_page(self):
        """创建步骤1：文件导入"""
        page = QWidget()
        layout = QHBoxLayout(page)
        margin = int(30 * self.spacing_scale)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(int(30 * self.spacing_scale))
        
        # 手工表卡片
        self.manual_card = FileDropCard(
            "手工表",
            "拖拽Excel文件到这里，或点击选择\n支持 .xlsx / .xls / .xlsm",
            compact=self.spacing_scale < 1.0
        )
        layout.addWidget(self.manual_card)
        
        # 系统表卡片
        self.system_card = FileDropCard(
            "系统表",
            "拖拽Excel文件到这里，或点击选择\n支持 .xlsx / .xls / .xlsm",
            compact=self.spacing_scale < 1.0
        )
        layout.addWidget(self.system_card)
        
        self.stacked_widget.addWidget(page)
        
    def _create_step2_page(self):
        """创建步骤2：配置规则"""
        page = QWidget()
        layout = QHBoxLayout(page)
        margin = int(15 * self.spacing_scale)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(int(15 * self.spacing_scale))
        
        # 左侧配置面板（紧凑模式）
        from ui.qt_config_panel import QtConfigPanel
        self.config_panel = QtConfigPanel(compact=self.spacing_scale < 1.0)
        
        # 右侧预览面板（紧凑模式）
        from ui.qt_result_preview import QtResultPreview
        self.result_preview = QtResultPreview(compact=self.spacing_scale < 1.0)
        
        # 使用分割器，根据屏幕调整比例
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.config_panel)
        splitter.addWidget(self.result_preview)
        # 较小屏幕给配置面板更多空间
        left_size = 450 if self.spacing_scale < 1.0 else 500
        right_size = 550 if self.spacing_scale < 1.0 else 700
        splitter.setSizes([left_size, right_size])
        
        layout.addWidget(splitter)
        self.stacked_widget.addWidget(page)
        
    def _create_step3_page(self):
        """创建步骤3：结果展示"""
        page = QWidget()
        layout = QVBoxLayout(page)
        margin = int(15 * self.spacing_scale)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(int(10 * self.spacing_scale))
        
        # 结果统计
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 10px;")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(10)
        
        self.stats_total = self._create_stat_card("总计", "0", "#2196F3")
        self.stats_match = self._create_stat_card("一致", "0", "#4CAF50")
        self.stats_diff = self._create_stat_card("差异", "0", "#FF9800")
        self.stats_missing = self._create_stat_card("缺失", "0", "#F44336")
        
        stats_layout.addWidget(self.stats_total)
        stats_layout.addWidget(self.stats_match)
        stats_layout.addWidget(self.stats_diff)
        stats_layout.addWidget(self.stats_missing)
        
        layout.addWidget(stats_frame)
        
        # 结果表格
        from ui.qt_result_preview import QtResultTable
        self.result_table = QtResultTable()
        layout.addWidget(self.result_table, 1)
        
        self.stacked_widget.addWidget(page)
        
    def _create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName(f"stat_{title}")
        layout.addWidget(value_label)
        
        return card
        
    def _create_footer(self, parent_layout: QVBoxLayout):
        """创建底部按钮栏"""
        footer = QFrame()
        footer.setStyleSheet("background-color: #fff; border-top: 1px solid #e0e0e0;")
        footer_layout = QHBoxLayout(footer)
        v_margin = 10 if self.spacing_scale < 1.0 else 15
        footer_layout.setContentsMargins(15, v_margin, 15, v_margin)
        
        # 左侧提示
        self.status_label = QLabel("请导入手工表和系统表")
        self.status_label.setStyleSheet("color: #666;")
        footer_layout.addWidget(self.status_label)
        
        footer_layout.addStretch()
        
        # 按钮尺寸根据屏幕调整
        btn_padding = "8px 20px" if self.spacing_scale < 1.0 else "10px 30px"
        
        # 导航按钮
        self.prev_btn = QPushButton("← 上一步")
        self.prev_btn.setVisible(False)
        footer_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("下一步 →")
        self.next_btn.setObjectName("primaryBtn")
        self.next_btn.setStyleSheet(f"""
            #primaryBtn {{
                background-color: #2196F3;
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: 5px;
                font-weight: bold;
            }}
            #primaryBtn:hover {{
                background-color: #1976D2;
            }}
            #primaryBtn:disabled {{
                background-color: #ccc;
            }}
        """)
        footer_layout.addWidget(self.next_btn)
        
        self.run_btn = QPushButton("🚀 执行对账")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setStyleSheet(f"""
            #runBtn {{
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: 5px;
                font-weight: bold;
            }}
            #runBtn:hover {{
                background-color: #388E3C;
            }}
        """)
        self.run_btn.setVisible(False)
        footer_layout.addWidget(self.run_btn)
        
        self.export_btn = QPushButton("📥 导出Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setStyleSheet(f"""
            #exportBtn {{
                background-color: #FF9800;
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: 5px;
                font-weight: bold;
            }}
            #exportBtn:hover {{
                background-color: #F57C00;
            }}
        """)
        self.export_btn.setVisible(False)
        footer_layout.addWidget(self.export_btn)
        
        parent_layout.addWidget(footer)
        
    def _connect_signals(self):
        """连接信号槽"""
        # 文件选择
        self.manual_card.select_btn.clicked.connect(lambda: self._select_file("manual"))
        self.system_card.select_btn.clicked.connect(lambda: self._select_file("system"))
        self.manual_card.file_dropped.connect(lambda p: self._load_file(p, "manual"))
        self.system_card.file_dropped.connect(lambda p: self._load_file(p, "system"))
        
        # 导航按钮
        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn.clicked.connect(self._go_next)
        self.run_btn.clicked.connect(self._run_comparison)
        self.export_btn.clicked.connect(self._export_results)
        
        # 模板
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        self.save_template_btn.clicked.connect(self._save_template)
        self.delete_template_btn.clicked.connect(self._delete_template)
        
        # 配置变更
        self.config_panel.config_changed.connect(self._on_config_changed)
        
    def _show_step(self, step: int):
        """显示指定步骤"""
        self.current_step = step
        self.step_indicator.set_step(step)
        self.stacked_widget.setCurrentIndex(step - 1)
        
        # 更新按钮状态
        self.prev_btn.setVisible(step > 1)
        self.next_btn.setVisible(step < 3)
        self.run_btn.setVisible(step == 2)
        self.export_btn.setVisible(step == 3)
        
        # 更新状态提示
        if step == 1:
            self._update_step1_status()
        elif step == 2:
            self.status_label.setText("配置主键和数值列后，点击执行对账")
        else:
            self.status_label.setText("对账完成！可导出Excel结果")
            
    def _update_step1_status(self):
        """更新步骤1状态"""
        manual_ok = self.manual_df is not None
        system_ok = self.system_df is not None
        
        if manual_ok and system_ok:
            self.status_label.setText(f"✓ 已导入: 手工表 {len(self.manual_df)}行, 系统表 {len(self.system_df)}行")
            self.next_btn.setEnabled(True)
        elif manual_ok:
            self.status_label.setText("✓ 已导入手工表, 请导入系统表")
            self.next_btn.setEnabled(False)
        elif system_ok:
            self.status_label.setText("请导入手工表, ✓ 已导入系统表")
            self.next_btn.setEnabled(False)
        else:
            self.status_label.setText("请导入手工表和系统表")
            self.next_btn.setEnabled(False)
            
    def _select_file(self, file_type: str):
        """选择文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{'手工表' if file_type == 'manual' else '系统表'}",
            "",
            "Excel文件 (*.xlsx *.xls *.xlsm)"
        )
        if filepath:
            self._load_file(filepath, file_type)
            
    def _load_file(self, filepath: str, file_type: str):
        """加载文件"""
        try:
            sheets = get_sheet_names(filepath)
            
            if len(sheets) > 1:
                # 多Sheet选择
                from ui.qt_dialogs import SheetSelectDialog
                dialog = SheetSelectDialog(sheets, self)
                if dialog.exec():
                    sheet_name = dialog.selected_sheet
                else:
                    return
            else:
                sheet_name = sheets[0]
                
            df = load_excel(filepath, sheet_name)
            
            if file_type == "manual":
                self.manual_df = df
                self.manual_path = filepath
                self.manual_card.set_file(filepath)
            else:
                self.system_df = df
                self.system_path = filepath
                self.system_card.set_file(filepath)
                
            self._update_step1_status()
            
            # 更新配置面板的列选项
            if self.manual_df is not None and self.system_df is not None:
                self.config_panel.set_columns(
                    list(self.manual_df.columns),
                    list(self.system_df.columns)
                )
                
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法读取文件:\n{str(e)}")
            
    def _go_prev(self):
        """上一步"""
        if self.current_step > 1:
            self._show_step(self.current_step - 1)
            
    def _go_next(self):
        """下一步"""
        if self.current_step < 3:
            self._show_step(self.current_step + 1)
            
    def _run_comparison(self):
        """执行对账"""
        try:
            config = self.config_panel.get_config()
            
            # 验证配置
            if not config.get("key_mappings"):
                QMessageBox.warning(self, "配置不完整", "请至少配置一个主键映射")
                return
            if not config.get("value_mapping", {}).get("manual"):
                QMessageBox.warning(self, "配置不完整", "请配置手工表数值列")
                return
                
            # 执行对账
            from ui.qt_dialogs import LoadingDialog
            loading = LoadingDialog("正在执行对账...", self)
            loading.show()
            QApplication.processEvents()
            
            engine = CompareEngine()
            self.result_df = engine.merge_and_compare(
                self.manual_df.copy(),
                self.system_df.copy(),
                config
            )
            
            loading.close()
            
            # 更新统计
            self._update_stats()
            
            # 更新结果表格
            self.result_table.set_data(self.result_df)
            
            # 进入步骤3
            self._show_step(3)
            
        except Exception as e:
            QMessageBox.critical(self, "对账失败", f"执行对账时出错:\n{str(e)}")
            
    def _update_stats(self):
        """更新统计信息"""
        if self.result_df is None:
            return
            
        total = len(self.result_df)
        match = len(self.result_df[self.result_df['比对状态'] == '✓'])
        diff = len(self.result_df[self.result_df['比对状态'] == '↕'])
        missing = len(self.result_df[self.result_df['比对状态'] == '✗'])
        
        self.findChild(QLabel, "stat_总计").setText(str(total))
        self.findChild(QLabel, "stat_一致").setText(str(match))
        self.findChild(QLabel, "stat_差异").setText(str(diff))
        self.findChild(QLabel, "stat_缺失").setText(str(missing))
        
    def _export_results(self):
        """导出结果"""
        if self.result_df is None:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存对账结果",
            f"对账结果_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel文件 (*.xlsx)"
        )
        
        if filepath:
            try:
                config = self.config_panel.get_config()
                engine = ExportEngine()
                engine.export_with_colors(self.result_df, filepath, config)
                
                QMessageBox.information(self, "导出成功", f"结果已保存到:\n{filepath}")
                
                # 打开文件夹
                os.startfile(os.path.dirname(filepath))
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时出错:\n{str(e)}")
                
    def _load_templates(self):
        """加载模板列表"""
        templates = load_templates()
        self.template_combo.clear()
        self.template_combo.addItem("(选择模板)")
        for t in templates:
            self.template_combo.addItem(t.get("name", "未命名"), t)
            
    def _on_template_selected(self, index: int):
        """模板选择事件"""
        if index <= 0:
            return
        template = self.template_combo.itemData(index)
        if template:
            config = template.get("config", {})
            self.config_panel.set_config(config)
            
    def _save_template(self):
        """保存模板"""
        from ui.qt_dialogs import InputDialog
        dialog = InputDialog("保存模板", "请输入模板名称:", self)
        if dialog.exec():
            name = dialog.get_text()
            if name:
                config = self.config_panel.get_config()
                save_template(name, config)
                self._load_templates()
                # 选中新模板
                index = self.template_combo.findText(name)
                if index >= 0:
                    self.template_combo.setCurrentIndex(index)
                QMessageBox.information(self, "保存成功", f"模板 '{name}' 已保存")
                
    def _delete_template(self):
        """删除模板"""
        index = self.template_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的模板")
            return
            
        template = self.template_combo.itemData(index)
        name = template.get("name", "")
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模板 '{name}' 吗？\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template_id = template.get("id") or template.get("name")
            success, msg = delete_template(template_id)
            if success:
                self._load_templates()
                QMessageBox.information(self, "删除成功", f"模板 '{name}' 已删除")
            else:
                QMessageBox.warning(self, "删除失败", msg)
                
    def _on_config_changed(self):
        """配置变更事件"""
        # 更新预览
        if self.manual_df is not None and self.system_df is not None:
            config = self.config_panel.get_config()
            self.result_preview.update_preview(
                self.manual_df,
                self.system_df,
                config
            )
