# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current directory
current_dir = Path('.')

# Define data files to include
datas = [
    # Include the logo
    ('SholaLogo.JPG', 'assets'),
    # Include existing data folders with their contents
    ('xml', 'xml'),
    ('processed', 'processed'),
    ('logs', 'logs'),
]

# Add any existing files in the folders
if (current_dir / 'xml').exists():
    for xml_file in (current_dir / 'xml').glob('*.xml'):
        datas.append((str(xml_file), 'xml'))

if (current_dir / 'processed').exists():
    for pdf_file in (current_dir / 'processed').glob('*.pdf'):
        datas.append((str(pdf_file), 'processed'))

if (current_dir / 'logs').exists():
    for log_file in (current_dir / 'logs').glob('*.log'):
        datas.append((str(log_file), 'logs'))

a = Analysis(
    ['main.py'],
    pathex=['src'],  # Add src to the path so PyInstaller can find modules
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt6 modules that might not be auto-detected
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        # PDF processing libraries
        'PyPDF2',
        'pdfplumber',
        'fitz',  # PyMuPDF
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.platypus',
        # Database
        'pyodbc',
        # File monitoring
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        # HTTP requests
        'requests',
        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        # Other potentially needed modules
        'xml.etree.ElementTree',
        'base64',
        'json',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MCFax',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Could add an icon file here if we had one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MCFax',
)

# Post-build: Create additional required folders in the distribution
import shutil
import os

dist_dir = Path('dist/MCFax')
if dist_dir.exists():
    # Create empty folders that the application needs
    required_folders = ['temp', 'settings']
    for folder in required_folders:
        folder_path = dist_dir / folder
        folder_path.mkdir(exist_ok=True)
        
        # Create a placeholder file to ensure the folder is included
        placeholder = folder_path / '.gitkeep'
        placeholder.touch()
    
    print(f"✓ Created required folders in {dist_dir}")
