"""
配置常量 - 颜色、字段定义等
"""

# ============== 应用配置 ==============
APP_NAME = "供应链智能对账系统"
APP_VERSION = "1.1.0"
WINDOW_SIZE = "1400x900"

# ============== UI 主题与字体 ==============
# 暗黑首选：cyborg（极简），其余为降级回退
UI_THEME = "cyborg"
UI_THEME_FALLBACKS = ["superhero", "darkly", "solar"]

# 屏幕友好的无衬线/等宽字体配置（尺寸较默认放大 1-2 磅）
UI_FONT_BASE = ("Segoe UI", 11)
UI_FONT_BASE_LARGE = ("Segoe UI", 13, "bold")
UI_FONT_TITLE = ("Segoe UI", 17, "bold")
UI_FONT_MONO = ("Consolas", 11)
UI_FONT_SMALL = ("Segoe UI", 10)

# 组件尺寸微调
TREE_ROW_HEIGHT = 28
CONTROL_PADDING = 8
CARD_PADDING = 10

# ============== Excel 样式配置 ==============
# 使用 openpyxl 的 ARGB 格式 (AARRGGBB)
EXCEL_COLORS = {
    "match": "FFD1FAE5",        # 绿色 - 一致
    "diff_pos": "FFD9F99D",     # 浅黄绿 - 手工 > 系统
    "diff_neg": "FFBFDBFE",     # 浅蓝 - 手工 < 系统
    "missing": "FFFECACA",      # 浅红 - 缺失
    "header": "FFE2E8F0",       # 表头灰色
}

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
