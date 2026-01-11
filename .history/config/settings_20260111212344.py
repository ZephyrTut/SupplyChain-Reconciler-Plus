"""
配置常量 - 颜色、字段定义等
"""

# ============== 应用配置 ==============
APP_NAME = "供应链智能对账系统"
APP_VERSION = "1.4.3"
WINDOW_SIZE = "1400x900"

# ============== Excel 样式配置 ==============
# 使用 openpyxl 的 ARGB 格式 (AARRGGBB)
EXCEL_COLORS = {
    "match": "FFD1FAE5",        # 绿色 - 一致
    "diff_pos": "FFD9F99D",     # 浅黄绿 - 手工 > 系统
    "diff_neg": "FFBFDBFE",     # 浅蓝 - 手工 < 系统
    "missing": "FFFECACA",      # 浅红 - 缺失
    "header": "FFE2E8F0",       # 表头灰色
}

# ============== 比对状态符号 ==============
MATCH_STATUS = "✓"      # 一致
DIFF_STATUS = "↕"       # 差异
MISSING_STATUS = "✗"    # 缺失

# ============== UI 配色约束（浅色主题） ==============
# 注意：所有UI组件必须遵循此配色规范，确保可读性
#
# 【背景色】
#   - 主背景: #f5f5f5 (浅灰)
#   - 卡片/面板背景: #ffffff (白色)
#   - 折叠区标题: #e8e8e8 (灰色)
#   - 输入框/下拉框: #ffffff (白色)
#
# 【文字色】
#   - 主要文字: #333333 (深灰，用于正文、标签)
#   - 次要文字: #666666 (中灰，用于提示、说明)
#   - 占位符: #999999 (浅灰)
#   - 链接/强调: #1976D2 (蓝色)
#
# 【边框色】
#   - 默认边框: #cccccc
#   - 悬停边框: #2196F3 (蓝色)
#   - 分割线: #e0e0e0
#
# 【禁止】
#   - ❌ 深色背景 + 深色文字
#   - ❌ 浅色背景 + 浅色文字
#   - ❌ 未经测试的配色组合

UI_COLORS = {
    # 背景色
    "bg_main": "#f5f5f5",           # 主背景
    "bg_card": "#ffffff",           # 卡片背景
    "bg_header": "#e8e8e8",         # 标题栏背景
    "bg_input": "#ffffff",          # 输入框背景
    
    # 文字色
    "text_primary": "#333333",      # 主要文字
    "text_secondary": "#666666",    # 次要文字
    "text_placeholder": "#999999",  # 占位符
    "text_accent": "#1976D2",       # 强调色/链接
    
    # 边框色
    "border_default": "#cccccc",    # 默认边框
    "border_hover": "#2196F3",      # 悬停边框
    "border_divider": "#e0e0e0",    # 分割线
    
    # 状态色
    "success": "#4CAF50",           # 成功/一致
    "warning": "#FF9800",           # 警告/差异
    "error": "#f44336",             # 错误/缺失
}

# UI 颜色配置 (Hex格式，用于PyQt6) - 状态相关
HEADER_BG = "#E3F2FD"       # 表头 - 浅蓝
HEADER_FG = "#1565C0"       # 表头文字 - 深蓝
MATCH_BG = "#E8F5E9"        # 一致 - 浅绿
MATCH_FG = "#2E7D32"        # 一致文字 - 深绿
DIFF_BG = "#FFF9C4"         # 差异 - 浅黄
DIFF_FG = "#F57F17"         # 差异文字 - 深橙
MISSING_BG = "#FFEBEE"      # 缺失 - 浅红
MISSING_FG = "#C62828"      # 缺失文字 - 深红

# ============== 比对状态 ==============
COMPARE_STATUS = {
    "match": "✓ 一致",
    "diff": "↕ 差异",
    "system_only": "✗ 手工缺失",
    "manual_only": "✗ 系统缺失",
}

# ============== 字段角色 ==============
FIELD_ROLES = {
    "key1": "主键1 (如: 订单号)",
    "key2": "主键2 (如: 料号)",
    "manual_qty": "手工数量",
    "system_qty": "系统数量",
    "status": "状态列 (透视)",
}

# ============== 默认字段别名 ==============
DEFAULT_ALIASES = {
    "key1": ["订单号", "到货单号", "ASN", "单号", "order", "asn_no"],
    "key2": ["料号", "零件号", "物料号", "SKU", "part_no", "material"],
    "manual_qty": ["数量", "到货数量", "qty", "quantity"],
    "system_qty": ["系统数量", "完成数量", "actual_qty"],
    "status": ["状态", "完成状态", "status", "state"],
}

# ============== 筛选操作符 ==============
FILTER_OPERATORS = {
    "EQUALS": "=",
    "NOT_EQUALS": "!=",
    "CONTAINS": "包含",
}

# ============== 存储路径 ==============
CONFIG_FILE = "reconciler_config.json"
TEMPLATES_FILE = "reconciler_templates.json"
