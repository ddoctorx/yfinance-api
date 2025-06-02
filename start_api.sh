#!/bin/bash

# Finance API 主启动脚本
# 启动完整的金融数据API服务 (包含所有数据源)
# 使用方法: ./start_api.sh

set -e

echo "🚀 启动 Finance API 服务"
echo "=========================================="
echo "📊 数据源: Yahoo Finance + Polygon.io + SEC API"
echo "🔧 架构: 单体应用 (所有功能在一个服务中)"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    echo "请先运行以下命令创建环境:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 配置文件"
    echo ""
    read -p "是否运行配置向导创建 .env 文件？(Y/n): " run_setup
    if [ "$run_setup" != "n" ] && [ "$run_setup" != "N" ]; then
        if [ -f "setup_env.sh" ]; then
            ./setup_env.sh
        else
            echo "📝 配置向导不存在，手动创建配置..."
            cp config.env .env
            echo "✅ 已从模板创建 .env 文件，请编辑后重新启动"
            exit 0
        fi
        echo ""
    else
        echo "❌ 请先创建 .env 配置文件"
        echo "   运行: cp config.env .env"
        echo "   然后编辑 .env 文件添加API密钥"
        exit 1
    fi
fi

# 加载环境变量
if [ -f ".env" ]; then
    echo "📋 加载配置文件: .env"
    export $(grep -v '^#' .env | xargs)
fi

# 设置默认值
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
DEBUG=${DEBUG:-true}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "✅ 服务配置:"
echo "   HOST: $HOST"
echo "   PORT: $PORT"
echo "   DEBUG: $DEBUG"
echo "   LOG_LEVEL: $LOG_LEVEL"
echo ""

# 检查API密钥配置
echo "🔑 API密钥状态:"

# Yahoo Finance (免费，无需密钥)
echo "   Yahoo Finance: ✅ 免费数据源 (主要)"

# Polygon.io 检查
if [ ! -z "$POLYGON_API_KEY" ] && [ "$POLYGON_API_KEY" != "your_polygon_api_key_here" ]; then
    echo "   Polygon.io: ✅ 已配置 (${POLYGON_API_KEY:0:10}...)"
    POLYGON_AVAILABLE=true
else
    echo "   Polygon.io: ⚠️  未配置 (降级功能受限)"
    POLYGON_AVAILABLE=false
fi

# SEC API 检查
if [ ! -z "$SEC_API_KEY" ] && [ "$SEC_API_KEY" != "your_sec_api_key_here" ]; then
    echo "   SEC API: ✅ 已配置 (${SEC_API_KEY:0:10}...)"
    SEC_AVAILABLE=true
else
    echo "   SEC API: ⚠️  未配置 (财报功能不可用)"
    SEC_AVAILABLE=false
fi

echo ""

# 显示功能状态
echo "📊 功能模块状态:"
echo "   股票报价: ✅ 可用 (Yahoo Finance)"
echo "   历史数据: ✅ 可用 (Yahoo Finance)"
echo "   公司信息: ✅ 可用 (Yahoo Finance)"
if [ "$POLYGON_AVAILABLE" = true ]; then
    echo "   智能降级: ✅ 可用 (Polygon.io备用)"
else
    echo "   智能降级: ⚠️  受限 (仅Yahoo Finance)"
fi
if [ "$SEC_AVAILABLE" = true ]; then
    echo "   SEC财报: ✅ 可用 (官方数据)"
else
    echo "   SEC财报: ❌ 不可用 (需要API密钥)"
fi

echo ""

# 启动服务
echo "🌟 启动API服务..."
echo "请稍候，正在初始化所有数据源..."
echo ""

# 后台启动服务
./venv/bin/python -m uvicorn app.main:app --host $HOST --port $PORT --reload &
SERVER_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查服务是否启动成功
if curl -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
    echo ""
    echo "🎉 服务启动成功！"
else
    echo ""
    echo "❌ 服务启动失败，请检查日志"
    exit 1
fi

echo ""
echo "=========================================="
echo "📚 API文档和访问地址:"
echo "=========================================="
echo "   🌟 Swagger UI: http://$HOST:$PORT/docs"
echo "   📄 ReDoc: http://$HOST:$PORT/redoc"
echo "   ❤️  健康检查: http://$HOST:$PORT/health"

echo "🔧 主要API端点:"
echo "   📈 股票报价: http://$HOST:$PORT/api/v1/quote/AAPL"
echo "   📊 历史数据: http://$HOST:$PORT/api/v1/history/AAPL"
echo "   🏢 公司信息: http://$HOST:$PORT/api/v1/quote/AAPL/info"
echo "   🧪 健康检查: http://$HOST:$PORT/api/v1/test/health-check"

if [ "$SEC_AVAILABLE" = true ]; then
    echo ""
    echo "💼 SEC财报API (已启用):"
    echo "   📋 财务报表: http://$HOST:$PORT/api/v1/sec/financials/AAPL"
    echo "   📈 季度收入: http://$HOST:$PORT/api/v1/sec/quarterly-revenue/AAPL"
    echo "   📊 财务比率: http://$HOST:$PORT/api/v1/sec/ratios/AAPL"
    echo "   📰 SEC新闻: http://$HOST:$PORT/api/v1/sec/news/AAPL"
fi

echo ""
echo "=========================================="
echo "💡 使用提示:"
echo "=========================================="
echo "   🌟 推荐先访问: http://$HOST:$PORT/docs"
echo "   🔧 可以直接在Swagger UI中测试所有接口"
echo "   📊 支持的股票代码: AAPL, MSFT, GOOGL, TSLA 等"
echo "   ⏹️  按 Ctrl+C 停止服务"

if [ "$SEC_AVAILABLE" = false ]; then
    echo ""
    echo "⚠️  要启用SEC财报功能:"
    echo "   1. 获取API密钥: https://sec-api.io/dashboard"
    echo "   2. 在 .env 文件中设置: SEC_API_KEY=your_key"
    echo "   3. 重启服务"
fi

if [ "$POLYGON_AVAILABLE" = false ]; then
    echo ""
    echo "⚠️  要启用完整降级功能:"
    echo "   1. 获取API密钥: https://polygon.io/dashboard/api-keys"
    echo "   2. 在 .env 文件中设置: POLYGON_API_KEY=your_key"
    echo "   3. 重启服务"
fi

echo ""
echo "🚀 服务运行中... (PID: $SERVER_PID)"

# 等待用户中断
wait $SERVER_PID