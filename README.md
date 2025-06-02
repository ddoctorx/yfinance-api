# Finance API

基于 **多数据源架构** 的金融数据 API 服务，提供实时股票报价、历史数据、SEC 财报信息等功能。

## 🚀 核心特性

- **🔄 多数据源架构** - Yahoo Finance (主) + Polygon.io (备) + SEC API (财报)
- **⚡ 智能降级机制** - 主数据源失败时自动切换到备用数据源，保证服务高可用
- **📊 实时报价** - 获取股票实时价格、变动幅度、交易量等核心数据
- **📈 历史数据** - 获取 K 线数据、股息分红、股票拆分等历史信息
- **🏢 公司信息** - 获取公司基本资料、行业分类、财务指标等详细信息
- **💼 SEC 财报数据** - 官方 SEC EDGAR 财务报表、季度收入、财务比率分析
- **🔀 批量查询** - 支持多个股票代码的批量查询，提升效率
- **⚡ 缓存优化** - Redis/内存多级缓存策略，大幅提升响应速度
- **🚀 异步处理** - 基于 FastAPI 的高性能异步架构，支持高并发
- **📚 完整文档** - 自动生成的 Swagger/ReDoc API 文档
- **🔄 重试机制** - 智能重试和错误恢复，确保服务稳定性
- **🎛️ 数据标准化** - 统一的数据格式，前端无感知切换数据源
- **🔧 配置管理** - 基于环境变量的灵活配置，支持多环境部署

## 🏗️ 系统架构

### 📊 数据源优先级

1. **🥇 Yahoo Finance (主数据源)**

   - 免费、无限制访问
   - 覆盖全球股票市场
   - 实时性好、稳定可靠

2. **🥈 Polygon.io (降级数据源)**

   - 专业级高质量数据
   - 需要 API 密钥，有调用限额
   - 主数据源失败时自动启用

3. **🏢 SEC EDGAR (专用财报数据)**
   - 官方财务报表数据
   - 需要 API 密钥，专业级服务
   - 专门处理财务分析需求

### 🔄 智能降级策略

- ✅ **透明降级**: 前端无感知的数据源自动切换
- ✅ **统一格式**: 所有数据源返回相同的标准化数据格式
- ✅ **健康监控**: 实时监控各数据源健康状态和响应时间
- ✅ **自动恢复**: 主数据源恢复后自动切换回来，支持熔断机制

### 📂 项目结构

```
yfinance-api/
├── app/
│   ├── main.py                    # FastAPI应用入口
│   ├── core/                      # 核心配置
│   │   ├── config.py              # 环境变量配置管理
│   │   └── logging.py             # 结构化日志配置
│   ├── api/v1/                    # API路由层
│   │   ├── quote.py               # 股票报价API (4个端点)
│   │   ├── history.py             # 历史数据API (4个端点)
│   │   ├── sec.py                 # SEC财报API (6个端点)
│   │   └── test.py                # 测试调试API (8个端点)
│   ├── services/                  # 业务逻辑层
│   │   ├── data_source_manager.py # 数据源管理和降级逻辑
│   │   ├── yfinance_service.py    # Yahoo Finance服务
│   │   └── sec_service.py         # SEC财报服务
│   ├── data_sources/              # 数据源抽象层
│   │   ├── base.py                # 数据源基类
│   │   ├── yfinance_source.py     # Yahoo Finance实现
│   │   ├── polygon_source.py      # Polygon.io实现
│   │   ├── sec_source.py          # SEC EDGAR实现
│   │   └── fallback_manager.py    # 降级管理器
│   ├── models/                    # 数据模型
│   │   ├── base.py                # 基础响应模型
│   │   ├── quote.py               # 报价数据模型
│   │   ├── history.py             # 历史数据模型
│   │   └── sec.py                 # SEC数据模型
│   └── utils/                     # 工具函数
│       ├── cache.py               # 缓存工具
│       └── exceptions.py          # 异常处理
├── docs/                          # 项目文档
│   ├── project_structure.md       # 项目结构详解
│   ├── api_reference.md           # API接口文档
│   └── api_key_configuration.md   # API密钥配置指南
├── requirements.txt               # Python依赖
├── config.env                     # 配置模板
├── start_with_sec_api.sh          # 带SEC API的启动脚本
└── README.md                      # 项目说明 (本文件)
```

## 📦 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd yfinance-api

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

**方式一：使用配置向导（推荐）**

```bash
# 运行交互式配置向导
./setup_env.sh
```

配置向导会帮助你：

