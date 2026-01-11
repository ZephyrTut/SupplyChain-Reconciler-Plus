# SupplyChain-Reconciler-Plus - Agent开发约束文档

## 项目概述

**项目名称**: SupplyChain-Reconciler-Plus  
**项目类型**: Python桌面应用（供应链对账系统）  
**当前版本**: v1.4.3  
**Python版本**: 3.10+  
**主要框架**: PyQt6, qt-material, pandas, openpyxl

---

## 核心功能定位

### 业务场景
- 双表对账：手工表（人工录入/盘点）vs 系统表（ERP/WMS/OMS导出）
- 数据比对：基于复合主键匹配，计算数值差异
- 数据清洗：正则表达式批量清洗列数据
- 透视分析：手工表支持出入库区分，系统表支持透视展开
- 结果导出：生成彩色Excel报告（一致/差异/缺失）

### 用户群体
- 财务部门：账目核对
- 供应链部门：库存对账
- 仓储部门：盘点核对
- **技术水平**: 无编程背景，仅会使用Excel

---

## 技术栈约束

### 必须使用的库
```python
PyQt6>=6.0.0            # UI框架（跨平台GUI）
qt-material>=2.14       # Material Design 主题
pandas>=1.5.0           # 数据处理（核心引擎）
openpyxl>=3.0.0         # Excel读写（支持颜色）
xlrd>=2.0.0             # Excel读取（.xls格式支持）
```

### 可选依赖
```python
pywin32>=300            # Windows活动Excel检测（仅Windows）
```

### 禁止使用的技术
-  数据库（SQLite/MySQL）- 用户不需要持久化大量数据
-  Web框架（Flask/Django）- 必须是桌面应用
-  NumPy高级功能 - pandas已足够

---

## 项目结构规范

```
SupplyChain-Reconciler-Plus/
 main.py              # 应用启动入口（PyQt6）
 config/              # 配置模块
    settings.py      # 全局常量（颜色、字段定义）
 core/                # 核心逻辑（不含UI）
    compare_engine.py    # 数据比对引擎
    export_engine.py     # Excel导出引擎
 ui/                  # 界面模块（PyQt6）
    qt_main_window.py    # 主窗口
    qt_config_panel.py   # 配置面板
    qt_result_preview.py # 结果预览
    qt_dialogs.py        # 对话框组件
 utils/               # 工具模块
    excel_utils.py       # Excel读写
    excel_detection.py   # 活动Excel检测
    storage.py           # 配置存储（JSON）
 tests/               # 测试模块
```

### 架构原则
1. **分层清晰**: UI层、核心层、工具层严格分离
2. **单一职责**: 每个文件只负责一个功能模块
3. **无循环依赖**: UI调用Core，Core使用Utils，禁止反向依赖

---

## 代码规范约束

### 命名规范
- 类名：PascalCase
- 函数/变量：snake_case
- 常量：UPPER_CASE
- 私有方法：前缀单下划线

### 异常处理规范
```python
#  正确：捕获具体异常
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    QMessageBox.critical(self, "错误", "文件不存在")
except PermissionError:
    QMessageBox.critical(self, "错误", "文件被占用")
```

---

## UI开发约束

### 必须使用 PyQt6 + qt-material 组件
```python
from PyQt6.QtWidgets import QPushButton, QComboBox, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

# 创建带信号的组件
button = QPushButton("确定")
button.clicked.connect(self._on_confirm)

combobox = QComboBox()
combobox.addItems(options)
combobox.currentTextChanged.connect(self._on_change)
```

### 布局管理规范
```python
# 使用布局管理器，避免固定坐标
layout = QVBoxLayout()
layout.setContentsMargins(10, 10, 10, 10)
layout.setSpacing(8)
layout.addWidget(widget)
```

### UI配色约束（重要！）
本项目使用【浅色主题】，所有UI组件必须遵循以下配色规范：

**背景色**:
- 主背景: #f5f5f5 (浅灰)
- 卡片/面板背景: #ffffff (白色)
- 折叠区标题: #f8f9fa (浅灰)
- 输入框/下拉框背景: #ffffff (白色)
- 对话框背景: #ffffff (白色)
- 按钮背景: #f5f5f5 (浅灰)

