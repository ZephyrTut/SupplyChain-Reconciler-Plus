"""筛选例外保留逻辑测试"""
import unittest
import pandas as pd

from core.compare_engine import CompareEngine


class TestFilterExceptions(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "库存地点名称": ["湖州仓", "武义仓", "上海仓", "杭州仓"],
                "供应商名称": ["甲公司", "为鼎供应", "乙公司", "为鼎"]
            }
        )

    def test_exception_or_keeps_vendor(self):
        """主筛选排除湖州/武义，例外保留为鼎"""
        filters = [("库存地点名称", "NOT_CONTAINS", "湖州,武义")]
        exceptions = [("供应商名称", "CONTAINS", "为鼎")]

        out = CompareEngine.apply_filters(self.df, filters, exceptions)
        result = set(out["库存地点名称"].tolist())

        self.assertIn("上海仓", result)
        self.assertIn("杭州仓", result)
        self.assertIn("武义仓", result)  # 因为例外命中“为鼎供应”
        self.assertNotIn("湖州仓", result)

    def test_no_exception_backward_compatible(self):
        """无例外时行为与原AND一致"""
        filters = [("库存地点名称", "NOT_CONTAINS", "湖州,武义")]
        out = CompareEngine.apply_filters(self.df, filters, None)

        self.assertEqual(set(out["库存地点名称"]), {"上海仓", "杭州仓"})

    def test_multiple_exceptions_or(self):
        """多个例外规则按OR生效"""
        filters = [("库存地点名称", "NOT_CONTAINS", "湖州,武义")]
        exceptions = [
            ("供应商名称", "CONTAINS", "为鼎"),
            ("库存地点名称", "CONTAINS", "湖州")
        ]
        out = CompareEngine.apply_filters(self.df, filters, exceptions)

        self.assertEqual(set(out["库存地点名称"]), {"湖州仓", "武义仓", "上海仓", "杭州仓"})

    def test_scoped_exception_only_bypasses_one_filter(self):
        """例外仅覆盖指定筛选，其他筛选仍生效"""
        df = pd.DataFrame(
            {
                "库存地点名称": ["上海仓", "湖州仓", "上海仓", "湖州仓"],
                "供应商名称": ["为鼎", "为鼎", "甲公司", "甲公司"]
            }
        )
        filters = [
            ("供应商名称", "NOT_IN_LIST", "为鼎"),
            ("库存地点名称", "NOT_CONTAINS", "湖州")
        ]
        exceptions = [
            {
                "column": "供应商名称",
                "operator": "EQUALS",
                "value": "为鼎",
                "target_filter": {
                    "column": "供应商名称",
                    "operator": "NOT_IN_LIST",
                    "value": "为鼎"
                }
            }
        ]

        out = CompareEngine.apply_filters(df, filters, exceptions)
        self.assertEqual(set(out["库存地点名称"]), {"上海仓"})


if __name__ == "__main__":
    unittest.main()
