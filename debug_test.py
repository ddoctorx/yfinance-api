#!/usr/bin/env python3
"""
调试脚本：测试数据源管理器的行为
"""
from app.services.data_source_manager import DataSourceManager
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_data_sources():
    """测试数据源"""
    print("=== 初始化数据源管理器 ===")
    manager = DataSourceManager()
    # DataSourceManager没有initialize方法，它在初始化时自动完成

    print("\n=== 测试有效股票代码 AAPL ===")
    try:
        result = await manager.get_fast_quote("AAPL")
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}: {e}")

    print("\n=== 测试有效股票代码 MSFT ===")
    try:
        result = await manager.get_fast_quote("MSFT")
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}: {e}")

    print("\n=== 测试无效股票代码 INVALID123 ===")
    try:
        result = await manager.get_fast_quote("INVALID123")
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}: {e}")

    print("\n=== 数据源状态 ===")
    status = manager.fallback_manager.get_status_summary()
    print(f"降级状态: {status}")


if __name__ == "__main__":
    asyncio.run(test_data_sources())
