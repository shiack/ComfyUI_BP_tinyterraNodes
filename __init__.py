from .ttNpy.tinyterraNodes import TTN_VERSIONS
from .ttNpy import ttNserver # Do Not Remove
import configparser
import folder_paths
import subprocess
import shutil
import os

# ------- CONFIG -------- #
cwd_path = os.path.dirname(os.path.realpath(__file__))
js_path = os.path.join(cwd_path, "js")
comfy_path = folder_paths.base_path

config_path = os.path.join(cwd_path, "config.ini")

optionValues = {
        "auto_update": ('true', 'false'),
        "enable_embed_autocomplete": ('true', 'false'),
        "enable_interface": ('true', 'false'),
        "enable_fullscreen": ('true', 'false'),
        "enable_dynamic_widgets": ('true', 'false'),
        "enable_dev_nodes": ('true', 'false'),
    }

def get_config():
    """Return a configparser.ConfigParser object."""
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def fix_config_format():
    """修复配置文件格式问题"""
    if not os.path.isfile(config_path):
        return
        
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    current_section = None
    
    for line in lines:
        stripped_line = line.strip()
        
        # 处理章节行
        if stripped_line.startswith('[') and stripped_line.endswith(']'):
            current_section = stripped_line
            fixed_lines.append(line)
            continue
            
        # 处理注释行和空行
        if not stripped_line or stripped_line.startswith(';') or stripped_line.startswith('#'):
            fixed_lines.append(line)
            continue
            
        # 处理键值对
        if '=' in line:
            # 分割键和值
            parts = line.split('=', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # 跳过空键
            if not key:
                print(f"Removing invalid line (empty key): {line.strip()}")
                continue
                
            # 修复键名：移除空格和特殊字符，用下划线替换空格
            fixed_key = key.replace(' ', '_').replace('\t', '_')
            
            # 确保键名是有效的
            if fixed_key and not fixed_key.startswith('='):
                fixed_lines.append(f"{fixed_key} = {value}\n")
            else:
                print(f"Removing invalid line: {line.strip()}")
        else:
            # 保持原样（可能是格式错误的行，但我们会保留）
            fixed_lines.append(line)
    
    # 写回文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

def update_config():
    """更新配置文件"""
    # 先修复格式问题
    fix_config_format()
    
    config = get_config()
    
    # 先清理可能存在的重复项
    clean_duplicate_config()
    
    # 更新版本信息（只在Versions section存在时）
    if hasattr(TTN_VERSIONS, 'items'):
        for node, version in TTN_VERSIONS.items():
            # 确保节点名称不包含空格
            node_clean = node.replace(' ', '_')
            config_write("Versions", node_clean, version)
    
    # 设置默认值（仅在缺失时）
    section_data = {
        "ttNodes": {
            "auto_update": 'False',
            "enable_interface": 'True',
            "enable_fullscreen": 'True',
            "enable_embed_autocomplete": 'True',
            "enable_dynamic_widgets": 'True',
            "enable_dev_nodes": 'False',
        }
    }

    for section, data in section_data.items():
        for option, default_value in data.items():
            current_value = config_read(section, option)
            if current_value is None:
                config_write(section, option, default_value)

def clean_duplicate_config():
    """清理重复的配置项"""
    config = get_config()
    cleaned = False
    
    for section in config.sections():
        seen_options = set()
        options_to_remove = []
        
        for option in config.options(section):
            if option in seen_options:
                options_to_remove.append(option)
                print(f"Removing duplicate option: [{section}] {option}")
            else:
                seen_options.add(option)
        
        for option in options_to_remove:
            config.remove_option(section, option)
            cleaned = True
    
    if cleaned:
        with open(config_path, 'w') as f:
            config.write(f)

def config_load():
    """Load the entire configuration into a dictionary."""
    config = get_config()
    return {section: dict(config.items(section)) for section in config.sections()}

def config_read(section, option):
    """Read a configuration option."""
    config = get_config()
    return config.get(section, option, fallback=None)

def config_write(section, option, value):
    """写入配置选项，确保不重复"""
    config = get_config()
    
    if not config.has_section(section):
        config.add_section(section)
    
    # 如果选项已存在，先移除再添加（避免重复）
    if config.has_option(section, option):
        config.remove_option(section, option)
    
    config.set(section, str(option), str(value))
    
    with open(config_path, 'w') as f:
        config.write(f)

def config_remove(section, option):
    """Remove an option from a section."""
    config = get_config()
    if config.has_section(section):
        config.remove_option(section, option)
        with open(config_path, 'w') as f:
            config.write(f)

def config_value_validator(section, option, default):
    value = str(config_read(section, option)).lower()
    if value not in optionValues[option]:
        print(f'\033[92m[{section} Config]\033[91m {option} - \'{value}\' not in {optionValues[option]}, reverting to default.\033[0m')
        config_write(section, option, default)
        return default
    else:
        return value

# Create a config file if not exists
if not os.path.isfile(config_path):
    with open(config_path, 'w') as f:
        pass

# 修复现有配置文件的格式问题
fix_config_format()
update_config()

# Autoupdate if True
if config_value_validator("ttNodes", "auto_update", 'false') == 'true':
    try:
        with subprocess.Popen(["git", "pull"], cwd=cwd_path, stdout=subprocess.PIPE) as p:
            p.wait()
            result = p.communicate()[0].decode()
            if result != "Already up to date.\n":
                print("\033[92m[t ttNodes Updated t]\033[0m")
    except:
        pass

# --------- WEB ---------- #
# Remove old web JS folder
web_extension_path = os.path.join(comfy_path, "web", "extensions", "tinyterraNodes")

if os.path.exists(web_extension_path):
    try:
        shutil.rmtree(web_extension_path)
    except:
        print("\033[92m[ttNodes] \033[0;31mFailed to remove old web extension.\033[0m")

js_files = {
    "interface": "enable_interface",
    "fullscreen": "enable_fullscreen",
    "embedAC": "enable_embed_autocomplete",
    "dynamicWidgets": "enable_dynamic_widgets",
}
for js_file, config_key in js_files.items():
    file_path = os.path.join(js_path, f"ttN{js_file}.js")
    if config_value_validator("ttNodes", config_key, 'true') == 'false' and os.path.isfile(file_path):
        os.rename(file_path, f"{file_path}.disable")
    elif config_value_validator("ttNodes", config_key, 'true') == 'true' and os.path.isfile(f"{file_path}.disable"):
        os.rename(f"{file_path}.disable", file_path)

# Enable Dev Nodes if True
if config_value_validator("ttNodes", "enable_dev_nodes", 'true') == 'true':
    from .ttNdev import NODE_CLASS_MAPPINGS as ttNdev_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as ttNdev_DISPLAY_NAME_MAPPINGS
else:
    ttNdev_CLASS_MAPPINGS = {}
    ttNdev_DISPLAY_NAME_MAPPINGS = {}

# ------- MAPPING ------- #
from .ttNpy.tinyterraNodes import NODE_CLASS_MAPPINGS as TTN_CLASS_MAPPINGS,  NODE_DISPLAY_NAME_MAPPINGS as TTN_DISPLAY_NAME_MAPPINGS
from .ttNpy.ttNlegacyNodes import NODE_CLASS_MAPPINGS as LEGACY_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as LEGACY_DISPLAY_NAME_MAPPINGS

NODE_CLASS_MAPPINGS = {**TTN_CLASS_MAPPINGS, **LEGACY_CLASS_MAPPINGS, **ttNdev_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**TTN_DISPLAY_NAME_MAPPINGS, **LEGACY_DISPLAY_NAME_MAPPINGS, **ttNdev_DISPLAY_NAME_MAPPINGS}

WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
