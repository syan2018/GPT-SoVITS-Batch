import yaml
import re
import customtkinter as ctk

def load_config(path='config.yaml'):
    """加载配置文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件 '{path}' 未找到。")
        # 在GUI中我们不能在这里创建主窗口，所以只打印并返回None
        # 调用者需要处理这个错误
        return None
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return None

def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    清理字符串，使其成为有效的文件名。
    
    - 移除或替换无效字符
    - 截断到最大长度
    """
    # 移除无效字符
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    # 替换空格
    sanitized = sanitized.replace(' ', '_')
    # 截断
    return sanitized[:max_length] 