#!/usr/bin/env python3
"""
SEC高级功能API测试脚本
测试所有SEC高级功能的API端点
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/sec-advanced"


class SecAdvancedAPITester:
    """SEC高级API测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}",
                        "message": error_text
                    }
        except Exception as e:
            return {
                "error": "Request failed",
                "message": str(e)
            }

    def print_result(self, test_name: str, result: Dict[str, Any]):
        """格式化打印测试结果"""
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print('='*60)

        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            print(f"   消息: {result.get('message', 'Unknown error')}")
        else:
            print("✅ 成功")
            # 只打印关键信息
            if "data" in result:
                data = result["data"]
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key in ['ticker', 'company_name', 'total_count', 'query', 'summary']:
                            print(f"   {key}: {value}")
                        elif isinstance(value, list) and len(value) > 0:
                            print(f"   {key}: {len(value)} 项数据")
                            if len(value) > 0:
                                print(
                                    f"   第一项: {list(value[0].keys()) if isinstance(value[0], dict) else str(value[0])[:100]}")

        print(f"数据源: {result.get('data_source', 'unknown')}")
        print(f"是否降级: {result.get('is_fallback', 'unknown')}")

    async def test_xbrl_company_data(self):
        """测试XBRL公司数据"""
        result = await self.make_request("/xbrl/company/AAPL", {
            "form_type": "10-K",
            "fiscal_year": 2023
        })
        self.print_result("XBRL公司数据 (AAPL)", result)
        return result

    async def test_full_text_search(self):
        """测试全文搜索"""
        result = await self.make_request("/search/full-text", {
            "query": "artificial intelligence",
            "form_types": "10-K,10-Q",
            "limit": 10
        })
        self.print_result("全文搜索 (AI)", result)
        return result

    async def test_company_search(self):
        """测试公司文件搜索"""
        result = await self.make_request("/search/company/TSLA", {
            "query": "revenue growth",
            "form_types": "10-K,10-Q",
            "years": 2
        })
        self.print_result("公司文件搜索 (TSLA)", result)
        return result

    async def test_insider_trading(self):
        """测试内幕交易数据"""
        result = await self.make_request("/insider-trading/AAPL", {
            "days_back": 60,
            "include_derivatives": True
        })
        self.print_result("内幕交易数据 (AAPL)", result)
        return result

    async def test_institutional_holdings(self):
        """测试机构持股数据"""
        result = await self.make_request("/institutional-holdings/MSFT", {
            "quarters": 4,
            "min_value": 1000000
        })
        self.print_result("机构持股数据 (MSFT)", result)
        return result

    async def test_recent_ipos(self):
        """测试最近IPO数据"""
        result = await self.make_request("/ipo/recent", {
            "days_back": 90,
            "min_offering_amount": 100000000
        })
        self.print_result("最近IPO数据", result)
        return result

    async def test_company_ipo(self):
        """测试公司IPO详情"""
        result = await self.make_request("/ipo/SNOW")
        self.print_result("公司IPO详情 (SNOW)", result)
        return result

    async def test_executive_compensation(self):
        """测试高管薪酬数据"""
        result = await self.make_request("/executive-compensation/AAPL", {
            "years": 3
        })
        self.print_result("高管薪酬数据 (AAPL)", result)
        return result

    async def test_company_governance(self):
        """测试公司治理信息"""
        result = await self.make_request("/governance/GOOGL", {
            "include_subsidiaries": True,
            "include_audit_fees": True
        })
        self.print_result("公司治理信息 (GOOGL)", result)
        return result

    async def test_enforcement_actions(self):
        """测试SEC执法行动"""
        result = await self.make_request("/enforcement/recent", {
            "days_back": 60
        })
        self.print_result("SEC执法行动", result)
        return result

    async def test_ticker_mapping(self):
        """测试股票代码映射"""
        result = await self.make_request("/mapping/ticker-to-cik/AAPL", {
            "include_historical": False
        })
        self.print_result("股票代码映射 (AAPL)", result)
        return result

    async def test_health_check(self):
        """测试健康检查"""
        result = await self.make_request("/health")
        self.print_result("健康检查", result)
        return result

    async def test_api_overview(self):
        """测试API概览"""
        result = await self.make_request("/")
        self.print_result("API概览", result)
        return result

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始SEC高级功能API测试")
        print(f"API地址: {self.base_url}")

        tests = [
            ("API概览", self.test_api_overview),
            ("健康检查", self.test_health_check),
            ("XBRL公司数据", self.test_xbrl_company_data),
            ("全文搜索", self.test_full_text_search),
            ("公司文件搜索", self.test_company_search),
            ("内幕交易", self.test_insider_trading),
            ("机构持股", self.test_institutional_holdings),
            ("最近IPO", self.test_recent_ipos),
            ("公司IPO详情", self.test_company_ipo),
            ("高管薪酬", self.test_executive_compensation),
            ("公司治理", self.test_company_governance),
            ("SEC执法", self.test_enforcement_actions),
            ("股票代码映射", self.test_ticker_mapping),
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 正在执行: {test_name}")
                result = await test_func()
                results[test_name] = "✅ 成功" if "error" not in result else "❌ 失败"
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                results[test_name] = f"❌ 异常: {str(e)}"

        # 打印测试总结
        print(f"\n{'='*60}")
        print("📊 测试总结")
        print('='*60)

        success_count = sum(1 for status in results.values() if "✅" in status)
        total_count = len(results)

        for test_name, status in results.items():
            print(f"{status} {test_name}")

        print(f"\n📈 总体结果: {success_count}/{total_count} 测试通过")

        if success_count == total_count:
            print("🎉 所有测试都通过了！")
        else:
            print("⚠️  部分测试失败，请检查配置和服务状态")


async def main():
    """主函数"""
    print("SEC高级功能API测试器")
    print("确保API服务正在运行在 http://localhost:8000")

    async with SecAdvancedAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
