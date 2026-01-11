# 🔧 核心引擎API

**CompareEngine & ExportEngine 详细参考**

---

## 📋 模块概述

核心引擎包含两个主要类：

| 类 | 文件 | 用途 |
|---|------|------|
| CompareEngine | core/compare_engine.py | 数据比对处理 |
| ExportEngine | core/export_engine.py | Excel导出 |

---

## 🔍 CompareEngine

### 类概述

CompareEngine 是数据比对的核心引擎，提供数据清洗、聚合、透视、比对等功能。

所有方法都是静态方法，无需实例化。

---

### clean_column()

**数据清洗**

```python
@staticmethod
def clean_column(
    df: pd.DataFrame,
    clean_rules: List[dict]
) -> pd.DataFrame:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| df | DataFrame | 要清洗的数据 |
| clean_rules | List[dict] | 清洗规则列表 |

**清洗规则格式**:

```python
{
    "column": str,      # 目标列名
    "mode": str,        # "删除匹配" | "保留匹配" | "替换为"
    "regexes": List[str], # 正则表达式列表
    "replace": str      # 替换值（仅替换模式使用）
}
```

**返回**: 清洗后的 DataFrame

**示例**:

```python
rules = [
    {
        "column": "到货单号",
        "mode": "删除匹配",
        "regexes": [r"-\d+$"]
    }
]

df = CompareEngine.clean_column(df, rules)
```

---

### apply_filters()

**应用筛选条件**

```python
@staticmethod
def apply_filters(
    df: pd.DataFrame,
    filters: List[dict]
) -> pd.DataFrame:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| df | DataFrame | 要筛选的数据 |
| filters | List[dict] | 筛选条件列表 |

**筛选条件格式**:

```python
{
    "column": str,      # 目标列名
    "operator": str,    # 操作符
    "value": str        # 筛选值
}
```

**操作符映射**:

| 中文操作符 | 内部值 | 说明 |
|-----------|--------|------|
| 等于 | EQUALS | 精确匹配 |
| 不等于 | NOT_EQUALS | 排除值 |
| 包含 | CONTAINS | 部分匹配 |
| 不包含 | NOT_CONTAINS | 排除部分匹配 |
| 包含于 | IN_LIST | 值在列表中 |
| 大于 | GREATER | 数值比较 |
| 小于 | LESS | 数值比较 |

**示例**:

```python
filters = [
    {"column": "状态", "operator": "等于", "value": "已审核"},
    {"column": "类型", "operator": "包含于", "value": "正常,补货"}
]

df = CompareEngine.apply_filters(df, filters)
```

---

### make_key()

**生成复合主键**

```python
@staticmethod
def make_key(
    df: pd.DataFrame,
    key_cols: List[str],
    keyname: str = "__KEY__"
) -> pd.DataFrame:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| df | DataFrame | 数据 |
| key_cols | List[str] | 主键列列表 |
| keyname | str | 生成的主键列名 |

**返回**: 添加了主键列的 DataFrame

**示例**:

```python
df = CompareEngine.make_key(df, ["订单编号", "物料编码"])
# 结果: 新增 __KEY__ 列，值为 "订单编号_物料编码"
```

---

### aggregate_manual_with_pivot()

**手工表透视聚合（出入库区分）**

```python
@staticmethod
def aggregate_manual_with_pivot(
    df: pd.DataFrame,
    key_col: str,
    value_col: str,
    pivot_config: dict,
    filters: List[dict] = None
) -> Tuple[pd.DataFrame, List[str], List[str]]:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| df | DataFrame | 手工表数据 |
| key_col | str | 主键列名 |
| value_col | str | 数值列名 |
| pivot_config | dict | 透视配置 |
| filters | List[dict] | 筛选条件 |

**透视配置格式**:

```python
{
    "enabled": True,
    "pivot_column": "业务类型",
    "out_values": ["发货", "退货"],
    "in_values": ["退仓"]
}
```

**返回**: (结果DataFrame, 出库列列表, 入库列列表)

**计算逻辑**:
```
手工数量 = Σout_values - Σin_values
```

**示例**:

```python
config = {
    "enabled": True,
    "pivot_column": "业务类型",
    "out_values": ["发货"],
    "in_values": ["退仓"]
}

result_df, out_cols, in_cols = CompareEngine.aggregate_manual_with_pivot(
    df=manual_df,
    key_col="__KEY__",
    value_col="数量",
    pivot_config=config
)
```

---

### aggregate_system()

**系统表聚合/透视**

