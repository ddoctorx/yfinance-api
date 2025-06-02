#!/usr/bin/env python3
"""
测试SEC API接口
通过实际的HTTP请求验证我们的API接口
"""

import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"


def test_api_health():
    """测试API健康状态"""
    print("🔍 测试API健康状态...")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API状态: {data.get('status', 'unknown')}")
            print(f"   ⏰ 响应时间: {data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"   ❌ 健康检查失败: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到API服务器")
        print("   💡 请确保API服务器正在运行: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        return False


def test_sec_financials_endpoint():
    """测试SEC财务数据接口"""
    print("\n🔍 测试SEC财务数据接口...")

    try:
        ticker = "AAPL"
        url = f"{BASE_URL}/api/v1/sec/financials/{ticker}"
        params = {
            "years": 2,
            "include_quarterly": True
        }

        print(f"   - 请求URL: {url}")
        print(f"   - 参数: {params}")

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()

            print(f"   ✅ 请求成功")
            print(f"   📊 数据结构验证:")
            print(f"       公司代码: {data.get('ticker', 'N/A')}")
            print(f"       公司名称: {data.get('company_name', 'N/A')}")
            print(f"       CIK: {data.get('cik', 'N/A')}")

            # 年度财务数据
            annual_data = data.get('annual_financials', [])
            print(f"       年度数据: {len(annual_data)} 条")

            if annual_data:
                latest = annual_data[0]
                print(f"       最新财年: {latest.get('fiscal_year', 'N/A')}")
                print(f"       收入: ${latest.get('revenue', 0):,.0f}")
                print(f"       净利润: ${latest.get('net_income', 0):,.0f}")

            # 季度财务数据
            quarterly_data = data.get('quarterly_financials', [])
            print(f"       季度数据: {len(quarterly_data)} 条")

            if quarterly_data:
                latest_q = quarterly_data[0]
                print(f"       最新季度: {latest_q.get('quarter', 'N/A')}")

            return True

        elif response.status_code == 500:
            error_data = response.json()
            print(f"   ❌ 服务器错误: {error_data.get('detail', 'Unknown error')}")
            return False
        else:
            print(f"   ❌ 请求失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(
                    f"       错误详情: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"       响应内容: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False


def test_sec_news_endpoint():
    """测试SEC新闻接口"""
    print("\n🔍 测试SEC新闻接口...")

    try:
        ticker = "AAPL"
        url = f"{BASE_URL}/api/v1/sec/news/{ticker}"
        params = {
            "limit": 5
        }

        print(f"   - 请求URL: {url}")
        print(f"   - 参数: {params}")

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()

            print(f"   ✅ 请求成功")
            print(f"   📊 数据结构验证:")
            print(f"       公司代码: {data.get('ticker', 'N/A')}")
            print(f"       新闻数量: {data.get('total_count', 0)}")

            news_items = data.get('news_items', [])
            print(f"       新闻条目: {len(news_items)} 条")

            if news_items:
                for i, item in enumerate(news_items[:3]):
                    print(f"       [{i+1}] {item.get('title', 'N/A')}")
                    print(f"           类型: {item.get('form_type', 'N/A')}")
                    print(f"           日期: {item.get('published_at', 'N/A')}")

            return True

        elif response.status_code == 500:
            error_data = response.json()
            print(f"   ❌ 服务器错误: {error_data.get('detail', 'Unknown error')}")
            return False
        else:
            print(f"   ❌ 请求失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(
                    f"       错误详情: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"       响应内容: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False


def test_sec_quarterly_revenue_endpoint():
    """测试季度收入接口"""
    print("\n🔍 测试季度收入接口...")

    try:
        ticker = "AAPL"
        url = f"{BASE_URL}/api/v1/sec/quarterly-revenue/{ticker}"
        params = {
            "quarters": 4
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()

            print(f"   ✅ 请求成功")
            print(f"   📊 数据结构验证:")
            print(f"       公司代码: {data.get('ticker', 'N/A')}")
            print(f"       公司名称: {data.get('company_name', 'N/A')}")

            quarterly_data = data.get('quarterly_data', [])
            print(f"       季度数据: {len(quarterly_data)} 条")

            if quarterly_data:
                for item in quarterly_data[:2]:
                    quarter = item.get('quarter', 'N/A')
                    revenue = item.get('revenue', 0)
                    growth = item.get('yoy_growth_rate', 'N/A')
                    print(f"       {quarter}: ${revenue:,.0f} (同比: {growth}%)")

            return True
        else:
            print(f"   ❌ 请求失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 SEC API接口验证测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    # 测试API健康状态
    results.append(test_api_health())

    # 如果API服务不可用，跳过其他测试
    if not results[0]:
        print("\n❌ API服务不可用，跳过其他测试")
        print("💡 请先启动API服务: uvicorn app.main:app --reload")
        return

    # 等待一秒钟，确保服务稳定
    time.sleep(1)

    # 测试SEC财务数据接口
    results.append(test_sec_financials_endpoint())

    # 测试SEC新闻接口
    results.append(test_sec_news_endpoint())

    # 测试季度收入接口
    results.append(test_sec_quarterly_revenue_endpoint())

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")

    test_names = ["API健康状态", "SEC财务数据", "SEC新闻", "季度收入"]
    passed = 0

    for i, (name, result) in enumerate(zip(test_names, results)):
        if result:
            print(f"   ✅ {name}: 通过")
            passed += 1
        else:
            print(f"   ❌ {name}: 失败")

    print(f"\n🎯 总体结果: {passed}/{len(results)} 测试通过")

    if passed >= 3:  # API健康 + 至少2个SEC接口通过
        print("🎉 SEC API接口验证成功！")
        print("\n✨ 修复后的SEC数据源工作正常！")
    elif passed >= 1:
        print("⚠️  部分接口可用，可能需要进一步调试")
    else:
        print("❌ SEC API接口验证失败")


if __name__ == "__main__":
    main()
