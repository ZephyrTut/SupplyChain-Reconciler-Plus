# SupplyChain-Reconciler-Plus 优化说明

## 📋 本次优化内容

### 1. ✅ 修复列名重复问题

**问题**：导出Excel时"手工数量"列重复出现
**原因**：
- `merge` 操作产生 `_manual`, `_system` 后缀列
- 多次重命名导致列重复
- 导出逻辑未排除中间列

**修复**：
- 优化 `compare_engine.py` 的 `merge_and_compare` 方法，提前重命名为标准列名
- 改进 `export_engine.py` 的 `_get_export_columns` 方法，明确排除带后缀的中间列
- 移除 `main_window.py` 中重复的重命名逻辑

**导出列顺序**（修复后）：
```
1. __KEY__      - 复合主键
2. 手工数量      - 手工表数值
3. 已发货/已关闭等 - 透视列（如果有）
4. 系统总计      - 系统表总计
5. 差值         - 计算结果
6. 比对状态      - ✓/↕/✗
```

---

### 2. 🎨 优化差值公式界面

**改进内容**：
- ✅ 使用 **代号系统** 让公式更直观：
  - `M` = 手工数量
  - `S` = 系统总计
  - `A/B/C...` = 透视列（按字母顺序）
  
- ✅ 添加实时变量提示
- ✅ 显示透视变量映射（如 `A=已发货, B=已关闭`）
- ✅ 提供常用公式示例

**公式示例**：
```python
# 基本差值
M - S

# 排除已关闭状态
M - (S - 已关闭)

# 只比对特定状态
M - (已完成 + 处理中)
```

---

### 3. 📊 新增字段映射预览

**新功能**：`ui/field_preview.py`

实时显示导出字段结构，包括：
- 字段代号（KEY, M, A/B/C, S, D, 状态）
- 字段名称（主键, 手工数量, 透视列等）
- 字段来源（来自哪个原始列）
- 差值公式预览

**效果预览**：
```
KEY    | 主键       | 订单编号 + 物料编码
M      | 手工数量    | 来自: 手工数量
A/B/C  | 透视列     | 已发货, 已关闭, 待审核
S      | 系统总计    | 透视后总计
D      | 差值       | 公式: M - (S - 已关闭)
状态   | 比对状态    | ✓一致 / ↕差异 / ✗缺失
```

---

### 4. 🎯 改进文件上传体验

**新组件**：`ui/drag_drop.py`

功能特性：
- ✅ 支持文件拖拽上传（如果安装 `tkinterdnd2`）
- ✅ 点击也可选择文件
- ✅ 悬停高亮效果
- ✅ 文件名实时显示

**安装拖拽支持**（可选）：
```bash
pip install tkinterdnd2
```

---

### 5. 🚀 性能和体验优化

- ✅ **智能字段识别**：自动检测常用字段（订单号、料号、数量等）
- ✅ **实时预览更新**：配置更改时立即显示效果
- ✅ **错误处理增强**：更详细的错误提示
- ✅ **配置持久化**：自动保存上次配置

---

## 🧪 测试

### 运行单元测试

```bash
python tests/test_core.py
```

### 使用测试数据

1. 创建测试数据：
   ```bash
   python tests/create_test_data.py
   ```

2. 启动应用：
   ```bash
   python main.py
   ```

3. 导入文件：
   - 手工表: `tests/data/手工表.xlsx`
   - 系统表: `tests/data/系统表.xlsx`

4. 配置字段：
   - 主键: 订单编号 + 物料编码
   - 数值列: 手工数量 vs 系统数量
   - 透视: 状态
   - 公式: `M - (S - 已关闭)`

5. 查看结果并导出

---

## 📝 配置示例

### 基础对账（无透视）

```json
{
  "key_columns": [
    {"manual": "订单号", "system": "订单号"}
  ],
  "value_columns": [
    {"manual": "手工数量", "system": "系统数量"}
  ],
  "diff_formula": "M - S"
}
```

