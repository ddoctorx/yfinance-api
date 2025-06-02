#!/usr/bin/env python3
"""
测试新的测试endpoints
验证直接数据源调用功能
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TEST_SYMBOL = "AAPL"


def make_request(endpoint: str) -> Dict[str, Any]:
    """发起HTTP请求"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": None
        }


def test_endpoints():
    """测试所有的测试endpoints"""
    print("🚀 开始测试所有测试endpoints")
    print("=" * 60)

    test_cases = [
        {
            "name": "Yahoo Finance 报价测试",
            "endpoint": f"/api/v1/test/yfinance/{TEST_SYMBOL}/quote",
            "description": "测试Yahoo Finance数据源直接调用"
        },
        {
            "name": "Polygon.io 原始数据测试",
            "endpoint": f"/api/v1/test/polygon/{TEST_SYMBOL}/raw",
            "description": "测试Polygon.io原始API响应"
        },
        {
            "name": "Polygon.io 报价测试",
            "endpoint": f"/api/v1/test/polygon/{TEST_SYMBOL}/quote",
            "description": "测试Polygon.io转换后的报价数据"
        },
        {
            "name": "Polygon.io 公司信息测试",
            "endpoint": f"/api/v1/test/polygon/{TEST_SYMBOL}/company",
            "description": "测试Polygon.io公司信息"
        },
        {
            "name": "数据源比较测试",
            "endpoint": f"/api/v1/test/compare/{TEST_SYMBOL}",
            "description": "比较不同数据源的数据差异"
        },
        {
            "name": "健康检查测试",
            "endpoint": "/api/v1/test/health-check",
            "description": "测试所有数据源的健康状态"
        },
        {
            "name": "API配置信息测试",
            "endpoint": "/api/v1/test/api-limits",
            "description": "查看API配置和限制信息"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   📋 {test_case['description']}")
        print(f"   🔗 GET {test_case['endpoint']}")

        result = make_request(test_case['endpoint'])

        if result['success']:
            print(f"   ✅ 成功 (HTTP {result['status_code']})")

            # 显示关键信息
            data = result['data']
            if 'symbol' in data:
                print(f"   📊 股票代码: {data['symbol']}")
            if 'data_source' in data:
                print(f"   📈 数据源: {data['data_source']}")
            if 'polygon_snapshot' in data:
                print(f"   📊 Polygon快照: 已获取")
            if 'polygon_ticker_details' in data:
                print(f"   📋 Polygon详情: 已获取")
            if 'overall_healthy' in data:
                health_status = "健康" if data['overall_healthy'] else "不健康"
                print(f"   🏥 整体状态: {health_status}")
            if 'polygon_config' in data:
                api_configured = "已配置" if data['polygon_config']['api_key_configured'] else "未配置"
                print(f"   🔑 Polygon API: {api_configured}")
                debug_mode = "启用" if data.get('debug_mode', False) else "禁用"
                print(f"   🐛 调试模式: {debug_mode}")

        else:
            print(f"   ❌ 失败 (HTTP {result.get('status_code', 'N/A')})")
            print(f"   📄 错误信息: {result['error'][:200]}...")

        results.append({
            "test_name": test_case['name'],
            "endpoint": test_case['endpoint'],
            "success": result['success'],
            "status_code": result.get('status_code'),
            "error": result.get('error') if not result['success'] else None
        })

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    successful = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"总计: {total} 个测试")
    print(f"成功: {successful} 个")
    print(f"失败: {total - successful} 个")
    print(f"成功率: {successful/total*100:.1f}%")

    if successful == total:
        print("\n🎉 所有测试都通过了!")
    else:
        print("\n⚠️  有部分测试失败，详情如下:")
        for result in results:
            if not result['success']:
                print(f"  ❌ {result['test_name']}")
                print(f"     {result['endpoint']}")
                if result['error']:
                    print(f"     错误: {result['error'][:100]}...")

    return results


def main():
    """主函数"""
    print("🧪 测试endpoints功能")
    print(f"🔗 服务器地址: {BASE_URL}")
    print(f"📊 测试股票: {TEST_SYMBOL}")

    # 先检查服务器是否在线
    health_check = make_request("/health")
    if not health_check['success']:
        print(f"\n❌ 服务器未响应: {health_check.get('error', '未知错误')}")
        print("请确保服务器正在运行: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    print("✅ 服务器在线，开始测试...")

    # 运行测试
    results = test_endpoints()

    return 0 if all(r['success'] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
