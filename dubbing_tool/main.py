import os
import sys
import customtkinter as ctk
from tkinter import messagebox
from dubbing_tool.api_client import ApiClient
from dubbing_tool.gui import App
from dubbing_tool.utils import load_config

def main():
    # --- 配置和初始化 ---
    # 获取exe文件所在目录，寻找config.yaml
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境
        app_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_path = os.path.join(app_dir, 'config.yaml')
    config = load_config(config_path)
    
    if config is None:
        # 创建一个临时的根窗口来显示错误消息
        root = ctk.CTk()
        root.withdraw() # 隐藏主窗口
        messagebox.showerror("配置错误", f"无法加载 config.yaml，请检查文件是否存在且格式正确。\n寻找路径: {config_path}")
        root.destroy()
        sys.exit(1)

    api_config = config.get('api', {})
    inference_defaults = config.get('inference_defaults', {})
    output_dir = config.get('output_dir', 'output')

    if not api_config.get('base_url'):
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("配置错误", "配置文件中缺少 API base_url。")
        root.destroy()
        sys.exit(1)

    # 确保输出目录存在（相对于exe文件位置）
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(app_dir, output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 初始化 API 客户端
    api_client = ApiClient(
        base_url=api_config['base_url'],
        default_params=inference_defaults
    )

    # --- 启动 GUI ---
    app = App(
        api_client=api_client,
        output_dir=output_dir
    )
    app.mainloop()

if __name__ == '__main__':
    main() 