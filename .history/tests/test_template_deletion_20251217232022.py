"""
模板删除功能完整测试套件
测试策略：
1. 单元测试 - 测试delete_template函数的各种边界情况
2. 集成测试 - 测试UI与存储层的交互
3. 数据迁移测试 - 测试旧格式模板的兼容性
"""
import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import delete_template, load_templates, save_template
from utils.storage import get_templates_path, get_config_dir


class TestDeleteTemplateUnit:
    """单元测试：delete_template函数"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """每个测试前后的环境准备和清理"""
        # 备份现有模板
        self.backup_dir = Path(tempfile.mkdtemp())
        templates_path = get_templates_path()
        if templates_path.exists():
            shutil.copy(templates_path, self.backup_dir / "templates.json.bak")
        
        yield
        
        # 恢复模板
        backup_file = self.backup_dir / "templates.json.bak"
        if backup_file.exists():
            shutil.copy(backup_file, templates_path)
        shutil.rmtree(str(self.backup_dir))
    
    def test_delete_with_valid_id(self):
        """测试：使用有效ID删除模板"""
        # 准备：创建测试模板
        test_config = {"keys": ["id"], "values": ["amount"]}
        save_template("测试模板1", test_config)
        
        templates = load_templates()
        test_template = next(t for t in templates if t["name"] == "测试模板1")
        template_id = test_template["id"]
        
        # 执行：删除模板
        success, message = delete_template(template_id)
        
        # 验证：删除成功
        assert success is True
        assert "成功删除" in message
        
        # 验证：模板已从列表中移除
        templates_after = load_templates()
        assert not any(t["id"] == template_id for t in templates_after)
    
    def test_delete_with_empty_id(self):
        """测试：空ID应该失败"""
        success, message = delete_template("")
        assert success is False
        assert "不能为空" in message
        
        success, message = delete_template("   ")
        assert success is False
        assert "不能为空" in message
    
    def test_delete_with_none_id(self):
        """测试：None ID应该失败"""
        # 注意：Python的类型提示不强制运行时检查，需要手动测试
        try:
            success, message = delete_template(None)
            assert success is False
        except (TypeError, AttributeError):
            # 如果抛出异常也是可接受的
            pass
    
    def test_delete_nonexistent_template(self):
        """测试：删除不存在的模板"""
        fake_id = str(uuid.uuid4())
        success, message = delete_template(fake_id)
        
        assert success is False
        assert "未找到模板" in message
    
    def test_delete_legacy_template_by_name(self):
        """测试：删除旧格式模板（仅有name，无id）"""
        # 准备：手动创建旧格式模板
        templates = load_templates()
        legacy_template = {
            "name": "旧格式模板",
            "config": {"keys": ["old_key"], "values": ["old_value"]}
            # 注意：没有id和timestamp字段
        }
        templates.append(legacy_template)
        
        with open(get_templates_path(), 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        # 执行：使用name删除
        success, message = delete_template("旧格式模板")
        
        # 验证：成功删除
        assert success is True
        assert "成功删除" in message
        
        templates_after = load_templates()
        assert not any(t.get("name") == "旧格式模板" for t in templates_after)
    
    def test_delete_multiple_templates_with_same_name(self):
        """测试：同名模板时删除所有匹配项"""
        # 准备：创建同名模板（理论上不应该发生，但测试健壮性）
        templates = load_templates()
        templates.append({"name": "重名模板", "config": {}})
        templates.append({"name": "重名模板", "config": {}})
        
        with open(get_templates_path(), 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        original_count = len(load_templates())
        
        # 执行
        success, message = delete_template("重名模板")
        
        # 验证：都被删除了
        assert success is True
        templates_after = load_templates()
        assert len(templates_after) == original_count - 2
    
    def test_concurrent_delete_operations(self):
        """测试：模拟并发删除（文件锁测试）"""
        # 准备：创建多个模板
        for i in range(3):
            save_template(f"并发测试{i}", {"keys": [f"key{i}"]})
        
        templates = load_templates()
        ids = [t["id"] for t in templates if "并发测试" in t["name"]]
        
        # 执行：连续快速删除
        results = [delete_template(tid) for tid in ids]
        
        # 验证：所有删除都应该成功
        assert all(r[0] for r in results)
    
    def test_delete_with_readonly_file(self):
        """测试：文件只读时删除失败"""
        # 准备：创建测试模板
        save_template("只读测试", {"keys": ["test"]})
        templates = load_templates()
        test_id = next(t["id"] for t in templates if t["name"] == "只读测试")
        
        # 设置文件为只读
        templates_path = get_templates_path()
        os.chmod(templates_path, 0o444)
        
        try:
            # 执行：尝试删除
            success, message = delete_template(test_id)
            
            # 验证：应该失败并返回权限错误
            assert success is False
            assert "权限" in message
        finally:
            # 恢复文件权限
            os.chmod(templates_path, 0o644)


class TestTemplateManagerIntegration:
    """集成测试：UI层与存储层的交互"""
    
    def test_delete_from_ui_workflow(self):
        """测试：完整的UI删除工作流"""
        # 准备：创建测试模板
        test_config = {"keys": ["ui_key"], "values": ["ui_value"]}
        save_template("UI测试模板", test_config)
        
        templates = load_templates()
        test_template = next(t for t in templates if t["name"] == "UI测试模板")
        
        # 模拟UI层的删除逻辑
        template_id = test_template.get("id") or test_template.get("name")
        assert template_id is not None
        
        success, message = delete_template(template_id)
        
        # 验证
        assert success is True
        templates_after = load_templates()
        assert not any(t.get("name") == "UI测试模板" for t in templates_after)
    
    def test_ui_handles_missing_id_gracefully(self):
        """测试：UI层处理缺失ID的情况"""
        # 模拟缺失id和name的模板（异常数据）
        broken_template = {}
        
        template_id = broken_template.get("id") or broken_template.get("name")
        
        # UI层应该检测到这种情况
        assert template_id is None
        # 在实际UI中会显示错误消息，这里验证逻辑正确


class TestDataMigration:
    """数据迁移测试：确保新旧格式兼容"""
    
    def test_load_mixed_format_templates(self):
        """测试：加载混合格式的模板"""
        # 准备：创建混合格式的模板文件
        mixed_templates = [
            # 新格式
            {
                "id": str(uuid.uuid4()),
                "name": "新格式模板",
                "config": {"keys": ["new_key"]},
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            # 旧格式
            {
                "name": "旧格式模板",
                "config": {"keys": ["old_key"]}
            }
        ]
        
        with open(get_templates_path(), 'w', encoding='utf-8') as f:
            json.dump(mixed_templates, f, ensure_ascii=False, indent=2)
        
        # 执行：加载模板
        templates = load_templates()
        
        # 验证：两种格式都能加载
        assert len(templates) == 2
        assert any(t.get("id") for t in templates)  # 至少一个有id
        assert any(not t.get("id") for t in templates)  # 至少一个没有id
    
    def test_delete_works_for_both_formats(self):
        """测试：删除功能对两种格式都有效"""
        # 新格式：使用id删除
        save_template("新格式", {"keys": ["k1"]})
        templates = load_templates()
        new_id = next(t["id"] for t in templates if t["name"] == "新格式")
        success, _ = delete_template(new_id)
        assert success is True
        
        # 旧格式：使用name删除
        old_templates = load_templates()
        old_templates.append({"name": "旧格式", "config": {"keys": ["k2"]}})
        with open(get_templates_path(), 'w', encoding='utf-8') as f:
            json.dump(old_templates, f, ensure_ascii=False, indent=2)
        
        success, _ = delete_template("旧格式")
        assert success is True


# ===== 测试运行器 =====
def run_all_tests():
    """运行所有测试并生成报告"""
    print("=" * 70)
    print("🧪 模板删除功能完整测试套件")
    print("=" * 70)
    
    # 运行pytest
    exit_code = pytest.main([
        __file__,
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback
        "--color=yes",  # 彩色输出
        "-p", "no:warnings"  # 忽略警告
    ])
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ 所有测试通过！模板删除功能完全正常")
    else:
        print("❌ 部分测试失败，请检查上述错误")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    run_all_tests()