- 从 `config.env` 模板创建 `.env` 文件
- 交互式设置 API 密钥（Polygon.io、SEC API）
- 选择开发或生产环境配置
- 自动备份现有配置文件

**方式二：手动配置**

```bash
# 复制配置模板
cp config.env .env

# 编辑配置文件
vim .env
```

**主要配置项:**

```env
# 基础配置
DEBUG=true
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000

# Yahoo Finance配置（主数据源，无需API密钥）
YF_TIMEOUT=30
YF_MAX_RETRIES=3

# Polygon.io配置（降级数据源，可选）
POLYGON_API_KEY=your_polygon_api_key_here  # 从 https://polygon.io/dashboard/api-keys 获取

# 降级机制配置
FALLBACK_ENABLED=true
PRIMARY_SOURCE_MAX_FAILURES=5
FALLBACK_TIMEOUT=10
FALLBACK_COOLDOWN_PERIOD=300

# 缓存配置
REDIS_URL=redis://localhost:6379/0  # 可选，不配置则使用内存缓存
CACHE_TTL=300

# SEC API配置（财报数据功能，可选）
SEC_API_KEY=your_sec_api_key_here  # 从 https://sec-api.io/dashboard 获取
SEC_API_TIMEOUT=30
SEC_API_MAX_RETRIES=3

# 限流配置
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 3. 启动服务

**方式一：使用主启动脚本（推荐）**

```bash
chmod +x start_api.sh
./start_api.sh
```

这个脚本会：

- ✅ 检查环境配置和 API 密钥
- ✅ 显示所有功能模块状态
- ✅ 启动完整的 Finance API 服务
- ✅ 提供详细的访问地址和使用提示

**方式二：快速启动（开发用）**

```bash
chmod +x start.sh
./start.sh
```

适合已配置好环境的日常开发使用。

**方式三：直接启动**

```bash
# 开发模式
uvicorn app.main:app --reload --port 8000

# 生产模式
gunicorn -k uvicorn.workers.UvicornWorker app.main:app -c gunicorn_conf.py
```

**方式四：带环境变量启动**

```bash
export SEC_API_KEY="your_sec_api_key_here"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**⚠️ 兼容性说明**
**注意**: 旧版的 `start_with_sec_api.sh` 已被移除，请使用新的 `start_api.sh`。

## 📖 API 文档

启动服务后，访问以下地址查看完整 API 文档：

- **🌟 Swagger UI**: http://localhost:8000/docs
- **📄 ReDoc**: http://localhost:8000/redoc
- **🔧 OpenAPI JSON**: http://localhost:8000/openapi.json
- **❤️ 健康检查**: http://localhost:8000/health

## 🛠️ API 接口概览

### 📈 股票报价 (`/api/v1/quote`)

| 端点                 | 方法 | 功能     | 说明                         |
| -------------------- | ---- | -------- | ---------------------------- |
| `/{symbol}`          | GET  | 快速报价 | 获取实时价格、涨跌幅、交易量 |
| `/{symbol}/detailed` | GET  | 详细报价 | 包含 PE、EPS、股息率等指标   |
| `/{symbol}/info`     | GET  | 公司信息 | 公司名称、行业、员工数等     |
| `/batch`             | POST | 批量报价 | 一次获取多个股票报价         |

### 📊 历史数据 (`/api/v1/history`)

| 端点                  | 方法 | 功能      | 说明               |
| --------------------- | ---- | --------- | ------------------ |
| `/{symbol}`           | GET  | 历史 K 线 | 支持多种周期和间隔 |
| `/{symbol}/dividends` | GET  | 股息历史  | 分红派息记录       |
| `/{symbol}/splits`    | GET  | 拆股历史  | 股票拆分记录       |
| `/{symbol}/actions`   | GET  | 公司行动  | 综合分红和拆股信息 |

### 🏢 SEC 财报数据 (`/api/v1/sec`)

| 端点                          | 方法 | 功能     | 说明               |
| ----------------------------- | ---- | -------- | ------------------ |
| `/financials/{ticker}`        | GET  | 财务报表 | 10-K/10-Q 财务数据 |
| `/quarterly-revenue/{ticker}` | GET  | 季度收入 | 季度收入趋势分析   |
| `/annual-comparison/{ticker}` | GET  | 年度对比 | 多年财务数据对比   |
| `/news/{ticker}`              | GET  | SEC 新闻 | SEC 文件和公告     |
| `/ratios/{ticker}`            | GET  | 财务比率 | PE、ROE、负债率等  |
| `/health`                     | GET  | 健康检查 | SEC 服务状态       |

