# Finance-API 项目说明书 (基于 **yfinance + FastAPI**)

> 版本: 0.1.0
> 更新日期: 2025-06-02

---

## 📑 目录

- [Finance-API 项目说明书 (基于 **yfinance + FastAPI**)](#finance-api-项目说明书-基于-yfinance--fastapi)
  - [📑 目录](#-目录)
  - [项目目录结构](#项目目录结构)
    - [目录说明](#目录说明)
  - [API 设计详解](#api-设计详解)
    - [全局约定](#全局约定)
    - [端点总览](#端点总览)
      - [错误码定义](#错误码定义)
  - [yfinance 数据映射一览](#yfinance-数据映射一览)
  - [运行与部署](#运行与部署)
  - [附录·依赖与脚本](#附录依赖与脚本)

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
│  │       └─ news.py
│  ├─ services/
│  │   └─ yfinance_service.py
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
| **services/**      | 业务逻辑封装    | 对 `yfinance` 调用集中管理，便于 mock / 缓存    |
| **models/**        | Pydantic 模型   | 定义请求/响应结构，确保数据契约                 |
| **utils/cache.py** | 缓存装饰器      | 选型 `aiocache` or Redis；TTL 根据业务配置      |
| **tests/**         | 单元 / 集成测试 | `pytest-asyncio` + `httpx.AsyncClient`          |

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

## yfinance 数据映射一览

> **版本**：0.2.61 (2025‑05‑12)

| 分类          | `Ticker` 属性/方法                                        | 描述（返回类型）              | 典型字段                                            |
| ------------- | --------------------------------------------------------- | ----------------------------- | --------------------------------------------------- |
| **元信息**    | `info`                                                    | 详细公司与报价元数据 (`dict`) | `sector`, `marketCap`, `beta`, `trailingPE`         |
|               | `fast_info`                                               | 精简快照 (`dict`) **推荐**    | `lastPrice`, `dayHigh`, `volume`, `marketCap`       |
| **价格**      | `history(start, end, interval, auto_adjust)`              | 历史 OHLCV (`DataFrame`)      | `Open` … `Volume`, `Dividends`, `Stock Splits`      |
| **股息/拆股** | `dividends`                                               | 系列 (`Series`)               | 日期 → 现金分红                                     |
|               | `splits`                                                  | 系列                          | 日期 → 拆分比例                                     |
|               | `actions`                                                 | `DataFrame`                   | 同时包含股息与拆股                                  |
| **财报**      | `income_stmt`, `balance_sheet`, `cashflow`                | 年报 (`DataFrame`)            | 多列年份                                            |
|               | `income_stmt_quarterly`, `..._ttm`                        | 季度/滚动四季                 | 同上                                                |
| **盈利**      | `earnings`                                                | 历史 EPS (`DataFrame`)        | `Revenue`, `Earnings`                               |
|               | `earnings_dates`                                          | 下一/历史财报日 (`DataFrame`) | `EPS Estimate`, `Reported EPS`                      |
| **期权**      | `options`                                                 | → list[str]                   | 所有到期日                                          |
|               | `option_chain(date)`                                      | `namedtuple(calls, puts)`     | 行权价、IV、OI                                      |
| **分析师**    | `recommendations`                                         | 买卖评级 (`DataFrame`)        | `Firm`, `To Grade`, `From Grade`                    |
|               | `analyst_price_targets`                                   | 目标价 (`DataFrame`)          | `low`, `mean`, `high`                               |
|               | `recommendations_summary`                                 | 汇总 (`dict`)                 | `strongBuy`, `hold`, ...                            |
| **ESG**       | `sustainability`                                          | ESG 评分 (`DataFrame`)        | `py_score`, `governanceScore`                       |
| **持股**      | `major_holders`                                           | 前十大股东 (`DataFrame`)      | `% Out`, `Value`                                    |
|               | `institutional_holders`                                   | 机构持股 (`DataFrame`)        | `Shares`, `Date Reported`                           |
|               | `insider_transactions`                                    | 内部人交易 (`DataFrame`)      | `Transaction`, `Shares`                             |
| **新闻**      | `news`                                                    | 列表 (`list[dict]`)           | `title`, `publisher`, `link`, `providerPublishTime` |
| **日历**      | `calendar`                                                | 关键事件 (`DataFrame`)        | `Ex-Dividend Date`, `Earnings Date`                 |
| **技术指标**  | `ta.rsi(period)`, `ta.sma(...)` _(需安装 `yfinance[ta]`)_ | 聚合自 `pandas_ta`            | RSI、SMA、EMA 等                                    |
| **市场/搜索** | `yfinance.Market("US").summary()`                         | 指数 & 行业表现               | `gainers`, `losers`                                 |
| **多标的**    | `yfinance.download("AAPL MSFT", period="1y")`             | 一次性批量下载                | 列 MultiIndex                                       |

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

| 名称                  | 版本约束   | 用途        |
| --------------------- | ---------- | ----------- |
| **yfinance**          | `>=0.2.61` | 金融数据    |
| **FastAPI**           | `>=0.111`  | Web 框架    |
| **uvicorn[standard]** | `>=0.29`   | ASGI 服务器 |
| **pandas**            | `>=2.2`    | 数据处理    |
| **aiocache[redis]**   | `>=0.12`   | 缓存后端    |
| **python-dotenv**     | `>=1.0`    | 读取 .env   |
| **pytest-asyncio**    | `>=0.23`   | 异步测试    |

---

> 数据来源基于公开的 Yahoo Finance 接口；请遵守 Yahoo 的使用条款。
> 文档编写参考了官方 README 与社区博文。

> which pip && ./venv/bin/pip install -r requirements.txt
> ./venv/bin/pip install
> ./venv/bin/python -m uvicorn app.main:app --reload --port 8000
> pkill -f uvicorn && sleep 2
