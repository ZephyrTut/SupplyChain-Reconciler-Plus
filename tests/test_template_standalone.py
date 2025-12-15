"""
模板删除功能测试（无需pytest）
独立运行测试，无需额外依赖
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid
import traceback
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import delete_template, load_templates, save_template
from utils.storage import get_templates_path


class TestRunner:
    """简单的测试运行器"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition, message=""):
        """断言为真"""
        if not condition:
            raise AssertionError(f"断言失败: {message}")
    
    def assert_false(self, condition, message=""):
        """断言为假"""
        if condition:
            raise AssertionError(f"断言失败: {message}")
    
    def assert_equal(self, a, b, message=""):
        """断言相等"""
        if a != b:
            raise AssertionError(f"断言失败: {a} != {b}. {message}")
    
    def assert_in(self, substring, string, message=""):
        """断言包含"""
        if substring not in string:
            raise AssertionError(f"断言失败: '{substring}' 不在 '{string}' 中. {message}")
    
    def run_test(self, test_func, test_name):
        """运行单个测试"""
        try:
            # 备份模板
            templates_path = get_templates_path()
            backup = None
            if templates_path.exists():
                with open(templates_path, 'r', encoding='utf-8') as f:
                    backup = f.read()
            
            # 运行测试
            test_func()
            
            # 恢复模板
            if backup:
                with open(templates_path, 'w', encoding='utf-8') as f:
                    f.write(backup)
            
            print(f"  ✅ {test_name}")
            self.passed += 1
            
        except Exception as e:
            print(f"  ❌ {test_name}")
            print(f"     错误: {str(e)}")
            self.failed += 1
            self.errors.append((test_name, str(e), traceback.format_exc()))
    
    def print_summary(self):
        """打印测试总结"""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"测试结果: {self.passed}/{total} 通过")
        
        if self.failed > 0:
            print(f"\n失败的测试 ({self.failed}):")
            for name, error, tb in self.errors:
                print(f"\n❌ {name}")
                print(f"   {error}")
                if "--verbose" in sys.argv:
                    print(f"\n{tb}")
        else:
            print("\n🎉 所有测试通过！")
        
        print("=" * 70)
        return self.failed == 0


# ===== 测试用例 =====
def test_delete_with_valid_id(runner):
    """测试：使用有效ID删除模板"""
    # 创建测试模板
    test_config = {"keys": ["id"], "values": ["amount"]}
    save_template("测试模板1", test_config)
    
    templates = load_templates()
    test_template = next((t for t in templates if t.get("name") == "测试模板1"), None)
    runner.assert_true(test_template is not None, "模板应该被创建")
    
    template_id = test_template.get("id")
    runner.assert_true(template_id is not None, "模板应该有ID")
    
    # 删除模板
    success, message = delete_template(template_id)
    
    # 验证
    runner.assert_true(success, "删除应该成功")
    runner.assert_in("成功删除", message)
    
    templates_after = load_templates()
    runner.assert_false(
        any(t.get("id") == template_id for t in templates_after),
        "模板应该被删除"
    )


def test_delete_with_empty_id(runner):
    """测试：空ID应该失败"""
    success, message = delete_template("")
    runner.assert_false(success, "空ID应该失败")
    runner.assert_in("不能为空", message)
    
    success, message = delete_template("   ")
    runner.assert_false(success, "空白ID应该失败")


def test_delete_nonexistent_template(runner):
    """测试：删除不存在的模板"""
    fake_id = str(uuid.uuid4())
    success, message = delete_template(fake_id)
    
    runner.assert_false(success, "删除不存在的模板应该失败")
    runner.assert_in("未找到模板", message)


def test_delete_legacy_template(runner):
    """测试：删除旧格式模板（无id字段）"""
    # 手动创建旧格式模板
    templates = load_templates()
    legacy_template = {
        "name": "旧格式模板",
        "config": {"keys": ["old_key"], "values": ["old_value"]}
    }
    templates.append(legacy_template)
    
    with open(get_templates_path(), 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)
    
    # 使用name删除
    success, message = delete_template("旧格式模板")
    
    runner.assert_true(success, "应该能删除旧格式模板")
    
    templates_after = load_templates()
    runner.assert_false(
        any(t.get("name") == "旧格式模板" for t in templates_after),
        "旧格式模板应该被删除"
    )


def test_delete_multiple_same_name(runner):
    """测试：删除同名模板"""
    templates = load_templates()
    templates.append({"name": "重名模板", "config": {}})
    templates.append({"name": "重名模板", "config": {}})
    
    with open(get_templates_path(), 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)
    
    original_count = len(load_templates())
    
    success, message = delete_template("重名模板")
    
    runner.assert_true(success)
    templates_after = load_templates()
    runner.assert_equal(
        len(templates_after), 
        original_count - 2,
        "应该删除所有同名模板"
    )


def test_ui_fallback_logic(runner):
    """测试：UI层的降级逻辑（id不存在时使用name）"""
    # 模拟旧格式模板
    templates = load_templates()
    old_template = {"name": "UI旧模板", "config": {}}
    templates.append(old_template)
    
    with open(get_templates_path(), 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)
    
    # 模拟UI代码
    template = {"name": "UI旧模板", "config": {}}
    template_id = template.get("id") or template.get("name")
    
    runner.assert_equal(template_id, "UI旧模板", "应该降级到name")
    
    success, _ = delete_template(template_id)
    runner.assert_true(success, "降级删除应该成功")


def test_message_format(runner):
    """测试：错误消息格式正确"""
    # 测试空ID消息
    _, msg1 = delete_template("")
    runner.assert_in("不能为空", msg1)
    
    # 测试不存在的模板消息
    _, msg2 = delete_template("fake-id-12345")
    runner.assert_in("未找到模板", msg2)
    
    # 测试成功消息
    save_template("消息测试", {"keys": []})
    templates = load_templates()
    test_template = next((t for t in templates if t.get("name") == "消息测试"), None)
    if test_template and test_template.get("id"):
        tid = test_template["id"]
        _, msg3 = delete_template(tid)
        runner.assert_in("成功删除", msg3)


def test_concurrent_deletes(runner):
    """测试：连续快速删除"""
    # 创建多个模板
    for i in range(3):
        save_template(f"并发测试{i}", {"keys": [f"key{i}"]})
    
    templates = load_templates()
    ids = [t.get("id") for t in templates if "并发测试" in t.get("name", "") and t.get("id")]
    
    # 连续删除
    results = [delete_template(tid) for tid in ids if tid]
    
    runner.assert_true(len(results) > 0, "应该有模板可删除")
    runner.assert_true(all(r[0] for r in results), "所有删除都应该成功")


# ===== 主函数 =====
def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 模板删除功能测试套件")
    print("=" * 70 + "\n")
    
    runner = TestRunner()
    
    # 定义所有测试
    tests = [
        (test_delete_with_valid_id, "使用有效ID删除模板"),
        (test_delete_with_empty_id, "空ID应该失败"),
        (test_delete_nonexistent_template, "删除不存在的模板"),
        (test_delete_legacy_template, "删除旧格式模板"),
        (test_delete_multiple_same_name, "删除同名模板"),
        (test_ui_fallback_logic, "UI层降级逻辑"),
        (test_message_format, "错误消息格式"),
        (test_concurrent_deletes, "连续快速删除"),
    ]
    
    # 运行所有测试
    for test_func, test_name in tests:
        runner.run_test(lambda: test_func(runner), test_name)
    
    # 打印总结
    success = runner.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
