# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - 把后端打成单文件 costpilot-server.exe
# 用法:
#   pip install pyinstaller
#   pyinstaller costpilot-server.spec --noconfirm
# 产出: dist/costpilot-server.exe
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 收集所有子模块(pydantic / sqlalchemy 等动态导入)
hidden_imports = []
hidden_imports += collect_submodules('fastapi')
hidden_imports += collect_submodules('pydantic')
hidden_imports += collect_submodules('sqlalchemy')
hidden_imports += collect_submodules('alembic')
hidden_imports += collect_submodules('openpyxl')
hidden_imports += collect_submodules('docx')
hidden_imports += collect_submodules('uvicorn')
hidden_imports += ['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
                  'uvicorn.protocols', 'uvicorn.protocols.http.auto',
                  'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on']

datas = []
datas += collect_data_files('alembic')
datas += collect_data_files('openpyxl')
datas += collect_data_files('docx')

# 配置文件 / 数据库 留给 setup 阶段加,不进 PyInstaller
# 用户首次启动时 alembic + import 自动建库

a = Analysis(
    ['packages/server/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PyQt6', 'matplotlib', 'pytest', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='costpilot-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 后端服务保留控制台,electron 启动时 stdio 重定向,无窗口闪现
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
