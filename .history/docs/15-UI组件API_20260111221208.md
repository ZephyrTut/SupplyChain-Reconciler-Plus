# 🎨 UI组件API

**PyQt6 UI组件详细参考**

---

## 📋 模块概述

UI模块基于PyQt6构建，使用qt-material主题。

| 文件 | 类 | 用途 |
|------|---|------|
| qt_main_window.py | QtMainWindow | 主窗口 |
| qt_config_panel.py | QtConfigPanel | 配置面板 |
| qt_result_preview.py | QtResultPreview | 结果预览 |
| qt_dialogs.py | 各种Dialog | 对话框 |

---

## 🖥️ QtMainWindow

### 类定义

```python
class QtMainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号
    file_loaded = pyqtSignal(str, str)  # (table_type, file_path)
    compare_completed = pyqtSignal(object)  # DataFrame
```

### 核心方法

#### __init__()

```python
def __init__(self):
    """初始化主窗口"""
    super().__init__()
    self.setWindowTitle(f"SupplyChain-Reconciler-Plus v{APP_VERSION}")
    self.setMinimumSize(1200, 800)
    self._init_ui()
    self._connect_signals()
    self._load_templates()
```

#### _init_ui()

```python
def _init_ui(self):
    """初始化UI布局"""
    # 创建中心部件
    central = QWidget()
    self.setCentralWidget(central)
    
    # 主布局
    layout = QVBoxLayout(central)
    
    # 步骤区域
    self._create_step1_area(layout)  # 文件导入
    self._create_step2_area(layout)  # 配置面板
    self._create_step3_area(layout)  # 结果预览
    
    # 状态栏
    self.statusBar().showMessage("✅ 就绪")
```

#### load_file()

```python
def load_file(self, table_type: str, file_path: str):
    """
    加载Excel文件
    
    Args:
        table_type: "manual" 或 "system"
        file_path: Excel文件路径
    """
    try:
        sheets = excel_utils.get_sheet_names(file_path)
        if table_type == "manual":
            self.combo_manual_sheet.clear()
            self.combo_manual_sheet.addItems(sheets)
            self._manual_file = file_path
        else:
            self.combo_system_sheet.clear()
            self.combo_system_sheet.addItems(sheets)
            self._system_file = file_path
        
        self.file_loaded.emit(table_type, file_path)
    except Exception as e:
        show_error(self, "加载失败", str(e))
```

#### run_compare()

```python
def run_compare(self):
    """执行对账"""
    config = self.config_panel.get_config()
    
    # 验证配置
    if not self._validate_config(config):
        return
    
    loading = LoadingDialog(self, "正在对账...")
    loading.show()
    
    try:
        # 读取数据
        manual_df = self._read_manual_data()
        system_df = self._read_system_data()
        
        # 执行比对
        result = self._execute_compare(manual_df, system_df, config)
        
        # 显示结果
        self.result_preview.set_data(result, self._pivot_values)
        
        self.compare_completed.emit(result)
    except Exception as e:
        show_error(self, "对账失败", str(e))
    finally:
        loading.close()
```

#### export_result()

```python
def export_result(self):
    """导出结果"""
    result = self.result_preview.get_result()
    if result is None:
        show_error(self, "无数据", "请先执行对账")
        return
    
    file_path = save_file(
        self,
        title="保存结果",
        filter="Excel文件 (*.xlsx)",
        default_name=f"对账结果_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    )
    
    if file_path:
        ExportEngine.export_results(
            file_path, result, 
            self._pivot_values,
            self._get_config_info()
        )
        show_info(self, "导出成功", f"已保存至:\n{file_path}")
```

---

## ⚙️ QtConfigPanel

### 类定义

```python
class QtConfigPanel(QWidget):
    """配置面板类"""
    
    # 信号
    config_changed = pyqtSignal()  # 配置变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
```

### 核心方法

#### get_config()

```python
def get_config(self) -> dict:
    """
    获取当前配置
    
    Returns:
        配置字典
    """
    return {
        "key_mappings": self._get_key_mappings(),
        "value_mapping": self._get_value_mapping(),
        "clean_rules": self._get_clean_rules(),
        "manual_filters": self._get_manual_filters(),
        "system_filters": self._get_system_filters(),
        "manual_pivot_config": self._get_manual_pivot_config(),
        "system_pivot_config": self._get_system_pivot_config(),
        "difference_formula": self._get_formula()
    }
```

#### set_config()

```python
def set_config(self, config: dict):
    """
    设置配置
    
    Args:
        config: 配置字典
    """
    self._set_key_mappings(config.get("key_mappings", []))
    self._set_value_mapping(config.get("value_mapping", {}))
    self._set_clean_rules(config.get("clean_rules", []))
    self._set_manual_filters(config.get("manual_filters", []))
    self._set_system_filters(config.get("system_filters", []))
    self._set_manual_pivot_config(config.get("manual_pivot_config", {}))
    self._set_system_pivot_config(config.get("system_pivot_config", {}))
    self._set_formula(config.get("difference_formula", "手工数量 - 系统总计"))
```

#### refresh_columns()

