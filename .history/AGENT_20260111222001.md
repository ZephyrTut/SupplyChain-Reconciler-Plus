# 🤖 AI Agent 开发约束文档

**SupplyChain-Reconciler-Plus - AI Agent 专用指南**

---

## ⚠️ 核心约束（必读）

### 1. 修改功能前必须先读取文档

**强制要求**: 在修改任何功能代码之前，**必须先读取** `docs/` 目录下的相关文档。

| 修改内容 | 必须先读取的文档 |
|---------|----------------|
| 数据导入相关 | `docs/03-数据导入.md` |
| 主键配置相关 | `docs/04-主键配置.md` |
| 数据清洗相关 | `docs/05-数据清洗.md` |
| 筛选条件相关 | `docs/06-筛选条件.md` |
| 透视聚合相关 | `docs/07-透视聚合.md` |
| 差值公式相关 | `docs/08-差值公式.md` |
| 导出功能相关 | `docs/09-结果导出.md` |
| 主窗口界面相关 | `docs/10-主窗口界面.md` |
| 配置面板相关 | `docs/11-配置面板.md` |
| 结果预览相关 | `docs/12-结果预览.md` |
| 对话框相关 | `docs/13-对话框组件.md` |
| CompareEngine | `docs/14-核心引擎API.md` |
| ExportEngine | `docs/14-核心引擎API.md` |
| UI组件 | `docs/15-UI组件API.md` |
| 工具函数 | `docs/16-工具函数API.md` |
| 配置常量 | `docs/17-配置常量.md` |
| 模板管理 | `docs/18-模板管理.md` |

### 2. 修改完成后必须同步更新文档

**强制要求**: 完成功能修改后，必须同步更新相关文档：

```
修改代码 → 更新 docs/ 对应文档 → 更新 PROJECT_OVERVIEW.md (如需) → 更新 README.md (如需)
```

---

## 📁 文档体系说明

### 文档目录结构

```
docs/
├── README.md              # 文档索引
├── 01-快速开始.md          # 用户入门
├── 02-安装配置.md          # 环境配置
├── 03-数据导入.md          # 数据导入功能
├── 04-主键配置.md          # 主键配置功能
├── 05-数据清洗.md          # 数据清洗功能
├── 06-筛选条件.md          # 筛选条件功能
├── 07-透视聚合.md          # 透视聚合功能
├── 08-差值公式.md          # 差值公式功能
├── 09-结果导出.md          # 导出功能
├── 10-主窗口界面.md        # 主窗口UI
├── 11-配置面板.md          # 配置面板UI
├── 12-结果预览.md          # 结果预览UI
├── 13-对话框组件.md        # 对话框UI
├── 14-核心引擎API.md       # Core层API
├── 15-UI组件API.md         # UI层API
├── 16-工具函数API.md       # Utils层API
├── 17-配置常量.md          # Config层
├── 18-模板管理.md          # 模板功能
└── 19-常见问题.md          # FAQ
```

### 文档层级

| 层级 | 文档 | 用途 |
|------|------|------|
| L1-顶层 | `PROJECT_OVERVIEW.md` | 项目全局概述 |
| L1-顶层 | `README.md` | 快速开始 |
| L2-约束 | `.github/copilot-instructions.md` | 开发约束 |
| L2-约束 | `AGENT.md` (本文件) | Agent专用约束 |
| L3-详细 | `docs/*.md` | 功能详细文档 |

---

## 🔄 文档同步规则

### 规则1: docs/ 为权威来源

`docs/` 目录下的文档是功能说明的**权威来源**，其他文档从这里同步。

```
docs/*.md (权威) → PROJECT_OVERVIEW.md (摘要)
docs/*.md (权威) → README.md (精简)
docs/*.md (权威) → .github/copilot-instructions.md (约束)
```

### 规则2: 修改触发更新

| 修改类型 | docs/ | PROJECT_OVERVIEW | README | copilot-instructions |
|---------|-------|-----------------|--------|---------------------|
| 新增功能 | ✅ 必须 | ✅ 必须 | ✅ 必须 | ✅ 必须 |
| 修改功能 | ✅ 必须 | ⚠️ 视情况 | ⚠️ 视情况 | ⚠️ 视情况 |
| Bug修复 | ❌ 通常不需要 | ❌ 不需要 | ❌ 不需要 | ❌ 不需要 |
| 重构代码 | ⚠️ API变化时 | ⚠️ API变化时 | ❌ 不需要 | ⚠️ 约束变化时 |

