#!/bin/bash
# Linux/Mac 启动脚本

echo ""
echo "================================"
echo "  EduBrain AI 后端启动脚本"
echo "================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未检测到 Python，请先安装 Python 3.10+"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败"
        exit 1
    fi
fi

echo ""
echo "启动 EduBrain AI 后端服务..."
echo "后端地址: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 web/app.py
