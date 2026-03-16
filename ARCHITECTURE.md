# 🏗️ ARCHITECTURE

**SupplyChain-Reconciler-Plus 系统架构设计**

---

## 📐 整体架构

### 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层 (UI)                      │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ 主窗口       │ 配置面板     │ 结果预览     │              │
│  │ (QtMainWindow) │ (QtConfigPanel) │ (QtResultPreview) │  │
│  └──────────────┴──────────────┴──────────────┘              │
│            ↓  信号/槽           ↓  配置获取                  │
├─────────────────────────────────────────────────────────────┤
│                       业务逻辑层 (Core)                      │
│  ┌────────────────────────────────────────────────┐          │
│  │  CompareEngine: 数据比对引擎                   │          │
│  │  - 数据清洗    - 主键生成   - 聚合透视        │          │
│  │  - 条件筛选    - 合并比对   - 差值计算        │          │
│  └────────────────────────────────────────────────┘          │
│  ┌────────────────────────────────────────────────┐          │
│  │  ExportEngine: 导出引擎                        │          │
│  │  - Excel写入   - 颜色标记   - 多Sheet处理     │          │
│  └────────────────────────────────────────────────┘          │
│            ↓  数据处理          ↓  数据结构                  │
├─────────────────────────────────────────────────────────────┤
│                       工具层 (Utils)                         │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ Excel操作    │ 配置存储     │ Excel检测    │              │
│  │ (excel_utils)│ (storage)    │(excel_detection)│          │
│  └──────────────┴──────────────┴──────────────┘              │
│            ↓  文件操作          ↓  系统调用                  │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)               │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ 文件系统     │ 数据库       │ 操作系统     │              │
│  └──────────────┴──────────────┴──────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 模块结构

### 顶级目录

```
SupplyChain-Reconciler-Plus/
├── main.py                    # 应用启动入口
├── start.py                   # 启动菜单（可选）
├── config/                    # 配置模块
│   ├── __init__.py
│   └── settings.py           # 全局常量
├── core/                      # 核心业务逻辑
│   ├── __init__.py
│   ├── compare_engine.py      # 数据比对引擎
│   └── export_engine.py       # Excel导出引擎
├── ui/                        # 用户界面
│   ├── __init__.py
│   ├── qt_main_window.py      # 主窗口
│   ├── qt_config_panel.py     # 配置面板
│   ├── qt_result_preview.py   # 结果预览
│   ├── qt_dialogs.py          # 对话框组件
│   └── scroll_utils.py        # UI工具（可选）
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── excel_utils.py         # Excel读写工具
│   ├── excel_detection.py     # 活动Excel检测
│   └── storage.py             # 配置/模板存储
├── tests/                     # 测试模块
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_asn_export.py
│   ├── test_template_*.py
│   └── README_TESTING.md
├── docs/                      # 详细功能文档（19份）
├── exports/                   # 导出结果目录
├── requirements.txt           # 依赖列表
├── CHANGELOG.md              # 版本历史
├── ARCHITECTURE.md           # 本文件
├── AGENT.md                  # Agent约束
└── ...其他文档
```

---

## 🔄 数据流向

### 完整对账流程

