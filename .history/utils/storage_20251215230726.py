"""
配置存储模块 - 配置和模板的持久化
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


def get_config_dir() -> Path:
    """获取配置目录"""
    # 使用用户数据目录
    if os.name == 'nt':  # Windows
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:  # macOS/Linux
        base = os.path.expanduser("~/.config")
    
    config_dir = Path(base) / "SupplyChain-Reconciler"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / "config.json"


def get_templates_path() -> Path:
    """获取模板文件路径"""
    return get_config_dir() / "templates.json"


def load_config() -> Optional[Dict[str, Any]]:
    """
    加载上次保存的配置
    
    Returns:
        配置字典，如果不存在返回None
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def save_config(config: Dict[str, Any]) -> bool:
    """
    保存当前配置
    
    Args:
        config: 配置字典
    
    Returns:
        是否成功
    """
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def load_templates() -> List[Dict[str, Any]]:
    """
    加载所有模板
    
    Returns:
        模板列表 [{"name": "模板名", "config": {...}}, ...]
    """
    templates_path = get_templates_path()
    
    if not templates_path.exists():
        return []
    
    try:
        with open(templates_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_template(name: str, config: Dict[str, Any]) -> bool:
    """
    保存模板
    
    Args:
        name: 模板名称
        config: 配置字典
    
    Returns:
        是否成功
    """
    import uuid
    from datetime import datetime
    
    templates = load_templates()
    
    # 查找是否存在同名模板
    found = False
    for t in templates:
        if t.get("name") == name:
            t["config"] = config
            t["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break
    
    if not found:
        templates.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "config": config,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    try:
        with open(get_templates_path(), 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def delete_template(template_id: str) -> tuple[bool, str]:
    """
    删除模板
    
    Args:
        template_id: 模板ID（优先）或模板名称（兼容旧代码）
    
    Returns:
        (成功状态, 错误信息或成功消息)
    """
    if not template_id or not template_id.strip():
        return False, "模板ID不能为空"
    
    try:
        templates = load_templates()
        original_count = len(templates)
        
        # 先尝试按ID删除，如果找不到则按名称删除（向后兼容）
        filtered_templates = [t for t in templates if t.get("id") != template_id and t.get("name") != template_id]
        
        if len(filtered_templates) == original_count:
            return False, f"未找到模板: {template_id}"
        
        # 保存删除后的模板列表
        templates_path = get_templates_path()
        with open(templates_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_templates, f, ensure_ascii=False, indent=2)
        
        return True, f"成功删除模板 (共 {original_count - len(filtered_templates)} 个)"
        
    except PermissionError:
        return False, "文件权限不足，无法删除模板"
    except json.JSONDecodeError as e:
        return False, f"模板文件格式错误: {str(e)}"
    except Exception as e:
        return False, f"删除失败: {str(e)}"


def get_recent_files() -> List[Dict[str, str]]:
    """
    获取最近打开的文件
    
    Returns:
        [{"path": "...", "type": "manual|system"}, ...]
    """
    config = load_config()
    if config:
        return config.get("recent_files", [])
    return []


def add_recent_file(filepath: str, file_type: str) -> None:
    """
    添加最近文件
    
    Args:
        filepath: 文件路径
        file_type: 文件类型 (manual/system)
    """
    config = load_config() or {}
    recent = config.get("recent_files", [])
    
    # 移除已存在的
    recent = [r for r in recent if r.get("path") != filepath]
    
    # 添加到开头
    recent.insert(0, {"path": filepath, "type": file_type})
    
    # 最多保留10个
    recent = recent[:10]
    
    config["recent_files"] = recent
    save_config(config)
