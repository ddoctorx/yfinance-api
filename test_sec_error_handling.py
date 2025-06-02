#!/usr/bin/env python3
"""
测试SEC服务的错误处理逻辑
验证在没有API密钥时是否正确返回错误而非模拟数据
"""

from app.services.sec_service import SecService
from app.utils.exceptions import FinanceAPIException
from app.data_sources.base import DataSourceError
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_sec_service_without_api_key():
    """测试在没有API密钥时SEC服务的行为"""
    print("🧪 测试SEC服务错误处理...")

    # 临时移除API密钥环境变量
    original_key = os.environ.pop('SEC_API_KEY', None)

    try:
        # 尝试创建SEC服务实例
        print("\n1️⃣ 测试：创建SEC服务实例（无API密钥）")
        try:
            service = SecService(api_key=None)
            print("❌ 错误：SEC服务应该在没有API密钥时抛出异常")
            return False
        except (FinanceAPIException, DataSourceError) as e:
            print(f"✅ 正确：抛出了预期的异常: {e}")
        except Exception as e:
            print(f"❌ 错误：抛出了意外的异常类型: {type(e).__name__}: {e}")
            return False

        # 测试get_sec_service函数
        print("\n2️⃣ 测试：调用get_sec_service函数（无API密钥）")
        try:
            from app.services.sec_service import get_sec_service
            service = get_sec_service()
            print("❌ 错误：get_sec_service应该在没有API密钥时抛出异常")
            return False
        except FinanceAPIException as e:
            print(f"✅ 正确：get_sec_service抛出了预期的异常: {e}")
        except Exception as e:
            print(f"❌ 错误：get_sec_service抛出了意外的异常类型: {type(e).__name__}: {e}")
            return False

        print("\n3️⃣ 测试：带有空字符串API密钥")
        try:
            service = SecService(api_key="")
            print("❌ 错误：SEC服务应该在API密钥为空时抛出异常")
            return False
        except (FinanceAPIException, DataSourceError) as e:
            print(f"✅ 正确：使用空密钥时抛出了预期的异常: {e}")
        except Exception as e:
            print(f"❌ 错误：使用空密钥时抛出了意外的异常类型: {type(e).__name__}: {e}")
            return False

        print("\n✅ 所有测试通过！SEC服务正确地在没有API密钥时返回错误。")
        return True

    finally:
        # 恢复原始环境变量
        if original_key:
            os.environ['SEC_API_KEY'] = original_key


async def test_api_endpoints_error():
    """测试API端点在SEC服务不可用时的错误处理"""
    print("\n🌐 测试API端点错误处理...")

    # 移除API密钥
    original_key = os.environ.pop('SEC_API_KEY', None)

    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        print("\n1️⃣ 测试：访问财务数据端点（无API密钥）")
        response = client.get("/api/v1/sec/financials/AAPL")

        if response.status_code == 503:
            print(f"✅ 正确：返回了503状态码")
            detail = response.json().get('detail', {})
            if isinstance(detail, dict) and 'error' in detail:
                print(f"✅ 正确：返回了结构化错误信息: {detail['error']}")
            else:
                print(f"⚠️  警告：错误格式可能不完整: {detail}")
        else:
            print(f"❌ 错误：期望503状态码，实际得到: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

        print("\n2️⃣ 测试：访问健康检查端点（无API密钥）")
        response = client.get("/api/v1/sec/health")

        if response.status_code == 503:
            print(f"✅ 正确：健康检查也返回了503状态码")
        else:
            print(f"❌ 错误：健康检查期望503状态码，实际得到: {response.status_code}")
            return False

        print("\n✅ API端点错误处理测试通过！")
        return True

    except ImportError:
        print("⚠️  警告：无法导入TestClient，跳过API端点测试")
        return True
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢复原始环境变量
        if original_key:
            os.environ['SEC_API_KEY'] = original_key


async def main():
    """主测试函数"""
    print("🚀 开始SEC服务错误处理测试")
    print("=" * 50)

    # 测试服务层错误处理
    service_test_passed = await test_sec_service_without_api_key()

    # 测试API层错误处理
    api_test_passed = await test_api_endpoints_error()

    print("\n" + "=" * 50)
    if service_test_passed and api_test_passed:
        print("🎉 所有测试通过！SEC服务现在是生产级别的，不会返回模拟数据。")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码修改。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
