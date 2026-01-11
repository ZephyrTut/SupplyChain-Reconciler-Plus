# SupplyChain-Reconciler-Plus - Agent开发约束文档

## 项目概述

**项目名称**: SupplyChain-Reconciler-Plus  
**项目类型**: Python桌面应用（供应链对账系统）  
**当前版本**: v1.4.0  
**Python版本**: 3.10+  
**主要框架**: PyQt6, qt-material, pandas, openpyxl

---

## 核心功能定位

### 业务场景
- 双表对账：手工表（人工录入/盘点）vs 系统表（ERP/WMS/OMS导出）
- 数据比对：基于复合主键匹配，计算数值差异
- 透视分析：自动处理系统表的透视列（如订单状态、月份等）
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
pandas>=2.0.0           # 数据处理（核心引擎）
openpyxl>=3.1.0        # Excel读写（支持颜色）
xlrd>=2.0.0            # Excel读取（.xls格式支持）
```

### 禁止使用的技术
- ❌ 数据库（SQLite/MySQL）- 用户不需要持久化大量数据
- ❌ Web框架（Flask/Django）- 必须是桌面应用
- ❌ NumPy高级功能 - pandas已足够

---

## 项目结构规范

```
SupplyChain-Reconciler-Plus/
├── config/              # 配置模块
│   └── settings.py     # 全局常量（颜色、字段定义）
├── core/               # 核心逻辑（不含UI）
│   ├── compare_engine.py   # 数据比对引擎
│   └── export_engine.py    # Excel导出引擎
├── ui/                 # 界面模块（PyQt6）
│   ├── qt_main_window.py   # 主窗口
│   ├── qt_config_panel.py  # 配置面板
│   ├── qt_result_preview.py # 结果预览
│   └── qt_dialogs.py       # 对话框组件
├── utils/              # 工具模块
│   ├── excel_utils.py      # Excel读写
│   ├── excel_detection.py  # 活动Excel检测
│   └── storage.py          # 配置存储（JSON）
└── tests/              # 测试模块
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
# ✅ 正确：捕获具体异常
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    QMessageBox.critical(self, "错误", "文件不存在")
except PermissionError:
    QMessageBox.critical(self, "错误", "文件被占用")
```

---

## UI开发约束

### 必须使用ttkbootstrap组件
```python
import ttkbootstrap as tb
button = tb.Button(parent, text="确定", bootstyle=SUCCESS)
combobox = tb.Combobox(parent, bootstyle=INFO)
```

### 滚动条处理规范
```python
from ui.scroll_utils import disable_combobox_scroll
combobox = tb.Combobox(parent, values=options)
disable_combobox_scroll(combobox)  # 防止滚轮联动
```

---

## 数据处理约束

### pandas操作规范
```python
# ✅ 明确设置副本
merged_df = manual_df.merge(system_df, how='left', on=key_cols).copy()

# ✅ 使用 .loc 避免警告
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

### 公式解析约束
```python
# 支持的公式格式
# M: 手工数量, S: 系统总计, A/B/C: 透视列

# ✅ 合法公式
"M - S"                # 基本差值
"M - (S - A)"          # 排除透视列A
"M - (A + B + C)"      # 对比多个透视列
```

---

## Excel导出约束

### 必须包含的列（顺序固定）
1. `__KEY__` - 复合主键
2. 手工数量 - 用户配置的手工表数值列
3. 透视列1, 透视列2, ... - 系统表透视后的列（如有）
4. `系统总计` - 系统表透视后的汇总
5. `差值` - 计算结果
6. `比对状态` - ✓/↕/✗

### 颜色标记规则
- ✓ 一致 → 浅绿色背景
- ↕ 差异 → 浅黄色背景
- ✗ 缺失 → 浅红色背景

---

## 配置管理约束

### 模板格式（JSON）
```json
{
  "templates": [
    {
      "id": "uuid-string",
      "name": "订单对账-标准模板",
      "config": {
        "key_mappings": [...],
        "value_mapping": {...},
        "pivot_column": {...},
        "pivot_values": [...],
        "difference_formula": "M - S"
      }
    }
  ]
}
```

### 模板操作约束
- 删除前必须二次确认
- 保存后自动选中新模板
- 模板ID使用UUID保证唯一性

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
from ui.loading import show_loading, hide_loading
show_loading(self.root, "正在处理...")
result = compare_engine.merge_and_compare(df1, df2, config)
hide_loading()

# 预览限制行数
preview_df = result_df.head(15)  # 只显示15行
```

---

## 用户体验约束

### 错误提示规范
```python
# ✅ 友好的错误提示
Messagebox.show_error(
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
- ❌ 禁止上传用户数据到网络
- ❌ 禁止存储敏感数据（密码、密钥）
- ❌ 禁止修改用户原始文件

### 代码质量
- ❌ 禁止使用全局变量（除常量）
- ❌ 禁止超过200行的函数
- ❌ 禁止在UI代码中直接操作pandas

---

## 文档维护约束

### 必须保持同步的文档
1. **PROJECT_OVERVIEW.md** - 完整项目文档（详细版）
2. **README.md** - 快速开始指南
3. **.github/copilot-instructions.md** - Agent开发约束（本文件）

### 文档更新触发条件
- 新增功能 → 更新所有3个文档
- 修改配置格式 → 更新 PROJECT_OVERVIEW.md
- 修复Bug → 通常无需更新文档

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

**最后更新**: 2025年12月15日  
**文档版本**: 1.0  
**适用Agent**: GitHub Copilot, Cursor, 其他AI编程助手  

**📚 详细文档**: 请参考 [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)
