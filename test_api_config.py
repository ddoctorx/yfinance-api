#!/usr/bin/env python3
"""
SEC API配置测试脚本
验证API密钥是否正确配置
"""

from app.core.config import settings
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))


def test_api_config():
    """测试API配置"""
    print("=== SEC API配置测试 ===")

    # 检查环境变量
    env_key = os.getenv("SEC_API_KEY")
    print(
        f"环境变量 SEC_API_KEY: {env_key[:10]}...{env_key[-10:] if env_key else 'None'}")

    # 检查settings配置（注意字段名是sec_api_key）
    settings_key = getattr(settings, "sec_api_key", None)
    print(
        f"Settings sec_api_key: {settings_key[:10]}...{settings_key[-10:] if settings_key else 'None'}")

    # 检查是否为默认值
    is_default = settings_key == "your_sec_api_key_here" if settings_key else True
    print(f"是否为默认值: {is_default}")

    # 检查密钥长度
    if settings_key:
        print(f"API密钥长度: {len(settings_key)}")
        print(f"API密钥格式正确: {len(settings_key) >= 40}")

    # 测试SEC API连接
    try:
        from sec_api import QueryApi
        query_api = QueryApi(api_key=settings_key)
        print("✅ SEC API对象创建成功")

        # 简单的健康检查
        try:
            # 尝试一个简单的查询
            result = query_api.get_filings({
                "query": "ticker:AAPL",
                "from": "0",
                "size": "1"
            })
            if result:
                print("✅ SEC API连接测试成功")
                print(f"返回数据量: {len(result.get('filings', []))}")
                return True
            else:
                print("❌ SEC API返回空结果")
                return False
        except Exception as api_e:
            print(f"❌ SEC API调用失败: {api_e}")
            return False

    except Exception as e:
        print(f"❌ SEC API初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = test_api_config()
    sys.exit(0 if success else 1)
