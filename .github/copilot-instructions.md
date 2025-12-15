# SupplyChain-Reconciler-Plus

供应链智能对账系统 - Python桌面应用

## 技术栈
- Python 3.10+
- ttkbootstrap (现代化Tkinter UI)
- pandas (数据处理)
- openpyxl (Excel读写，支持背景颜色)

## 项目结构
```
SupplyChain-Reconciler-Plus/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py        # 常量、颜色、字段定义
├── core/                   # 核心逻辑
│   ├── __init__.py
│   ├── compare_engine.py  # 数据比对引擎
│   └── export_engine.py   # Excel导出引擎
├── ui/                     # 界面模块
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   ├── config_panel.py    # 配置面板
│   └── preview_panel.py   # 预览面板
└── utils/                  # 工具模块
    ├── __init__.py
    ├── excel_utils.py     # Excel工具
    └── storage.py         # 配置存储
```

## 功能特性
- [x] 双表对账（手工表 vs 系统表）
- [x] 复合主键配置
- [x] 透视列（Pivot）支持
- [x] 动态差值公式配置
- [x] 配置模板保存/加载
- [x] 实时匹配预览（左右表并排）
- [x] 导出带颜色背景的Excel结果
