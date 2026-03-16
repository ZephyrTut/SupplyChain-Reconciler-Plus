# -*- coding: utf-8 -*-
"""
SupplyChain-Reconciler-Plus v1.4.4
供应链智能对账系统 - Python 桌面应用 (PyQt6 版本)

核心功能:
  ✓ 双表对账（手工表 vs 系统表）
  ✓ 复合主键支持（多列组合）
  ✓ 透视列聚合（自动分组统计）
  ✓ 出入库区分（手工表透视）
  ✓ 数据清洗（正则表达式）
  ✓ 动态差值公式（支持自定义表达式）
  ✓ 配置模板保存/加载
  ✓ 实时匹配预览
  ✓ 导出带颜色背景的Excel结果
  ✓ 支持 .xls/.xlsx/.xlsm 格式
 
技术栈:
  - PyQt6 + qt-material（现代化UI框架）
  - pandas（高性能数据处理）
  - openpyxl + xlrd（Excel读写）

快速开始:
  python main.py
"""

import sys
import os
from config.settings import APP_VERSION


def main():
    """主函数 - PyQt6 版本"""
    try:
        # 确保在正确的目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 导入 PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("SupplyChain-Reconciler-Plus")
        app.setApplicationVersion(APP_VERSION)
        
        # 设置默认字体
        font = QFont("Microsoft YaHei", 9)
        app.setFont(font)
        
        # 应用 qt-material 主题
        try:
            from qt_material import apply_stylesheet
            # 使用浅色主题，设置 invert_secondary 让标题栏也是浅色
            extra = {
                'density_scale': '0',
                'font_family': 'Microsoft YaHei',
            }
            apply_stylesheet(app, theme='light_blue.xml', extra=extra, invert_secondary=True)
            
            # 覆盖对话框样式，确保统一的浅色风格
            app.setStyleSheet(app.styleSheet() + """
                QDialog {
                    background-color: #ffffff;
                }
                QDialog QLabel {
                    color: #333333;
                }
                QMessageBox {
                    background-color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #333333;
                }
            """)
            print("✓ qt-material 主题已加载")
        except ImportError:
            print("⚠ qt-material 未安装，使用默认样式")
            # 使用备用样式
            app.setStyleSheet("""
                QMainWindow {
                    background-color: #fafafa;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QLineEdit, QComboBox {
                    padding: 6px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
            """)
        
        # 导入并创建主窗口
        from ui.qt_main_window import QtMainWindow
        
        print(f"\n🚀 SupplyChain-Reconciler-Plus v{APP_VERSION} 启动中...")
        print("   UI框架: PyQt6 + qt-material\n")
        
        window = QtMainWindow()
        window.show()
        
        # 运行事件循环
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n请确保已安装所有依赖:")
        print("  pip install -r requirements.txt")
        print("\n必需的依赖:")
        print("  - PyQt6>=6.0.0")
        print("  - qt-material>=2.14")
        print("  - pandas>=2.0.0")
        print("  - openpyxl>=3.1.0")
        print("  - xlrd>=2.0.0\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 应用错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
