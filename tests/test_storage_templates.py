"""
模板存储功能测试
"""
import os
import json
import unittest
import tempfile
from datetime import datetime
from pathlib import Path

from utils.storage import get_config_dir, get_templates_path, load_templates, save_template


class TestStorageTemplates(unittest.TestCase):
    """测试模板存储兼容性与保存稳定性"""

    def setUp(self):
        self._old_appdata = os.environ.get("APPDATA")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["APPDATA"] = self.temp_dir.name

    def tearDown(self):
        if self._old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self._old_appdata
        self.temp_dir.cleanup()

    def test_config_dir_uses_plus_name(self):
        """配置目录应使用 SupplyChain-Reconciler-Plus"""
        config_dir = get_config_dir()
        self.assertEqual(config_dir.name, "SupplyChain-Reconciler-Plus")

    def test_load_templates_supports_wrapped_format(self):
        """兼容 {'templates': [...]} 结构"""
        templates_path = get_templates_path()
        templates_path.parent.mkdir(parents=True, exist_ok=True)

        wrapped = {
            "templates": [
                {
                    "id": "1",
                    "name": "包装格式模板",
                    "config": {"difference_formula": "C - B"},
                    "timestamp": "2026-03-16 10:00:00"
                }
            ]
        }
        templates_path.write_text(json.dumps(wrapped, ensure_ascii=False), encoding="utf-8")

        templates = load_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["name"], "包装格式模板")

    def test_save_template_with_non_serializable_values(self):
        """包含 datetime 等值时也应可保存"""
        ok = save_template("复杂模板", {
            "difference_formula": "C - B",
            "extra": {
                "created_at": datetime(2026, 3, 16, 12, 30, 0)
            }
        })

        self.assertTrue(ok)
        templates = load_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["name"], "复杂模板")

        created_at = templates[0]["config"]["extra"]["created_at"]
        self.assertIsInstance(created_at, str)


if __name__ == "__main__":
    unittest.main()