**文字色**:
- 主要文字: #333333 (深灰，用于正文、标签、按钮)
- 次要文字: #666666 (中灰，用于提示、说明)
- 占位符: #999999 (浅灰)
- 链接/强调: #1976D2 (蓝色)
- 主按钮文字: #ffffff (白色，仅用于蓝色背景按钮)

**边框色**:
- 默认边框: #cccccc 或 #ddd
- 悬停边框: #2196F3 (蓝色)
- 分割线: #e0e0e0

**样式设置示例**:
```python
#  正确：使用浅色主题配色
label.setStyleSheet("color: #333333;")
combo.setStyleSheet("background-color: #ffffff; color: #333333; border: 1px solid #ccc;")
btn.setStyleSheet("background-color: #f5f5f5; color: #333333; border: 1px solid #ddd;")

#  错误：深色背景与浅色主题冲突
combo.setStyleSheet("background-color: #2d2d2d; color: white;")
```

**下拉框禁用滚轮**:
```python
# 避免下拉框滚轮影响外部滚动
from ui.qt_config_panel import NoScrollComboBox
combo = NoScrollComboBox()
```

---

## 数据处理约束

### pandas操作规范
```python
#  明确设置副本
merged_df = manual_df.merge(system_df, how='left', on=key_cols).copy()

#  使用 .loc 避免警告
df.loc[:, 'new_column'] = values
```

### 透视处理规范
```python
pivoted = df.pivot_table(
    index=key_cols,
    columns=pivot_col,
    values=value_col,
    aggfunc='sum',      # 必须显式指定
    fill_value=0
)
```

### 数据清洗规范
```python
# 清洗规则格式
clean_rule = {
    "column": "到货单号",       # 要清洗的列
    "mode": "删除匹配",         # 删除匹配 | 保留匹配 | 替换为
    "regexes": ["-\\d+$"],      # 正则表达式列表
    "replace": ""               # 替换值（仅替换为模式使用）
}
```

### 公式解析约束
```python
# 支持的公式格式（使用变量名）
# 可用变量: 手工数量, 系统总计, 透视列名

#  合法公式
"手工数量 - 系统总计"                    # 基本差值
"手工数量 - (系统总计 - 已关闭)"         # 排除某透视列
"手工数量 - (已完成 + 处理中)"           # 只对比指定透视列
```

---

## 核心引擎类说明

### CompareEngine (core/compare_engine.py)

**主要方法**:
- `clean_column(df, clean_rules)`: 数据清洗（支持多正则）
- `aggregate_manual_with_pivot(df, key_col, value_col, pivot_config, filters)`: 手工表透视聚合（出入库区分）
- `aggregate_system(df, key_col, value_cols, pivot_config, filters)`: 系统表聚合/透视
- `make_key(df, key_cols, keyname)`: 生成复合主键
- `merge_and_compare(manual_df, system_df, ...)`: 合并比对 + 差值计算

**筛选操作符映射**:
```python
OPERATOR_MAP = {
    "等于": "EQUALS",
    "不等于": "NOT_EQUALS",
    "包含": "CONTAINS",
    "不包含": "NOT_CONTAINS",
    "包含于": "IN_LIST",
    "大于": "GREATER",
    "小于": "LESS"
}
```

### ExportEngine (core/export_engine.py)

**导出列顺序规范**:
1. `__KEY__` - 复合主键
2. 透视列（按名称排序）
3. `系统总计`
4. `手工数量`
5. `差值`
6. `比对状态`

**颜色标记规则**:
-  一致  浅绿色背景 (FFD1FAE5)
-  差异  浅黄色背景 (FFD9F99D/FFBFDBFE)
-  缺失  浅红色背景 (FFFECACA)

---

## 配置管理约束

### 模板格式（JSON）
```json
{
  "id": "uuid-string",
  "name": "订单对账-标准模板",
  "config": {
    "key_mappings": [...],
    "value_mapping": {...},
    "manual_filters": [...],
    "system_filters": [...],
    "manual_pivot_config": {...},
    "system_pivot_config": {...},
    "clean_rules": [...],
    "difference_formula": "手工数量 - 系统总计"
  },
  "timestamp": "2026-01-11 12:00:00"
}
```

### 模板操作约束
- 删除前必须二次确认
- 保存后自动选中新模板
- 模板ID使用UUID保证唯一性
- 同名模板自动覆盖

---

## 性能约束

