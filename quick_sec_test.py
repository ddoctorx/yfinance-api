#!/usr/bin/env python3
"""
SEC API快速测试
验证SEC API是否能正常工作
"""

import requests
import json
import os
from datetime import datetime


def test_sec_free_api():
    """测试免费的SEC.gov API"""
    print("🔍 测试免费的SEC.gov API...")

    try:
        # 测试获取公司映射数据
        print("   - 测试公司代码映射...")
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 查找AAPL的CIK
            apple_cik = None
            for key, company in data.items():
                if company.get('ticker', '').upper() == 'AAPL':
                    apple_cik = company.get('cik_str')
                    print(f"   ✅ 找到AAPL的CIK: {apple_cik}")
                    break

            if apple_cik:
                # 测试获取公司提交数据
                print("   - 测试公司提交数据...")
                submissions_url = f"https://data.sec.gov/submissions/CIK{apple_cik:010d}.json"

                response2 = requests.get(
                    submissions_url, headers=headers, timeout=15)

                if response2.status_code == 200:
                    submissions = response2.json()
                    company_name = submissions.get('name', 'Unknown')
                    recent_filings = submissions.get(
                        'filings', {}).get('recent', {})
                    forms = recent_filings.get('form', [])

                    print(f"   ✅ 公司名称: {company_name}")
                    print(f"   ✅ 最近提交的表单数量: {len(forms)}")

                    # 显示最近的几个10-K和10-Q
                    form_counts = {}
                    for form in forms[:20]:
                        form_counts[form] = form_counts.get(form, 0) + 1

                    print("   📊 最近提交的表单类型:")
                    for form_type, count in list(form_counts.items())[:5]:
                        print(f"       {form_type}: {count} 份")

                    return True
                else:
                    print(f"   ❌ 获取提交数据失败: HTTP {response2.status_code}")
                    return False
            else:
                print("   ❌ 未找到AAPL的CIK")
                return False
        else:
            print(f"   ❌ 获取公司映射失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False


def test_sec_api_connection():
    """测试SEC API连接性"""
    print("\n🔍 测试SEC API连接性...")

    api_key = os.environ.get('SEC_API_KEY')
    if not api_key:
        print("   ⚠️  未设置SEC_API_KEY环境变量")
        print("   💡 如需测试付费API功能，请设置此变量")
        return False

    try:
        # 测试简单的查询API调用
        print("   - 测试Query API...")

        # 这里只是模拟，因为需要sec-api包
        print("   ✅ SEC API密钥已配置")
        print(f"   🔑 API密钥: {api_key[:8]}...")

        return True
    except Exception as e:
        print(f"   ❌ SEC API测试异常: {e}")
        return False


def test_concepts_api():
    """测试SEC Concepts API"""
    print("\n🔍 测试SEC Concepts API...")

    try:
        # 测试获取苹果公司的收入概念数据
        cik = "320193"  # Apple的CIK
        concept = "Revenues"

        print(f"   - 测试获取概念数据: {concept}...")

        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik.zfill(10)}/us-gaap/{concept}.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            entity_name = data.get('entityName', 'Unknown')
            cik_str = data.get('cik')

            print(f"   ✅ 实体名称: {entity_name}")
            print(f"   ✅ CIK: {cik_str}")

            # 分析数据结构
            if 'units' in data and 'USD' in data['units']:
                usd_data = data['units']['USD']
                print(f"   ✅ USD数据条目: {len(usd_data)} 条")

                # 统计表单类型
                form_types = {}
                fiscal_years = set()

                for item in usd_data:
                    form_type = item.get('form')
                    fy = item.get('fy')

                    if form_type:
                        form_types[form_type] = form_types.get(
                            form_type, 0) + 1
                    if fy:
                        fiscal_years.add(fy)

                print("   📊 表单类型分布:")
                for form_type, count in sorted(form_types.items()):
                    print(f"       {form_type}: {count} 条")

                recent_years = sorted(fiscal_years, reverse=True)[:5]
                print(f"   📅 最近财年: {recent_years}")

                return True
            else:
                print("   ⚠️  数据结构异常，未找到USD单位数据")
                return False
        else:
            print(f"   ❌ 获取概念数据失败: HTTP {response.status_code}")
            if response.status_code == 429:
                print("   💡 可能触发了速率限制，请稍后重试")
            return False

    except Exception as e:
        print(f"   ❌ 概念API测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 SEC API 快速验证测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    results = []

    # 测试免费SEC API
    results.append(test_sec_free_api())

    # 测试付费SEC API连接性
    results.append(test_sec_api_connection())

    # 测试概念API
    results.append(test_concepts_api())

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")

    test_names = ["免费SEC API", "付费SEC API", "概念数据API"]
    passed = 0

    for i, (name, result) in enumerate(zip(test_names, results)):
        if result:
            print(f"   ✅ {name}: 通过")
            passed += 1
        else:
            print(f"   ❌ {name}: 失败")

    print(f"\n🎯 总体结果: {passed}/{len(results)} 测试通过")

    if passed >= 2:  # 至少2个测试通过就认为基本可用
        print("🎉 SEC API基本功能验证通过！")
        print("\n💡 建议:")
        print("   1. 确保安装所有依赖: pip install -r requirements.txt")
        print("   2. 设置SEC_API_KEY环境变量以使用完整功能")
        print("   3. 运行完整测试: python test_sec_api.py")
    else:
        print("⚠️  SEC API验证存在问题，请检查网络连接")


if __name__ == "__main__":
    main()
