"""清洗去中文保留关键词测试"""
import unittest
import pandas as pd

from core.compare_engine import CompareEngine


class TestCleanKeywords(unittest.TestCase):
    def test_keep_full_chinese_and_keyword(self):
        df = pd.DataFrame({
            "备注": ["换单A01", "全中文备注", "ABC123", None]
        })
        rules = [
            {
                "column": "备注",
                "mode": "去中文保留关键词",
                "keywords": ["换单"]
            }
        ]

        out = CompareEngine.clean_column(df, rules)
        self.assertEqual(out.loc[0, "备注"], "换单A01")
        self.assertEqual(out.loc[1, "备注"], "全中文备注")
        self.assertEqual(out.loc[2, "备注"], "ABC123")
        self.assertTrue(pd.isna(out.loc[3, "备注"]))


if __name__ == "__main__":
    unittest.main()