```
用户导入 Excel
     ↓
┌────────────────────────────────────────┐
│ Step 1: 文件加载                       │
├────────────────────────────────────────┤
│ 1. excel_utils.read_excel()            │
│    - 读取Sheet内容为DataFrame         │
│    - 自动类型推断                     │
│ 2. QtConfigPanel.set_sample_data()     │
│    - 显示前5行数据预览                │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ Step 2: 配置处理                       │
├────────────────────────────────────────┤
│ 1. QtConfigPanel.get_config()          │
│    - 获取所有配置项                   │
│ 2. 配置验证                           │
│    - 检查主键、数值列必填             │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ Step 3: 数据预处理                     │
├────────────────────────────────────────┤
│ 1. CompareEngine.clean_column()        │
│    - 正则清洗数据                     │
│ 2. CompareEngine.apply_filters()       │
│    - 应用筛选条件                     │
│ 3. CompareEngine.make_key()            │
│    - 生成复合主键                     │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ Step 4: 透视聚合                       │
├────────────────────────────────────────┤
│ 1. CompareEngine.aggregate_manual_*()  │
│    - 手工表透视+出入库区分            │
│ 2. CompareEngine.aggregate_system()    │
│    - 系统表透视+状态展开              │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ Step 5: 合并比对                       │
├────────────────────────────────────────┤
│ 1. CompareEngine.merge_and_compare()   │
│    - 左外连接(手工表为主)             │
│    - 计算差值                         │
│    - 标记比对状态                     │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ Step 6: 结果导出                       │
├────────────────────────────────────────┤
│ 1. QtResultPreview.set_data()          │
│    - 显示前15行预览                   │
│    - 计算统计信息                     │
│ 2. ExportEngine.export_results()       │
│    - 生成带颜色的Excel                │
│    - 创建多个Sheet                    │
└────────────────────────────────────────┘
     ↓
导出 Excel 完成
```

---

## 🔌 模块接口

### CompareEngine 公共接口

```python
class CompareEngine:
    """数据比对引擎"""
    
    # 数据处理
    @staticmethod
    def clean_column(df, clean_rules) → DataFrame
    
    @staticmethod
    def apply_filters(df, filters) → DataFrame
    
    @staticmethod
    def make_key(df, key_cols, keyname) → DataFrame
    
    # 透视聚合
    @staticmethod
    def aggregate_manual_with_pivot(
        df, key_col, value_col, pivot_config, filters
    ) → Tuple[DataFrame, List, List]
    
    @staticmethod
    def aggregate_system(
        df, key_col, value_cols, pivot_column, filters
    ) → Tuple[DataFrame, List]
    
    # 核心对账
    @staticmethod
    def merge_and_compare(
        manual_df, system_df, key_col, formula, pivot_values
    ) → DataFrame
```

### ExportEngine 公共接口

```python
class ExportEngine:
    """Excel导出引擎"""
    
    @staticmethod
    def export_results(
        out_path, result_df, pivot_values, config_info
    ) → None
```

### QtConfigPanel 公共接口

```python
class QtConfigPanel(QWidget):
    """配置面板"""
    
    def get_config(self) → dict
    def set_config(self, config) → None
    def refresh_columns(self, manual_cols, system_cols) → None
```

---

## 💾 数据结构

### 核心数据模型

#### 1. 配置对象 (Config)

```python
{
    "key_mappings": [
        {"manual_col": str, "system_col": str},
        ...
    ],
    "value_mapping": {
        "manual_col": str,
        "system_col": str
    },
    "clean_rules": [
        {
            "column": str,
            "mode": str,  # "删除匹配"|"保留匹配"|"替换为"
            "regexes": [str],
            "replace": str
        },
        ...
    ],
    "manual_filters": [...],
    "system_filters": [...],
    "manual_pivot_config": {
        "enabled": bool,
        "pivot_column": str,
        "out_values": [str],
        "in_values": [str]
    },
    "system_pivot_config": {
        "enabled": bool,
        "pivot_column": str
    },
    "difference_formula": str
}
```

#### 2. 结果数据 (Result DataFrame)

```
| __KEY__ | 透视列1 | 透视列2 | 系统总计 | 手工数量 | 差值 | 比对状态 |
|---------|--------|--------|---------|---------|------|---------|
| str     | num    | num    | num     | num     | num  | str     |
```

#### 3. 模板对象 (Template)

```python
{
    "id": str,  # UUID
    "name": str,
    "config": {...},  # 同上Config
    "timestamp": str
}
```

---

## 🔐 设计原则

### 1. 分层清晰

```
规则: 
- UI → Core → Utils (单向依赖)
- Core 不依赖 UI
- Utils 不依赖 UI 和 Core
```

**好处**:
- 代码耦合度低
- 易于测试
- 易于维护

### 2. 单一职责

