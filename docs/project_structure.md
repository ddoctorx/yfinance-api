# Finance API 项目结构文档

## 📁 项目概览

Finance API 是一个基于 FastAPI 的金融数据聚合服务，集成了多个数据源，提供股票报价、历史数据和 SEC 财报信息。

### 🚀 核心特性

- **多数据源聚合**: Yahoo Finance (主) + Polygon.io (备) + SEC API (财报)
- **智能降级机制**: 主数据源失败时自动切换到备用数据源
- **统一 API 接口**: 标准化的 RESTful API，前端无感知切换
- **缓存优化**: Redis/内存缓存，提升响应速度
- **错误处理**: 完善的异常处理和日志记录
- **配置管理**: 环境变量配置，支持多环境部署

## 📂 目录结构

```
yfinance-api/
├── app/                          # 应用主目录
│   ├── main.py                   # FastAPI应用入口
│   ├── __init__.py
│   │
│   ├── core/                     # 核心配置模块
│   │   ├── config.py             # 应用配置管理
│   │   ├── logging.py            # 日志配置
│   │   └── __init__.py
│   │
│   ├── api/                      # API路由层
│   │   └── v1/                   # API v1版本
│   │       ├── __init__.py       # 路由注册
│   │       ├── quote.py          # 股票报价API (4个端点)
│   │       ├── history.py        # 历史数据API (4个端点)
│   │       ├── sec.py            # SEC财报API (6个端点)
│   │       └── test.py           # 测试调试API (8个端点)
│   │
│   ├── services/                 # 业务逻辑层
│   │   ├── data_source_manager.py # 数据源管理服务
│   │   ├── yfinance_service.py   # Yahoo Finance服务
│   │   ├── sec_service.py        # SEC财报服务
│   │   └── __init__.py
│   │
│   ├── data_sources/             # 数据源抽象层
│   │   ├── base.py               # 数据源基类
│   │   ├── yfinance_source.py    # Yahoo Finance数据源
│   │   ├── polygon_source.py     # Polygon.io数据源
│   │   ├── sec_source.py         # SEC数据源
│   │   ├── fallback_manager.py   # 降级管理器
│   │   └── __init__.py
│   │
│   ├── adapters/                 # 数据适配器层
│   │   ├── polygon_adapter.py    # Polygon数据适配器
│   │   ├── data_normalizer.py    # 数据标准化器
│   │   └── __init__.py
│   │
│   ├── models/                   # 数据模型层
│   │   ├── base.py               # 基础模型定义
│   │   ├── quote.py              # 报价数据模型
│   │   ├── history.py            # 历史数据模型
│   │   ├── sec.py                # SEC数据模型
│   │   └── __init__.py
│   │
│   ├── utils/                    # 工具函数层
│   │   ├── cache.py              # 缓存工具
│   │   ├── exceptions.py         # 异常处理
│   │   └── __init__.py
│   │
│   └── tests/                    # 测试文件
│       └── __init__.py
│
├── docs/                         # 项目文档
│   ├── api_key_configuration.md  # API密钥配置指南
│   ├── project_structure.md      # 项目结构文档 (本文件)
│   └── api_reference.md          # API接口文档
│
├── requirements.txt              # Python依赖
├── config.env                    # 配置模板
├── start_with_sec_api.sh         # 带SEC API的启动脚本
├── gunicorn_conf.py             # Gunicorn配置
└── README.md                    # 项目说明
```

## 🔧 模块详解

### 1. 核心配置 (`app/core/`)

**config.py**

- 使用 Pydantic Settings 管理配置
- 支持环境变量和 .env 文件
- 包含所有数据源的配置项

**logging.py**

- 结构化日志配置
- 支持 JSON 格式输出
- 不同级别的日志处理

### 2. API 路由层 (`app/api/v1/`)

**quote.py** - 股票报价 API (4 个端点)

- `GET /{symbol}` - 快速报价
- `GET /{symbol}/detailed` - 详细报价
- `GET /{symbol}/info` - 公司信息
- `POST /batch` - 批量报价

**history.py** - 历史数据 API (4 个端点)

- `GET /{symbol}` - 历史 K 线数据
- `GET /{symbol}/dividends` - 股息历史
- `GET /{symbol}/splits` - 拆股历史
- `GET /{symbol}/actions` - 公司行动

**sec.py** - SEC 财报 API (6 个端点)

- `GET /financials/{ticker}` - 财务报表
- `GET /quarterly-revenue/{ticker}` - 季度收入
- `GET /annual-comparison/{ticker}` - 年度对比
- `GET /news/{ticker}` - SEC 新闻
- `GET /ratios/{ticker}` - 财务比率
- `GET /health` - 健康检查

