# SEC 高级功能测试指南

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装缺失的依赖包
pip install requests-cache sec-api aiohttp

# 如果遇到任何依赖问题，可以运行：
pip install -r requirements.txt
```

### 2. 配置 SEC API 密钥

您需要一个 SEC-API 密钥来使用高级功能。可以从 [sec-api.io](https://sec-api.io) 获取免费或付费密钥。

**方法 1：环境变量**

```bash
export SEC_API_KEY="your_sec_api_key_here"
```

**方法 2：创建.env 文件**

```bash
# 在项目根目录创建.env文件
echo "SEC_API_KEY=your_sec_api_key_here" > .env
```

### 3. 启动 API 服务

```bash
# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者使用Python直接运行
python -m app.main
```

### 4. 验证服务运行

打开浏览器访问：

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- SEC 高级功能概览：http://localhost:8000/api/v1/sec-advanced/

## 🧪 测试方法

### 方法 1：自动化测试脚本 (推荐)

运行提供的完整测试脚本：

```bash
python test_sec_advanced.py
```

这个脚本会测试所有 12 个 SEC 高级功能端点，并提供详细的测试报告。

### 方法 2：手动 API 测试

#### 基础功能测试

**1. 健康检查**

```bash
curl http://localhost:8000/api/v1/sec-advanced/health
```

**2. API 概览**

```bash
curl http://localhost:8000/api/v1/sec-advanced/
```

#### 核心功能测试

**3. XBRL 公司数据 (苹果公司)**

```bash
curl "http://localhost:8000/api/v1/sec-advanced/xbrl/company/AAPL?form_type=10-K&fiscal_year=2023"
```

**4. 全文搜索**

```bash
curl "http://localhost:8000/api/v1/sec-advanced/search/full-text?query=artificial%20intelligence&form_types=10-K,10-Q&limit=5"
```

**5. 内幕交易数据**

```bash
curl "http://localhost:8000/api/v1/sec-advanced/insider-trading/AAPL?days_back=60"
```

**6. 机构持股数据**

```bash
curl "http://localhost:8000/api/v1/sec-advanced/institutional-holdings/MSFT?quarters=4"
```

**7. 最近 IPO 数据**

```bash
curl "http://localhost:8000/api/v1/sec-advanced/ipo/recent?days_back=90"
```

### 方法 3：使用 Swagger UI

1. 访问 http://localhost:8000/docs
2. 找到 "SEC 高级功能" 分组
3. 点击任意端点进行交互式测试
4. 填写参数并点击 "Try it out"

## 📊 功能清单

### ✅ 已实现的功能

| 功能          | 端点                               | 说明                     |
| ------------- | ---------------------------------- | ------------------------ |
| **XBRL 转换** | `/xbrl/company/{ticker}`           | 获取公司 XBRL 财务数据   |
| **全文搜索**  | `/search/full-text`                | SEC 文件全文搜索         |
| **公司搜索**  | `/search/company/{ticker}`         | 公司特定文件搜索         |
| **内幕交易**  | `/insider-trading/{ticker}`        | 内幕交易数据(Form 3/4/5) |
| **机构持股**  | `/institutional-holdings/{ticker}` | 机构持股数据(Form 13F)   |
| **IPO 数据**  | `/ipo/recent`, `/ipo/{ticker}`     | IPO 和股票发行数据       |
| **高管薪酬**  | `/executive-compensation/{ticker}` | 高管薪酬信息             |
| **公司治理**  | `/governance/{ticker}`             | 公司治理信息             |
| **执法行动**  | `/enforcement/recent`              | SEC 执法行动             |
| **实体映射**  | `/mapping/ticker-to-cik/{ticker}`  | 股票代码到 CIK 映射      |
| **健康检查**  | `/health`                          | 服务状态监控             |
| **API 概览**  | `/`                                | 功能概览和文档           |

## 🔧 故障排除

### 常见问题

**1. ModuleNotFoundError: No module named 'requests_cache'**

```bash
pip install requests-cache
```

**2. SEC API 密钥相关错误**

- 确认密钥正确设置
- 检查密钥是否有效（访问 sec-api.io 控制台）
- 确认密钥有足够的配额

**3. 服务启动失败**

- 检查端口 8000 是否被占用
- 确认所有依赖包都已安装
- 查看终端错误日志

**4. API 请求超时**

- SEC API 响应可能较慢，属于正常现象
- 可以减少查询的数据量（如时间范围、结果数量）

### 调试模式

启用调试日志：

```bash
export LOG_LEVEL=DEBUG
python -m app.main
```

## 📈 性能优化

### 缓存策略

系统已实现分层缓存：

- XBRL 数据：2 小时
- 搜索结果：30 分钟
- 内幕交易：1 小时
- 机构持股：6 小时
- IPO 数据：1 小时
- 薪酬数据：24 小时
- 治理数据：24 小时
- 执法数据：2 小时
- 映射数据：24 小时

### 限流建议

- 避免频繁调用相同的端点
- 使用合理的查询参数（如限制结果数量）
- 批量操作时添加适当的延迟

## 📝 示例响应

### XBRL 数据响应示例

```json
{
  "symbol": "AAPL",
  "data": {
    "ticker": "AAPL",
    "company_name": "Apple Inc",
    "form_type": "10-K",
    "fiscal_year": 2023,
    "xbrl_data": {
      "financial_concepts": {
        "Revenue": 394328000000,
        "NetIncome": 97394000000,
        "TotalAssets": 352755000000
      }
    }
  },
  "data_source": "sec_xbrl_api",
  "is_fallback": false
}
```

## 💡 使用建议

1. **首次测试**：先运行健康检查和 API 概览
2. **功能验证**：使用知名公司股票代码（如 AAPL、MSFT、GOOGL）
3. **错误处理**：注意检查响应中的 error 字段
4. **性能考虑**：使用合理的查询参数，避免过度查询
5. **监控用量**：关注 SEC API 的使用配额

## 🎯 下一步

测试完成后，您可以：

1. 集成到现有的金融分析工作流
2. 开发自定义的 SEC 数据分析应用
3. 构建监管合规监控系统
4. 创建投资决策支持工具

---

**需要帮助？**

- 查看 API 文档：http://localhost:8000/docs
- 检查服务状态：http://localhost:8000/health
- 查看日志输出了解详细错误信息
