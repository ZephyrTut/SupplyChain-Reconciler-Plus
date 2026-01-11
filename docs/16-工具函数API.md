# 🛠️ 工具函数API

**utils模块详细参考**

---

## 📋 模块概述

utils模块提供项目中使用的通用工具函数。

| 文件 | 用途 |
|------|------|
| excel_utils.py | Excel读写操作 |
| excel_detection.py | Windows活动Excel检测 |
| storage.py | 配置/模板持久化 |

---

## 📊 excel_utils

### 模块概述

提供Excel文件读写功能，支持多种格式。

---

### get_sheet_names()

**获取Excel工作表名称列表**

```python
def get_sheet_names(file_path: str) -> List[str]:
    """
    获取Excel文件的所有Sheet名称
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        Sheet名称列表
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
```

**示例**:

```python
from utils.excel_utils import get_sheet_names

sheets = get_sheet_names("data.xlsx")
# ["Sheet1", "执行报表", "汇总"]
```

---

### read_excel()

**读取Excel文件**

```python
def read_excel(
    file_path: str,
    sheet_name: str = None,
    header_row: int = 0
) -> pd.DataFrame:
    """
    读取Excel文件为DataFrame
    
    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称，None则读取第一个
        header_row: 表头行号（0开始）
        
    Returns:
        pandas DataFrame
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 文件被占用
        ValueError: Sheet不存在
    """
```

**示例**:

```python
from utils.excel_utils import read_excel

# 读取第一个Sheet
df = read_excel("data.xlsx")

# 读取指定Sheet
df = read_excel("data.xlsx", sheet_name="执行报表")

# 指定表头行
df = read_excel("data.xlsx", header_row=1)
```

---

### read_excel_preview()

**读取Excel预览数据**

```python
def read_excel_preview(
    file_path: str,
    sheet_name: str = None,
    rows: int = 5
) -> pd.DataFrame:
    """
    读取Excel文件的前几行用于预览
    
    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称
        rows: 读取行数
        
    Returns:
        前N行的DataFrame
    """
```

**示例**:

```python
preview = read_excel_preview("data.xlsx", rows=5)
```

---

### get_column_types()

**获取列数据类型**

```python
def get_column_types(
    file_path: str,
    sheet_name: str = None
) -> Dict[str, str]:
    """
    分析Excel列的数据类型
    
    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称
        
    Returns:
        {列名: 类型} 字典
        类型: "numeric", "text", "date", "mixed"
    """
```

**示例**:

```python
types = get_column_types("data.xlsx")
# {"订单编号": "text", "数量": "numeric", "日期": "date"}
```

---

### write_excel()

**写入Excel文件**

```python
def write_excel(
    df: pd.DataFrame,
    file_path: str,
    sheet_name: str = "Sheet1"
) -> None:
    """
    将DataFrame写入Excel文件
    
    Args:
        df: 要写入的数据
        file_path: 输出文件路径
        sheet_name: 工作表名称
    """
```

---

## 🔍 excel_detection

### 模块概述

检测Windows系统中已打开的Excel文件（仅Windows可用）。

---

### get_open_excel_files()

**获取已打开的Excel文件列表**

```python
def get_open_excel_files() -> List[str]:
    """
    获取当前在Excel中打开的文件路径列表
    
    仅Windows可用，其他系统返回空列表
    
    Returns:
        已打开的Excel文件路径列表
    """
```

**示例**:

```python
from utils.excel_detection import get_open_excel_files

open_files = get_open_excel_files()
# ["C:\\Users\\test\\Desktop\\data.xlsx"]
```

---

### is_file_open()

**检查文件是否已打开**

```python
def is_file_open(file_path: str) -> bool:
    """
    检查指定文件是否在Excel中打开
    
    Args:
        file_path: 文件路径
        
    Returns:
        True if open, False otherwise
    """
```

**示例**:

```python
from utils.excel_detection import is_file_open

if is_file_open("data.xlsx"):
    print("文件已打开，请先关闭")
```

---

### get_active_excel_path()

**获取当前活动的Excel文件**