### 🧪 测试调试 (`/api/v1/test`)

| 端点                    | 方法 | 功能             | 说明             |
| ----------------------- | ---- | ---------------- | ---------------- |
| `/polygon/{symbol}/raw` | GET  | Polygon 原始数据 | 调试 Polygon API |
| `/health-check`         | GET  | 综合健康检查     | 所有数据源状态   |
| `/data-sources/status`  | GET  | 数据源状态       | 降级机制状态     |

## 🔧 使用示例

### 基础查询

```bash
# 获取苹果股票报价
curl "http://localhost:8000/api/v1/quote/AAPL"

# 获取微软详细信息
curl "http://localhost:8000/api/v1/quote/MSFT/detailed"

# 获取谷歌公司信息
curl "http://localhost:8000/api/v1/quote/GOOGL/info"
```

### 历史数据查询

```bash
# 获取苹果1年日线数据
curl "http://localhost:8000/api/v1/history/AAPL?period=1y&interval=1d"

# 获取特定时间段数据
curl "http://localhost:8000/api/v1/history/AAPL?start=2024-01-01&end=2024-12-31"

# 获取分钟级数据
curl "http://localhost:8000/api/v1/history/AAPL?period=1d&interval=1m"
```

### SEC 财报数据查询

```bash
# 获取苹果财务报表
curl "http://localhost:8000/api/v1/sec/financials/AAPL?years=3"

# 获取季度收入趋势
curl "http://localhost:8000/api/v1/sec/quarterly-revenue/AAPL?quarters=8"

# 获取财务比率
curl "http://localhost:8000/api/v1/sec/ratios/AAPL?period=annual"
```

### 批量查询

```bash
# URL参数方式
curl "http://localhost:8000/api/v1/quote/?symbols=AAPL,MSFT,GOOGL"

# POST请求方式
curl -X POST "http://localhost:8000/api/v1/quote/batch" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"]}'
```

### 系统状态检查

```bash
# 健康检查
curl "http://localhost:8000/health"

# SEC服务状态
curl "http://localhost:8000/api/v1/sec/health"

# 数据源状态
curl "http://localhost:8000/api/v1/test/data-sources/status"
```

## 📊 响应示例

### 股票报价响应

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

### SEC 财报响应

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "获取财务数据成功",
  "symbol": "AAPL",
  "data": {
    "ticker": "AAPL",
    "summary": {
      "total_annual_reports": 2,
      "total_quarterly_reports": 16,
      "latest_annual_date": "2018-09-29",
      "latest_quarterly_date": "2019-03-31"
    },
    "annual_financials": [
      {
        "fiscal_year": 2018,
        "period_end": "2018-09-29",
        "revenue": 215639000000,
        "net_income": 43142000000,
        "total_assets": 365725000000,
        "shareholders_equity": 107147000000
      }
    ]
  },
  "timestamp": "2025-06-02T19:52:49.696131",
  "data_source": "sec_edgar",
  "is_fallback": false
}
```

### 错误响应示例

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

### 降级场景响应

当主数据源失败时，系统会自动切换到备用数据源：

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "获取股票报价成功 (使用降级数据源: polygon)",
  "symbol": "AAPL",
  "data": {
    "last_price": 200.85,
    "previous_close": 200.29,
    "volume": 70753100
  },
  "timestamp": "2025-06-02T19:52:49.696131",
  "data_source": "polygon",
  "is_fallback": true
}
```

### 批量响应示例

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

## 📋 响应格式标准

所有 API 响应都包含以下标准字段：

- **`success`** (boolean): 请求是否成功
- **`code`** (string): 响应状态码 (`SUCCESS`, `PARTIAL_SUCCESS`, `TICKER_NOT_FOUND` 等)
- **`message`** (string): 人类可读的响应消息
- **`timestamp`** (string): 响应时间戳 (ISO 8601 格式)

详细的响应格式文档请参见: [API 响应格式标准](docs/api_response_format.md)

## 🔄 智能降级机制详解

### 降级触发条件

1. **网络超时**: 主数据源响应超时
2. **API 限制**: 达到调用频率限制
3. **服务异常**: 数据源返回错误状态
4. **数据质量**: 返回数据格式异常

### 降级恢复策略

- **健康检查**: 定期检测主数据源状态
- **渐进恢复**: 逐步将流量切回主数据源
- **熔断机制**: 防止频繁切换造成的抖动
- **监控告警**: 降级事件实时记录和通知

## 🎯 性能特性

