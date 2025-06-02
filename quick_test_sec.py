#!/usr/bin/env python3
"""
SEC高级功能快速测试脚本
测试基本功能，避免需要真实API密钥的复杂测试
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/sec-advanced"


def test_endpoint(endpoint_path, test_name):
    """测试单个端点"""
    url = f"{BASE_URL}{endpoint_path}"
    print(f"\n🔄 测试: {test_name}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ 成功")
            print(
                f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")
        else:
            print(f"❌ 失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"错误内容: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")


def main():
    """主测试函数"""
    print("🚀 SEC高级功能快速测试")
    print("=" * 50)

    # 测试基本端点
    test_cases = [
        ("/", "API概览"),
        ("/health", "健康检查"),
    ]

    for endpoint, name in test_cases:
        test_endpoint(endpoint, name)
        time.sleep(1)  # 避免请求过快

    print("\n" + "=" * 50)
    print("📝 测试说明:")
    print("• API概览和健康检查应该正常工作")
    print("• 其他功能需要有效的SEC API密钥才能正常工作")
    print("• 如果要测试完整功能，请设置环境变量 SEC_API_KEY")
    print("• 更多测试请运行: ./venv/bin/python test_sec_advanced.py")


if __name__ == "__main__":
    main()
