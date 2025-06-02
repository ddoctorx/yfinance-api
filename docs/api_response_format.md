# API 响应格式标准

## 📋 概述

Finance API 使用标准化的响应格式，所有接口都包含 `success`、`code`、`message` 字段，确保客户端能够统一处理成功和失败的情况。

## 🎯 设计原则

1. **一致性** - 所有接口使用相同的响应结构
2. **明确性** - 明确区分成功和失败状态
3. **信息性** - 提供详细的状态码和消息
4. **可扩展性** - 支持不同类型的数据响应

## 📝 响应格式

### 🟢 成功响应格式

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "symbol": "AAPL",
  "data": {
    // 具体的数据内容
  },
  "timestamp": "2025-06-02T19:52:49.696131",
  "data_source": "yahoo_finance",
  "is_fallback": false
}
```

**字段说明：**

| 字段          | 类型    | 必需 | 说明                          |
| ------------- | ------- | ---- | ----------------------------- |
| `success`     | boolean | ✅   | 请求是否成功                  |
| `code`        | string  | ✅   | 响应状态码                    |
| `message`     | string  | ✅   | 人类可读的响应消息            |
| `symbol`      | string  | ❌   | 股票代码 (适用于单个股票查询) |
| `data`        | object  | ❌   | 响应数据                      |
| `timestamp`   | string  | ✅   | 响应时间戳 (ISO 8601 格式)    |
| `data_source` | string  | ❌   | 数据来源                      |
| `is_fallback` | boolean | ❌   | 是否使用降级数据源            |

### 🔴 错误响应格式

```json
{
  "success": false,
  "code": "TICKER_NOT_FOUND",
  "message": "未找到股票代码: INVALID_SYMBOL",
  "detail": "未找到股票代码: 无法获取 INVALID_SYMBOL 的数据",
  "timestamp": "2025-06-02T19:53:00.941177",
  "details": {}
}
```

**字段说明：**

| 字段        | 类型    | 必需 | 说明         |
| ----------- | ------- | ---- | ------------ |
| `success`   | boolean | ✅   | 固定为 false |
| `code`      | string  | ✅   | 错误代码     |
| `message`   | string  | ✅   | 错误消息     |
| `detail`    | string  | ❌   | 详细错误信息 |
| `timestamp` | string  | ✅   | 错误时间戳   |
| `details`   | object  | ❌   | 额外错误信息 |

### 📊 批量响应格式

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "批量获取报价成功，共2个股票",
  "data": {
    "AAPL": {
      // AAPL数据
    },
    "MSFT": {
      // MSFT数据
    }
  },
  "errors": {
    "INVALID": "获取报价失败"
  },
  "timestamp": "2025-06-02T19:53:07.626682"
}
```

**特殊字段：**

| 字段     | 类型   | 说明                           |
| -------- | ------ | ------------------------------ |
| `data`   | object | 成功获取的数据，按 symbol 分组 |
| `errors` | object | 失败的错误信息，按 symbol 分组 |

## 📈 状态码规范

### 成功状态码

| 状态码            | 说明     | 使用场景           |
| ----------------- | -------- | ------------------ |
| `SUCCESS`         | 操作成功 | 所有成功的单一操作 |
| `PARTIAL_SUCCESS` | 部分成功 | 批量操作中部分成功 |

### 错误状态码

| 状态码                | HTTP 状态码 | 说明           | 使用场景           |
| --------------------- | ----------- | -------------- | ------------------ |
| `BAD_REQUEST`         | 400         | 请求参数错误   | 参数验证失败       |
| `UNAUTHORIZED`        | 401         | 未授权         | API 密钥无效或缺失 |
| `FORBIDDEN`           | 403         | 禁止访问       | 权限不足           |
| `NOT_FOUND`           | 404         | 资源未找到     | 接口不存在         |
| `TICKER_NOT_FOUND`    | 404         | 股票代码未找到 | 无效的股票代码     |
| `INVALID_PARAM`       | 400         | 无效参数       | 参数格式错误       |
| `VALIDATION_ERROR`    | 422         | 验证错误       | 数据验证失败       |
| `TOO_MANY_REQUESTS`   | 429         | 请求过多       | 超出限流           |
| `INTERNAL_ERROR`      | 500         | 内部错误       | 服务器内部错误     |
| `BAD_GATEWAY`         | 502         | 网关错误       | 上游服务错误       |
| `SERVICE_UNAVAILABLE` | 503         | 服务不可用     | 服务暂时不可用     |
| `GATEWAY_TIMEOUT`     | 504         | 网关超时       | 上游服务超时       |
| `PARTIAL_FAILURE`     | 200         | 部分失败       | 批量操作全部失败   |

