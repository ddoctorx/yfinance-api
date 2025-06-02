# SEC 财报数据 API 使用指南

## 📋 概览

本 API 模块基于 SEC EDGAR 官方数据源，提供美股公司的财务报表数据和相关信息。所有数据来源于美国证券交易委员会(SEC)的官方 XBRL 文件，确保数据的权威性和准确性。

## 🌟 主要功能

### 1. 财务报表数据

- **年度报告** (10-K): 公司年度财务报表
- **季度报告** (10-Q): 公司季度财务报表
- **损益表**: 营业收入、净利润、毛利润等
- **资产负债表**: 总资产、总负债、股东权益等
- **现金流量表**: 经营现金流、投资现金流、筹资现金流等

### 2. 数据分析功能

- **季度收入趋势**: 按季度展示收入变化，包含同比增长率
- **年度财务对比**: 多年财务指标对比和增长率计算
- **财务比率计算**: ROA、ROE、负债权益比等关键比率

### 3. SEC 新闻和文件

- **最新 SEC 文件**: 10-K、10-Q、8-K 等文件提交记录
- **直接链接**: 提供 SEC 官网的直接访问链接
- **文件摘要**: 文件类型、提交日期等基本信息

## 📊 数据来源

- **官方来源**: [SEC EDGAR API](https://api.edgarfiling.sec.gov/docs/index.html)
- **数据格式**: XBRL (eXtensible Business Reporting Language)
- **数据更新**: 实时同步 SEC 官方数据
- **免费使用**: 基于 SEC 公开数据，完全免费

## 🔧 API 端点

### 基础信息

- **Base URL**: `http://your-api-domain.com/v1/sec`
- **认证**: 无需认证 (基于 SEC 公开数据)
- **限流**: 每分钟 10-100 次请求 (根据配置)

### 主要端点

#### 1. 获取公司财务数据

```
GET /v1/sec/financials/{ticker}
```

**参数**:

- `ticker` (必需): 美股股票代码 (如: AAPL, MSFT, GOOGL)
- `years` (可选): 获取年数，默认 5 年，范围 1-10
- `include_quarterly` (可选): 是否包含季度数据，默认 true
- `use_cache` (可选): 是否使用缓存，默认 true

**示例**:

```bash
curl "http://localhost:8000/v1/sec/financials/AAPL?years=3&include_quarterly=true"
```

#### 2. 获取季度收入数据

```
GET /v1/sec/quarterly-revenue/{ticker}
```

**参数**:

- `ticker` (必需): 股票代码
- `quarters` (可选): 获取季度数，默认 8，范围 1-20
- `use_cache` (可选): 是否使用缓存

**示例**:

```bash
curl "http://localhost:8000/v1/sec/quarterly-revenue/MSFT?quarters=8"
```

#### 3. 获取年度财务对比

```
GET /v1/sec/annual-comparison/{ticker}
```

**参数**:

- `ticker` (必需): 股票代码
- `years` (可选): 对比年数，默认 5 年，范围 1-10

#### 4. 获取 SEC 新闻和文件

```
GET /v1/sec/news/{ticker}
```

**参数**:

- `ticker` (必需): 股票代码
- `limit` (可选): 新闻数量限制，默认 20，范围 1-100

#### 5. 获取财务比率

```
GET /v1/sec/ratios/{ticker}
```

**参数**:

- `ticker` (必需): 股票代码
- `period` (可选): 期间类型，"annual" 或 "quarterly"，默认"annual"

#### 6. 健康检查

```
GET /v1/sec/health
```

## 💡 使用示例

### Python 示例

```python
import requests
import json

# 获取苹果公司最近3年财务数据
response = requests.get(
    "http://localhost:8000/v1/sec/financials/AAPL",
    params={
        "years": 3,
        "include_quarterly": True
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"公司名称: {data['company_name']}")
    print(f"年度报告数: {len(data['annual_reports'])}")
    print(f"季度报告数: {len(data['quarterly_reports'])}")

    # 显示最新年度收入
    if data['annual_reports']:
        latest = data['annual_reports'][0]
        revenue = latest['income_statement']['revenue']
        print(f"最新年度收入: ${revenue:,.0f}")
else:
    print(f"请求失败: {response.status_code}")
```

### JavaScript 示例

```javascript
// 获取微软公司季度收入趋势
fetch('http://localhost:8000/v1/sec/quarterly-revenue/MSFT?quarters=8')
  .then(response => response.json())
  .then(data => {
    console.log(`公司: ${data.company_name}`);
    console.log(`季度数: ${data.total_quarters}`);

    data.quarterly_revenues.forEach(quarter => {
      console.log(`${quarter.quarter}: $${quarter.revenue.toLocaleString()}`);
      if (quarter.yoy_growth_rate) {
        console.log(`  同比增长: ${quarter.yoy_growth_rate}%`);
      }
    });
  })
  .catch(error => console.error('Error:', error));
```

## 📈 响应格式

### 财务数据响应结构

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "cik": "0000320193",
  "last_updated": "2024-01-15T10:30:00",
  "annual_reports": [
    {
      "year": 2023,
      "filing_date": "2023-10-27T00:00:00",
      "period_end_date": "2023-09-30T00:00:00",
      "income_statement": {
        "revenue": 383285000000,
        "net_income": 96995000000,
        "period": "FY2023",
        "form_type": "10-K"
      },
      "balance_sheet": {
        "total_assets": 352755000000,
        "total_liabilities": 290437000000,
        "stockholders_equity": 62317000000,
        "period": "FY2023",
        "form_type": "10-K"
      }
    }
  ],
  "quarterly_reports": [...]
}
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装SEC相关依赖
pip install sec-api requests-cache
```

### 2. 启动 API 服务

```bash
# 启动开发服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 测试 API

```bash
# 运行测试脚本
python test_sec_endpoints.py
```

### 4. 访问文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## ⚡ 性能优化

### 缓存策略

- **财务数据**: 缓存 1 小时 (数据变化不频繁)
- **新闻数据**: 缓存 30 分钟 (相对实时性要求)
- **财务比率**: 缓存 1 小时 (计算密集型)

### 请求优化

- 使用 `use_cache=true` 参数提高响应速度
- 合理设置 `years` 和 `quarters` 参数，避免过大的数据量
- 并发请求时注意 API 限流

## 🔍 故障排除

### 常见问题

#### 1. 股票代码未找到

```json
{
  "detail": "未找到股票代码 INVALID 对应的CIK"
}
```

**解决方案**: 确保使用正确的美股股票代码

#### 2. 数据不足

某些公司可能没有完整的 XBRL 数据，导致部分字段为空。这是正常现象。

#### 3. 请求超时

SEC API 有时响应较慢，可以适当增加超时时间或启用缓存。

### 调试模式

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --log-level debug
```

## 📝 更新日志

### v1.0.0 (2024-01-15)

- ✨ 初始版本发布
- 📊 支持 10-K/10-Q 财务报表数据
- 📈 季度收入趋势分析
- 🔢 财务比率计算
- 📰 SEC 新闻和文件查询
- 💾 Redis 缓存支持

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- **GitHub Issues**: [项目仓库](https://github.com/your-repo)
- **文档参考**: [SEC EDGAR API 官方文档](https://api.edgarfiling.sec.gov/docs/index.html)

---

**免责声明**: 本 API 基于 SEC 公开数据构建，仅供研究和学习使用。投资决策请基于专业分析和多方面信息。