### 高级对账（带透视）

```json
{
  "key_columns": [
    {"manual": "订单号", "system": "订单号"},
    {"manual": "物料", "system": "物料"}
  ],
  "value_columns": [
    {"manual": "手工数量", "system": "系统数量"}
  ],
  "pivot_column": "状态",
  "system_filters": [
    {"column": "类型", "operator": "EQUALS", "value": "采购"}
  ],
  "diff_formula": "M - (S - 已关闭)"
}
```

---

## 🎨 字段代号说明

为了让公式更直观，使用以下代号：

| 代号 | 含义 | 说明 |
|------|------|------|
| `KEY` | 主键 | 多列组合的复合主键 |
| `M` | 手工数量 | Manual，左表数值 |
| `S` | 系统总计 | System，右表总计 |
| `A/B/C...` | 透视列 | 按字母顺序的透视值 |
| `D` | 差值 | Difference，计算结果 |

**公式中可直接使用**：
- 固定变量: `手工数量`, `系统总计`（或 `M`, `S`）
- 透视变量: 透视列的实际值（如 `已发货`, `已关闭`）

---

## 🔧 技术要点

### 1. 列名冲突处理

```python
# 旧方案（会产生重复列）
result = manual_df.merge(system_df, on=key_col, how='outer', 
                        suffixes=('_manual', '_system'))
result["手工数量"] = result[manual_val_col]  # 重复！

# 新方案（提前重命名，避免冲突）
manual_clean = manual_df.rename(columns={manual_val_col: "手工数量"})
system_clean = system_df.rename(columns={system_val_col: "系统总计"})
result = manual_clean[[key_col, "手工数量"]].merge(
    system_clean, on=key_col, how='outer'
)
```

### 2. 导出列过滤

```python
# 严格定义导出顺序
cols = []
if "__KEY__" in df.columns:
    cols.append("__KEY__")
if "手工数量" in df.columns:
    cols.append("手工数量")
# ... 透视列、系统总计、差值、状态

# 排除中间列
exclude_suffixes = ('_manual', '_system', '_x', '_y')
final_cols = [c for c in cols 
              if not any(c.endswith(s) for s in exclude_suffixes)]
```

### 3. 公式变量替换

```python
# 按长度降序替换，避免部分匹配
variables = {"手工数量": 100, "系统总计": 80, "已关闭": 20}
expr = "手工数量 - (系统总计 - 已关闭)"

for var_name in sorted(variables.keys(), key=len, reverse=True):
    expr = expr.replace(var_name, str(float(variables[var_name])))

result = eval(expr)  # 100 - (80 - 20) = 40
```

---

## 📦 依赖更新

```txt
pandas>=1.5.0
openpyxl>=3.0.0
ttkbootstrap>=1.10.0
tkinterdnd2>=0.3.0  # 可选，用于拖拽功能
```

---

## 🎯 下一步计划

- [ ] 添加进度条和加载动画
- [ ] 支持更多Excel格式（xlsb）
- [ ] 导出多Sheet对比
- [ ] 历史记录和回滚
- [ ] 批量对账功能

---

## 💡 使用技巧

1. **快速配置**：使用模板功能保存常用配置
2. **公式调试**：先用简单公式测试，再逐步复杂化
3. **字段预览**：观察字段映射预览确认配置正确
4. **透视优化**：系统表数据量大时使用筛选缩小范围
5. **导出检查**：导出后检查颜色标记是否符合预期

---

## 🐛 已知问题

- ~~导出时手工数量重复~~ ✅ 已修复
- ~~公式变量不明确~~ ✅ 已优化
- 拖拽功能需要额外安装 `tkinterdnd2`

---

## 📞 技术支持

如遇问题，请检查：
1. Python版本 >= 3.9
2. 依赖已完整安装
3. Excel文件格式正确
4. 配置的列名存在于数据中

---

**更新日期**: 2025-12-12
**版本**: v1.1.0