### 规则3: 版本号同步

修改功能后，以下位置的版本号需要同步：
- `config/settings.py` → `APP_VERSION`
- `main.py` → docstring中的版本
- `PROJECT_OVERVIEW.md` → 顶部版本
- `README.md` → 顶部版本
- `.github/copilot-instructions.md` → 顶部版本
- `AGENT.md` → 底部版本

---

## 📝 文档更新示例

### 示例1: 修改筛选条件功能

```
1. 读取文档
   → read_file: docs/06-筛选条件.md

2. 理解现有实现
   → read_file: core/compare_engine.py (apply_filters方法)

3. 修改代码
   → 修改 apply_filters 方法

4. 更新文档
   → 更新 docs/06-筛选条件.md
   → 更新 docs/14-核心引擎API.md (如API签名变化)
   → 检查 PROJECT_OVERVIEW.md 是否需要更新
```

### 示例2: 新增UI组件

```
1. 读取文档
   → read_file: docs/15-UI组件API.md
   → read_file: docs/17-配置常量.md (UI颜色)

2. 开发新组件
   → 遵循 UI配色约束
   → 使用 NoScrollComboBox 等现有组件

3. 更新文档
   → 更新 docs/15-UI组件API.md (新增组件说明)
   → 更新相关功能文档
```

---

## ⛔ 禁止事项

### 1. 禁止跳过文档直接修改

```
❌ 错误流程: 收到需求 → 直接修改代码
✅ 正确流程: 收到需求 → 读取相关文档 → 修改代码 → 更新文档
```

### 2. 禁止文档与代码不一致

```
❌ 错误: 修改了代码但不更新文档
❌ 错误: 文档描述的功能与代码实现不符
✅ 正确: 代码和文档始终保持同步
```

### 3. 禁止破坏文档结构

```
❌ 错误: 删除文档中的章节
❌ 错误: 改变文档的编号顺序
✅ 正确: 在现有结构内更新内容
```

---

## 🔍 快速查询表

### 按模块查找文档

| 代码文件 | 对应文档 |
|---------|---------|
| `core/compare_engine.py` | `docs/14-核心引擎API.md` |
| `core/export_engine.py` | `docs/14-核心引擎API.md`, `docs/09-结果导出.md` |
| `ui/qt_main_window.py` | `docs/10-主窗口界面.md`, `docs/15-UI组件API.md` |
| `ui/qt_config_panel.py` | `docs/11-配置面板.md`, `docs/15-UI组件API.md` |
| `ui/qt_result_preview.py` | `docs/12-结果预览.md`, `docs/15-UI组件API.md` |
| `ui/qt_dialogs.py` | `docs/13-对话框组件.md` |
| `utils/excel_utils.py` | `docs/16-工具函数API.md` |
| `utils/storage.py` | `docs/16-工具函数API.md`, `docs/18-模板管理.md` |
| `config/settings.py` | `docs/17-配置常量.md` |

### 按功能查找文档

| 功能 | 对应文档 |
|------|---------|
| Excel导入 | `docs/03-数据导入.md` |
| 复合主键 | `docs/04-主键配置.md` |
| 正则清洗 | `docs/05-数据清洗.md` |
| 条件筛选 | `docs/06-筛选条件.md` |
| 透视聚合 | `docs/07-透视聚合.md` |
| 差值计算 | `docs/08-差值公式.md` |
| Excel导出 | `docs/09-结果导出.md` |
| 模板管理 | `docs/18-模板管理.md` |

---

## ✅ 检查清单

修改代码前后，使用此清单确认：

### 修改前
- [ ] 已读取相关功能文档 (`docs/XX-功能名.md`)
- [ ] 已读取相关API文档 (`docs/14/15/16-API.md`)
- [ ] 已理解现有实现逻辑

### 修改后
- [ ] 代码符合约束规范
- [ ] 已更新 `docs/` 相关文档
- [ ] 已检查 `PROJECT_OVERVIEW.md` 是否需要更新
- [ ] 已检查 `README.md` 是否需要更新
- [ ] 版本号已同步（如有需要）

---

**文档版本**: 1.4.3  
**最后更新**: 2026年1月11日  
**适用对象**: GitHub Copilot, Cursor, Claude, ChatGPT 等 AI Agent
