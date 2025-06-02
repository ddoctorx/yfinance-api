#!/usr/bin/env python3
"""
测试新的Polygon官方客户端实现
"""

import asyncio
import sys
from app.data_sources.polygon_source import PolygonDataSource


async def test_polygon_client():
    """测试Polygon官方客户端的所有功能"""

    print("🔄 初始化Polygon数据源...")
    polygon = PolygonDataSource()

    test_symbol = "AAPL"

    # 1. 健康检查测试
    print("\n1️⃣ 测试健康检查")
    try:
        health = await polygon.health_check()
        print(f"✅ 健康检查: {health}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

    # 2. 快速报价测试
    print(f"\n2️⃣ 测试快速报价 ({test_symbol})")
    try:
        fast_quote = await polygon.get_fast_quote(test_symbol)
        print(f"✅ 快速报价: {fast_quote}")
    except Exception as e:
        print(f"❌ 快速报价失败: {e}")

    # 3. 详细报价测试
    print(f"\n3️⃣ 测试详细报价 ({test_symbol})")
    try:
        detailed_quote = await polygon.get_detailed_quote(test_symbol)
        print(f"✅ 详细报价: {detailed_quote}")
    except Exception as e:
        print(f"❌ 详细报价失败: {e}")

    # 4. 公司信息测试
    print(f"\n4️⃣ 测试公司信息 ({test_symbol})")
    try:
        company_info = await polygon.get_company_info(test_symbol)
        print(f"✅ 公司信息: {company_info}")
    except Exception as e:
        print(f"❌ 公司信息失败: {e}")

    # 5. 历史数据测试
    print(f"\n5️⃣ 测试历史数据 ({test_symbol}, 1个月)")
    try:
        history_data = await polygon.get_history_data(test_symbol, "1mo")
        if hasattr(history_data, 'prices') and history_data.prices:
            print(f"✅ 历史数据: 获取到 {len(history_data.prices)} 个数据点")
            print(
                f"   最新价格: {history_data.prices[-1] if history_data.prices else 'N/A'}")
        else:
            print(f"✅ 历史数据对象: {type(history_data)}")
            print(f"   数据内容: {history_data}")
    except Exception as e:
        print(f"❌ 历史数据失败: {e}")

    # 6. 原始报价调试测试
    print(f"\n6️⃣ 调试测试: 原始报价数据 ({test_symbol})")
    try:
        raw_quote = await polygon.get_raw_quote(test_symbol)
        print(f"✅ 原始报价对象类型: {type(raw_quote)}")
        print(f"   原始报价属性: {dir(raw_quote)}")
        if hasattr(raw_quote, '__dict__'):
            print(f"   原始报价数据: {raw_quote.__dict__}")
        else:
            print(f"   原始报价内容: {raw_quote}")
    except Exception as e:
        print(f"❌ 原始报价调试失败: {e}")

    # 7. 原始ticker详情调试测试
    print(f"\n7️⃣ 调试测试: 原始ticker详情 ({test_symbol})")
    try:
        raw_details = await polygon.get_raw_ticker_details(test_symbol)
        print(f"✅ 原始详情对象类型: {type(raw_details)}")
        print(f"   原始详情属性: {dir(raw_details)}")
        if hasattr(raw_details, '__dict__'):
            print(f"   原始详情数据: {raw_details.__dict__}")
        else:
            print(f"   原始详情内容: {raw_details}")
    except Exception as e:
        print(f"❌ 原始详情调试失败: {e}")

    print("\n🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_polygon_client())