```
每个模块只负责一个功能:
- CompareEngine: 只做数据比对
- ExportEngine: 只做Excel导出
- excel_utils: 只做Excel读写
- storage: 只做配置存储
```

### 3. 不可变数据流

```python
# 正确：操作后返回新对象
result = df.merge(other_df).copy()

# 避免：直接修改原对象
df.merge(other_df, inplace=True)
```

### 4. 显式配置

```python
# 正确：所有配置通过参数传递
pivot_df = aggregate_system(df, config=pivot_config)

# 避免：使用隐藏的全局状态
pivot_df = aggregate_system(df)  # 依赖全局变量
```

---

## 🔄 关键交互流

### 文件导入流程

```
用户拖拽文件或点击选择
     ↓
QtMainWindow._on_select_file()
     ↓
excel_utils.get_sheet_names()
     ↓
更新 Sheet 下拉框
     ↓
excel_utils.read_excel_preview()
     ↓
QtConfigPanel.set_sample_data()
```

### 配置保存流程

```
用户点击"保存模板"
     ↓
InputDialog 获取模板名称
     ↓
QtConfigPanel.get_config()
     ↓
storage.save_template(name, config)
     ↓
写入 templates.json
     ↓
刷新模板下拉框
```

### 对账执行流程

```
用户点击"执行对账"
     ↓
验证配置完整性
     ↓
读取两个文件
     ↓
CompareEngine.merge_and_compare()
     ↓
QtResultPreview.set_data()
     ↓
显示预览 + 统计
```

---

## 🚀 扩展点

### 1. 新增筛选操作符

```
位置: core/compare_engine.py
修改 OPERATOR_MAP 常量
```

### 2. 新增数据清洗模式

```
位置: core/compare_engine.py
修改 clean_column() 方法
```

### 3. 新增导出格式

```
位置: core/export_engine.py
创建新的 export_* 方法
```

### 4. 新增UI组件

```
位置: ui/qt_dialogs.py
创建新的 Dialog 类
```

---

## 📊 依赖关系图

```
main.py
  ↓
QtMainWindow
  ├→ QtConfigPanel
  │   ├→ CompareEngine (读取配置后调用)
  │   └→ excel_utils
  ├→ QtResultPreview
  │   └→ CompareEngine (获取结果后处理)
  ├→ ExportEngine
  │   └→ openpyxl
  └→ storage
      └→ json

CompareEngine
  ├→ pandas
  ├→ re (正则)
  └→ utils

ExportEngine
  ├→ openpyxl
  └→ config.settings (颜色配置)

excel_utils
  ├→ pandas
  ├→ openpyxl
  └→ xlrd

storage
  ├→ json
  ├→ uuid
  └→ pathlib
```

---

## 💡 设计决策

### 为什么使用 pandas?
- 数据处理强大
- 内存效率高
- API易用

### 为什么分离 Core 和 UI?
- 便于单元测试
- 便于复用（如CLI/API）
- 代码维护性好

### 为什么使用 JSON 存储模板?
- 轻量级，易于备份
- 人类可读
- 跨平台支持

### 为什么限制预览为 15 行?
- 防止大数据量导致UI卡顿
- 足够用户验证配置
- 完整数据在导出中保留

---

## 🔧 性能考虑

### 瓶颈分析

| 操作 | 瓶颈 | 优化策略 |
|------|------|---------|
| 读取大文件 | I/O | pandas优化 |
| 透视操作 | 内存 | 限制行数 |
| Excel导出 | openpyxl写入 | 流式写入 |
| 模板操作 | JSON序列化 | 增量更新 |

### 优化建议

1. **分批处理**: 超过10万行建议分批
2. **懒加载**: 预览使用head()
3. **缓存**: 重复操作的中间结果
4. **异步**: 长操作使用加载动画

---

## 📚 相关文档

- [核心引擎API](docs/14-核心引擎API.md)
- [UI组件API](docs/15-UI组件API.md)
- [工具函数API](docs/16-工具函数API.md)
- [开发约束](AGENT.md)

---

**最后更新**: 2026年3月16日  
**文档版本**: 1.4.4
