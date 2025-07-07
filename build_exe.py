#!/usr/bin/env python3
"""
自动打包脚本
使用PyInstaller将应用打包成独立的exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd):
    """运行命令并显示输出"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    print("=== GPT-SoVITS-Batch 打包工具 ===")
    
    # 检查是否安装了PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("× PyInstaller 未安装，正在安装...")
        if not run_command("pip install pyinstaller"):
            print("安装 PyInstaller 失败，请手动安装")
            return
    
    # 创建dist目录
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("清理旧的打包文件...")
        shutil.rmtree(dist_dir)
    
    # 创建build目录
    build_dir = Path("build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    print("开始打包...")
    
    # PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--onefile",  # 打包成单个文件
        "--windowed",  # 不显示控制台窗口
        "--add-data", "config.yaml;.",  # 包含配置文件
        "--add-data", "raw_scripts;raw_scripts",  # 包含脚本目录
        "--add-data", "images;images",  # 包含图片目录
        "--name", "GPT-SoVITS-Batch",  # 程序名称
        "--icon", "images/tmp3CCE.png" if Path("images/tmp3CCE.png").exists() else None,  # 图标
        "dubbing_tool/main.py"  # 入口文件
    ]
    
    # 移除None值
    cmd = [arg for arg in cmd if arg is not None]
    
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)
    
    if run_command(cmd_str):
        print("\n✓ 打包成功!")
        print(f"生成的exe文件位于: {dist_dir / 'GPT-SoVITS-Batch.exe'}")
        print("\n使用说明:")
        print("1. 将生成的exe文件复制到目标机器")
        print("2. 确保目标机器上有config.yaml配置文件")
        print("3. 双击运行exe文件即可")
    else:
        print("\n× 打包失败!")

if __name__ == "__main__":
    main() 