@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+ 并勾选 "Add to PATH"
    pause & exit /b 1
)
python -c "import requests" >nul 2>nul
if errorlevel 1 (
    echo [提示] 正在安装 requests ...
    python -m pip install -r requirements.txt
)
python tvbox_gui.py
if errorlevel 1 pause
