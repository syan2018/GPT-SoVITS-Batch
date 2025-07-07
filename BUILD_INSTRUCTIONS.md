# GPT-SoVITS-Batch 打包说明

本文档介绍如何将GPT-SoVITS-Batch应用打包成独立的Windows可执行文件(.exe)。

## 前提条件

1. **Python 3.7+**: 确保已安装Python 3.7或更高版本
2. **pip**: Python包管理器
3. **Windows系统**: 打包需要在Windows系统上进行

## 快速打包

### 方法1: 使用批处理脚本（推荐）

1. 双击运行 `build.bat` 文件
2. 等待打包完成
3. 在 `dist` 目录中找到生成的 `GPT-SoVITS-Batch.exe`

### 方法2: 使用Python脚本

```bash
python build_exe.py
```

### 方法3: 手动打包

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行PyInstaller：
   ```bash
   pyinstaller GPT-SoVITS-Batch.spec
   ```

## 打包输出

打包成功后，会在 `dist` 目录中生成：
- `GPT-SoVITS-Batch.exe` - 主程序可执行文件

## 分发给用户

### 完整分发包

为了让用户能够正常运行程序，请创建一个包含以下文件的文件夹：

```
GPT-SoVITS-Batch/
├── GPT-SoVITS-Batch.exe    # 主程序
├── config.yaml             # 配置文件
├── raw_scripts/            # 脚本目录（可选）
│   ├── 青丘山剧本.txt
│   └── 青丘山剧本.yaml
└── README_USER.md          # 用户说明文档
```

### 用户使用说明

1. 将整个文件夹复制到目标机器
2. 根据需要修改 `config.yaml` 配置文件
3. 双击 `GPT-SoVITS-Batch.exe` 运行程序

## 常见问题

### 1. 打包失败

**问题**: PyInstaller打包过程中报错
**解决**: 
- 确保所有依赖都已正确安装
- 检查Python版本是否兼容
- 尝试升级PyInstaller: `pip install --upgrade pyinstaller`

### 2. 程序无法启动

**问题**: 双击exe文件没有反应或闪退
**解决**:
- 确保 `config.yaml` 文件存在且格式正确
- 检查配置文件中的API地址是否正确
- 尝试在命令行中运行exe以查看错误信息

### 3. 缺少依赖

**问题**: 程序提示缺少某些模块
**解决**:
- 在 `GPT-SoVITS-Batch.spec` 中添加缺失的模块到 `hiddenimports` 列表
- 重新打包

### 4. 文件体积过大

**问题**: 生成的exe文件太大
**解决**:
- 在spec文件中添加更多的excludes
- 使用 `--upx` 选项压缩（已默认启用）
- 考虑使用 `--onedir` 模式而非 `--onefile`

## 高级配置

### 自定义图标

修改 `GPT-SoVITS-Batch.spec` 文件中的icon路径：
```python
icon='your_icon.ico'
```

### 修改打包参数

编辑 `GPT-SoVITS-Batch.spec` 文件，可以调整：
- `console=True` - 显示控制台窗口（调试用）
- `upx=False` - 禁用UPX压缩
- 添加更多的 `datas` 项来包含其他文件

## 版本信息

- PyInstaller版本: 推荐使用最新稳定版
- 支持的Python版本: 3.7+
- 测试环境: Windows 10/11

## 技术支持

如果在打包过程中遇到问题，请检查：
1. Python和pip是否正确安装
2. 所有依赖是否安装成功
3. 是否有足够的磁盘空间
4. 杀毒软件是否误杀了生成的exe文件 