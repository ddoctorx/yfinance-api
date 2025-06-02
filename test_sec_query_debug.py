#!/usr/bin/env python3
"""
SEC API查询调试工具
直接测试SEC API的响应来理解数据结构
"""

import requests
import json
import os
from datetime import datetime


def test_sec_api_query():
    """测试SEC API的直接查询"""

    api_key = os.environ.get('SEC_API_KEY')
    if not api_key:
        print("❌ 错误: 未找到SEC API密钥")
        print("请设置环境变量 SEC_API_KEY")
        return

    # 根据官方文档构建查询
    query_payload = {
        "query": "ticker:\"AAPL\" AND formType:\"10-K\"",
        "from": "0",
        "size": "2",
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    print("🔍 测试SEC API查询...")
    print(f"查询payload: {json.dumps(query_payload, indent=2)}")
    print(f"API端点: https://api.sec-api.io")

    try:
        response = requests.post(
            'https://api.sec-api.io',
            json=query_payload,
            headers=headers,
            timeout=30
        )

        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ 查询成功!")

            # 打印响应结构
            print(f"\n📊 响应数据结构:")
            print(f"  - 根键: {list(data.keys())}")

            if 'filings' in data:
                filings = data['filings']
                print(f"  - 文件数量: {len(filings)}")

                if filings:
                    print(f"\n📄 第一个文件的结构:")
                    first_filing = filings[0]
                    print(f"  - 键: {list(first_filing.keys())}")

                    # 打印重要字段
                    important_fields = [
                        'companyName', 'formType', 'filedAt', 'periodOfReport',
                        'ticker', 'cik', 'accessionNo', 'linkToFilingDetails'
                    ]

                    print(f"\n🔍 重要字段值:")
                    for field in important_fields:
                        value = first_filing.get(field, 'N/A')
                        print(f"  - {field}: {value}")

                    # 检查是否有entities信息
                    if 'entities' in first_filing:
                        entities = first_filing['entities']
                        print(f"\n🏢 实体信息 ({len(entities)} 个):")
                        if entities:
                            first_entity = entities[0]
                            print(f"  - 实体键: {list(first_entity.keys())}")
                            for key, value in first_entity.items():
                                print(f"    {key}: {value}")

                    # 保存完整响应到文件用于调试
                    with open('sec_api_response_debug.json', 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 完整响应已保存到: sec_api_response_debug.json")
            else:
                print("❌ 响应中没有'filings'字段")
                print(f"实际响应: {json.dumps(data, indent=2)}")

        else:
            print(f"❌ 查询失败: HTTP {response.status_code}")
            print(f"错误响应: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {e}")


if __name__ == "__main__":
    test_sec_api_query()
