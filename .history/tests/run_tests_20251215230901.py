"""
自动化测试运行脚本
用途：一键运行所有测试并生成报告
使用方法：python tests/run_tests.py
"""
import subprocess
import sys
from pathlib import Path

def check_pytest_installed():
    """检查pytest是否安装"""
    try:
        import pytest
        return True
    except ImportError:
        return False

def install_pytest():
    """安装pytest"""
    print("📦 正在安装pytest...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
    print("✅ pytest安装成功\n")

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 SupplyChain-Reconciler-Plus 自动化测试")
    print("=" * 70 + "\n")
    
    # 检查pytest
    if not check_pytest_installed():
        install_pytest()
    
    # 运行模板删除测试
    print("🧪 运行模板删除功能测试...\n")
    test_file = Path(__file__).parent / "test_template_deletion.py"
    
    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=False
    )
    
    # 返回结果
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