**test.py** - 测试调试 API (8 个端点)

- `GET /polygon/{symbol}/raw` - Polygon 原始数据
- `GET /polygon/{symbol}/quote` - Polygon 报价
- `GET /polygon/{symbol}/company` - Polygon 公司信息
- `GET /yfinance/{symbol}/quote` - Yahoo Finance 报价
- `GET /health-check` - 综合健康检查
- `GET /data-sources/status` - 数据源状态
- `POST /simulate-failure` - 模拟故障
- `POST /reset-fallback` - 重置降级

### 3. 业务逻辑层 (`app/services/`)

**data_source_manager.py**

- 统一的数据源管理入口
- 实现智能降级机制
- 负载均衡和错误处理

**yfinance_service.py**

- Yahoo Finance API 封装
- 数据获取和处理逻辑
- 缓存策略实现

**sec_service.py**

- SEC EDGAR API 集成
- 财报数据解析和处理
- XBRL 数据标准化

### 4. 数据源抽象层 (`app/data_sources/`)

**base.py**

- 定义数据源基类接口
- 标准化数据源方法签名
- 错误处理抽象

**yfinance_source.py**

- Yahoo Finance 数据源实现
- 继承 BaseDataSource
- 实现所有必需接口

**polygon_source.py**

- Polygon.io 数据源实现
- 官方 API 客户端集成
- 数据格式标准化

**sec_source.py**

- SEC EDGAR 数据源实现
- 支持实时 API 和模拟模式
- 财报数据专用处理

**fallback_manager.py**

- 降级策略管理
- 健康状态监控
- 自动故障恢复

### 5. 数据模型层 (`app/models/`)

**base.py**

- 基础响应模型
- 分页和批量请求模型
- 统一错误响应格式

**quote.py**

- 股票报价数据模型
- 快速报价和详细报价
- 公司信息模型

**history.py**

- 历史数据模型
- K 线数据结构
- 股息和拆股模型

**sec.py**

- SEC 财报数据模型
- 财务报表结构
- 财务比率模型

### 6. 数据适配器层 (`app/adapters/`)

**polygon_adapter.py**

- Polygon API 响应转换
- 数据格式标准化
- 字段映射和计算

**data_normalizer.py**

- 跨数据源数据标准化
- 统一字段命名
- 数据类型转换

### 7. 工具函数层 (`app/utils/`)

**cache.py**

- Redis 和内存缓存抽象
- 缓存策略实现
- TTL 管理

**exceptions.py**

- 自定义异常类
- 错误处理中间件
- HTTP 状态码映射

## 🔄 数据流架构

```
客户端请求
    ↓
FastAPI路由层 (api/v1/)
    ↓
业务服务层 (services/)
    ↓
数据源管理器 (DataSourceManager)
    ↓
[主数据源] → [降级数据源] → [缓存层]
    ↓
数据适配器 (adapters/)
    ↓
数据模型验证 (models/)
    ↓
标准化响应返回
```

## 📊 数据源优先级

1. **Yahoo Finance** (主数据源)

   - 免费、无限制
   - 覆盖全球市场
   - 实时性好

2. **Polygon.io** (降级数据源)

   - 专业级数据质量
   - 需要 API 密钥
   - 限额管理

3. **SEC EDGAR** (专用财报数据)
   - 官方财报数据
   - 需要 API 密钥
   - 专门处理财务信息

## 🛡️ 错误处理机制

- **数据源级别**: 单个数据源失败时自动降级
- **服务级别**: 服务异常时返回标准化错误
- **API 级别**: HTTP 状态码和详细错误信息
- **监控级别**: 结构化日志记录所有异常

## 📈 性能优化

- **缓存策略**: 不同数据类型采用不同 TTL
- **连接池**: 复用 HTTP 连接降低延迟
- **异步处理**: 全异步架构提升并发性能
- **批量请求**: 支持批量获取减少 API 调用

## 🔧 配置管理

- **环境变量**: 支持 12-Factor App 配置原则
- **配置验证**: Pydantic 自动验证配置项
- **多环境**: 开发/测试/生产环境分离
- **敏感信息**: API 密钥等敏感配置独立管理

## 📝 日志策略

- **结构化日志**: JSON 格式便于分析
- **分级记录**: DEBUG/INFO/WARNING/ERROR
- **请求追踪**: 每个请求分配唯一 ID
- **性能监控**: 响应时间和错误率统计

## 🧪 测试框架

- **单元测试**: 各模块独立测试
- **集成测试**: 数据源集成验证
- **性能测试**: 负载和压力测试
- **端到端测试**: 完整 API 流程验证
