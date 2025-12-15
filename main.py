# -*- coding: utf-8 -*-
"""
SupplyChain-Reconciler-Plus v1.1.0
供应链智能对账系统 - Python 桌面应用

核心功能:
  ✓ 双表对账（手工表 vs 系统表）
  ✓ 复合主键支持（1-3列组合）
  ✓ 透视列聚合（自动分组统计）
  ✓ 动态差值公式（支持自定义表达式）
  ✓ 配置模板保存/加载
  ✓ 实时匹配预览（左右表并排）
  ✓ 导出带颜色背景的Excel结果

本次优化 (v1.1.0):
  ✓ 修复列名重复问题
  ✓ 改进公式变量系统（使用代号 M/S/A/B/C）
  ✓ 添加字段映射可视化预览
  ✓ 支持文件拖拽上传
  ✓ 加载动画和进度显示
  ✓ 智能字段识别

快速开始:
  1. python main.py          # 直接启动
  2. python start.py         # 交互式菜单
  3. python tests/quick_test.py  # 功能测试
"""

import sys
import os


def main():
    """主函数"""
    try:
        # 确保在正确的目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 导入并启动应用
        from ui import MainWindow
        
        print("\n🚀 SupplyChain-Reconciler-Plus v1.1.0 启动中...\n")
        
        app = MainWindow()
        app.run()
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n请确保已安装所有依赖:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 应用错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
