# Finance API

基于 **yfinance + FastAPI** 的金融数据 API 服务，提供实时股票报价、历史数据、公司信息等功能。

## 🚀 特性

- **实时报价** - 获取股票实时价格和基本信息
- **历史数据** - 获取 K 线数据、股息、拆股等历史信息
- **公司信息** - 获取公司基本资料和财务指标
- **批量查询** - 支持多个股票代码的批量查询
- **缓存优化** - 多级缓存策略提升响应速度
- **异步处理** - 基于 FastAPI 的高性能异步架构
- **完整文档** - 自动生成的 API 文档
- **重试机制** - 智能重试确保服务稳定性

## 📦 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd yfinance-api
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp config.env .env
# 根据需要修改 .env 文件中的配置
```

## 🏃 运行

### 开发模式

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 生产模式

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app -c gunicorn_conf.py
```

## 📖 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 API 使用示例

### 健康检查

```bash
curl http://localhost:8000/health
```

### 获取单个股票报价

```bash
curl http://localhost:8000/api/v1/quote/AAPL
```

### 批量获取股票报价

```bash
curl "http://localhost:8000/api/v1/quote/?symbols=AAPL,MSFT,GOOGL"
```

### 获取历史数据

```bash
curl "http://localhost:8000/api/v1/history/AAPL?period=1y&interval=1d"
```

### 获取公司信息

```bash
curl http://localhost:8000/api/v1/quote/AAPL/info
```

## 📊 响应示例

### 股票报价响应

```json
{
  "symbol": "AAPL",
  "data": {
    "last_price": 200.85,
    "previous_close": 199.0,
    "open_price": 199.37,
    "day_high": 201.96,
    "day_low": 196.78,
    "volume": 70753100,
    "market_cap": 2999855482597,
    "currency": "USD"
  },
  "timestamp": "2025-06-02T15:21:05.649716"
}
```

### 批量查询响应

```json
{
  "data": {
    "AAPL": {
      /* 报价数据 */
    },
    "MSFT": {
      /* 报价数据 */
    },
    "GOOGL": {
      /* 报价数据 */
    }
  },
  "errors": {},
  "timestamp": "2025-06-02T15:21:14.751226"
}
```

## ⚙️ 配置说明

主要配置项（在 `.env` 文件中）：

```env
# 应用配置
DEBUG=true
LOG_LEVEL=INFO

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 缓存配置
REDIS_URL=redis://localhost:6379/0  # 可选，不配置则使用内存缓存
CACHE_TTL=300

# yfinance配置
YF_TIMEOUT=30
YF_MAX_RETRIES=3

# 限流配置
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## 🏗️ 项目结构

```
yfinance-api/
├── app/
│   ├── main.py              # 应用入口
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   └── logging.py       # 日志配置
│   ├── api/v1/              # API路由
│   │   ├── quote.py         # 报价API
│   │   └── history.py       # 历史数据API
│   ├── services/            # 业务逻辑
│   │   └── yfinance_service.py
│   ├── models/              # 数据模型
│   │   ├── base.py          # 基础模型
│   │   ├── quote.py         # 报价模型
│   │   └── history.py       # 历史数据模型
│   ├── utils/               # 工具函数
│   │   ├── cache.py         # 缓存工具
│   │   └── exceptions.py    # 异常处理
│   └── tests/               # 测试文件
├── requirements.txt         # 依赖列表
├── config.env              # 配置模板
└── README.md               # 项目说明
```

## 🔄 缓存策略

- **实时报价**: 缓存 1 分钟
- **历史数据**: 缓存 1 小时
- **公司信息**: 缓存 1 天
- **新闻数据**: 缓存 30 分钟

## 🚦 限流规则

- 每分钟最多 100 次请求
- 批量查询最多支持 10 个股票代码

## 📝 开发说明

### 添加新的 API 端点

1. 在 `app/models/` 中定义数据模型
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/api/v1/` 中创建路由
4. 在 `app/main.py` 中注册路由

### 运行测试

```bash
pytest app/tests/
```

## 📄 许可证

本项目基于 MIT 许可证开源。

## ⚠️ 免责声明

本项目仅供学习和研究使用。所有数据来源于 Yahoo Finance，请遵守相关使用条款。投资有风险，请谨慎决策。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 0.1.0  
**更新日期**: 2025-06-02

## 🔄 重试机制

API 具备智能重试功能，当 yfinance 调用失败时会自动重试：

### 重试策略

- **重试次数**：默认 5 次（可配置 `YF_MAX_RETRIES`）
- **退避策略**：指数退避（1s, 2s, 4s, 8s, 16s）
- **总等待时间**：最多 31 秒
- **异常分类**：
  - ✅ **网络/临时错误**：会进行重试
  - ❌ **股票代码不存在**：不会重试，直接返回 404
  - ❌ **参数错误**：不会重试，直接返回 400

### 配置环境变量

```bash
# 设置最大重试次数（推荐5次）
export YF_MAX_RETRIES=5

# 设置yfinance会话超时
export YF_SESSION_TIMEOUT=30
```

### 重试时间表

| 重试次数    | 等待时间 | 累计时间 |
| ----------- | -------- | -------- |
| 第 1 次重试 | 1 秒     | 1 秒     |
| 第 2 次重试 | 2 秒     | 3 秒     |
| 第 3 次重试 | 4 秒     | 7 秒     |
| 第 4 次重试 | 8 秒     | 15 秒    |
| 第 5 次重试 | 16 秒    | 31 秒    |

### 重试日志示例

```json
{
  "event": "yfinance调用失败，8秒后重试",
  "attempt": 4,
  "max_retries": 5,
  "error": "Connection timeout"
}
```