```python
@staticmethod
def aggregate_system(
    df: pd.DataFrame,
    key_col: str,
    value_cols: List[str],
    pivot_column: str = None,
    filters: List[dict] = None
) -> Tuple[pd.DataFrame, List[str]]:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| df | DataFrame | 系统表数据 |
| key_col | str | 主键列名 |
| value_cols | List[str] | 数值列列表 |
| pivot_column | str | 透视列名（可选） |
| filters | List[dict] | 筛选条件 |

**返回**: (结果DataFrame, 透视值列表)

**示例**:

```python
result_df, pivot_values = CompareEngine.aggregate_system(
    df=system_df,
    key_col="__KEY__",
    value_cols=["数量"],
    pivot_column="订单状态"
)
# pivot_values: ["已完成", "处理中", "待审核"]
```

---

### merge_and_compare()

**合并比对（核心方法）**

```python
@staticmethod
def merge_and_compare(
    manual_df: pd.DataFrame,
    system_df: pd.DataFrame,
    key_col: str = "__KEY__",
    formula: str = "手工数量 - 系统总计",
    pivot_values: List[str] = None
) -> pd.DataFrame:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| manual_df | DataFrame | 处理后的手工表 |
| system_df | DataFrame | 处理后的系统表 |
| key_col | str | 主键列名 |
| formula | str | 差值计算公式 |
| pivot_values | List[str] | 透视值列表 |

**返回**: 比对结果 DataFrame

**结果列**:
- __KEY__
- 透视列（如有）
- 系统总计
- 手工数量
- 差值
- 比对状态

**比对状态**:
- ✓ 一致 (差值=0)
- ↕ 差异(+) (差值>0)
- ↕ 差异(-) (差值<0)
- ✗ 仅手工存在
- ✗ 仅系统存在

**示例**:

```python
result = CompareEngine.merge_and_compare(
    manual_df=processed_manual,
    system_df=processed_system,
    formula="手工数量 - (系统总计 - 已关闭)",
    pivot_values=["已完成", "已关闭"]
)
```

---

## 📤 ExportEngine

### 类概述

ExportEngine 负责将比对结果导出为带颜色标记的Excel文件。

---

### export_results()

**导出比对结果**

```python
@staticmethod
def export_results(
    out_path: str,
    result_df: pd.DataFrame,
    pivot_values: List[str] = None,
    config_info: dict = None
) -> None:
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| out_path | str | 输出文件路径 |
| result_df | DataFrame | 比对结果数据 |
| pivot_values | List[str] | 透视值列表 |
| config_info | dict | 配置信息（用于说明Sheet） |

**config_info 格式**:

```python
{
    "manual_file": "手工表.xlsx",
    "manual_sheet": "Sheet1",
    "system_file": "系统表.xlsx",
    "system_sheet": "执行报表",
    "key_mappings": [...],
    "formula": "手工数量 - 系统总计",
    "filters": {...}
}
```

**生成的Sheet**:

| Sheet名 | 内容 |
|---------|------|
| 完整结果 | 所有数据（带颜色） |
| 差异数据 | 仅差异和缺失 |
| 说明 | 配置和统计信息 |

**示例**:

```python
ExportEngine.export_results(
    out_path="对账结果_20260111.xlsx",
    result_df=result,
    pivot_values=["已完成", "处理中"],
    config_info={
        "manual_file": "订单数据.xlsx",
        "system_file": "系统导出.xlsx",
        "formula": "手工数量 - 系统总计"
    }
)
```

---

### 颜色配置

```python
# config/settings.py
EXCEL_COLORS = {
    "match": "FFD1FAE5",      # 一致 - 浅绿
    "diff_pos": "FFD9F99D",   # 差异(正) - 浅黄
    "diff_neg": "FFBFDBFE",   # 差异(负) - 浅蓝
    "missing": "FFFECACA",    # 缺失 - 浅红
    "header": "FFE2E8F0",     # 表头 - 浅灰
}
```

---

## 🔄 完整使用流程

### 典型调用流程

```python
from core.compare_engine import CompareEngine
from core.export_engine import ExportEngine

# 1. 读取数据
manual_df = pd.read_excel("手工表.xlsx")
system_df = pd.read_excel("系统表.xlsx")

# 2. 数据清洗
manual_df = CompareEngine.clean_column(manual_df, clean_rules)
system_df = CompareEngine.clean_column(system_df, clean_rules)

# 3. 生成主键
manual_df = CompareEngine.make_key(manual_df, ["订单编号", "物料编码"])
system_df = CompareEngine.make_key(system_df, ["订单号", "零件号"])

# 4. 手工表聚合（带透视）
manual_agg, out_cols, in_cols = CompareEngine.aggregate_manual_with_pivot(
    manual_df, "__KEY__", "数量", manual_pivot_config, manual_filters
)

# 5. 系统表聚合（带透视）
system_agg, pivot_values = CompareEngine.aggregate_system(
    system_df, "__KEY__", ["数量"], "订单状态", system_filters
)

# 6. 合并比对
result = CompareEngine.merge_and_compare(
    manual_agg, system_agg, 
    formula="手工数量 - 系统总计",
    pivot_values=pivot_values
)

# 7. 导出结果
ExportEngine.export_results(
    "对账结果.xlsx", result, pivot_values, config_info
)
```

---

## ⚠️ 注意事项

### 数据类型

- 主键列会被转换为字符串
- 数值列会被转换为数字类型
- 空值处理为0

### 性能考虑

| 数据量 | 预计耗时 |
|--------|---------|
| < 1000行 | < 1秒 |
| 1000-10000行 | 1-5秒 |
| 10000-100000行 | 5-30秒 |

### 内存使用

- 大数据集建议分批处理
- 透视操作会增加内存消耗

---

## ▶️ 下一步

了解UI组件API，查看 [UI组件API](./15-UI组件API.md)。
