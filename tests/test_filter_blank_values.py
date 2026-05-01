"""筛选空白值逻辑测试"""
import unittest
import pandas as pd

from core.compare_engine import CompareEngine
from config.settings import BLANK_TOKEN


class TestFilterBlankValues(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "备注": ["", "   ", None, "正常", "含空"]
            }
        )

    def test_equals_blank(self):
        filters = [("备注", "EQUALS", BLANK_TOKEN)]
        out = CompareEngine.apply_filters(self.df, filters, None)
        self.assertEqual(len(out), 3)

    def test_not_equals_blank(self):
        filters = [("备注", "NOT_EQUALS", BLANK_TOKEN)]
        out = CompareEngine.apply_filters(self.df, filters, None)
        self.assertEqual(set(out["备注"].tolist()), {"正常", "含空"})

    def test_in_list_blank_and_value(self):
        filters = [("备注", "IN_LIST", f"{BLANK_TOKEN},正常")]
        out = CompareEngine.apply_filters(self.df, filters, None)
        self.assertEqual(len(out), 4)

    def test_not_in_list_blank(self):
        filters = [("备注", "NOT_IN_LIST", BLANK_TOKEN)]
        out = CompareEngine.apply_filters(self.df, filters, None)
        self.assertEqual(set(out["备注"].tolist()), {"正常", "含空"})

    def test_contains_blank(self):
        filters = [("备注", "CONTAINS", BLANK_TOKEN)]
        out = CompareEngine.apply_filters(self.df, filters, None)
        self.assertEqual(len(out), 3)


if __name__ == "__main__":
    unittest.main()
