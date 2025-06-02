#!/usr/bin/env python3
"""
测试降级系统
验证 yfinance -> Polygon.io 的自动降级机制
"""

from app.core.logging import get_logger
from app.core.config import settings
from app.services.data_source_manager import DataSourceManager
import asyncio
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


logger = get_logger(__name__)


async def test_basic_functionality():
    """测试基本功能"""
    print("🚀 开始测试数据源管理器...")

    # 创建数据源管理器
    manager = DataSourceManager()

    # 测试获取快速报价
    print("\n📊 测试快速报价...")
    try:
        quote = await manager.get_fast_quote("AAPL")
        print(f"✅ 快速报价成功: ${quote.last_price}")
        print(f"   数据源: {getattr(quote, 'data_source', 'unknown')}")
    except Exception as e:
        print(f"❌ 快速报价失败: {e}")

    # 测试获取详细报价
    print("\n📈 测试详细报价...")
    try:
        detailed = await manager.get_detailed_quote("AAPL")
        print(f"✅ 详细报价成功: ${detailed.last_price}")
        print(
            f"   市值: ${detailed.market_cap:,}" if detailed.market_cap else "   市值: N/A")
        print(f"   数据源: {getattr(detailed, 'data_source', 'unknown')}")
    except Exception as e:
        print(f"❌ 详细报价失败: {e}")

    # 测试获取公司信息
    print("\n🏢 测试公司信息...")
    try:
        info = await manager.get_company_info("AAPL")
        print(f"✅ 公司信息成功: {info.name}")
        print(f"   行业: {info.sector}")
        print(f"   数据源: {getattr(info, 'data_source', 'unknown')}")
    except Exception as e:
        print(f"❌ 公司信息失败: {e}")

    # 测试历史数据
    print("\n📊 测试历史数据...")
    try:
        history = await manager.get_history("AAPL", period="5d")
        if isinstance(history, dict) and 'prices' in history:
            prices = history['prices']
            if 'Close' in prices and prices['Close']:
                print(f"✅ 历史数据成功: {len(prices['Close'])} 个数据点")
            else:
                print(f"✅ 历史数据成功: 数据格式不同")
        else:
            print(f"✅ 历史数据成功: {type(history)}")
        print(
            f"   数据源: {history.get('data_source', 'unknown') if isinstance(history, dict) else 'unknown'}")
    except Exception as e:
        print(f"❌ 历史数据失败: {e}")

    # 显示状态
    print("\n📊 数据源状态:")
    status = manager.get_status()
    fallback_status = status.get('fallback_manager', {})

    if 'sources' in fallback_status:
        for source in fallback_status['sources']:
            health_indicator = "🟢" if source['status'] == 'healthy' else "🟡" if source['status'] == 'degraded' else "🔴"
            print(
                f"   {health_indicator} {source['name']}: {source['status']}")
            print(f"      请求数: {source['metrics']['total_requests']}")
            print(f"      成功率: {source['metrics']['success_rate']:.2%}")
    else:
        print("   状态信息不可用")

    await manager.shutdown()


async def test_fallback_mechanism():
    """测试降级机制"""
    print("\n\n🔄 测试降级机制...")

    manager = DataSourceManager()

    # 手动触发降级
    print("🔧 手动触发降级...")
    await manager.force_fallback("测试降级机制")

    # 检查状态
    status = manager.get_status()
    fallback_status = status.get('fallback_manager', {})
    print(
        f"   降级状态: {'启用' if fallback_status.get('should_use_fallback', False) else '禁用'}")
    print(f"   连续失败次数: {fallback_status.get('consecutive_failures', 0)}")

    # 在降级状态下获取数据
    print("\n📊 在降级状态下获取数据...")
    try:
        quote = await manager.get_fast_quote("AAPL")
        print(f"✅ 降级数据获取成功: ${quote.last_price}")
        is_fallback = getattr(quote, 'is_fallback', False)
        data_source = getattr(quote, 'data_source', 'unknown')
        print(f"   是否降级数据: {'是' if is_fallback else '否'}")
        print(f"   数据源: {data_source}")
    except Exception as e:
        print(f"❌ 降级数据获取失败: {e}")

    # 重置降级状态
    print("\n🔄 重置降级状态...")
    await manager.reset_fallback()

    status = manager.get_status()
    fallback_status = status.get('fallback_manager', {})
    print(
        f"   重置后状态: {'启用' if fallback_status.get('should_use_fallback', False) else '禁用'}")

    await manager.shutdown()


async def test_health_check():
    """测试健康检查"""
    print("\n\n🏥 测试健康检查...")

    manager = DataSourceManager()

    # 执行健康检查
    health_results = await manager.health_check()

    print("健康检查结果:")
    for source_name, is_healthy in health_results.items():
        status_indicator = "🟢" if is_healthy else "🔴"
        print(
            f"   {status_indicator} {source_name}: {'健康' if is_healthy else '不健康'}")

    await manager.shutdown()


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Polygon.io 降级系统测试")
    print("=" * 60)

    # 显示配置信息
    print(f"🔧 配置信息:")
    print(f"   降级启用: {settings.fallback_enabled}")
    print(f"   最大失败次数: {settings.primary_source_max_failures}")
    print(f"   超时时间: {settings.fallback_timeout}秒")
    print(f"   冷却期: {settings.fallback_cooldown_period}秒")
    print(f"   Polygon API密钥: {'已配置' if settings.polygon_api_key else '未配置'}")

    if not settings.polygon_api_key:
        print("❌ 错误: 未配置 Polygon API 密钥")
        return

    try:
        # 测试基本功能
        await test_basic_functionality()

        # 测试降级机制
        await test_fallback_mechanism()

        # 测试健康检查
        await test_health_check()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
