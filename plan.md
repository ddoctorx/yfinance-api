# Finance-API 项目说明书 (基于 **多数据源架构**)

> 版本: 0.2.0
> 更新日期: 2025-06-02

---

## 📑 目录

- [Finance-API 项目说明书 (基于 **多数据源架构**)](#finance-api-项目说明书-基于-多数据源架构)
  - [📑 目录](#-目录)
  - [🏗️ 多数据源架构概览](#️-多数据源架构概览)
    - [数据源优先级](#数据源优先级)
    - [架构特点](#架构特点)
  - [项目目录结构](#项目目录结构)
    - [目录说明](#目录说明)
  - [API 设计详解](#api-设计详解)
    - [全局约定](#全局约定)
    - [端点总览](#端点总览)
      - [错误码定义](#错误码定义)
  - [数据源对比一览](#数据源对比一览)
  - [运行与部署](#运行与部署)
  - [附录·依赖与脚本](#附录依赖与脚本)
    - [测试脚本](#测试脚本)
    - [运行命令速查](#运行命令速查)

---

## 🏗️ 多数据源架构概览

本项目采用**多数据源架构**，通过智能降级机制确保高可用性：

### 数据源优先级

1. **🥇 Yahoo Finance (主数据源)**

   - 免费、无限制访问
   - 覆盖全面的股票数据
   - 稳定可靠的数据质量

2. **🥈 Polygon.io (降级数据源)**
   - 专业级高质量数据
   - 备用增强数据源
   - 需要 API 密钥，但免费账户亦可用于降级

### 架构特点

- ✅ **透明降级**: 前端无感知的数据源切换
- ✅ **统一格式**: 所有数据源返回相同的数据格式
- ✅ **智能监控**: 实时监控数据源健康状态
- ✅ **自动恢复**: 主数据源恢复时自动切换回来
- ✅ **数据标准化**: 确保不同数据源的数据一致性

---

## 项目目录结构

```text
finance-api/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │   ├─ config.py
│  │   └─ logging.py
│  ├─ api/
│  │   └─ v1/
│  │       ├─ __init__.py
│  │       ├─ quote.py
│  │       ├─ history.py
│  │       ├─ financials.py
│  │       ├─ options.py
│  │       ├─ earnings.py
│  │       ├─ holders.py
│  │       ├─ sustainability.py
│  │       ├─ news.py
│  │       └─ test.py              # 🆕 测试&监控端点
│  ├─ data_sources/                 # 🆕 多数据源层
│  │   ├─ __init__.py
│  │   ├─ base.py                  # 数据源基类
│  │   ├─ yfinance_source.py       # Yahoo Finance数据源
│  │   ├─ polygon_source.py        # Polygon.io数据源
│  │   └─ fallback_manager.py      # 降级管理器
│  ├─ adapters/                    # 🆕 数据适配器层
│  │   ├─ __init__.py
│  │   ├─ polygon_adapter.py       # Polygon数据适配器
│  │   └─ data_normalizer.py       # 数据标准化器
│  ├─ services/
│  │   └─ data_source_manager.py   # 🔄 数据源管理服务 (重构)
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ base.py
│  │   ├─ quote.py
│  │   ├─ history.py
│  │   ├─ financials.py
│  │   ├─ options.py
│  │   └─ ...
│  ├─ utils/
│  │   ├─ cache.py
│  │   └─ exceptions.py
│  └─ tests/
│      ├─ __init__.py
│      └─ test_quote.py
├─ docs/                          # 📚 文档目录
│  └─ polygon_integration_plan.md
├─ test_polygon_client.py         # 🆕 Polygon客户端测试
├─ test_api_fallback.py          # 🆕 降级机制测试
├─ Dockerfile
├─ requirements.txt
├─ README.md
└─ .env
```

### 目录说明

| 目录/文件          | 作用            | 关键点                                          |
| ------------------ | --------------- | ----------------------------------------------- |
| **app/main.py**    | 应用入口        | 创建 `FastAPI()`，引入路由、事件、异常处理      |
| **core/config.py** | 全局配置        | 基于 `pydantic.BaseSettings`；读取 `.env`       |
| **api/v1/**        | 路由层          | 每个文件对应一个业务域，统一 `prefix="/api/v1"` |
| **data_sources/**  | 🆕 数据源抽象层 | 各数据源的统一接口实现，支持降级机制            |
| **adapters/**      | 🆕 数据适配器层 | 不同数据源格式转换，确保输出一致性              |
| **services/**      | 业务逻辑封装    | 数据源管理和调度，降级策略实现                  |
| **models/**        | Pydantic 模型   | 定义请求/响应结构，确保数据契约                 |
| **utils/cache.py** | 缓存装饰器      | 选型 `aiocache` or Redis；TTL 根据业务配置      |
| **tests/**         | 单元 / 集成测试 | `pytest-asyncio` + `httpx.AsyncClient`          |
| **docs/**          | 📚 项目文档     | 架构设计、集成计划等文档                        |

---

## API 设计详解

### 全局约定

- 基础路径：`/api/v1`
- 统一返回格式：

```json
{
  "symbol": "AAPL",
  "data": { ... },
  "timestamp": "2025-06-02T14:00:05+08:00"
}
```

- 错误响应：

```json
{
  "detail": "Ticker not found",
  "code": "TICKER_NOT_FOUND"
}
```

### 端点总览

| Path                        | Method | 功能         | 主要参数                             | 对应 yfinance                                                            |
| --------------------------- | ------ | ------------ | ------------------------------------ | ------------------------------------------------------------------------ |
| `/health`                   | GET    | 健康检查     | -                                    | -                                                                        |
| `/quote/{symbol}`           | GET    | 实时快照     | -                                    | `Ticker.fast_info`, 部分字段来自 `Ticker.info`                           |
| `/quotes`                   | GET    | 批量快照     | `symbols` (CSV)                      | 同上，内部并发聚合                                                       |
| `/history/{symbol}`         | GET    | 历史 K 线    | `start`, `end`, `interval`, `adjust` | `Ticker.history()`                                                       |
| `/financials/{symbol}`      | GET    | 财报         | `statement`, `freq`                  | `Ticker.income_stmt`, `balance_sheet`, `cashflow`, `income_stmt_..._ttm` |
| `/earnings/{symbol}`        | GET    | EPS & 财报日 | -                                    | `earnings`, `earnings_dates`                                             |
| `/dividends/{symbol}`       | GET    | 股息流水     | -                                    | `Ticker.dividends`                                                       |
| `/splits/{symbol}`          | GET    | 拆分历史     | -                                    | `Ticker.splits`                                                          |
| `/options/{symbol}`         | GET    | 到期日列表   | -                                    | `Ticker.options`                                                         |
| `/options/{symbol}/{date}`  | GET    | 期权链       | `date` Path                          | `Ticker.option_chain(date)`                                              |
| `/recommendations/{symbol}` | GET    | 分析师评级   | -                                    | `Ticker.recommendations`, `recommendations_summary`                      |
| `/price_targets/{symbol}`   | GET    | 目标价       | -                                    | `Ticker.analyst_price_targets`                                           |
| `/sustainability/{symbol}`  | GET    | ESG 评分     | -                                    | `Ticker.sustainability`                                                  |
| `/holders/{symbol}`         | GET    | 股东结构     | `type`=major/institutional/insider   | `major_holders`, `institutional_holders`, `insider_transactions`         |
| `/news/{symbol}`            | GET    | 公司新闻     | `limit`                              | `Ticker.news`                                                            |

> **示例：`/history/{symbol}`** > _Query_：`/api/v1/history/AAPL?start=2024-01-01&end=2025-06-01&interval=1d` > _Response_（节选）：
>
> ```json
> {
>   "symbol": "AAPL",
>   "data": [
>     {"Date": "2024-01-02", "Open": 184.01, "High": 186.77, "Low": 183.93, "Close": 186.15, "Volume": 68987200},
>     ...
>   ],
>   "timestamp": "2025-06-02T14:03:34+08:00"
> }
> ```

#### 错误码定义

| HTTP | code                | 场景           |
| ---- | ------------------- | -------------- |
| 400  | INVALID_PARAM       | 参数校验失败   |
| 404  | TICKER_NOT_FOUND    | 未找到证券     |
| 502  | YAHOO_API_ERROR     | Yahoo 接口异常 |
| 503  | SERVICE_UNAVAILABLE | 限流或系统维护 |

---

## 数据源对比一览

| 数据源            | 优点                                 | 缺点                                    |
| ----------------- | ------------------------------------ | --------------------------------------- |
| **Yahoo Finance** | 免费、无限制访问，覆盖全面，稳定可靠 | 数据质量可能受限，部分数据需要 API 密钥 |
| **Polygon.io**    | 专业级高质量数据，需要 API 密钥      | 需要 API 密钥，免费账户亦可用于降级     |

---

## 运行与部署

1. **依赖安装**
   ```bash
   pip install -r requirements.txt  # yfinance[ta] fastapi uvicorn[standard] pydantic[dotenv] aiocache
   ```
2. **开发启动**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
3. **生产部署**
   - Gunicorn + Uvicorn worker：`gunicorn -k uvicorn.workers.UvicornWorker app.main:app -c gunicorn_conf.py`
   - Docker：
     ```dockerfile
     FROM python:3.12-slim
     WORKDIR /code
     COPY requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     COPY . .
     CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
     ```
4. **监控与告警**
   - 指标：请求延迟、错误率、Yahoo API 命中/失败
   - Sentry + Prometheus + Grafana

---

## 附录·依赖与脚本

| 名称                   | 版本约束   | 用途                   |
| ---------------------- | ---------- | ---------------------- |
| **yfinance**           | `>=0.2.61` | Yahoo Finance 金融数据 |
| **polygon-api-client** | `>=1.14.5` | Polygon.io 金融数据    |
| **FastAPI**            | `>=0.111`  | Web 框架               |
| **uvicorn[standard]**  | `>=0.29`   | ASGI 服务器            |
| **pandas**             | `>=2.2`    | 数据处理               |
| **aiocache[redis]**    | `>=0.12`   | 缓存后端               |
| **python-dotenv**      | `>=1.0`    | 读取 .env              |
| **pytest-asyncio**     | `>=0.23`   | 异步测试               |
| **httpx**              | `>=0.27`   | HTTP 客户端            |
| **structlog**          | `>=24.1`   | 结构化日志             |

### 测试脚本

| 脚本名称                 | 用途                   |
| ------------------------ | ---------------------- |
| `test_polygon_client.py` | 测试 Polygon.io 客户端 |
| `test_api_fallback.py`   | 测试多数据源降级机制   |
| `app/tests/`             | 单元测试和集成测试     |

---

> 数据来源基于公开的 Yahoo Finance 接口和 Polygon.io API；请遵守相应的使用条款。
> 文档编写参考了官方 README 与社区博文。

### 运行命令速查

```bash
# 安装依赖
./venv/bin/pip install -r requirements.txt

# 启动开发服务器
./venv/bin/python -m uvicorn app.main:app --reload --port 8000

# 测试降级机制
python test_api_fallback.py

# 测试 Polygon 客户端
python test_polygon_client.py

# 停止服务
pkill -f uvicorn && sleep 2
```
