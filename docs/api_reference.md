# Finance API 接口文档

## 📚 API 概览

Finance API 提供统一的金融数据接口，支持股票报价、历史数据和 SEC 财报信息查询。

**基础 URL**: `http://localhost:8000/api/v1`

**支持格式**: JSON

**认证方式**: 无需认证 (部分高级功能需要 API 密钥)

## 📊 接口分类

### 1. 📈 股票报价 (`/quote`)

#### 1.1 获取快速报价

```
GET /api/v1/quote/{symbol}
```

**功能**: 获取股票实时报价信息

**路径参数**:

- `symbol` (string, required): 股票代码，如 AAPL, MSFT, GOOGL

**响应示例**:

```json
{
  "symbol": "AAPL",
  "data": {
    "symbol": "AAPL",
    "current_price": 175.5,
    "change": 2.5,
    "change_percent": 1.45,
    "volume": 45678900,
    "market_cap": 2800000000000,
    "data_source": "yahoo_finance",
    "last_updated": "2025-06-02T10:30:00Z"
  },
  "success": true,
  "timestamp": "2025-06-02T10:30:05Z"
}
```

#### 1.2 获取详细报价

```
GET /api/v1/quote/{symbol}/detailed
```

**功能**: 获取包含详细财务指标的报价信息

**响应示例**:

```json
{
  "symbol": "AAPL",
  "data": {
    "symbol": "AAPL",
    "current_price": 175.5,
    "change": 2.5,
    "change_percent": 1.45,
    "volume": 45678900,
    "market_cap": 2800000000000,
    "pe_ratio": 28.5,
    "eps": 6.16,
    "dividend_yield": 0.52,
    "beta": 1.25,
    "52_week_high": 199.62,
    "52_week_low": 164.08,
    "data_source": "yahoo_finance"
  }
}
```

#### 1.3 获取公司信息

```
GET /api/v1/quote/{symbol}/info
```

**功能**: 获取公司基本信息

**响应示例**:

```json
{
  "symbol": "AAPL",
  "data": {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "country": "United States",
    "employees": 164000,
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones...",
    "data_source": "yahoo_finance"
  }
}
```

#### 1.4 批量获取报价

```
POST /api/v1/quote/batch
```

**功能**: 批量获取多个股票的报价

**请求体**:

```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

**响应示例**:

```json
{
  "data": {
    "AAPL": {
      "symbol": "AAPL",
      "current_price": 175.5,
      "change": 2.5
    },
    "MSFT": {
      "symbol": "MSFT",
      "current_price": 415.3,
      "change": -1.2
    }
  },
  "errors": {
    "GOOGL": "获取报价失败"
  }
}
```

### 2. 📊 历史数据 (`/history`)

#### 2.1 获取历史 K 线数据

```
GET /api/v1/history/{symbol}
```

**功能**: 获取股票历史价格数据

**路径参数**:

- `symbol` (string, required): 股票代码

**查询参数**:

- `period` (string, optional): 数据周期，默认 "1y"
  - 可选值: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`
- `interval` (string, optional): 数据间隔，默认 "1d"
  - 可选值: `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`
- `start` (string, optional): 开始日期 (YYYY-MM-DD)
- `end` (string, optional): 结束日期 (YYYY-MM-DD)
- `auto_adjust` (boolean, optional): 是否自动调整价格，默认 true
- `prepost` (boolean, optional): 是否包含盘前盘后，默认 false
- `actions` (boolean, optional): 是否包含分红拆股，默认 true

**响应示例**:

```json
{
  "symbol": "AAPL",
  "data": {
    "prices": [
      {
        "date": "2025-06-01",
        "open": 173.0,
        "high": 175.5,
        "low": 172.8,
        "close": 175.5,
        "volume": 45678900
      }
    ],
    "metadata": {
      "start_date": "2024-06-01",
      "end_date": "2025-06-01",
      "interval": "1d",
      "data_points": 252
    }
  }
}
```

#### 2.2 获取股息历史

```
GET /api/v1/history/{symbol}/dividends
```

#### 2.3 获取拆股历史

```
GET /api/v1/history/{symbol}/splits
```

#### 2.4 获取公司行动

```
GET /api/v1/history/{symbol}/actions
```

### 3. 🏢 SEC 财报数据 (`/sec`)

#### 3.1 获取财务报表

```
GET /api/v1/sec/financials/{ticker}
```

**功能**: 获取公司 SEC 财务报表数据

**路径参数**:

- `ticker` (string, required): 美股股票代码

**查询参数**:

- `years` (integer, optional): 获取年数 (1-10)，默认 5
- `include_quarterly` (boolean, optional): 是否包含季度数据，默认 true
- `use_cache` (boolean, optional): 是否使用缓存，默认 true

**响应示例**:

```json
{
  "ticker": "AAPL",
  "summary": {
    "total_annual_reports": 2,
    "total_quarterly_reports": 0,
    "latest_annual_date": "2018-09-29",
    "latest_quarterly_date": null
  },
  "annual_financials": [
    {
      "fiscal_year": 2018,
      "period_end": "2018-09-29",
      "filing_date": "2018-11-05",
      "revenue": 215639000000,
      "net_income": 43142000000,
      "total_assets": 365725000000,
      "total_liabilities": 258578000000,
      "shareholders_equity": 107147000000,
      "operating_cash_flow": 52463000000
    }
  ],
  "quarterly_financials": [],
  "data_source": "sec_edgar",
  "cache_used": true,
  "last_updated": "2025-06-02T10:30:00Z"
}
```

#### 3.2 获取季度收入

```
GET /api/v1/sec/quarterly-revenue/{ticker}
```

**查询参数**:

- `quarters` (integer, optional): 获取季度数 (1-20)，默认 8

**响应示例**:

```json
{
  "ticker": "AAPL",
  "total_quarters": 0,
  "quarterly_revenue": [],
  "growth_analysis": {
    "latest_quarter_yoy_growth": null,
    "average_growth_rate": null
  },
  "data_source": "sec_edgar"
}
```

#### 3.3 获取年度对比

```
GET /api/v1/sec/annual-comparison/{ticker}
```

**查询参数**:

- `years` (integer, optional): 对比年数 (1-10)，默认 5

#### 3.4 获取 SEC 新闻

```
GET /api/v1/sec/news/{ticker}
```

**查询参数**:

- `limit` (integer, optional): 新闻数量 (1-100)，默认 20

**响应示例**:

```json
{
  "ticker": "AAPL",
  "total_count": 1,
  "filings": [
    {
      "form_type": "8-K",
      "filing_date": "2023-08-04",
      "acceptance_datetime": "2023-08-04T06:01:36.000Z",
      "document_url": "https://sec.gov/edgar/data/320193/000032019323000077/0000320193-23-000077-index.htm",
      "description": "Current report filing"
    }
  ],
  "data_source": "sec_edgar"
}
```

#### 3.5 获取财务比率

```
GET /api/v1/sec/ratios/{ticker}
```

**查询参数**:

- `period` (string, optional): 期间类型，默认 "annual"
  - 可选值: `annual`, `quarterly`

**响应示例**:

```json
{
  "ticker": "AAPL",
  "period": "annual",
  "ratios": {
    "debt_to_equity": 0.1667,
    "roa": 6.67,
    "roe": 6.67,
    "current_ratio": null,
    "pe_ratio": null,
    "pb_ratio": null
  },
  "calculation_date": "2025-06-02T10:30:00Z",
  "data_source": "sec_edgar"
}
```

#### 3.6 SEC 服务健康检查

```
GET /api/v1/sec/health
```

**响应示例**:

```json
{
  "service": "sec_service",
  "status": "healthy",
  "api_available": true,
  "cache_enabled": true,
  "last_checked": "2025-06-02T10:30:00Z"
}
```

### 4. 🧪 测试调试 (`/test`)

#### 4.1 Polygon 原始数据测试

```
GET /api/v1/test/polygon/{symbol}/raw
```

#### 4.2 Polygon 报价测试

```
GET /api/v1/test/polygon/{symbol}/quote
```

#### 4.3 数据源状态检查

```
GET /api/v1/test/data-sources/status
```

#### 4.4 健康检查

```
GET /api/v1/test/health-check
```

### 5. 🏥 系统监控

#### 5.1 系统健康检查

```
GET /health
```

**响应示例**:

```json
{
  "service": "finance_api",
  "version": "0.1.0",
  "status": "healthy",
  "timestamp": "2025-06-02T10:30:00Z",
  "uptime_seconds": 3600,
  "data_sources": {
    "yahoo_finance": "healthy",
    "polygon": "healthy",
    "sec": "healthy"
  }
}
```

#### 5.2 数据源状态

```
GET /data-sources/status
```

#### 5.3 缓存信息

```
GET /cache/info
```

## 🔧 错误响应格式

### 标准错误响应

```json
{
  "error": "InvalidParameterError",
  "message": "股票代码格式无效",
  "details": {
    "parameter": "symbol",
    "value": "",
    "expected": "非空股票代码"
  },
  "timestamp": "2025-06-02T10:30:00Z",
  "path": "/api/v1/quote/",
  "request_id": "req_12345"
}
```

### HTTP 状态码说明

- `200` - 请求成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `429` - 请求频率超限
- `500` - 服务器内部错误
- `502` - 数据源不可用
- `503` - 服务暂时不可用

## 📋 数据源说明

### Yahoo Finance (主数据源)

- **优点**: 免费、无限制、覆盖全球
- **限制**: 数据延迟 15 分钟
- **用途**: 报价、历史数据、公司信息

### Polygon.io (备用数据源)

- **优点**: 专业级数据、实时性好
- **限制**: 需要 API 密钥、有调用限额
- **用途**: 报价、历史数据降级

### SEC EDGAR (财报数据)

- **优点**: 官方财报数据、权威性高
- **限制**: 需要 API 密钥、仅美股
- **用途**: 财务报表、SEC 文件

## 🚀 使用示例

### 1. 获取苹果股票报价

```bash
curl "http://localhost:8000/api/v1/quote/AAPL"
```

### 2. 获取微软历史数据

```bash
curl "http://localhost:8000/api/v1/history/MSFT?period=3mo&interval=1d"
```

### 3. 获取苹果财务报表

```bash
curl "http://localhost:8000/api/v1/sec/financials/AAPL?years=2"
```

### 4. 批量获取报价

```bash
curl -X POST "http://localhost:8000/api/v1/quote/batch" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
```

## 🔄 智能降级机制

当主数据源 (Yahoo Finance) 失败时，系统会自动切换到备用数据源 (Polygon.io)：

1. **透明切换**: 前端无感知，API 接口保持一致
2. **状态标识**: 响应中包含 `data_source` 和 `is_fallback` 字段
3. **自动恢复**: 主数据源恢复后自动切回
4. **监控告警**: 降级事件会记录到日志

## 📊 性能指标

- **响应时间**: 通常 < 500ms
- **缓存命中率**: > 80%
- **可用性**: > 99.9%
- **并发支持**: 1000+ QPS

## 🔐 安全说明

- **API 密钥**: 通过环境变量配置，不在代码中硬编码
- **限流保护**: 防止 API 滥用
- **输入验证**: 所有参数经过严格验证
- **日志记录**: 详细的访问和错误日志

## 📞 技术支持

- **在线文档**: http://localhost:8000/docs (Swagger UI)
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **项目地址**: GitHub Repository URL
