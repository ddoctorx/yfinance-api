import os
import sys

# 临时移除API密钥
os.environ.pop('SEC_API_KEY', None)

try:
    from app.utils.exceptions import FinanceAPIException
    from app.data_sources.base import DataSourceError
    from app.data_sources.sec_source import SecDataSource

    print("测试SEC数据源错误处理...")

    # 尝试创建没有API密钥的数据源
    source = SecDataSource(api_key=None)
    print("❌ 错误：应该抛出异常，但没有抛出")

except DataSourceError as e:
    print(f"✅ 正确：抛出了预期的DataSourceError: {e}")

except FinanceAPIException as e:
    print(f"✅ 也正确：抛出了FinanceAPIException: {e}")

except Exception as e:
    print(f"⚠️ 意外异常类型: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
