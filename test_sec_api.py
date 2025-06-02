#!/usr/bin/env python3
"""
SEC API测试脚本
用于验证SEC数据源的修复是否有效
"""

from app.core.logging import get_logger
from app.data_sources.base import DataSourceError
from app.data_sources.sec_source import SecDataSource
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


logger = get_logger(__name__)


class SecApiTester:
    def __init__(self, api_key: str = None):
        """初始化测试器"""
        self.api_key = api_key or os.environ.get('SEC_API_KEY')
        if not self.api_key:
            print("❌ 错误: 未找到SEC API密钥")
            print("请设置环境变量 SEC_API_KEY 或在初始化时提供")
            print("获取API密钥: https://sec-api.io/")
            sys.exit(1)

        try:
            self.sec_source = SecDataSource(api_key=self.api_key)
            print("✅ SEC数据源初始化成功")
        except Exception as e:
            print(f"❌ SEC数据源初始化失败: {e}")
            sys.exit(1)

    async def test_health_check(self):
        """测试健康检查"""
        print("\n🔍 测试健康检查...")
        try:
            is_healthy = await self.sec_source.health_check()
            if is_healthy:
                print("✅ 健康检查通过")
                return True
            else:
                print("❌ 健康检查失败")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False

    async def test_get_cik(self, ticker: str = "AAPL"):
        """测试获取CIK"""
        print(f"\n🔍 测试获取CIK: {ticker}")
        try:
            cik = await self.sec_source._get_company_cik(ticker)
            if cik:
                print(f"✅ 获取CIK成功: {ticker} -> {cik}")
                return cik
            else:
                print(f"❌ 未找到CIK: {ticker}")
                return None
        except Exception as e:
            print(f"❌ 获取CIK异常: {e}")
            return None

    async def test_company_financials(self, ticker: str = "AAPL"):
        """测试获取财务数据"""
        print(f"\n🔍 测试获取财务数据: {ticker}")
        try:
            financials = await self.sec_source.get_company_financials(
                ticker=ticker,
                years=2,
                include_quarterly=True
            )

            if financials:
                print(f"✅ 财务数据获取成功")
                print(f"   公司名称: {financials.get('company_name', 'N/A')}")
                print(f"   CIK: {financials.get('cik', 'N/A')}")

                # 年度数据
                annual_data = financials.get('annual_financials', [])
                print(f"   年度数据: {len(annual_data)} 条")
                for i, item in enumerate(annual_data[:2]):  # 只显示前2条
                    print(f"     [{i+1}] 财年: {item.get('fiscal_year', 'N/A')}")
                    print(f"         收入: ${item.get('revenue', 0):,.0f}")
                    print(f"         净利润: ${item.get('net_income', 0):,.0f}")
                    print(f"         申报日期: {item.get('filing_date', 'N/A')}")

                # 季度数据
                quarterly_data = financials.get('quarterly_financials', [])
                print(f"   季度数据: {len(quarterly_data)} 条")
                for i, item in enumerate(quarterly_data[:2]):  # 只显示前2条
                    print(f"     [{i+1}] 季度: {item.get('quarter', 'N/A')}")
                    print(f"         收入: ${item.get('revenue', 0):,.0f}")
                    print(f"         净利润: ${item.get('net_income', 0):,.0f}")

                return True
            else:
                print(f"❌ 未获取到财务数据")
                return False

        except DataSourceError as e:
            print(f"❌ 数据源错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 获取财务数据异常: {e}")
            return False

    async def test_company_news(self, ticker: str = "AAPL"):
        """测试获取SEC新闻"""
        print(f"\n🔍 测试获取SEC新闻: {ticker}")
        try:
            news_items = await self.sec_source.get_company_news(
                ticker=ticker,
                limit=5,
                days_back=90
            )

            if news_items:
                print(f"✅ SEC新闻获取成功: {len(news_items)} 条")
                for i, item in enumerate(news_items[:3]):  # 只显示前3条
                    print(f"   [{i+1}] {item.get('title', 'N/A')}")
                    print(f"       表单类型: {item.get('form_type', 'N/A')}")
                    print(f"       提交日期: {item.get('published_at', 'N/A')}")
                return True
            else:
                print(f"❌ 未获取到SEC新闻")
                return False

        except DataSourceError as e:
            print(f"❌ 数据源错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 获取SEC新闻异常: {e}")
            return False

    async def test_health_status(self):
        """测试健康状态"""
        print(f"\n🔍 测试健康状态...")
        try:
            status = await self.sec_source.get_health_status()
            print(f"✅ 健康状态获取成功:")
            print(f"   状态: {status.get('status', 'N/A')}")
            print(f"   数据源: {status.get('source', 'N/A')}")
            print(f"   API密钥配置: {status.get('api_key_configured', False)}")
            print(f"   缓存启用: {status.get('cache_enabled', False)}")
            print(f"   检查时间: {status.get('last_checked', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ 获取健康状态异常: {e}")
            return False

    async def run_all_tests(self, ticker: str = "AAPL"):
        """运行所有测试"""
        print(f"🚀 开始SEC API测试 - 测试股票: {ticker}")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        results = []

        # 测试健康检查
        results.append(await self.test_health_check())

        # 测试获取CIK
        cik = await self.test_get_cik(ticker)
        results.append(bool(cik))

        # 测试财务数据
        results.append(await self.test_company_financials(ticker))

        # 测试SEC新闻
        results.append(await self.test_company_news(ticker))

        # 测试健康状态
        results.append(await self.test_health_status())

        # 总结结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        test_names = ["健康检查", "获取CIK", "财务数据", "SEC新闻", "健康状态"]

        passed = sum(results)
        total = len(results)

        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {i+1}. {name}: {status}")

        print(f"\n🎯 总体结果: {passed}/{total} 测试通过")

        if passed == total:
            print("🎉 所有测试通过！SEC API修复成功!")
            return True
        else:
            print("⚠️  部分测试失败，请检查配置或网络连接")
            return False


async def main():
    """主函数"""
    # 可以在这里指定API密钥
    api_key = None  # 或者直接设置: api_key = "your-api-key-here"

    # 可以在这里指定测试的股票代码
    test_ticker = "AAPL"  # 默认测试苹果公司

    print("🔧 SEC API 修复验证工具")
    print("=" * 40)

    if len(sys.argv) > 1:
        test_ticker = sys.argv[1].upper()
        print(f"使用命令行参数指定的股票代码: {test_ticker}")

    tester = SecApiTester(api_key=api_key)

    try:
        success = await tester.run_all_tests(test_ticker)
        if success:
            print("\n✨ 验证完成：SEC API修复有效！")
            sys.exit(0)
        else:
            print("\n💥 验证失败：请检查错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生未预期错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
