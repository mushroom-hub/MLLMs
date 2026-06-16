@echo off
REM Windows 启动脚本
REM 一键启动后端服务

echo.
echo ================================
echo   EduBrain AI 后端启动脚本
echo ================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip list | findstr flask >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动 EduBrain AI 后端服务...
echo 后端地址: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务
echo.

python web/app.py

pause
