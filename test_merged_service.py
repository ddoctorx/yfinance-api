#!/usr/bin/env python3
"""
测试合并后的SEC服务
"""

from app.services.sec_service import SecService
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_merged_service():
    """测试合并后的SEC服务"""
    print("=== 测试合并后的SEC服务 ===")

    # 初始化服务
    service = SecService()
    print("✅ SEC服务初始化成功")

    print(f"📊 高级功能可用: {service.advanced_available}")

    # 测试基础功能
    try:
        result = await service.get_company_financials("AAPL", "annual")
        print(f"✅ 基础功能测试成功 - 财务数据获取")
    except Exception as e:
        print(f"❌ 基础功能测试失败: {str(e)}")

    # 测试高级功能（如果可用）
    if service.advanced_available:
        try:
            result = await service.get_ticker_to_cik_mapping("AAPL")
            print(f"✅ 高级功能测试成功 - CIK映射: {result.get('cik')}")
        except Exception as e:
            print(f"❌ 高级功能测试失败: {str(e)}")
    else:
        print("⚠️  高级功能不可用（未配置API密钥）")

    # 健康检查
    try:
        health = await service.get_health_status()
        print(f"✅ 健康检查通过 - 状态: {health.get('status')}")
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")

    # 关闭服务
    await service.shutdown()
    print("✅ 服务已正确关闭")


if __name__ == "__main__":
    asyncio.run(test_merged_service())
