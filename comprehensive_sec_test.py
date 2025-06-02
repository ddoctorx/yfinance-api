#!/usr/bin/env python3
"""
SEC高级服务综合测试脚本
测试所有SecAdvancedService的功能
"""

from app.core.config import settings
from app.utils.exceptions import FinanceAPIException
from app.services.sec_advanced_service import SecAdvancedService
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class SecAdvancedServiceTester:
    """SEC高级服务测试器"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化测试器"""
        try:
            self.service = SecAdvancedService(api_key=api_key)
            self.test_results = {}
            self.start_time = datetime.now()
        except Exception as e:
            print(f"❌ 初始化SEC高级服务失败: {e}")
            raise

    def print_separator(self, title: str):
        """打印分隔符"""
        print(f"\n{'='*80}")
        print(f" {title}")
        print('='*80)

    def print_result(self, test_name: str, success: bool, data: Any = None, error: str = None):
        """打印测试结果"""
        status = "✅ 成功" if success else "❌ 失败"
        print(f"\n{status} {test_name}")

        if success and data:
            # 打印关键信息
            if isinstance(data, dict):
                if 'total_count' in data:
                    print(f"   总数量: {data['total_count']}")
                if 'data' in data and isinstance(data['data'], list):
                    print(f"   数据项数: {len(data['data'])}")
                if 'summary' in data:
                    print(f"   摘要: {data['summary']}")
                if 'company_name' in data:
                    print(f"   公司名称: {data['company_name']}")
                if 'ticker' in data:
                    print(f"   股票代码: {data['ticker']}")

                # 显示部分数据结构
                if isinstance(data, dict) and len(data) > 0:
                    keys = list(data.keys())[:5]  # 只显示前5个键
                    print(f"   数据字段: {', '.join(keys)}")

        if error:
            print(f"   错误: {error}")

        self.test_results[test_name] = success

    # ===== XBRL转换功能测试 =====

    async def test_convert_xbrl_to_json(self):
        """测试XBRL转JSON转换"""
        test_name = "XBRL转JSON转换"
        try:
            # 使用一个实际的SEC XBRL文件URL
            filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000077/aapl-20230930_htm.xml"

            result = await self.service.convert_xbrl_to_json(
                filing_url=filing_url,
                include_dimensions=True,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    async def test_get_company_xbrl_data(self):
        """测试获取公司XBRL数据"""
        test_name = "公司XBRL数据"
        try:
            result = await self.service.get_company_xbrl_data(
                ticker="AAPL",
                form_type="10-K",
                fiscal_year=2023,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 全文搜索功能测试 =====

    async def test_full_text_search(self):
        """测试全文搜索"""
        test_name = "SEC全文搜索"
        try:
            result = await self.service.full_text_search(
                query="artificial intelligence machine learning",
                form_types=["10-K", "10-Q"],
                date_from="2023-01-01",
                date_to="2023-12-31",
                limit=10,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    async def test_search_company_filings(self):
        """测试公司文件搜索"""
        test_name = "公司文件搜索"
        try:
            result = await self.service.search_company_filings(
                ticker="TSLA",
                query="revenue growth electric vehicle",
                form_types=["10-K", "10-Q"],
                years=2,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 内幕交易数据测试 =====

    async def test_get_insider_trading(self):
        """测试内幕交易数据"""
        test_name = "内幕交易数据"
        try:
            result = await self.service.get_insider_trading(
                ticker="AAPL",
                days_back=90,
                include_derivatives=True,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 机构持股数据测试 =====

    async def test_get_institutional_holdings(self):
        """测试机构持股数据"""
        test_name = "机构持股数据"
        try:
            result = await self.service.get_institutional_holdings(
                ticker="MSFT",
                quarters=4,
                min_value=1000000,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== IPO数据测试 =====

    async def test_get_recent_ipos(self):
        """测试最近IPO数据"""
        test_name = "最近IPO数据"
        try:
            result = await self.service.get_recent_ipos(
                days_back=90,
                min_offering_amount=50000000,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    async def test_get_company_ipo_details(self):
        """测试公司IPO详情"""
        test_name = "公司IPO详情"
        try:
            result = await self.service.get_company_ipo_details(
                ticker="SNOW",
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 高管薪酬数据测试 =====

    async def test_get_executive_compensation(self):
        """测试高管薪酬数据"""
        test_name = "高管薪酬数据"
        try:
            result = await self.service.get_executive_compensation(
                ticker="AAPL",
                years=3,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 公司治理数据测试 =====

    async def test_get_company_governance(self):
        """测试公司治理信息"""
        test_name = "公司治理信息"
        try:
            result = await self.service.get_company_governance(
                ticker="GOOGL",
                include_subsidiaries=True,
                include_audit_fees=True,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== SEC执法数据测试 =====

    async def test_get_recent_enforcement_actions(self):
        """测试SEC执法行动"""
        test_name = "SEC执法行动"
        try:
            result = await self.service.get_recent_enforcement_actions(
                days_back=90,
                action_type=None,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 映射和实体数据测试 =====

    async def test_get_ticker_to_cik_mapping(self):
        """测试股票代码到CIK映射"""
        test_name = "股票代码CIK映射"
        try:
            result = await self.service.get_ticker_to_cik_mapping(
                ticker="AAPL",
                include_historical=False,
                use_cache=True
            )

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 健康检查测试 =====

    async def test_get_health_status(self):
        """测试健康检查"""
        test_name = "服务健康检查"
        try:
            result = await self.service.get_health_status()

            self.print_result(test_name, True, result)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 错误处理测试 =====

    async def test_error_handling(self):
        """测试错误处理"""
        test_name = "错误处理测试"
        try:
            # 测试无效股票代码
            try:
                await self.service.get_insider_trading(
                    ticker="INVALID_TICKER_123",
                    days_back=30
                )
                self.print_result(f"{test_name} - 无效股票代码",
                                  False, error="应该抛出异常但没有")
            except FinanceAPIException:
                self.print_result(f"{test_name} - 无效股票代码", True)

            # 测试无效参数
            try:
                await self.service.get_institutional_holdings(
                    ticker="AAPL",
                    quarters=20  # 超出范围
                )
                self.print_result(f"{test_name} - 无效参数",
                                  False, error="应该抛出异常但没有")
            except FinanceAPIException:
                self.print_result(f"{test_name} - 无效参数", True)

        except Exception as e:
            self.print_result(test_name, False, error=str(e))

    # ===== 运行所有测试 =====

    async def run_all_tests(self):
        """运行所有测试"""
        self.print_separator("SEC高级服务综合测试开始")
        print(f"测试开始时间: {self.start_time}")
        print(
            f"API密钥状态: {'已配置' if getattr(settings, 'SEC_API_KEY', None) else '未配置'}")

        # 定义所有测试
        tests = [
            ("健康检查", self.test_get_health_status),
            ("XBRL转JSON转换", self.test_convert_xbrl_to_json),
            ("公司XBRL数据", self.test_get_company_xbrl_data),
            ("SEC全文搜索", self.test_full_text_search),
            ("公司文件搜索", self.test_search_company_filings),
            ("内幕交易数据", self.test_get_insider_trading),
            ("机构持股数据", self.test_get_institutional_holdings),
            ("最近IPO数据", self.test_get_recent_ipos),
            ("公司IPO详情", self.test_get_company_ipo_details),
            ("高管薪酬数据", self.test_get_executive_compensation),
            ("公司治理信息", self.test_get_company_governance),
            ("SEC执法行动", self.test_get_recent_enforcement_actions),
            ("股票代码CIK映射", self.test_get_ticker_to_cik_mapping),
            ("错误处理测试", self.test_error_handling),
        ]

        # 运行测试
        for test_name, test_func in tests:
            self.print_separator(f"测试: {test_name}")
            try:
                await test_func()
            except Exception as e:
                print(f"❌ 测试异常: {test_name}")
                print(f"   错误: {str(e)}")
                print(f"   追踪: {traceback.format_exc()}")
                self.test_results[test_name] = False

        # 生成测试报告
        await self.generate_test_report()

    async def generate_test_report(self):
        """生成测试报告"""
        self.print_separator("测试报告")

        end_time = datetime.now()
        duration = end_time - self.start_time

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests *
                        100) if total_tests > 0 else 0

        print(f"📊 测试统计")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   测试耗时: {duration.total_seconds():.2f}秒")

        print(f"\n📋 详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name}")

        if success_rate == 100:
            print(f"\n🎉 所有测试都通过了！SEC高级服务运行良好。")
        elif success_rate >= 80:
            print(f"\n✅ 大部分测试通过。建议检查失败的测试。")
        else:
            print(f"\n⚠️  多个测试失败。请检查服务配置和网络连接。")

        # 保存测试报告到文件
        report_data = {
            "test_time": self.start_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "api_key_configured": bool(getattr(settings, 'SEC_API_KEY', None))
        }

        with open("sec_advanced_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 测试报告已保存到: sec_advanced_test_report.json")

    async def cleanup(self):
        """清理资源"""
        try:
            await self.service.shutdown()
            print(f"✅ 服务资源已清理")
        except Exception as e:
            print(f"⚠️  清理资源时出错: {e}")


async def main():
    """主函数"""
    print("🚀 SEC高级服务综合测试器")
    print("=" * 80)

    api_key = getattr(settings, 'SEC_API_KEY', None)
    if not api_key:
        print("⚠️  警告: 未检测到SEC_API_KEY，可能会影响某些功能")
        print("   请在config.env中配置SEC_API_KEY")

    tester = None
    try:
        # 初始化测试器
        tester = SecAdvancedServiceTester(api_key=api_key)

        # 运行所有测试
        await tester.run_all_tests()

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试器运行失败: {e}")
        traceback.print_exc()
    finally:
        # 清理资源
        if tester:
            await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
