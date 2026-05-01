# -*- coding: utf-8 -*-
"""
SupplyChain-Reconciler-Plus v1.5.0
Python desktop application (PyQt6).
"""

import sys
import os
from config.settings import APP_VERSION


def main():
    """Main entry (PyQt6)."""
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFont

        app = QApplication(sys.argv)
        app.setApplicationName("SupplyChain-Reconciler-Plus")
        app.setApplicationVersion(APP_VERSION)

        font = QFont("Microsoft YaHei", 9)
        app.setFont(font)

        try:
            from qt_material import apply_stylesheet

            extra = {
                "density_scale": "0",
                "font_family": "Microsoft YaHei",
            }
            apply_stylesheet(app, theme="light_blue.xml", extra=extra, invert_secondary=True)
            app.setStyleSheet(app.styleSheet() + """
                QDialog { background-color: #ffffff; }
                QDialog QLabel { color: #333333; }
                QMessageBox { background-color: #ffffff; }
                QMessageBox QLabel { color: #333333; }
            """)
            print("qt-material theme loaded")
        except ImportError:
            print("qt-material not installed, using default style")
            app.setStyleSheet("""
                QMainWindow { background-color: #fafafa; }
                QPushButton { padding: 8px 16px; border-radius: 4px; }
                QLineEdit, QComboBox {
                    padding: 6px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
            """)

        from ui.qt_main_window import QtMainWindow

        print(f"\nStarting SupplyChain-Reconciler-Plus v{APP_VERSION}...\n")
        window = QtMainWindow()
        window.show()

        sys.exit(app.exec())

    except ImportError as e:
        print(f"\nImport error: {e}")
        print("\nPlease ensure dependencies are installed:")
        print("  pip install -r requirements.txt")
        print("\nRequired packages:")
        print("  - PyQt6>=6.0.0")
        print("  - qt-material>=2.14")
        print("  - pandas>=2.0.0")
        print("  - openpyxl>=3.1.0")
        print("  - xlrd>=2.0.0\n")
        sys.exit(1)

    except Exception as e:
        print(f"\nApplication error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
