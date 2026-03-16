"""
配置存储模块 - 配置和模板的持久化
"""
import json
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path


APP_DIR_NAME = "SupplyChain-Reconciler-Plus"
LEGACY_APP_DIR_NAME = "SupplyChain-Reconciler"


def _make_json_safe(value: Any) -> Any:
    """将对象转换为可 JSON 序列化的数据。"""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(v) for v in value]

    # 兼容 datetime / pandas / numpy 等对象
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)


def _migrate_legacy_files(new_dir: Path, legacy_dir: Path) -> None:
    """将旧目录中的配置文件迁移到新目录（仅在新目录不存在对应文件时）。"""
    if not legacy_dir.exists():
        return

    for filename in ["config.json", "templates.json"]:
        src = legacy_dir / filename
        dst = new_dir / filename
        if src.exists() and not dst.exists():
            try:
                dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
            except Exception:
                continue


def _resolve_default_templates_path() -> Optional[Path]:
    """解析默认模板文件路径（源码运行与打包运行均兼容）。"""
    candidates: List[Path] = []

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(Path(getattr(sys, '_MEIPASS')) / 'templates.json')

    project_root = Path(__file__).resolve().parent.parent
    candidates.append(project_root / 'templates.json')
    candidates.append(Path.cwd() / 'templates.json')

    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def _ensure_default_templates(config_dir: Path) -> None:
    """首次运行时，若用户目录缺少模板文件则写入默认 templates.json。"""
    target = config_dir / 'templates.json'
    if target.exists():
        return

    source = _resolve_default_templates_path()
    if source is None:
        return

    try:
        data = source.read_text(encoding='utf-8')
        json.loads(data)
        target.write_text(data, encoding='utf-8')
    except Exception:
        return


def get_config_dir() -> Path:
    """获取配置目录"""
    # 使用用户数据目录
    if os.name == 'nt':  # Windows
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:  # macOS/Linux
        base = os.path.expanduser("~/.config")

    config_dir = Path(base) / APP_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)

    # 兼容旧版本目录迁移
    legacy_dir = Path(base) / LEGACY_APP_DIR_NAME
    _migrate_legacy_files(config_dir, legacy_dir)
    _ensure_default_templates(config_dir)
    
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
            data = json.load(f)

        # 新旧格式兼容
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            templates = data.get("templates", [])
            return templates if isinstance(templates, list) else []
        return []
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
    if not isinstance(templates, list):
        templates = []

    name = str(name).strip()
    if not name:
        return False

    safe_config = _make_json_safe(config)
    
    # 查找是否存在同名模板
    found = False
    for t in templates:
        if t.get("name") == name:
            # 更新模板：保留id（如果有），更新config和timestamp
            if "id" not in t:
                t["id"] = str(uuid.uuid4())
            t["config"] = safe_config
            t["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break
    
    if not found:
        templates.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "config": safe_config,
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
    print(f"\n{'='*70}")
    print(f"[DELETE_TEMPLATE] 开始删除模板")
    print(f"[DELETE_TEMPLATE] 接收到的template_id: {repr(template_id)}")
    print(f"[DELETE_TEMPLATE] template_id类型: {type(template_id)}")
    
    if not template_id or not template_id.strip():
        error_msg = "模板ID不能为空"
        print(f"[DELETE_TEMPLATE] ❌ 验证失败: {error_msg}")
        print(f"{'='*70}\n")
        return False, error_msg
    
    try:
        print(f"[DELETE_TEMPLATE] 📂 加载模板文件...")
        templates = load_templates()
        original_count = len(templates)
        print(f"[DELETE_TEMPLATE] 当前模板总数: {original_count}")
        
        # 打印所有模板信息用于调试
        print(f"[DELETE_TEMPLATE] 现有模板列表:")
        for idx, t in enumerate(templates, 1):
            print(f"  {idx}. name={t.get('name')}, id={t.get('id')}")
        
        # 先尝试按ID删除，如果找不到则按名称删除（向后兼容）
        print(f"[DELETE_TEMPLATE] 🔍 查找并过滤模板...")
        filtered_templates = [t for t in templates if t.get("id") != template_id and t.get("name") != template_id]
        
        deleted_count = original_count - len(filtered_templates)
        print(f"[DELETE_TEMPLATE] 过滤后剩余: {len(filtered_templates)} 个")
        print(f"[DELETE_TEMPLATE] 将删除: {deleted_count} 个模板")
        
        if len(filtered_templates) == original_count:
            error_msg = f"未找到模板: {template_id}"
            print(f"[DELETE_TEMPLATE] ❌ {error_msg}")
            print(f"{'='*70}\n")
            return False, error_msg
        
        # 保存删除后的模板列表
        print(f"[DELETE_TEMPLATE] 💾 保存到文件...")
        templates_path = get_templates_path()
        print(f"[DELETE_TEMPLATE] 文件路径: {templates_path}")
        
        with open(templates_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_templates, f, ensure_ascii=False, indent=2)
        
        success_msg = f"成功删除模板 (共 {original_count - len(filtered_templates)} 个)"
        print(f"[DELETE_TEMPLATE] ✅ {success_msg}")
        print(f"{'='*70}\n")
        return True, success_msg
        
    except PermissionError as e:
        error_msg = "文件权限不足，无法删除模板"
        print(f"[DELETE_TEMPLATE] ❌ PermissionError: {e}")
        print(f"[DELETE_TEMPLATE] {error_msg}")
        print(f"{'='*70}\n")
        return False, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"模板文件格式错误: {str(e)}"
        print(f"[DELETE_TEMPLATE] ❌ JSONDecodeError: {e}")
        print(f"[DELETE_TEMPLATE] {error_msg}")
        print(f"{'='*70}\n")
        return False, error_msg
    except Exception as e:
        error_msg = f"删除失败: {str(e)}"
        print(f"[DELETE_TEMPLATE] ❌ Exception: {type(e).__name__}")
        print(f"[DELETE_TEMPLATE] 错误详情: {e}")
        import traceback
        print(f"[DELETE_TEMPLATE] 堆栈跟踪:\n{traceback.format_exc()}")
        print(f"{'='*70}\n")
        return False, error_msg


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
