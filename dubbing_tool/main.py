import os
import customtkinter as ctk
from .api_client import ApiClient
from .gui import App
from .utils import load_config

def main():
    # --- 配置和初始化 ---
    config = load_config()
    if config is None:
        # 创建一个临时的根窗口来显示错误消息
        root = ctk.CTk()
        root.withdraw() # 隐藏主窗口
        ctk.messagebox.showerror("配置错误", "无法加载 config.yaml，请检查文件是否存在且格式正确。")
        root.destroy()
        exit(1)

    api_config = config.get('api', {})
    character_mapping = config.get('characters', {})
    inference_defaults = config.get('inference_defaults', {})
    output_dir = config.get('output_dir', 'output')

    if not api_config.get('base_url'):
        root = ctk.CTk()
        root.withdraw()
        ctk.messagebox.showerror("配置错误", "配置文件中缺少 API base_url。")
        root.destroy()
        exit(1)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 初始化 API 客户端
    api_client = ApiClient(
        base_url=api_config['base_url'],
        default_params=inference_defaults
    )

    # --- 启动 GUI ---
    app = App(
        api_client=api_client,
        character_mapping=character_mapping,
        output_dir=output_dir
    )
    app.mainloop()

if __name__ == '__main__':
    main() 