## 🔄 数据源信息

当使用多数据源架构时，响应会包含数据源相关信息：

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "获取股票报价成功 (使用降级数据源: polygon)",
  "data_source": "polygon",
  "is_fallback": true
  // ...其他字段
}
```

**降级场景说明：**

- `data_source`: 实际使用的数据源名称
- `is_fallback`: 是否使用了降级数据源
- `message`: 在降级时会包含相关提示信息

## 🧪 响应示例

### 1. 单个股票报价 - 成功

```bash
GET /api/v1/quote/AAPL
```

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "获取股票报价成功",
  "symbol": "AAPL",
  "data": {
    "last_price": 200.85000610351562,
    "previous_close": 200.29,
    "open_price": 199.3699951171875,
    "day_high": 201.9600067138672,
    "day_low": 196.77999877929688,
    "volume": 70753100,
    "market_cap": 2999855482597,
    "shares": 14935799808,
    "currency": "USD"
  },
  "timestamp": "2025-06-02T19:52:49.696131",
  "data_source": "yahoo_finance",
  "is_fallback": false
}
```

### 2. 股票代码不存在 - 错误

```bash
GET /api/v1/quote/INVALID
```

```json
{
  "success": false,
  "code": "TICKER_NOT_FOUND",
  "message": "未找到股票代码: INVALID",
  "detail": "无法获取 INVALID 的数据",
  "timestamp": "2025-06-02T19:53:00.941177",
  "details": {}
}
```

### 3. 批量查询 - 部分成功

```bash
GET /api/v1/quote/?symbols=AAPL,INVALID,MSFT
```

```json
{
  "success": true,
  "code": "PARTIAL_SUCCESS",
  "message": "批量获取报价部分成功，成功2个，失败1个",
  "data": {
    "AAPL": {
      "last_price": 200.85
      // ...AAPL数据
    },
    "MSFT": {
      "last_price": 460.36
      // ...MSFT数据
    }
  },
  "errors": {
    "INVALID": "获取报价失败"
  },
  "timestamp": "2025-06-02T19:53:07.626682"
}
```

### 4. 健康检查 - 降级状态

```bash
GET /health
```

```json
{
  "success": false,
  "code": "DEGRADED",
  "message": "服务运行异常或降级",
  "status": "degraded",
  "version": "0.1.0",
  "timestamp": "2025-06-02T19:52:41.579082",
  "dependencies": {
    "cache": "healthy",
    "data_sources": "degraded"
  }
}
```

## 💡 客户端处理建议

### JavaScript 示例

```javascript
async function handleApiResponse(response) {
  const data = await response.json();

  if (data.success) {
    // 处理成功情况
    console.log(`操作成功: ${data.message}`);

    if (data.is_fallback) {
      console.warn(`使用降级数据源: ${data.data_source}`);
    }

    return data.data;
  } else {
    // 处理错误情况
    console.error(`操作失败 [${data.code}]: ${data.message}`);
    throw new Error(data.message);
  }
}

// 使用示例
try {
  const quoteData = await fetch('/api/v1/quote/AAPL').then(handleApiResponse);
  console.log('股票数据:', quoteData);
} catch (error) {
  console.error('获取股票数据失败:', error.message);
}
```

### Python 示例

```python
import requests

def handle_api_response(response):
    data = response.json()

    if data['success']:
        // 处理成功情况
        print(f"操作成功: {data['message']}")

        if data.get('is_fallback'):
            print(f"警告: 使用降级数据源: {data['data_source']}")

        return data['data']
    else:
        // 处理错误情况
        error_msg = f"操作失败 [{data['code']}]: {data['message']}"
        print(error_msg)
        raise Exception(error_msg)

// 使用示例
try:
    response = requests.get('/api/v1/quote/AAPL')
    quote_data = handle_api_response(response)
    print('股票数据:', quote_data)
except Exception as e:
    print(f'获取股票数据失败: {e}')
```

## 🔧 版本兼容性

- **v1.0.0+**: 支持完整的标准化响应格式
- **升级指南**: 从旧版本升级时，需要更新客户端代码以处理新的响应结构

---

**💡 提示**: 建议客户端始终检查 `success` 字段来判断请求是否成功，并根据 `code` 字段进行具体的错误处理。
