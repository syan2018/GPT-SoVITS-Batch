import yaml
from typing import Dict, Any

def parse_script(file_path: str) -> Dict[str, Any] | None:
    """
    解析 YAML 格式的剧本文件。

    :param file_path: 剧本文件的路径。
    :return: 包含剧本内容的字典，如果失败则返回 None。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            script_data = yaml.safe_load(f)
        
        # 基本的验证
        if 'scenes' not in script_data or not isinstance(script_data['scenes'], list):
            print(f"错误: 剧本 '{file_path}' 缺少 'scenes' 列表。")
            return None
            
        return script_data

    except FileNotFoundError:
        print(f"错误: 文件未找到 '{file_path}'")
        return None
    except yaml.YAMLError as e:
        print(f"错误: 解析 YAML 文件 '{file_path}' 时出错: {e}")
        return None
    except Exception as e:
        print(f"解析文件时发生未知错误: {e}")
        return None

if __name__ == '__main__':
    # 用于测试解析器
    test_script_path = '../raw_scripts/青丘山剧本.yaml'
    parsed_data = parse_script(test_script_path)
    
    if parsed_data:
        print(f"剧本标题: {parsed_data.get('script_name', '无标题')}")
        print(f"共解析出 {len(parsed_data.get('scenes', []))} 个章节。")
        first_scene = parsed_data.get('scenes', [{}])[0]
        print(f"第一个章节 '{first_scene.get('scene_name')}' 有 {len(first_scene.get('dialogues', []))} 句对话。")
        print("\n前2条对话示例:")
        for item in first_scene.get('dialogues', [])[:2]:
            print(item) 