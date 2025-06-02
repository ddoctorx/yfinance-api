"""
SEC API endpoints 测试文件

测试SEC财报数据API的各个端点功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import requests
from typing import Dict, Any


class SecAPITester:
    """SEC API端点测试工具"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        # 修正基础路径
        self.sec_base = f"{base_url}/api/v1/sec/sec"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "SEC-API-Tester/1.0"
        })

    async def test_endpoint(self, endpoint, description):
        """测试单个端点"""
        print(f"\n🧪 测试: {description}")
        print(f"📡 端点: {endpoint}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    print(f"📊 状态码: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 成功 - 数据大小: {len(json.dumps(data))} 字符")
                        return data
                    else:
                        error_text = await response.text()
                        print(f"❌ 失败 - 错误: {error_text}")
                        return None

        except Exception as e:
            print(f"🚫 异常: {str(e)}")
            return None

    async def run_tests(self):
        """运行所有测试"""
        print("🚀 开始测试SEC API endpoints")
        print("=" * 50)

        # 测试公司：苹果公司 (AAPL)
        ticker = "AAPL"

        # 1. 测试SEC API概览
        await self.test_endpoint(
            "/v1/sec/",
            "SEC API概览"
        )

        # 2. 测试健康检查
        await self.test_endpoint(
            "/v1/sec/health",
            "SEC服务健康检查"
        )

        # 3. 测试获取财务数据
        await self.test_endpoint(
            f"/v1/sec/financials/{ticker}?years=3&include_quarterly=true",
            f"获取{ticker}财务数据 (3年含季度)"
        )

        # 4. 测试季度收入数据
        await self.test_endpoint(
            f"/v1/sec/quarterly-revenue/{ticker}?quarters=8",
            f"获取{ticker}季度收入 (8个季度)"
        )

        # 5. 测试年度对比
        await self.test_endpoint(
            f"/v1/sec/annual-comparison/{ticker}?years=5",
            f"获取{ticker}年度对比 (5年)"
        )

        # 6. 测试SEC新闻
        await self.test_endpoint(
            f"/v1/sec/news/{ticker}?limit=10",
            f"获取{ticker}SEC新闻 (10条)"
        )

        # 7. 测试财务比率
        await self.test_endpoint(
            f"/v1/sec/ratios/{ticker}?period=annual",
            f"获取{ticker}年度财务比率"
        )

        # 8. 测试错误处理
        await self.test_endpoint(
            "/v1/sec/financials/INVALID_TICKER",
            "错误处理测试 (无效股票代码)"
        )

        print("\n" + "=" * 50)
        print("🏁 测试完成!")

    async def test_specific_features(self):
        """测试特定功能"""
        print("\n🔍 详细功能测试")
        print("=" * 30)

        # 测试苹果公司财务数据
        print("\n📈 测试苹果公司 (AAPL) 详细财务数据:")
        data = await self.test_endpoint(
            "/v1/sec/financials/AAPL?years=2&include_quarterly=true",
            "AAPL 2年财务数据"
        )

        if data:
            print(f"  📋 公司名称: {data.get('company_name', 'N/A')}")
            print(f"  🏢 CIK编号: {data.get('cik', 'N/A')}")
            print(f"  📅 最后更新: {data.get('last_updated', 'N/A')}")
            print(f"  📊 年度报告数: {len(data.get('annual_reports', []))}")
            print(f"  📈 季度报告数: {len(data.get('quarterly_reports', []))}")

            # 显示最新年度数据
            if data.get('annual_reports'):
                latest_annual = data['annual_reports'][0]
                print(f"\n  💰 最新年度数据 ({latest_annual.get('year', 'N/A')}):")
                if latest_annual.get('income_statement'):
                    income = latest_annual['income_statement']
                    print(
                        f"    收入: ${income.get('revenue', 'N/A'):,}" if income.get('revenue') else "    收入: N/A")
                    print(f"    净利润: ${income.get('net_income', 'N/A'):,}" if income.get(
                        'net_income') else "    净利润: N/A")

        # 测试微软公司季度收入
        print("\n📊 测试微软公司 (MSFT) 季度收入:")
        data = await self.test_endpoint(
            "/v1/sec/quarterly-revenue/MSFT?quarters=4",
            "MSFT 4个季度收入"
        )

        if data:
            print(f"  🏢 公司: {data.get('company_name', 'N/A')}")
            print(f"  📈 季度数: {data.get('total_quarters', 0)}")

            for i, quarter in enumerate(data.get('quarterly_revenues', [])[:2]):
                print(
                    f"  📅 {quarter.get('quarter', 'N/A')}: ${quarter.get('revenue', 0):,.0f}")
                if quarter.get('yoy_growth_rate'):
                    print(f"     📈 同比增长: {quarter['yoy_growth_rate']:.1f}%")


async def main():
    """主函数"""
    tester = SecAPITester()

    print("🌟 SEC API 端点测试工具")
    print("⚠️  请确保API服务在 http://localhost:8000 上运行")
    print()

    # 运行基础测试
    await tester.run_tests()

    # 运行详细功能测试
    await tester.test_specific_features()


if __name__ == "__main__":
    asyncio.run(main())
