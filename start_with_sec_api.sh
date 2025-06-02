#!/bin/bash

# Finance API 启动脚本 (包含SEC API配置)
# 使用方法: ./start_with_sec_api.sh

set -e

echo "🚀 启动 Finance API (包含SEC财报功能)"
echo "================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 设置SEC API密钥 (用户提供的真实密钥)
export SEC_API_KEY="1235d649f00e88f49b15dde9f8d0404b0344757e443f3f05e6b0d2a78f3f0b51"

# 设置其他环境变量
export DEBUG=true
export LOG_LEVEL=INFO
export HOST=127.0.0.1
export PORT=8000

echo "✅ 环境变量配置:"
echo "   SEC_API_KEY: ${SEC_API_KEY:0:10}..."
echo "   HOST: $HOST"
echo "   PORT: $PORT"
echo ""

# 启动服务
echo "🌟 启动API服务..."
./venv/bin/python -m uvicorn app.main:app --host $HOST --port $PORT --reload

echo ""
echo "📚 API文档地址:"
echo "   Swagger UI: http://$HOST:$PORT/docs"
echo "   ReDoc: http://$HOST:$PORT/redoc"
echo ""
echo "🔧 SEC API端点:"
echo "   健康检查: http://$HOST:$PORT/api/v1/sec/health"
echo "   财务数据: http://$HOST:$PORT/api/v1/sec/financials/AAPL"
echo "   SEC新闻: http://$HOST:$PORT/api/v1/sec/news/AAPL"
echo "   财务比率: http://$HOST:$PORT/api/v1/sec/ratios/AAPL" 