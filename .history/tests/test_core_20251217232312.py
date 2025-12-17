"""
单元测试 - 测试核心功能
"""
import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import CompareEngine, ExportEngine
from utils import load_excel, get_sheet_names
from config import COMPARE_STATUS


class TestCompareEngine(unittest.TestCase):
    """测试比对引擎"""
    
    def setUp(self):
        """准备测试数据"""
        self.manual_data = {
            "订单号": ["A001", "A002", "A003"],
            "物料": ["SKU1", "SKU2", "SKU3"],
            "数量": [100, 200, 150]
        }
        self.manual_df = pd.DataFrame(self.manual_data)
        
        self.system_data = {
            "订单号": ["A001", "A002", "A004"],
            "物料": ["SKU1", "SKU2", "SKU4"],
            "数量": [100, 250, 300]
        }
        self.system_df = pd.DataFrame(self.system_data)
    
    def test_make_key(self):
        """测试主键生成"""
        df = CompareEngine.make_key(self.manual_df, ["订单号", "物料"])
        
        self.assertIn("__KEY__", df.columns)
        self.assertEqual(df["__KEY__"].iloc[0], "A001 | SKU1")
        self.assertEqual(len(df), len(self.manual_df))
    
    def test_aggregate_data_simple(self):
        """测试简单聚合"""
        df = CompareEngine.make_key(self.manual_df, ["订单号", "物料"])
        agg_df, pivot_values = CompareEngine.aggregate_data(
            df, "__KEY__", ["数量"]
        )
        
        self.assertEqual(len(agg_df), 3)
        self.assertIn("数量", agg_df.columns)
        self.assertEqual(len(pivot_values), 0)
    
    def test_aggregate_with_pivot(self):
        """测试带透视的聚合"""
        # 创建带状态列的数据
        data = {
            "__KEY__": ["A001", "A001", "A002"],
            "状态": ["已发货", "已关闭", "已发货"],
            "数量": [50, 30, 100]
        }
        df = pd.DataFrame(data)
        
        agg_df, pivot_values = CompareEngine.aggregate_data(
            df, "__KEY__", ["数量"], pivot_col="状态"
        )

        # 当前实现：透视列名为透视值本身，并提供“系统总计”
        self.assertIn("已发货", agg_df.columns)
        self.assertIn("已关闭", agg_df.columns)
        self.assertIn("系统总计", agg_df.columns)

        a001_row = agg_df[agg_df["__KEY__"] == "A001"].iloc[0]
        self.assertEqual(a001_row["系统总计"], 80)
        self.assertIn("已发货", pivot_values)
        self.assertIn("已关闭", pivot_values)
    
    def test_merge_and_compare(self):
        """测试合并比对"""
        manual_df = CompareEngine.make_key(self.manual_df, ["订单号", "物料"])
        system_df = CompareEngine.make_key(self.system_df, ["订单号", "物料"])
        
        manual_agg, _ = CompareEngine.aggregate_data(manual_df, "__KEY__", ["数量"])
        system_agg, _ = CompareEngine.aggregate_data(system_df, "__KEY__", ["数量"])
        
        result = CompareEngine.merge_and_compare(
            manual_agg, system_agg, "__KEY__", "数量", "数量"
        )
        
        self.assertIn("比对状态", result.columns)
        self.assertIn("差值", result.columns)
        
        # A001应该一致
        a001_row = result[result["__KEY__"] == "A001 | SKU1"].iloc[0]
        self.assertEqual(a001_row["比对状态"], COMPARE_STATUS["match"])
        self.assertEqual(a001_row["差值"], 0)
        
        # A002应该有差异
        a002_row = result[result["__KEY__"] == "A002 | SKU2"].iloc[0]
        self.assertEqual(a002_row["比对状态"], COMPARE_STATUS["diff"])
        self.assertEqual(a002_row["差值"], -50)
    
    def test_diff_formula(self):
        """测试差值公式"""
        # 创建带透视的数据
        manual_data = pd.DataFrame({
            "__KEY__": ["A001"],
            "手工数量": [100]
        })
        
        system_data = pd.DataFrame({
            "__KEY__": ["A001"],
            "系统总计": [80],
            "已发货": [50],
            "已关闭": [30]
        })
        
        result = CompareEngine.merge_and_compare(
            manual_data, system_data, "__KEY__",
            "手工数量", "系统总计",
            diff_formula="手工数量 - (系统总计 - 已关闭)",
            pivot_values=["已发货", "已关闭"]
        )
        
        # 100 - (80 - 30) = 50
        self.assertEqual(result.iloc[0]["差值"], 50)


class TestExcelUtils(unittest.TestCase):
    """测试Excel工具"""
    
    @classmethod
    def setUpClass(cls):
        """创建测试文件"""
        cls.test_file = "tests/data/test_temp.xlsx"
        os.makedirs("tests/data", exist_ok=True)
        
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        df.to_excel(cls.test_file, index=False, sheet_name="TestSheet")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试文件"""
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)
    
    def test_get_sheet_names(self):
        """测试获取Sheet名称"""
        sheets = get_sheet_names(self.test_file)
        self.assertIn("TestSheet", sheets)
    
    def test_load_excel(self):
        """测试加载Excel"""
        df = load_excel(self.test_file, "TestSheet")
        self.assertEqual(len(df), 3)
        self.assertIn("A", df.columns)
        self.assertIn("B", df.columns)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """准备测试数据文件"""
        from tests.create_test_data import create_test_files
        cls.manual_path, cls.system_path = create_test_files()
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 加载数据
        manual_df = load_excel(self.manual_path, "Sheet1")
        system_df = load_excel(self.system_path, "数据")
        
        self.assertIsNotNone(manual_df)
        self.assertIsNotNone(system_df)
        
        # 2. 生成主键
        manual_with_key = CompareEngine.make_key(
            manual_df, ["订单编号", "物料编码"]
        )
        system_with_key = CompareEngine.make_key(
            system_df, ["订单编号", "物料编码"]
        )
        
        # 3. 聚合（系统表带透视）
        manual_agg, _ = CompareEngine.aggregate_data(
            manual_with_key, "__KEY__", ["手工数量"]
        )
        
        system_agg, pivot_values = CompareEngine.aggregate_data(
            system_with_key, "__KEY__", ["系统数量"],
            pivot_col="状态"
        )
        
        self.assertTrue(len(pivot_values) >= 2)  # 应该有多个状态
        self.assertIn("系统总计", system_agg.columns)
        
        # 4. 比对
        result = CompareEngine.merge_and_compare(
            manual_agg, system_agg, "__KEY__",
            "手工数量", "系统总计",
            pivot_values=pivot_values
        )
        
        # 验证结果
        self.assertIn("比对状态", result.columns)
        self.assertIn("差值", result.columns)
        
        # 应该有不同状态的数据
        status_counts = result["比对状态"].value_counts()
        self.assertTrue(len(status_counts) >= 2)
        
        # 导出测试
        output_path = "tests/data/test_result.xlsx"
        ExportEngine.export_results(
            output_path, result, pivot_values,
            {"key_columns": "订单编号+物料编码"}
        )
        
        self.assertTrue(os.path.exists(output_path))
        print(f"\n✓ 集成测试通过！结果已导出到: {output_path}")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestCompareEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestExcelUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "="*60)
    print(f"测试完成: 运行 {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
