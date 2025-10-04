@echo off
chcp 65001 >nul
title OCR工具 - 便携式版本
echo ========================================
echo OCR工具启动中...
echo ========================================

REM 设置当前目录为脚本所在目录
cd /d "%~dp0"

REM 设置环境变量避免中文路径问题
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

REM 设置Python环境变量
set PYTHONHOME=%~dp0python-3.9.0-embed-amd64
set PYTHONPATH=%~dp0python-3.9.0-embed-amd64\Lib;%~dp0python-3.9.0-embed-amd64\DLLs;%~dp0
set PATH=%PYTHONHOME%;%PYTHONHOME%\DLLs;%PYTHONHOME%\Lib\site-packages\paddle\libs;%PATH%

REM 设置TCL/TK环境变量
set TCL_LIBRARY=%~dp0python-3.9.0-embed-amd64\tcl\tcl8.6
set TK_LIBRARY=%~dp0python-3.9.0-embed-amd64\tcl\tk8.6

REM 设置PaddleOCR环境变量 - 关键修复！
set PADDLEOCR_HOME=%~dp0models
set PADDLEOCR_DISABLE_DOWNLOAD=True
set PADDLEOCR_DOWNLOAD=False

echo 环境变量设置完成
echo Python路径: %PYTHONHOME%
echo PaddleOCR模型路径: %PADDLEOCR_HOME%
echo 禁用网络下载: %PADDLEOCR_DISABLE_DOWNLOAD%
echo.

REM 启动OCR程序
echo 正在启动OCR程序...
"%~dp0python-3.9.0-embed-amd64\python.exe" "%~dp0main.py"

REM 如果程序异常退出，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo 程序异常退出，错误代码: %errorlevel%
    echo ========================================
    pause
)
