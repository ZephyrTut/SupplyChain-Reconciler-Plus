"""
配置常量 - 颜色、字段定义等
"""

# ============== 应用配置 ==============
APP_NAME = "供应链智能对账系统"
APP_VERSION = "1.4.0"
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

# ============== UI 颜色配置 (Hex格式，用于PyQt6) ==============
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
