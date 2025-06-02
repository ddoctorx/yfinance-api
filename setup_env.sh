#!/bin/bash

# Finance API 环境配置脚本
# 用于快速设置开发或生产环境

echo "🚀 Finance API 环境配置向导"
echo "================================"

# 检查是否已存在 .env 文件
if [ -f ".env" ]; then
    echo "⚠️  发现现有的 .env 文件"
    read -p "是否要备份现有配置并创建新的？(y/N): " backup_existing
    if [ "$backup_existing" = "y" ] || [ "$backup_existing" = "Y" ]; then
        mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ 已备份到 .env.backup.$(date +%Y%m%d_%H%M%S)"
    else
        echo "❌ 配置已取消"
        exit 0
    fi
fi

# 复制配置模板
cp config.env .env
echo "✅ 已从 config.env 创建 .env 文件"

echo ""
echo "📝 请配置以下API密钥（可选）："
echo ""

# 询问 Polygon API 密钥
echo "1. Polygon.io API 密钥（用于数据源降级）"
echo "   获取地址: https://polygon.io/dashboard/api-keys"
read -p "   请输入Polygon API密钥 (回车跳过): " polygon_key

if [ ! -z "$polygon_key" ]; then
    sed -i.bak "s/POLYGON_API_KEY=your_polygon_api_key_here/POLYGON_API_KEY=$polygon_key/" .env
    echo "   ✅ Polygon API密钥已设置"
fi

echo ""

# 询问 SEC API 密钥
echo "2. SEC API 密钥（用于财务报表数据）"
echo "   获取地址: https://sec-api.io/dashboard"
read -p "   请输入SEC API密钥 (回车跳过): " sec_key

if [ ! -z "$sec_key" ]; then
    sed -i.bak "s/SEC_API_KEY=your_sec_api_key_here/SEC_API_KEY=$sec_key/" .env
    echo "   ✅ SEC API密钥已设置"
fi

echo ""

# 询问环境类型
echo "3. 环境配置"
read -p "   这是生产环境吗？(y/N): " is_production

if [ "$is_production" = "y" ] || [ "$is_production" = "Y" ]; then
    sed -i.bak 's/DEBUG=true/DEBUG=false/' .env
    sed -i.bak 's/LOG_LEVEL=INFO/LOG_LEVEL=WARNING/' .env
    sed -i.bak 's/CORS_ORIGINS=\*/CORS_ORIGINS=your_frontend_domain.com/' .env
    echo "   ✅ 已配置为生产环境"
else
    echo "   ✅ 保持开发环境配置"
fi

# 清理备份文件
rm -f .env.bak

echo ""
echo "🎉 配置完成！"
echo ""
echo "📋 下一步："
echo "1. 如果跳过了API密钥配置，可以稍后编辑 .env 文件添加"
echo "2. 运行 ./start_with_sec_api.sh 启动服务"
echo "3. 访问 http://localhost:8000/docs 查看API文档"
echo ""
echo "📁 配置文件位置："
echo "   配置模板: config.env"
echo "   实际配置: .env"
echo ""
echo "🔑 API密钥获取地址："
echo "   Polygon.io: https://polygon.io/dashboard/api-keys"
echo "   SEC API:    https://sec-api.io/dashboard"
echo ""