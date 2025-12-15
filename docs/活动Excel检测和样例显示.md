"""
活动Excel检测和样例显示功能 - 使用说明
"""

# 功能总结

## 1. 活动Excel检测功能修复 ✓

### 已修复的问题：
- ✓ 添加了工作表名称获取
- ✓ 改进了COM对象连接（支持 EnsureDispatch 和 Dispatch 两种方式）
- ✓ 增强了WPS检测（识别更多WPS特征）
- ✓ 添加了COM对象释放，避免内存泄漏
- ✓ 更详细的错误信息和调试输出

### 返回数据结构：
```python
{
    'path': '完整文件路径',
    'name': '工作簿名称',
    'sheet_name': '当前工作表名'
}
```

### 测试结果：
```
✓ 检测到活动Excel:
  - 文件名: 对账结果_20251214_012744.xlsx
  - 路径: C:\Users\XXK\Desktop\差值比对\对账结果_20251214_012744.xlsx
  - 工作表: 📋 完整结果
✓ 返回数据结构完整
```

## 2. 手工表/系统表样例显示 ✓

### 新增UI组件：
在结果预览面板顶部添加了两个样例显示区域：

**手工表样例区域（蓝色）：**
- 显示主键字段（最多3个，超过显示...）
- 显示数值字段
- 格式：`主键: 字段1 + 字段2 | 数值: 手工数量`

**系统表样例区域（绿色）：**
- 显示主键字段（最多3个，超过显示...）
- 显示数值字段
- 如果有透视，显示透视列和值数量
- 格式：`主键: 字段1 + 字段2 | 数值: 系统数量 | 透视: 状态 (3值)`

### 动态更新：
- 配置主键和数值字段后自动更新显示
- 清空配置时显示"配置后显示"

## 3. WPS和Office兼容性 ✓

### Office支持：
- ✓ Microsoft Excel 2007+
- ✓ 检测活动工作簿
- ✓ 获取文件路径和工作表名
- ✓ 自动释放COM对象

### WPS支持：
- ⚠ 检测到WPS时友好提示
- ⚠ 建议使用手动选择文件
- ✓ 不会导致程序崩溃

错误提示示例：
```
WPS Office 提示

检测到 WPS Office 环境

检测到 WPS Office。

WPS 的 COM 接口与 Excel 不同，暂不支持自动检测。
请手动选择文件或将文件另存为 Excel 格式后使用文件选择功能。

建议：请使用 Microsoft Excel 或手动选择文件。
```

## 4. 使用方法

### 活动Excel检测：
1. 在Excel中打开并保存文件（Ctrl+S）
2. 点击"📊 活动Excel"按钮
3. 自动检测并导入当前打开的Excel
4. 如有多个工作表，需选择要导入的Sheet

### 样例显示查看：
1. 导入手工表和系统表文件
2. 配置主键和数值字段
3. 自动在结果预览面板顶部显示配置摘要
4. 便于快速确认配置是否正确

## 5. 技术细节

### 修改的文件：
1. `utils/excel_detection.py` - 活动Excel检测核心逻辑
2. `ui/result_preview.py` - 结果预览面板（添加样例显示）
3. `ui/main_window.py` - 主窗口（拖拽和检测调用）
4. `tests/test_drag_drop.py` - 测试脚本

### 关键改进：
```python
# 改进的COM连接
try:
    excel = win32.gencache.EnsureDispatch('Excel.Application')
except:
    excel = win32.Dispatch('Excel.Application')

# 获取工作表名称
sheet_name = ""
try:
    if hasattr(excel, 'ActiveSheet') and excel.ActiveSheet:
        sheet_name = excel.ActiveSheet.Name
except:
    pass

# COM对象释放
finally:
    if excel:
        try:
            del excel
        except:
            pass
```

## 6. 测试验证

运行测试：
```bash
python tests/test_drag_drop.py
```

预期结果：
- ✓ 拖拽功能可用
- ✓ 活动Excel检测成功（如果打开了Excel）
- ✓ 文件类型验证正确
- ✓ 返回完整的数据结构（path, name, sheet_name）

---

**更新时间：** 2025-12-15
**版本：** v1.2.0
