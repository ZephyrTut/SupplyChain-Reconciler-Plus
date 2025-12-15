# SupplyChain-Reconciler-Plus

供应链智能对账系统 - 基于Python的桌面应用

**当前版本**: v1.2.0 | **更新日期**: 2025-12-15

## ✨ 最新更新

### v1.2.0 (2025-12-15)
**Bug修复:**
- ✅ 修复预览更新TypeError ('str' object has no attribute 'get')
- ✅ 修复下拉框滚动联动主滚动条
- ✅ 修复下拉框选中值随滚动变化
- ✅ 增强错误处理和异常捕获

**新增功能:**
- ✨ 手工表/系统表样例显示区
- ✨ 活动Excel检测增强（工作表名）
- ✨ 拖拽分区域导入（手工表区/系统表区）
- ✨ Combobox滚轮事件隔离

📖 详细说明: [Bug修复总结](docs/Bug修复总结_v1.2.0.md)

## 🎯 核心功能
- 🔄 双表对账（手工表 vs 系统表）
- 🔑 复合主键配置
- 📊 透视列（Pivot）支持
- 📐 动态差值公式
- 💾 配置模板
- 👁️ 实时匹配预览
- 📋 彩色Excel导出

## 安装
```bash
pip install -r requirements.txt
```

## 运行
```bash
python main.py
```
