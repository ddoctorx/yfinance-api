#!/usr/bin/env python3
"""
测试金融API降级机制
从Polygon.io降级到Yahoo Finance
"""

import asyncio
import sys
import os
from app.main import app
from app.core.config import settings
from app.data_sources.fallback_manager import FallbackManager
from app.data_sources.polygon_source import PolygonDataSource
from app.data_sources.yfinance_source import YFinanceDataSource


async def test_api_fallback():
    """测试API降级机制"""

    print("🧪 测试金融API降级机制")
    print("=" * 50)

    # 初始化数据源
    polygon_source = PolygonDataSource()
    yahoo_source = YFinanceDataSource()

    # 初始化降级管理器
    manager = FallbackManager(
        primary_source=polygon_source,
        fallback_sources=[yahoo_source]
    )
    await manager.initialize()

    test_symbol = "AAPL"

    # 测试1: 快速报价（应该从Polygon降级到Yahoo）
    print(f"1️⃣ 测试快速报价降级 ({test_symbol})")
    try:
        quote_data = await manager.get_fast_quote(test_symbol)
        print(f"✅ 降级成功获取快速报价:")
        print(f"   📊 股票代码: {test_symbol}")
        print(f"   💰 最新价格: ${quote_data.last_price}")
        print(f"   📈 前收盘价: ${quote_data.previous_close}")
        print(f"   🔄 涨跌: {quote_data.change} ({quote_data.change_percent}%)")
        print(f"   📊 交易量: {quote_data.volume}")
        if hasattr(quote_data, 'timestamp'):
            print(f"   🕐 时间戳: {quote_data.timestamp}")
    except Exception as e:
        print(f"❌ 快速报价降级失败: {e}")

    print()

    # 测试2: 详细报价（应该从Polygon降级到Yahoo）
    print(f"2️⃣ 测试详细报价降级 ({test_symbol})")
    try:
        detailed_quote = await manager.get_detailed_quote(test_symbol)
        print(f"✅ 降级成功获取详细报价:")
        print(f"   📊 股票代码: {test_symbol}")
        print(f"   💰 最新价格: ${detailed_quote.last_price}")
        if hasattr(detailed_quote, 'company_name'):
            print(f"   🏢 公司名称: {detailed_quote.company_name}")
        if hasattr(detailed_quote, 'market_cap'):
            print(f"   💰 市值: {detailed_quote.market_cap}")
        if hasattr(detailed_quote, 'pe_ratio'):
            print(f"   📈 PE比率: {detailed_quote.pe_ratio}")
        if hasattr(detailed_quote, 'day_high'):
            print(f"   📊 当日最高: ${detailed_quote.day_high}")
        if hasattr(detailed_quote, 'day_low'):
            print(f"   📊 当日最低: ${detailed_quote.day_low}")
    except Exception as e:
        print(f"❌ 详细报价降级失败: {e}")

    print()

    # 测试3: 公司信息（应该从Polygon降级到Yahoo）
    print(f"3️⃣ 测试公司信息降级 ({test_symbol})")
    try:
        company_info = await manager.get_company_info(test_symbol)
        print(f"✅ 降级成功获取公司信息:")
        print(f"   🏢 公司名称: {company_info.name}")
        print(f"   🌐 网站: {company_info.website}")
        print(f"   👥 员工数: {company_info.employees}")
        print(f"   🌍 国家: {company_info.country}")
        print(f"   🏭 行业: {company_info.industry}")
        if hasattr(company_info, 'business_summary') and company_info.business_summary:
            print(f"   📝 业务摘要: {company_info.business_summary[:100]}...")
    except Exception as e:
        print(f"❌ 公司信息降级失败: {e}")

    print()

    # 测试4: 历史数据（应该从Polygon降级到Yahoo）
    print(f"4️⃣ 测试历史数据降级 ({test_symbol}, 1个月)")
    try:
        history_data = await manager.get_history(test_symbol, period="1mo")
        print(f"✅ 降级成功获取历史数据:")

        if hasattr(history_data, 'prices') and history_data.prices:
            print(f"   📊 数据点数量: {len(history_data.prices)}")
            print(f"   📅 最早价格: ${history_data.prices[0]}")
            print(f"   📅 最新价格: ${history_data.prices[-1]}")
        elif isinstance(history_data, dict):
            prices = history_data.get('prices', [])
            print(f"   📊 数据点数量: {len(prices)}")
            if prices:
                print(f"   📅 最早价格: ${prices[0]}")
                print(f"   📅 最新价格: ${prices[-1]}")
        else:
            print(f"   📊 历史数据格式: {type(history_data)}")
            print(f"   📊 历史数据内容: {str(history_data)[:200]}...")

    except Exception as e:
        print(f"❌ 历史数据降级失败: {e}")

    print()

    # 测试5: 数据源优先级验证
    print("5️⃣ 测试数据源优先级和健康状态")
    sources_to_check = getattr(manager, 'all_sources', [
                               manager.primary_source] + manager.fallback_sources)
    for i, source in enumerate(sources_to_check, 1):
        try:
            health = await source.health_check()
            print(f"   数据源 {i} ({source.name}): {health}")
        except Exception as e:
            print(f"   数据源 {i} ({source.name}): ❌ {e}")

    print()
    print("🎉 降级机制测试完成!")

if __name__ == "__main__":
    asyncio.run(test_api_fallback())