```python
def refresh_columns(
    self, 
    manual_columns: List[str], 
    system_columns: List[str]
):
    """
    刷新列选项
    
    Args:
        manual_columns: 手工表列名列表
        system_columns: 系统表列名列表
    """
    self._manual_columns = manual_columns
    self._system_columns = system_columns
    
    # 更新所有下拉框
    self._refresh_key_combos()
    self._refresh_value_combos()
    self._refresh_filter_combos()
    self._refresh_pivot_combos()
```

#### set_sample_data()

```python
def set_sample_data(
    self, 
    manual_df: pd.DataFrame, 
    system_df: pd.DataFrame
):
    """
    设置样例数据
    
    Args:
        manual_df: 手工表数据(前5行)
        system_df: 系统表数据(前5行)
    """
    self._update_sample_table(self.manual_sample_table, manual_df)
    self._update_sample_table(self.system_sample_table, system_df)
```

### 内部组件

#### NoScrollComboBox

```python
class NoScrollComboBox(QComboBox):
    """禁用滚轮的下拉框"""
    
    def wheelEvent(self, event):
        event.ignore()
```

#### CollapsibleSection

```python
class CollapsibleSection(QWidget):
    """可折叠区域"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._init_ui()
    
    def toggle(self):
        """切换展开/折叠"""
        self.content.setVisible(not self.content.isVisible())
    
    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        self.content.setVisible(expanded)
```

---

## 📊 QtResultPreview

### 类定义

```python
class QtResultPreview(QWidget):
    """结果预览类"""
    
    PREVIEW_LIMIT = 15  # 预览行数限制
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result_df = None
        self._pivot_values = []
        self._init_ui()
```

### 核心方法

#### set_data()

```python
def set_data(
    self, 
    df: pd.DataFrame, 
    pivot_values: List[str] = None
):
    """
    设置预览数据
    
    Args:
        df: 结果数据
        pivot_values: 透视值列表
    """
    self._result_df = df
    self._pivot_values = pivot_values or []
    self._refresh_table()
    self._update_stats()
```

#### get_result()

```python
def get_result(self) -> pd.DataFrame:
    """
    获取完整结果
    
    Returns:
        结果DataFrame，如无数据返回None
    """
    return self._result_df
```

#### get_stats()

```python
def get_stats(self) -> dict:
    """
    获取统计信息
    
    Returns:
        {
            "total": int,
            "match": int,
            "diff": int,
            "missing": int
        }
    """
    if self._result_df is None:
        return {"total": 0, "match": 0, "diff": 0, "missing": 0}
    
    total = len(self._result_df)
    match = len(self._result_df[self._result_df["差值"] == 0])
    missing = len(self._result_df[
        self._result_df["比对状态"].str.contains("✗")
    ])
    
    return {
        "total": total,
        "match": match,
        "diff": total - match - missing,
        "missing": missing
    }
```

#### clear()

```python
def clear(self):
    """清空预览"""
    self._result_df = None
    self._pivot_values = []
    self.table.setRowCount(0)
    self.stats_label.setText("")
```

---

## 🎨 样式常量

### UI颜色配置

```python
# config/settings.py
UI_COLORS = {
    # 背景色
    "bg_main": "#f5f5f5",
    "bg_card": "#ffffff",
    "bg_input": "#ffffff",
    
    # 文字色
    "text_primary": "#333333",
    "text_secondary": "#666666",
    "text_placeholder": "#999999",
    
    # 边框色
    "border_default": "#cccccc",
    "border_hover": "#2196F3",
    
    # 强调色
    "accent": "#1976D2",
    "accent_hover": "#1565C0",
    
    # 状态色
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#f44336",
}

PREVIEW_COLORS = {
    "match": "#D1FAE5",
    "diff_pos": "#D9F99D",
    "diff_neg": "#BFDBFE",
    "missing": "#FECACA",
}
```

### 通用样式模板

```python
BUTTON_STYLE = """
    QPushButton {
        background-color: #f5f5f5;
        color: #333333;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
        border-color: #2196F3;
    }
"""

INPUT_STYLE = """
    QLineEdit, QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 6px 8px;
    }
    QLineEdit:focus, QComboBox:focus {
        border-color: #2196F3;
    }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        gridline-color: #e0e0e0;
    }
    QHeaderView::section {
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        font-weight: bold;
    }
"""
```

---

## 📌 使用示例

### 创建主窗口

```python
import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from ui.qt_main_window import QtMainWindow

app = QApplication(sys.argv)
apply_stylesheet(app, theme='light_blue.xml')

window = QtMainWindow()
window.show()

sys.exit(app.exec())
```

### 自定义配置面板

```python
from ui.qt_config_panel import QtConfigPanel

panel = QtConfigPanel()
panel.refresh_columns(
    manual_columns=["订单编号", "物料编码", "数量"],
    system_columns=["订单号", "零件号", "执行数量"]
)

# 监听配置变化
panel.config_changed.connect(on_config_changed)

# 获取配置
config = panel.get_config()
```

---

## ▶️ 下一步

了解工具函数，查看 [工具函数API](./16-工具函数API.md)。