```python
def get_active_excel_path() -> Optional[str]:
    """
    获取当前Excel窗口中活动的文件路径
    
    Returns:
        文件路径，无活动文件返回None
    """
```

---

## 💾 storage

### 模块概述

提供配置和模板的持久化存储功能。

---

### 存储路径

```python
# 配置文件位置
# Windows: %APPDATA%\SupplyChain-Reconciler-Plus\
# macOS: ~/Library/Application Support/SupplyChain-Reconciler-Plus/
# Linux: ~/.config/SupplyChain-Reconciler-Plus/
```

---

### save_template()

**保存配置模板**

```python
def save_template(name: str, config: dict) -> str:
    """
    保存配置模板
    
    Args:
        name: 模板名称
        config: 配置字典
        
    Returns:
        模板ID (UUID)
    """
```

**示例**:

```python
from utils.storage import save_template

template_id = save_template("ASN对账模板", {
    "key_mappings": [...],
    "value_mapping": {...},
    "difference_formula": "手工数量 - 系统总计"
})
```

---

### load_template()

**加载配置模板**

```python
def load_template(template_id: str) -> Optional[dict]:
    """
    加载配置模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        配置字典，不存在返回None
    """
```

**示例**:

```python
from utils.storage import load_template

config = load_template("abc123-def456")
if config:
    panel.set_config(config)
```

---

### get_all_templates()

**获取所有模板**

```python
def get_all_templates() -> List[dict]:
    """
    获取所有保存的模板
    
    Returns:
        模板列表，每个包含 id, name, timestamp
    """
```

**示例**:

```python
from utils.storage import get_all_templates

templates = get_all_templates()
for t in templates:
    print(f"{t['name']} - {t['timestamp']}")
```

---

### delete_template()

**删除模板**

```python
def delete_template(template_id: str) -> bool:
    """
    删除配置模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        True if deleted, False if not found
    """
```

---

### 模板数据格式

```python
# templates.json
{
    "templates": [
        {
            "id": "uuid-string",
            "name": "ASN对账-标准模板",
            "config": {
                "key_mappings": [
                    {"manual_col": "到货单号", "system_col": "ASN编号"}
                ],
                "value_mapping": {
                    "manual_col": "数量",
                    "system_col": "执行数量"
                },
                "clean_rules": [...],
                "manual_filters": [...],
                "system_filters": [...],
                "manual_pivot_config": {...},
                "system_pivot_config": {...},
                "difference_formula": "手工数量 - 系统总计"
            },
            "timestamp": "2026-01-11 12:00:00"
        }
    ]
}
```

---

### save_app_settings()

**保存应用设置**

```python
def save_app_settings(settings: dict) -> None:
    """
    保存应用设置
    
    Args:
        settings: 设置字典
    """
```

**设置项**:

```python
{
    "last_manual_dir": "D:/data",
    "last_system_dir": "D:/data",
    "last_export_dir": "D:/exports",
    "window_size": [1200, 800],
    "window_pos": [100, 100]
}
```

---

### load_app_settings()

**加载应用设置**

```python
def load_app_settings() -> dict:
    """
    加载应用设置
    
    Returns:
        设置字典，不存在则返回默认值
    """
```

---

## 🔧 通用工具

### 路径处理

```python
from utils.storage import get_data_dir, ensure_dir

# 获取数据目录
data_dir = get_data_dir()

# 确保目录存在
ensure_dir(data_dir / "exports")
```

### 时间格式化

```python
from utils.storage import format_timestamp

ts = format_timestamp()  # "2026-01-11 12:00:00"
```

---

## ⚠️ 注意事项

### excel_utils

- 大文件读取可能较慢
- .xls格式需要xlrd库
- 文件被占用时无法读取

### excel_detection

- 仅Windows可用
- 需要pywin32库
- Excel必须通过COM接口启动

### storage

- 首次运行自动创建目录
- 模板文件使用JSON格式
- 同名模板自动覆盖

---

## ▶️ 下一步

了解配置常量，查看 [配置常量](./17-配置常量.md)。