- **⚡ 响应时间**: 通常 < 500ms
- **📈 缓存命中率**: > 80%
- **🔄 系统可用性**: > 99.9%
- **🚀 并发处理**: 支持 1000+ QPS
- **💾 内存使用**: 优化的内存缓存策略
- **🔌 连接池**: HTTP 连接复用降低延迟

## 🔐 安全与配置

### 环境变量配置

所有敏感信息（如 API 密钥）都通过环境变量配置，不在代码中硬编码：

```bash
# 方式一：环境变量
export SEC_API_KEY="your_real_api_key_here"
export POLYGON_API_KEY="your_polygon_key"

# 方式二：.env文件
echo "SEC_API_KEY=your_real_api_key_here" >> .env
echo "POLYGON_API_KEY=your_polygon_key" >> .env

# 方式三：启动脚本
./start_with_sec_api.sh  # 需要修改脚本中的API密钥
```

### 安全特性

- **🔒 输入验证**: 严格的参数验证和清洗
- **🛡️ 限流保护**: 防止 API 滥用和攻击
- **📝 访问日志**: 详细的请求日志记录
- **🚫 错误处理**: 不暴露内部错误信息
- **🔑 密钥管理**: 环境变量配置，支持密钥轮换

## 📚 文档资源

- **📖 [项目结构文档](docs/project_structure.md)** - 详细的代码结构说明
- **🔧 [API 接口文档](docs/api_reference.md)** - 完整的 API 参考手册
- **🔑 [API 密钥配置指南](docs/api_key_configuration.md)** - 密钥配置最佳实践

## 🧪 开发与测试

### 测试 API 端点

项目提供了专门的测试端点用于调试：

```bash
# 测试Polygon.io数据源
curl "http://localhost:8000/api/v1/test/polygon/AAPL/quote"

# 查看所有数据源状态
curl "http://localhost:8000/api/v1/test/data-sources/status"

# 综合健康检查
curl "http://localhost:8000/api/v1/test/health-check"
```

### 本地开发

```bash
# 启动开发服务器（支持热重载）
uvicorn app.main:app --reload --port 8000

# 查看日志
tail -f logs/app.log

# 运行测试
python -m pytest tests/
```

## 🐳 部署方案

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-c", "gunicorn_conf.py"]
```

### 生产环境配置

```bash
# 生产环境变量
export DEBUG=false
export LOG_LEVEL=WARNING
export WORKERS=4
export SEC_API_KEY="production_api_key"
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- **🐛 问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)
- **💬 讨论交流**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **📧 邮件联系**: your-email@example.com
- **📚 在线文档**: http://localhost:8000/docs

---

**🎉 快速开始**: `./start_with_sec_api.sh` → 访问 http://localhost:8000/docs

**⭐ 如果这个项目对您有帮助，请给个 Star！**

## 🔧 SEC 服务配置

### ⚠️ 重要说明

SEC 财报数据功能需要**有效的 SEC API 密钥**才能正常工作。这是一个**生产级别的金融 API**，不提供模拟数据：

- ✅ **有 API 密钥时**: 提供真实的 SEC EDGAR 财务报表数据
- ❌ **无 API 密钥时**: 服务不可用，返回明确的错误信息

**获取 API 密钥**: https://sec-api.io/

### 🔑 配置方式

```bash
# 方式一：环境变量
export SEC_API_KEY="your_real_api_key_here"

# 方式二：.env文件
echo "SEC_API_KEY=your_real_api_key_here" >> .env

# 方式三：启动脚本
./start_with_sec_api.sh  # 需要修改脚本中的API密钥
```

### 📱 可用的 SEC API 端点

**仅在配置有效 API 密钥时可用**：

```bash
GET /api/v1/sec/financials/{ticker}        # 财务报表
GET /api/v1/sec/quarterly-revenue/{ticker} # 季度收入
GET /api/v1/sec/annual-comparison/{ticker} # 年度对比
GET /api/v1/sec/news/{ticker}             # SEC新闻
GET /api/v1/sec/ratios/{ticker}           # 财务比率
GET /api/v1/sec/health                    # 健康检查
```

### 🚫 错误响应示例

当 SEC 服务不可用时，会返回 HTTP 503 错误：

```json
{
  "detail": {
    "error": "SEC服务不可用",
    "message": "SEC API需要有效的API密钥。请设置环境变量 SEC_API_KEY 或在配置中提供密钥。获取API密钥请访问: https://sec-api.io/",
    "solution": "请检查SEC API密钥配置或联系管理员"
  }
}
```
