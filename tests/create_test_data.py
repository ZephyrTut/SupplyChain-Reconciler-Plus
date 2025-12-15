"""
创建测试数据 - 生成Excel测试文件
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
import os


def create_manual_table():
    """创建手工表测试数据"""
    data = {
        "订单编号": ["PO001", "PO002", "PO003", "PO004", "PO005", "PO006", "PO007"],
        "物料编码": ["SKU-A", "SKU-B", "SKU-C", "SKU-A", "SKU-D", "SKU-E", "SKU-F"],
        "手工数量": [100, 200, 150, 80, 300, 120, 90],
        "手工金额": [1000, 4000, 3000, 800, 6000, 2400, 1800],
        "备注": ["正常", "正常", "正常", "正常", "正常", "仅手工有", "正常"]
    }
    return pd.DataFrame(data)


def create_system_table():
    """创建系统表测试数据"""
    data = {
        "订单编号": [
            "PO001", "PO001", "PO001",  # 同一订单多行（需要聚合）
            "PO002", "PO002",
            "PO003", "PO003", "PO003",
            "PO004", "PO004",
            "PO007", "PO007",
            "PO008",  # 仅系统有
        ],
        "物料编码": [
            "SKU-A", "SKU-A", "SKU-A",
            "SKU-B", "SKU-B",
            "SKU-C", "SKU-C", "SKU-C",
            "SKU-A", "SKU-A",
            "SKU-F", "SKU-F",
            "SKU-G",
        ],
        "状态": [
            "已发货", "已关闭", "待审核",
            "已发货", "已关闭",
            "已发货", "已发货", "已关闭",
            "已发货", "待审核",
            "已发货", "已关闭",
            "已发货",
        ],
        "系统数量": [
            50, 30, 20,  # 总计100 = 手工一致
            100, 50,     # 总计150 ≠ 手工200（有差异）
            80, 50, 20,  # 总计150 = 手工一致
            40, 40,      # 总计80 = 手工一致
            50, 50,      # 总计100 ≠ 手工90（有差异）
            200,
        ],
        "系统金额": [
            500, 300, 200,
            2000, 1000,
            1600, 1000, 400,
            400, 400,
            1000, 1000,
            4000,
        ]
    }
    return pd.DataFrame(data)


def create_test_files(output_dir="tests/data"):
    """创建测试Excel文件"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建手工表
    manual_df = create_manual_table()
    manual_path = os.path.join(output_dir, "手工表.xlsx")
    manual_df.to_excel(manual_path, index=False, sheet_name="Sheet1")
    print(f"✓ 已创建: {manual_path}")
    print(f"  行数: {len(manual_df)}")
    
    # 创建系统表
    system_df = create_system_table()
    system_path = os.path.join(output_dir, "系统表.xlsx")
    system_df.to_excel(system_path, index=False, sheet_name="数据")
    print(f"✓ 已创建: {system_path}")
    print(f"  行数: {len(system_df)}")
    
    return manual_path, system_path


def print_test_scenario():
    """打印测试场景说明"""
    print("\n" + "="*60)
    print("测试数据说明")
    print("="*60)
    print("\n【主键配置】")
    print("  - 手工表主键: 订单编号 + 物料编码")
    print("  - 系统表主键: 订单编号 + 物料编码")
    
    print("\n【透视配置】")
    print("  - 系统表透视列: 状态")
    print("  - 透视值: 已发货, 已关闭, 待审核")
    
    print("\n【预期结果】")
    print("  PO001-SKU-A: ✓ 一致 (手工100 = 系统总计100)")
    print("  PO002-SKU-B: ⚠ 有差异 (手工200 ≠ 系统总计150, 差值50)")
    print("  PO003-SKU-C: ✓ 一致 (手工150 = 系统总计150)")
    print("  PO004-SKU-A: ✓ 一致 (手工80 = 系统总计80)")
    print("  PO005-SKU-D: ✗ 仅手工有 (系统缺)")
    print("  PO006-SKU-E: ✗ 仅手工有 (系统缺)")
    print("  PO007-SKU-F: ⚠ 有差异 (手工90 ≠ 系统总计100, 差值-10)")
    print("  PO008-SKU-G: ✗ 仅系统有 (手工缺)")
    
    print("\n【差值公式测试】")
    print("  公式: 手工数量 - (系统总计 - 已关闭)")
    print("  PO001-SKU-A: 100 - (100-30) = 30")
    print("  PO002-SKU-B: 200 - (150-50) = 100")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    create_test_files()
    print_test_scenario()
