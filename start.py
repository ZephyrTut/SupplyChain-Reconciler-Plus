"""
快速启动指南 - 演示应用核心功能
"""
import os
import sys


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         🚀 SupplyChain-Reconciler-Plus v1.1.0                    ║
║                                                                  ║
║           供应链智能对账系统 - Python 桌面应用                      ║
║                                                                  ║
║         支持双表对账 | 透视汇总 | 动态公式 | 带颜色导出             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印菜单"""
    menu = """
🎯 请选择操作:

  1. 🚀 启动应用程序
  2. 🧪 运行快速测试
  3. 📊 查看测试数据
  4. 📖 查看使用文档
  5. 🔧 检查依赖环境
  6. ❌ 退出

请输入选择 (1-6):
    """
    print(menu)


def launch_app():
    """启动应用程序"""
    print("\n⏳ 正在启动应用程序...\n")
    try:
        from ui import MainWindow
        app = MainWindow()
        app.run()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n请确保已安装所有依赖:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ 应用错误: {e}")
        return False
    return True


def run_quick_test():
    """运行快速测试"""
    print("\n⏳ 运行快速测试...\n")
    os.system("python tests/quick_test.py")


def view_test_data():
    """查看测试数据"""
    print("\n📊 测试数据说明\n")
    print("=" * 60)
    
    try:
        import pandas as pd
        
        # 检查文件是否存在
        manual_file = "tests/data/手工表.xlsx"
        system_file = "tests/data/系统表.xlsx"
        
        if not os.path.exists(manual_file) or not os.path.exists(system_file):
            print("⚠ 测试数据不存在，正在创建...\n")
            os.system("python tests/create_test_data.py")
            return
        
        # 读取并显示
        manual_df = pd.read_excel(manual_file)
        system_df = pd.read_excel(system_file)
        
        print("\n📄 手工表数据:")
        print(f"  文件: {manual_file}")
        print(f"  行数: {len(manual_df)}")
        print(f"  列: {list(manual_df.columns)}\n")
        print(manual_df.to_string(index=False))
        
        print("\n" + "=" * 60)
        print("\n🗄️ 系统表数据:")
        print(f"  文件: {system_file}")
        print(f"  行数: {len(system_df)}")
        print(f"  列: {list(system_df.columns)}\n")
        print(system_df.to_string(index=False))
        
        print("\n" + "=" * 60)
        print("\n💡 快速开始:")
        print("  1. 在应用中导入这两个文件")
        print("  2. 配置主键: 订单编号 + 物料编码")
        print("  3. 配置数值: 手工数量 vs 系统数量")
        print("  4. 设置透视: 状态")
        print("  5. 公式: M - (S - 已关闭)")
        print("  6. 执行对账并导出")
        
    except Exception as e:
        print(f"❌ 读取测试数据失败: {e}")


def show_docs():
    """显示使用文档"""
    print("\n📖 使用文档\n")
    print("=" * 60)
    
    docs = """
【基本流程】

Step 1: 导入文件
  - 选择手工表 Excel 文件
  - 选择系统表 Excel 文件
  - 点击"智能解析"按钮

Step 2: 配置字段
  ✓ 配置主键 (1-3列)
    - 手工表: 选择主键列
    - 系统表: 选择对应的主键列
  
  ✓ 配置数值列 (1-2列)
    - 手工表: 选择数值列
    - 系统表: 选择对应的数值列
  
  ✓ 设置透视 (可选)
    - 系统表透视列: 用于分组统计
    - 例如: 订单状态, 物料类型等
  
  ✓ 配置公式 (可选)
    - M: 手工数量
    - S: 系统总计
    - A/B/C...: 透视列值
    - 例如: M - (S - 已关闭)

Step 3: 查看结果
  - 统计卡片显示数量
  - 表格显示详细结果
  - 支持导出到 Excel

【导出字段说明】

导出 Excel 包含以下字段:

  1. KEY    - 复合主键
  2. M      - 手工数量（左表）
  3. A/B/C  - 透视列（如果有）
  4. S      - 系统总计（右表）
  5. D      - 差值（计算结果）
  6. 状态   - 比对状态 (✓一致/↕差异/✗缺失)

【常见问题】

Q: 如何处理重复数据?
A: 使用"透视"和"聚合"功能自动合并重复行

Q: 如何排除某些数据?
A: 在系统表配置中添加筛选条件

Q: 如何自定义差值计算?
A: 使用差值公式功能，支持表达式语言

Q: 导出的 Excel 如何查看?
A: 会生成带颜色标记的 Excel 文件，不同状态不同颜色

【技术支持】

- 查看 OPTIMIZATION.md 了解最新优化
- 查看 README.md 了解项目信息
- 运行 python tests/quick_test.py 进行功能测试
    """
    
    print(docs)
    print("=" * 60)


def check_environment():
    """检查依赖环境"""
    print("\n🔧 检查环境\n")
    print("=" * 60)
    
    required_packages = {
        'pandas': '数据处理',
        'openpyxl': 'Excel 读写',
        'ttkbootstrap': 'UI 框架',
    }
    
    optional_packages = {
        'tkinterdnd2': '文件拖拽支持（可选）',
    }
    
    print("\n✓ 必需依赖:\n")
    for pkg, desc in required_packages.items():
        try:
            __import__(pkg)
            print(f"  ✓ {pkg:20} - {desc}")
        except ImportError:
            print(f"  ✗ {pkg:20} - {desc} (未安装)")
    
    print("\n⚠ 可选依赖:\n")
    for pkg, desc in optional_packages.items():
        try:
            __import__(pkg)
            print(f"  ✓ {pkg:20} - {desc}")
        except ImportError:
            print(f"  ○ {pkg:20} - {desc} (未安装)")
    
    print("\n" + "=" * 60)
    print("\n安装依赖:")
    print("  pip install -r requirements.txt")
    
    print("\n安装拖拽支持 (可选):")
    print("  pip install tkinterdnd2")


def main():
    """主菜单"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        print_banner()
        print_menu()
        
        choice = input().strip()
        
        if choice == '1':
            if launch_app():
                print("\n✅ 应用已关闭")
            break
        
        elif choice == '2':
            run_quick_test()
            input("\n按 Enter 继续...")
        
        elif choice == '3':
            view_test_data()
            input("\n按 Enter 继续...")
        
        elif choice == '4':
            show_docs()
            input("\n按 Enter 继续...")
        
        elif choice == '5':
            check_environment()
            input("\n按 Enter 继续...")
        
        elif choice == '6':
            print("\n👋 再见!")
            break
        
        else:
            print("\n❌ 无效选择，请重试")
            input("\n按 Enter 继续...")
        
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
