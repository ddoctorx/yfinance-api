#!/usr/bin/env python3
"""
简单的SEC API测试脚本
"""

import requests
import json
import os
from datetime import datetime


def test_sec_endpoints():
    """测试SEC API端点"""

    base_url = "http://localhost:8000"

    print("🧪 开始测试SEC API功能...")
    print(f"📍 API服务器: {base_url}")

    # 测试用的股票代码
    test_ticker = "AAPL"

    try:
        # 1. 测试健康检查
        print("\n1️⃣ 测试健康检查...")
        response = requests.get(f"{base_url}/api/v1/sec/sec/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")

        # 2. 测试API概览
        print("\n2️⃣ 测试API概览...")
        response = requests.get(f"{base_url}/api/v1/sec/sec/")
        if response.status_code == 200:
            data = response.json()
            print("✅ API概览获取成功")
            print(f"   描述: {data.get('description', 'N/A')}")
        else:
            print(f"❌ API概览失败: {response.status_code}")

        # 3. 测试公司财务数据
        print(f"\n3️⃣ 测试获取 {test_ticker} 财务数据...")
        response = requests.get(
            f"{base_url}/api/v1/sec/sec/financials/{test_ticker}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 财务数据获取成功")
            print(f"   公司名称: {data.get('company_name', 'N/A')}")
            print(f"   年度财务记录数: {len(data.get('annual_financials', []))}")
            print(f"   季度财务记录数: {len(data.get('quarterly_financials', []))}")
        else:
            print(f"❌ 财务数据获取失败: {response.status_code}")

        # 4. 测试季度收入
        print(f"\n4️⃣ 测试获取 {test_ticker} 季度收入...")
        response = requests.get(
            f"{base_url}/api/v1/sec/sec/revenue/{test_ticker}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 季度收入获取成功")
            print(f"   股票代码: {data.get('ticker', 'N/A')}")
            print(f"   季度数据条数: {len(data.get('quarterly_data', []))}")
        else:
            print(f"❌ 季度收入获取失败: {response.status_code}")

        # 5. 测试SEC新闻
        print(f"\n5️⃣ 测试获取 {test_ticker} SEC新闻...")
        response = requests.get(
            f"{base_url}/api/v1/sec/sec/news/{test_ticker}")
        if response.status_code == 200:
            data = response.json()
            print("✅ SEC新闻获取成功")
            print(f"   新闻条数: {len(data.get('news_items', []))}")
            if data.get('news_items'):
                first_news = data['news_items'][0]
                print(f"   第一条新闻: {first_news.get('title', 'N/A')}")
        else:
            print(f"❌ SEC新闻获取失败: {response.status_code}")

        # 6. 测试财务比率
        print(f"\n6️⃣ 测试获取 {test_ticker} 财务比率...")
        response = requests.get(
            f"{base_url}/api/v1/sec/sec/ratios/{test_ticker}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 财务比率获取成功")
            print(f"   期间: {data.get('period', 'N/A')}")
            if data.get('ratios'):
                ratios = data['ratios']
                print(f"   ROA: {ratios.get('roa', 'N/A')}%")
                print(f"   ROE: {ratios.get('roe', 'N/A')}%")
        else:
            print(f"❌ 财务比率获取失败: {response.status_code}")

        print("\n🎉 SEC API测试完成!")

        # 检查是否在模拟模式
        sec_api_key = os.environ.get('SEC_API_KEY')
        if not sec_api_key:
            print("\n💡 注意: 当前运行在模拟数据模式")
            print("   如需获取真实数据，请:")
            print("   1. 获取 sec-api.io 的API密钥")
            print("   2. 设置环境变量: export SEC_API_KEY='your_api_key'")
            print("   3. 重启API服务")
        else:
            print(f"\n✅ 使用真实API密钥: {sec_api_key[:10]}...")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("   请确保API服务器正在运行: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    test_sec_endpoints()
