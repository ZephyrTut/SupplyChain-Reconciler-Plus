"""自动映射系统零件号测试"""
import unittest
import pandas as pd

from core.compare_engine import CompareEngine


class TestAutoMapSystemParts(unittest.TestCase):
    def setUp(self):
        self.config = {
            "enabled": True,
            "suffixes": ["-001", "-002"],
            "system": {
                "supplier_col": "供应商",
                "order_col": "订单号",
                "part_col": "零件号"
            },
            "manual": {
                "supplier_col": "供应商",
                "order_col": "订单号",
                "part_col": "零件号"
            }
        }

    def test_single_match_maps_suffix(self):
        manual_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-001"]
            }
        )
        system_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-000"]
            }
        )

        mapped_df, stats = CompareEngine.auto_map_system_parts(
            system_df,
            manual_df,
            self.config
        )

        self.assertEqual(mapped_df.loc[0, "零件号"], "P-001")
        self.assertEqual(stats["candidates"], 1)
        self.assertEqual(stats["matched"], 1)
        self.assertEqual(stats["ambiguous"], 0)
        self.assertEqual(stats["unmatched"], 0)

    def test_ambiguous_suffix_keeps_original(self):
        manual_df = pd.DataFrame(
            {
                "供应商": ["A", "A"],
                "订单号": ["O1", "O1"],
                "零件号": ["P-001", "P-002"]
            }
        )
        system_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-000"]
            }
        )

        mapped_df, stats = CompareEngine.auto_map_system_parts(
            system_df,
            manual_df,
            self.config
        )

        self.assertEqual(mapped_df.loc[0, "零件号"], "P-000")
        self.assertEqual(stats["candidates"], 1)
        self.assertEqual(stats["matched"], 0)
        self.assertEqual(stats["ambiguous"], 1)
        self.assertEqual(stats["unmatched"], 0)

    def test_unmatched_suffix_keeps_original(self):
        manual_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["X-001"]
            }
        )
        system_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-000"]
            }
        )

        mapped_df, stats = CompareEngine.auto_map_system_parts(
            system_df,
            manual_df,
            self.config
        )

        self.assertEqual(mapped_df.loc[0, "零件号"], "P-000")
        self.assertEqual(stats["candidates"], 1)
        self.assertEqual(stats["matched"], 0)
        self.assertEqual(stats["ambiguous"], 0)
        self.assertEqual(stats["unmatched"], 1)

    def test_output_column_preserves_original(self):
        manual_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-001"]
            }
        )
        system_df = pd.DataFrame(
            {
                "供应商": ["A"],
                "订单号": ["O1"],
                "零件号": ["P-000"]
            }
        )

        mapped_df, _ = CompareEngine.auto_map_system_parts(
            system_df,
            manual_df,
            self.config,
            output_column="__MAPPED_PART__"
        )

        self.assertEqual(mapped_df.loc[0, "零件号"], "P-000")
        self.assertEqual(mapped_df.loc[0, "__MAPPED_PART__"], "P-001")

    def test_supplier_prefix_normalization(self):
        manual_df = pd.DataFrame(
            {
                "供应商": ["东莞市硅翔绝缘材料有限公司"],
                "订单号": ["O1"],
                "零件号": ["P-001"]
            }
        )
        system_df = pd.DataFrame(
            {
                "供应商": ["1DC-东莞市硅翔绝缘材料有限公司"],
                "订单号": ["O1"],
                "零件号": ["P-000"]
            }
        )

        mapped_df, stats = CompareEngine.auto_map_system_parts(
            system_df,
            manual_df,
            self.config
        )

        self.assertEqual(mapped_df.loc[0, "零件号"], "P-001")
        self.assertEqual(stats["matched"], 1)


if __name__ == "__main__":
    unittest.main()
