# API Key 配置指南

## 概览

本系统支持多种 API 密钥配置方式，推荐使用环境变量而非硬编码方式进行配置。

## 当前状态

✅ **已解决**: API key 现在通过环境变量配置，不再硬编码在代码中

## 配置方式

### 1. 环境变量 (推荐)

```bash
# 设置SEC API密钥
export SEC_API_KEY="your_sec_api_key_here"

# 启动服务
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. .env 文件配置

创建`.env`文件（基于`config.env`模板）：

```env
# SEC API 配置
SEC_API_KEY=your_sec_api_key_here
SEC_API_TIMEOUT=30
SEC_API_MAX_RETRIES=3

# 其他配置...
DEBUG=true
LOG_LEVEL=INFO
```

### 3. 使用启动脚本

使用提供的启动脚本：

```bash
# 编辑脚本中的API key
vim start_with_sec_api.sh

# 运行脚本
./start_with_sec_api.sh
```

## 支持的 API 密钥类型

### SEC API (sec-api.io)

- **用途**: 获取 SEC 财务报表数据
- **环境变量**: `SEC_API_KEY`
- **获取地址**: https://sec-api.io/dashboard
- **配置位置**: `app/core/config.py`

### Polygon.io API

- **用途**: 股价数据备用数据源
- **环境变量**: `POLYGON_API_KEY`
- **获取地址**: https://polygon.io/dashboard/api-keys
- **配置位置**: `app/core/config.py`

## 配置文件结构

### app/core/config.py

```python
class Settings(BaseSettings):
    # SEC API 配置
    sec_api_key: Optional[str] = Field(
        default=None,
        env="SEC_API_KEY",
        description="SEC API密钥，用于获取财务报表数据"
    )
    sec_api_timeout: int = Field(
        default=30, env="SEC_API_TIMEOUT")
    sec_api_max_retries: int = Field(
        default=3, env="SEC_API_MAX_RETRIES")
```

## 安全最佳实践

### ✅ 推荐做法

1. **使用环境变量**: 将 API key 设置为环境变量
2. **使用.env 文件**: 本地开发时使用.env 文件（已添加到.gitignore）
3. **生产环境**: 通过 CI/CD 系统的环境变量设置
4. **定期轮换**: 定期更换 API 密钥

### ❌ 避免做法

1. **硬编码**: 不要在代码中硬编码 API key
2. **版本控制**: 不要将 API key 提交到版本控制系统
3. **明文日志**: 不要在日志中输出完整的 API key
4. **公开分享**: 不要在公开场所分享 API key

## 验证配置

### 1. 检查配置状态

```bash
# 检查SEC API key是否正确配置
export SEC_API_KEY="your_key_here"
python -c "from app.core.config import settings; print(f'SEC API Key: {settings.sec_api_key[:10] if settings.sec_api_key else None}...')"
```

### 2. 健康检查

```bash
# 启动服务后检查健康状态
curl http://127.0.0.1:8000/api/v1/sec/health
```

预期响应：

```json
{
  "service": "sec_service",
  "status": "healthy",
  "data_source_status": {
    "api_available": true,
    "cache_enabled": true
  }
}
```

### 3. 功能测试

```bash
# 测试SEC财务数据接口
curl "http://127.0.0.1:8000/api/v1/sec/financials/AAPL?years=1"
```

## 问题排查

### API key 未配置

**症状**: 服务运行在模拟数据模式

```
WARNING - SEC API密钥未提供，将使用模拟数据模式
```

**解决方案**: 设置`SEC_API_KEY`环境变量

### API key 无效

**症状**: API 请求返回认证错误

```
ERROR - SEC API客户端初始化失败: Invalid API key
```

**解决方案**:

1. 检查 API key 是否正确
2. 确认账户状态和配额
3. 联系 sec-api.io 支持

### 权限不足

**症状**: 部分 API 返回权限错误

```
HTTP 403 - Insufficient permissions
```

**解决方案**:

1. 升级 API 账户级别
2. 检查 API 使用配额
3. 确认 API key 权限范围

## 代码修改历史

### v1.0 (修改前)

- API key 硬编码在多个文件中
- 存在安全风险
- 不便于部署和维护

### v2.0 (修改后)

- 使用环境变量配置
- 支持.env 文件
- 统一配置管理
- 安全最佳实践

## 相关文件

- `app/core/config.py` - 配置定义
- `config.env` - 配置模板
- `start_with_sec_api.sh` - 启动脚本
- `app/services/sec_service.py` - SEC 服务实现
- `app/api/v1/sec.py` - SEC API 路由