### 数据量限制
- 小数据集 (< 1000行): < 1秒
- 中数据集 (1000-10000行): 1-5秒
- 大数据集 (10000-100000行): 5-30秒
- 超大数据集 (> 100000行): 不推荐，建议分批处理

### UI响应优化
```python
# 长时间操作使用加载动画
from ui.qt_dialogs import LoadingDialog
loading = LoadingDialog(self, "正在处理...")
loading.show()
# 处理逻辑
loading.close()

# 预览限制行数
preview_df = result_df.head(15)  # 只显示15行
```

---

## 用户体验约束

### 错误提示规范
```python
#  友好的错误提示
from ui.qt_dialogs import show_error
show_error(
    self,
    title="导入失败",
    message="手工表缺少必填列：订单编号\n\n请检查Excel文件是否正确。"
)
```

### 操作流程约束
1. 步骤1 - 导入文件：必须先导入文件才能进入步骤2
2. 步骤2 - 配置规则：必须配置主键和数值列才能执行对账
3. 步骤3 - 执行对账：必须先执行对账才能导出结果

---

## 禁止的操作

### 数据安全
-  禁止上传用户数据到网络
-  禁止存储敏感数据（密码、密钥）
-  禁止修改用户原始文件

### 代码质量
-  禁止使用全局变量（除常量）
-  禁止超过200行的函数
-  禁止在UI代码中直接操作pandas

---

## 文档维护约束（重要！）

### ⚠️ 强制要求：修改功能前必须先读取文档

**在修改任何功能代码之前，必须先读取 `docs/` 目录下的相关文档！**

| 修改内容 | 必须先读取的文档 |
|---------|----------------|
| 数据导入 | `docs/03-数据导入.md` |
| 主键配置 | `docs/04-主键配置.md` |
| 数据清洗 | `docs/05-数据清洗.md` |
| 筛选条件 | `docs/06-筛选条件.md` |
| 透视聚合 | `docs/07-透视聚合.md` |
| 差值公式 | `docs/08-差值公式.md` |
| 结果导出 | `docs/09-结果导出.md` |
| 主窗口 | `docs/10-主窗口界面.md` |
| 配置面板 | `docs/11-配置面板.md` |
| 结果预览 | `docs/12-结果预览.md` |
| 对话框 | `docs/13-对话框组件.md` |
| Core引擎 | `docs/14-核心引擎API.md` |
| UI组件 | `docs/15-UI组件API.md` |
| 工具函数 | `docs/16-工具函数API.md` |
| 配置常量 | `docs/17-配置常量.md` |
| 模板管理 | `docs/18-模板管理.md` |

### 必须保持同步的文档

**docs/ 目录是权威来源，其他文档从这里同步：**

| 文档 | 层级 | 说明 |
|------|------|------|
| `docs/*.md` | L3-详细 | 功能详细文档（权威来源） |
| `PROJECT_OVERVIEW.md` | L1-顶层 | 项目概述（从docs同步） |
| `README.md` | L1-顶层 | 快速开始（从docs同步） |
| `.github/copilot-instructions.md` | L2-约束 | 开发约束（本文件） |
| `AGENT.md` | L2-约束 | Agent专用约束（详细规则） |

### 文档更新流程

```
修改代码 → 更新 docs/ 对应文档 → 检查并更新其他文档
```

### 文档更新触发条件
- 新增功能 → 更新 docs/ + PROJECT_OVERVIEW + README
- 修改功能 → 更新 docs/（视情况更新其他）
- 修复Bug → 通常无需更新文档

** 详细文档约束**: 请参考 [AGENT.md](../AGENT.md)

---

## 总结：开发金科玉律

1. **分层清晰**: UI不处理数据，Core不操作界面
2. **用户第一**: 所有提示使用通俗语言，避免技术术语
3. **稳定优先**: 不追求新特性，保证现有功能稳定
4. **文档同步**: 代码变化必须更新文档
5. **测试覆盖**: 新功能必须有测试用例
6. **性能意识**: 大数据集必须优化，避免卡顿
7. **安全第一**: 不修改用户文件，不上传数据

---

**最后更新**: 2026年1月11日  
**文档版本**: 1.4.3  
**适用Agent**: GitHub Copilot, Cursor, 其他AI编程助手  

** 详细文档**: 请参考 [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)
