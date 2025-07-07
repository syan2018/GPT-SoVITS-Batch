@echo off
chcp 65001 >nul
echo === GPT-SoVITS-Batch 打包工具 ===
echo.

echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 安装/更新依赖...
pip install -r requirements.txt

echo.
echo 开始打包...
pyinstaller GPT-SoVITS-Batch.spec

if %errorlevel% equ 0 (
    echo.
    echo ✓ 打包成功!
    echo 生成的exe文件位于: dist\GPT-SoVITS-Batch.exe
    echo.
    echo 使用说明:
    echo 1. 将dist文件夹中的GPT-SoVITS-Batch.exe复制到目标机器
    echo 2. 确保目标机器上有config.yaml配置文件
    echo 3. 双击运行exe文件即可
) else (
    echo.
    echo × 打包失败!
    echo 请检查错误信息
)

echo.
pause 