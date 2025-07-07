# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 获取项目根目录
project_root = Path.cwd()

a = Analysis(
    ['dubbing_tool/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('raw_scripts', 'raw_scripts'),
        ('images', 'images'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'PIL._tkinter_finder',
        'requests',
        'yaml',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 移除不必要的文件以减小体积
a.datas = [x for x in a.datas if not x[0].startswith('tcl')]
a.datas = [x for x in a.datas if not x[0].startswith('tk')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GPT-SoVITS-Batch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
) 