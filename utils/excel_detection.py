"""
活动Excel检测模块 - 检测当前打开的Excel文件
"""
import os
from typing import Optional, Dict


def auto_detect_active_workbook() -> Optional[Dict[str, str]]:
    """
    自动检测活动的 Excel 工作簿
    
    尝试检测：
    1. Windows + Excel (通过 win32com)
    2. WPS (通过 win32com，但返回提示)
    
    Returns:
        包含 'path', 'name', 'sheet_name' 的字典，如果检测失败返回 None
        
    Raises:
        RuntimeError: 如果检测到 WPS
    """
    try:
        import win32com.client as win32
    except ImportError:
        return None
    
    excel = None
    try:
        # 尝试连接到 Excel Application
        try:
            excel = win32.gencache.EnsureDispatch('Excel.Application')
        except:
            # 如果 EnsureDispatch 失败，尝试 Dispatch
            excel = win32.Dispatch('Excel.Application')
        
        # 检查是否有活动工作簿
        if not excel or not hasattr(excel, 'Workbooks'):
            return None
            
        if excel.Workbooks.Count == 0:
            return None
        
        active_wb = excel.ActiveWorkbook
        if not active_wb:
            return None
        
        # 获取完整路径
        full_path = active_wb.FullName
        workbook_name = active_wb.Name
        
        # 获取当前工作表名称
        sheet_name = ""
        try:
            if hasattr(excel, 'ActiveSheet') and excel.ActiveSheet:
                sheet_name = excel.ActiveSheet.Name
        except:
            pass
        
        # 检查是否已保存（未保存的文件路径可能不完整）
        if not os.path.exists(full_path):
            # 文件未保存
            return {
                'path': None,
                'name': workbook_name,
                'sheet_name': sheet_name
            }
        
        return {
            'path': full_path,
            'name': workbook_name,
            'sheet_name': sheet_name
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # 检测是否为 WPS
        if 'wps' in error_msg or 'et.application' in error_msg or 'kingsoft' in error_msg:
            raise RuntimeError(
                "检测到 WPS Office。\n\n"
                "WPS 的 COM 接口与 Excel 不同，暂不支持自动检测。\n"
                "请手动选择文件或将文件另存为 Excel 格式后使用文件选择功能。"
            )
        
        # 其他错误，返回 None
        return None
    finally:
        # 释放 COM对象
        if excel:
            try:
                del excel
            except:
                pass


def get_active_excel_info() -> Optional[Dict[str, str]]:
    """
    获取活动 Excel 信息（别名函数，便于调用）
    
    Returns:
        包含 'path' 和 'name' 的字典，如果检测失败返回 None
    """
    return auto_detect_active_workbook()
