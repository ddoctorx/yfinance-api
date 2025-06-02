#!/bin/bash

# Finance API 快速启动脚本
# 用法: ./start.sh

set -e

echo "🚀 Finance API - 快速启动"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 setup"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "❌ 配置文件不存在，请先运行 ./start_api.sh 进行完整配置"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs) 2>/dev/null || true

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

echo "🌟 启动服务 http://$HOST:$PORT"

# 启动服务
./venv/bin/python -m uvicorn app.main:app --host $HOST --port $PORT --reload