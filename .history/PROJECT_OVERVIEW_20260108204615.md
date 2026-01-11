# SupplyChain-Reconciler-Plus 项目文档

**供应链智能对账系统** - Python桌面应用  
**当前版本**: v1.3.0  
**最后更新**: 2025年12月15日

---

## 📋 目录
- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心功能](#核心功能)
- [版本历史](#版本历史)
- [安装与运行](#安装与运行)
- [使用指南](#使用指南)
- [开发说明](#开发说明)

---

## 项目概述

SupplyChain-Reconciler-Plus 是一个基于Python的供应链对账桌面应用，专为企业财务和供应链部门设计，用于快速比对手工表与系统表的数据差异。

### 应用场景
- 库存对账（手工盘点 vs ERP系统）
- 订单核对（手工记录 vs 订单系统）
- 财务对账（人工账目 vs 财务系统）
- 任何需要双表数据比对的场景

### 核心优势
- ✅ **零代码配置**: 图形界面完成所有配置，无需编程
- ✅ **复合主键**: 支持多字段组合主键
- ✅ **透视分析**: 自动处理系统表的透视列（如订单状态、月份等）
- ✅ **自定义公式**: 灵活配置差值计算公式
- ✅ **模板管理**: 保存常用配置，一键应用
- ✅ **实时预览**: 配置即时生效，所见即所得
- ✅ **彩色导出**: Excel结果自动标色（一致/差异/缺失）

---

## 技术栈

### 核心框架
- **Python**: 3.10+
- **ttkbootstrap**: 现代化Tkinter UI框架
- **pandas**: 高性能数据处理
- **openpyxl**: Excel读写及样式控制

### 可选依赖
- **tkinterdnd2**: 文件拖拽支持（提升用户体验）
- **xlrd**: 读取旧版Excel (.xls)
- **pywin32**: Windows活动Excel检测

### 开发工具
- **pytest**: 单元测试框架
- **unittest**: Python标准测试库

---

## 项目结构

```
SupplyChain-Reconciler-Plus/
├── main.py                    # 应用启动入口
├── start.py                   # 备用启动脚本
├── requirements.txt           # 依赖清单
├── PROJECT_OVERVIEW.md        # 项目总文档（本文件）
├── README.md                  # 快速开始指南
│
├── config/                    # 配置模块
│   ├── __init__.py
│   └── settings.py           # 全局常量、颜色、字段定义
│
├── core/                      # 核心逻辑
│   ├── __init__.py
│   ├── compare_engine.py     # 数据比对引擎（主键匹配、透视处理）
│   └── export_engine.py      # Excel导出引擎（颜色、格式）
│
├── ui/                        # 界面模块
│   ├── __init__.py
│   ├── main_window.py        # 主窗口（三步骤流程控制）
│   ├── config_panel.py       # 配置面板（主键、筛选、透视、公式）
│   ├── result_preview.py     # 结果预览面板（Treeview + 样例）
│   ├── template_manager.py   # 模板管理（保存/加载/删除）
│   ├── scroll_utils.py       # 滚动工具（统一滚动行为）
│   └── loading.py            # 加载动画
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── excel_utils.py        # Excel读写工具
│   ├── excel_detection.py    # 活动Excel检测（Windows）
│   └── storage.py            # 配置持久化（JSON）
│
└── tests/                     # 测试模块
    ├── __init__.py
    ├── run_tests.py          # 测试运行器
    ├── test_core.py          # 核心功能测试
    ├── test_template_*.py    # 模板功能测试
    └── create_test_data.py   # 测试数据生成器
```

---

## 核心功能

### 1. 双表对账
- **手工表**: 人工录入或盘点的数据
- **系统表**: ERP/WMS/OMS等系统导出的数据
- **比对结果**: 
  - ✓ 一致（浅绿色）
  - ↕ 差异（浅黄色）
  - ✗ 缺失（浅红色 - 手工表有但系统表无）

### 2. 复合主键配置
支持多字段组合主键，例如：
- 订单编号 + 物料编码
- 客户ID + 产品SKU
- 仓库 + 批次号

### 3. 透视列（Pivot）支持
自动处理系统表的透视数据：
```
系统表原始数据:
订单号 | 状态   | 数量
A001  | 已完成 | 100
A001  | 处理中 | 50

透视后:
订单号 | 已完成 | 处理中 | 系统总计
A001  | 100   | 50    | 150
```

### 4. 动态差值公式
使用字母代号自定义公式：
- **M**: 手工数量
- **S**: 系统总计
- **A/B/C...**: 透视列（按字母顺序）

**常用公式示例**:
```python
M - S                    # 基本差值
M - (S - A)             # 排除透视列A
M - (A + B)             # 只对比透视列A和B
M - (A + B + C)         # 对比多个透视列
```

### 5. 配置模板
- **保存模板**: 一键保存当前配置（主键、筛选、透视、公式）
- **加载模板**: 快速应用常用配置
- **删除模板**: 清理无用模板
- **模板格式**: JSON存储（config_templates.json）

### 6. 实时匹配预览
- **样例显示**: 手工表和系统表前5条数据
- **字段映射**: 显示字母代号与字段名对应关系
- **结果预览**: 显示前15行对账结果
- **状态统计**: 一致/差异/缺失数量

### 7. 彩色Excel导出
导出结果包含：
- **表头**: 浅蓝色背景 + 加粗字体
- **一致行**: 浅绿色背景 + 深绿色字体
- **差异行**: 浅黄色背景 + 深黄色字体
- **缺失行**: 浅红色背景 + 深红色字体
- **列宽**: 自动调整，主键列150px，其他列90px

---

## 版本历史

### v1.3.0 (2025-12-15)

#### ✨ 新增功能
1. **样例显示增强**
   - 手工表和系统表样例从单行改为显示前5条数据
   - 样例区域可独立滚动（固定高度100px）
   - 系统表额外显示透视信息

2. **结果预览优化**
   - Treeview显示行数从8行增加到15行
   - 状态栏显示"预览前15行 / 共XX行"

3. **模板管理增强**
   - 新增删除模板按钮
   - 删除前二次确认对话框
   - 删除后自动刷新模板列表

4. **滚动条UI统一优化**
   - 创建通用滚动条工具模块 [ui/scroll_utils.py](ui/scroll_utils.py)
   - 统一所有滚动容器的鼠标滚轮行为
   - Combobox下拉框滚动事件隔离

#### 🐛 修复问题
- ✅ 修复滚动配置面板时Combobox下拉框联动滚动
- ✅ 修复样例标签未实时更新数据的问题
- ✅ 修复模板删除对话框参数错误

#### 🔧 技术改进
- 新增文件: [ui/scroll_utils.py](ui/scroll_utils.py) - 滚动条工具库
- 重构: [ui/result_preview.py](ui/result_preview.py) - 样例区域重构
- 优化: [ui/main_window.py](ui/main_window.py) - 模板删除功能
- 改进: [ui/config_panel.py](ui/config_panel.py) - 滚动事件隔离

### v1.2.0 (2025-12-14)

#### ✨ 新增功能
1. **优化模板功能**
   - 使用模板后下拉框直接显示模板名称
   - 保存模板后自动选中新保存的模板

2. **新增数据样例预览**
   - 在配置页面顶部显示手工表和系统表样例（前5行）
   - 并排显示，最多显示10列

3. **优化结果预览样式**
   - 表头格式改为 `字母 (字段名)` 格式
   - 表头添加浅蓝色背景，加粗字体
   - 行颜色优化（绿/黄/红）

4. **系统表筛选下拉框**
   - 系统表筛选的"值"输入框改为下拉框
   - 选择列后自动加载该列的唯一值

5. **差值公式快速选择**
   - 添加"快速选择"下拉框
   - 智能选项根据透视列动态生成
   - 使用字母代号（A/B/C/D/E）

6. **修复透视列自动变化Bug**
   - 只在透视列字段本身变化时才重新计算透视值
   - 透视列顺序保持稳定

7. **增强导入功能**
   - 支持文件拖拽导入（需要tkinterdnd2库）
   - 支持多种格式（.xlsx/.xls/.xlsm）
   - 多Sheet文件自动列出所有Sheet供选择

#### 🐛 Bug修复
- ✅ 修复预览更新TypeError ('str' object has no attribute 'get')
- ✅ 修复下拉框滚动联动主滚动条
- ✅ 修复下拉框选中值随滚动变化
- ✅ 修复列名重复问题（导出Excel时"手工数量"列重复）
- ✅ 增强错误处理和异常捕获

### v1.1.0 及更早版本
- 基础对账功能
- 复合主键支持
- 透视列处理
- 配置模板
- Excel导出

---

## 安装与运行

### 环境要求
- **操作系统**: Windows 10+ / macOS 10.14+ / Linux
- **Python**: 3.10 或更高版本
- **内存**: 建议2GB以上
- **磁盘**: 50MB（不含数据文件）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/SupplyChain-Reconciler-Plus.git
cd SupplyChain-Reconciler-Plus
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **可选依赖**（推荐安装）
```bash
# 文件拖拽支持
pip install tkinterdnd2

# 旧版Excel支持
pip install xlrd

# Windows活动Excel检测（仅Windows）
pip install pywin32
```

### 运行应用

**方式一**: 直接运行
```bash
python main.py
```

**方式二**: 使用启动脚本
```bash
python start.py
```

**方式三**: Windows批处理（创建快捷方式）
```batch
@echo off
python main.py
pause
```

---

## 使用指南

### 快速开始（3步流程）

#### 步骤1: 导入文件
1. 点击"选择手工表文件"按钮（或拖拽文件到手工表区域）
2. 选择Excel文件（.xlsx/.xls/.xlsm）
3. 如有多个Sheet，选择目标Sheet
4. 重复操作导入系统表文件

**提示**: 
- 支持拖拽上传（需安装tkinterdnd2）
- 点击"📊 活动Excel"可直接导入当前打开的Excel（仅Windows）

#### 步骤2: 配置比对规则

##### 2.1 配置主键映射
```
手工表主键              系统表主键
[订单编号] ←→ [订单编号]
[物料编码] ←→ [物料编码]
```
- 点击"➕ 添加主键"增加字段
- 支持多字段复合主键
- 左右字段必须一一对应

##### 2.2 配置数值列映射
```
手工数量列: [手工数量]
系统数量列: [系统数量]
```

##### 2.3 配置筛选条件（可选）
**手工表筛选**:
```
列: [状态]
操作: [等于]
值: [已审核]
```

**系统表筛选**:
```
列: [状态]
操作: [等于]
值: [已发货] (从下拉框选择)
```

##### 2.4 配置透视列（可选）
如果系统表需要透视汇总：
```
透视列: [订单状态]
透视值: [已完成, 处理中, 待审核] (自动加载)
```

##### 2.5 配置差值公式
**方式一**: 使用快速选择
```
快速选择: [D - E (手工 - 系统总计)]
```

**方式二**: 自定义公式
```
自定义公式: M - (S - A)
```

**可用变量**:
- M: 手工数量
- S: 系统总计
- A/B/C: 透视列（按字母顺序）

#### 步骤3: 执行对账

1. 点击"🚀 执行对账"按钮
2. 等待处理（显示加载动画）
3. 查看结果预览：
   - 前15行数据
   - 统计信息（一致/差异/缺失）
4. 点击"📥 导出Excel"保存结果

### 配置模板使用

#### 保存模板
1. 完成步骤2的所有配置
2. 点击"💾 保存模板"
3. 输入模板名称（如"订单对账-标准模板"）
4. 模板自动选中

#### 使用模板
1. 导入文件后（步骤1完成）
2. 从顶部下拉框选择模板
3. 所有配置自动填充

#### 删除模板
1. 从下拉框选择要删除的模板
2. 点击"🗑️ 删除模板"
3. 确认删除操作

### 样例显示说明

**手工表样例** (蓝色区域):
```
1. 订单A001, SKU-123 = 100
2. 订单A002, SKU-456 = 200
3. 订单A003, SKU-789 = 150
4. 订单A004, SKU-101 = 300
5. 订单A005, SKU-112 = 250
... 共38条数据
```

**系统表样例** (绿色区域):
```
1. 订单A001, SKU-123 = 95
2. 订单A002, SKU-456 = 200
3. 订单A003, SKU-789 = 140
4. 订单A004, SKU-101 = 310
5. 订单A005, SKU-112 = 250
... 共38条数据
透视: 订单状态 (3值)
```

### 结果解读

#### 比对状态说明
- **✓ 一致**: 手工数量与系统数量相等（差值=0）
- **↕ 差异**: 手工数量与系统数量不一致（差值≠0）
- **✗ 缺失**: 手工表有数据但系统表无匹配记录

#### 导出文件示例
文件名格式: `对账结果_YYYYMMDD_HHMMSS.xlsx`

**列结构**:
```
| __KEY__      | 手工数量 | 已完成 | 处理中 | 系统总计 | 差值 | 比对状态 |
|-------------|---------|-------|-------|---------|-----|---------|
| A001_SKU123 | 100     | 80    | 20    | 100     | 0   | ✓       |
| A002_SKU456 | 200     | 180   | 15    | 195     | 5   | ↕       |
| A003_SKU789 | 150     | -     | -     | -       | 150 | ✗       |
```

---

## 开发说明

### 代码规范
- **风格**: 遵循PEP 8
- **注释**: 所有公共方法必须有文档字符串
- **命名**: 
  - 类名: PascalCase
  - 函数/变量: snake_case
  - 常量: UPPER_CASE

### 架构设计

#### 分层结构
```
UI层 (ui/)
    ↓ 调用
核心层 (core/)
    ↓ 使用
工具层 (utils/)
    ↓ 读取
配置层 (config/)
```

#### 核心类说明

**CompareEngine** (core/compare_engine.py)
- `merge_and_compare()`: 主键匹配 + 透视处理 + 差值计算
- `_pivot_data()`: 透视列展开
- `_calculate_difference()`: 公式解析执行

**ExportEngine** (core/export_engine.py)
- `export_with_colors()`: Excel导出 + 颜色标记
- `_apply_styles()`: 单元格样式应用

**ConfigPanel** (ui/config_panel.py)
- `get_config()`: 获取当前所有配置
- `set_config()`: 加载配置到UI
- `_update_preview()`: 触发预览更新

**TemplateManager** (ui/template_manager.py)
- `save_template()`: 保存配置到JSON
- `load_template()`: 从JSON加载配置
- `delete_template()`: 删除指定模板

### 测试

#### 运行所有测试
```bash
# Windows
run_tests.bat

# Linux/macOS
chmod +x run_tests.sh
./run_tests.sh

# 或直接运行
python -m pytest tests/
```

#### 运行特定测试
```bash
# 测试核心功能
python tests/test_core.py

# 测试模板功能
python tests/test_template_standalone.py
```

#### 创建测试数据
```bash
python tests/create_test_data.py
```

### 添加新功能

#### 1. 添加UI组件
```python
# 在 ui/ 目录创建新文件
class NewFeaturePanel(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # UI布局代码
        pass
```

#### 2. 添加核心逻辑
```python
# 在 core/ 目录扩展现有引擎
class CompareEngine:
    def new_comparison_method(self, data):
        # 新的比对逻辑
        pass
```

#### 3. 添加工具函数
```python
# 在 utils/ 目录创建或扩展工具
def new_utility_function(param):
    """
    功能描述
    
    Args:
        param: 参数说明
    
    Returns:
        返回值说明
    """
    pass
```

#### 4. 添加配置项
```python
# 在 config/settings.py 添加常量
NEW_FEATURE_CONFIG = {
    "option1": "value1",
    "option2": "value2"
}
```

### 调试技巧

#### 1. 启用调试日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 查看中间数据
```python
# 在 compare_engine.py 添加临时输出
print(f"调试: merged_df形状 = {merged_df.shape}")
print(merged_df.head())
```

#### 3. 使用断点
```python
import pdb; pdb.set_trace()  # 在需要的位置插入
```

### 常见问题排查

#### 问题1: 导入文件失败
**检查项**:
- 文件路径是否包含特殊字符
- 文件是否被其他程序占用
- Excel格式是否为.xlsx/.xls/.xlsm

#### 问题2: 透视列为空
**检查项**:
- 系统表是否包含透视列字段
- 透视列是否选择正确
- 数据是否有空值

#### 问题3: 导出失败
**检查项**:
- 是否有写入权限
- 目标文件是否已打开
- 磁盘空间是否充足

#### 问题4: 模板无法加载
**检查项**:
- config_templates.json是否存在
- JSON格式是否正确
- 模板ID是否唯一

---

## 文件说明

### 配置文件
- **config_templates.json**: 保存的模板配置（自动创建）
- **settings.py**: 全局常量和颜色定义

### 数据文件
- **测试数据**: tests/data/ 目录
- **用户数据**: 用户选择的Excel文件（不保存在项目内）

### 日志文件
- 当前版本不生成日志文件
- 可在代码中添加logging配置启用日志

---

## 性能指标

### 数据处理能力
- **小数据集** (< 1000行): < 1秒
- **中数据集** (1000-10000行): 1-5秒
- **大数据集** (10000-100000行): 5-30秒
- **超大数据集** (> 100000行): 30秒以上（建议分批处理）

### 内存占用
- **基础应用**: ~50MB
- **处理1万行**: ~100MB
- **处理10万行**: ~500MB

### 优化建议
1. 使用筛选条件减少数据量
2. 避免过多透视列（建议≤5个）
3. 大数据集分批处理
4. 定期清理旧的配置模板

---

## 兼容性

### Python版本
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ❌ Python 3.9 及以下（未测试）

### 操作系统
- ✅ Windows 10/11
- ✅ macOS 10.14+
- ✅ Ubuntu 20.04+
- ⚠ 其他Linux发行版（需测试）

### Excel版本
- ✅ Microsoft Excel 2016+
- ✅ WPS Office（部分功能受限）
- ✅ LibreOffice Calc（导入导出正常）
- ⚠ Excel 2010及更早版本（需安装xlrd）

---

## 许可证

本项目采用 MIT 许可证。

---

## 联系方式

- **项目地址**: https://github.com/yourusername/SupplyChain-Reconciler-Plus
- **问题反馈**: 请在GitHub Issues提交
- **功能建议**: 欢迎提交Pull Request

---

## 致谢

感谢以下开源项目的支持：
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) - 现代化UI框架
- [pandas](https://pandas.pydata.org/) - 数据处理库
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel操作库

---

**最后更新**: 2025年12月15日  
**文档版本**: 1.0
