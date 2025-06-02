#!/usr/bin/env python3
"""
SEC高级功能综合测试脚本
测试所有SEC高级API端点
"""

from app.core.config import settings
from app.services.sec_service import SecService
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_sec_advanced_features():
    """测试所有SEC高级功能"""
    print("=== SEC高级功能综合测试 ===\n")

    # 检查API密钥
    if not settings.sec_api_key:
        print("❌ 错误: 未设置SEC_API_KEY环境变量")
        return

    # 初始化服务
    service = SecService(api_key=settings.sec_api_key)

    # 检查高级功能是否可用
    if not service.advanced_available:
        print("❌ 错误: SEC高级功能不可用，请检查API密钥")
        return

    print("✅ SEC服务已初始化，高级功能可用\n")

    test_ticker = "AAPL"

    # 测试列表
    tests = [
        ("股票代码到CIK映射", test_ticker_to_cik_mapping),
        ("内幕交易数据", test_insider_trading),
        ("机构持股数据", test_institutional_holdings),
        ("最近IPO数据", test_recent_ipos),
        ("公司IPO详情", test_company_ipo_details),
        ("高管薪酬数据", test_executive_compensation),
        ("公司治理信息", test_company_governance),
        ("SEC执法行动", test_enforcement_actions),
        ("全文搜索", test_full_text_search),
        ("公司文件搜索", test_company_filings_search),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"🧪 测试: {test_name}")
        try:
            await test_func(service, test_ticker)
            print(f"✅ {test_name} - 测试通过\n")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} - 测试失败: {str(e)}\n")
            failed += 1

    # 健康检查
    print("🧪 测试: 健康检查")
    try:
        health = await service.get_health_status()
        print(f"✅ 健康检查 - 状态: {health.get('status', 'unknown')}\n")
        passed += 1
    except Exception as e:
        print(f"❌ 健康检查 - 失败: {str(e)}\n")
        failed += 1

    # 总结
    total = passed + failed
    print(f"=== 测试总结 ===")
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/total*100:.1f}%" if total > 0 else "无测试")

    # 关闭服务
    await service.shutdown()


async def test_ticker_to_cik_mapping(service: SecService, ticker: str):
    """测试股票代码到CIK映射"""
    result = await service.get_ticker_to_cik_mapping(ticker)
    assert 'ticker' in result
    assert 'cik' in result
    print(f"   CIK映射: {ticker} -> {result.get('cik')}")


async def test_insider_trading(service: SecService, ticker: str):
    """测试内幕交易数据"""
    result = await service.get_insider_trading(ticker, days_back=30)
    assert 'ticker' in result
    assert 'trading_data' in result
    print(f"   内幕交易记录数: {len(result.get('trading_data', []))}")


async def test_institutional_holdings(service: SecService, ticker: str):
    """测试机构持股数据"""
    result = await service.get_institutional_holdings(ticker, quarters=2)
    assert 'ticker' in result
    assert 'holdings_data' in result
    print(f"   机构持股记录数: {len(result.get('holdings_data', []))}")


async def test_recent_ipos(service: SecService, ticker: str):
    """测试最近IPO数据"""
    result = await service.get_recent_ipos(days_back=30)
    assert 'ipo_data' in result
    print(f"   最近IPO数量: {len(result.get('ipo_data', []))}")


async def test_company_ipo_details(service: SecService, ticker: str):
    """测试公司IPO详情"""
    try:
        result = await service.get_company_ipo_details(ticker)
        assert 'ticker' in result
        print(f"   IPO详情获取成功")
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"   {ticker} 无IPO信息（正常）")
        else:
            raise


async def test_executive_compensation(service: SecService, ticker: str):
    """测试高管薪酬数据"""
    result = await service.get_executive_compensation(ticker, years=2)
    assert 'ticker' in result
    assert 'compensation_data' in result
    print(f"   高管薪酬记录数: {len(result.get('compensation_data', []))}")


async def test_company_governance(service: SecService, ticker: str):
    """测试公司治理信息"""
    result = await service.get_company_governance(ticker)
    assert 'ticker' in result
    assert 'governance_data' in result
    print(f"   治理信息获取成功")


async def test_enforcement_actions(service: SecService, ticker: str):
    """测试SEC执法行动"""
    result = await service.get_recent_enforcement_actions(days_back=90)
    assert 'enforcement_actions' in result
    print(f"   最近执法行动数: {len(result.get('enforcement_actions', []))}")


async def test_full_text_search(service: SecService, ticker: str):
    """测试全文搜索"""
    result = await service.full_text_search(
        query="revenue growth",
        form_types=["10-K"],
        limit=5
    )
    assert 'search_results' in result
    print(f"   全文搜索结果数: {len(result.get('search_results', []))}")


async def test_company_filings_search(service: SecService, ticker: str):
    """测试公司文件搜索"""
    result = await service.search_company_filings(
        ticker=ticker,
        query="revenue",
        form_types=["10-K", "10-Q"],
        years=1
    )
    assert 'ticker' in result
    assert 'search_results' in result
    print(f"   公司文件搜索结果数: {len(result.get('search_results', []))}")


if __name__ == "__main__":
    asyncio.run(test_sec_advanced_features())
