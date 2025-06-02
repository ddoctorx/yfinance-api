"""
报价API测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "dependencies" in data


def test_root_endpoint():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_cache_info():
    """测试缓存信息端点"""
    response = client.get("/cache/info")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "ttl_seconds" in data


def test_get_quote():
    """测试获取单个股票报价"""
    response = client.get("/api/v1/quote/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "data" in data
    assert "timestamp" in data

    # 检查报价数据结构
    quote_data = data["data"]
    assert "last_price" in quote_data
    assert "currency" in quote_data


def test_get_quote_invalid_symbol():
    """测试无效股票代码"""
    response = client.get("/api/v1/quote/INVALID123")
    # 可能返回404或者空数据，取决于yfinance的行为
    assert response.status_code in [200, 404]


def test_batch_quotes():
    """测试批量获取报价"""
    response = client.get("/api/v1/quote/?symbols=AAPL,MSFT")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "errors" in data
    assert "timestamp" in data

    # 检查是否包含请求的股票
    assert "AAPL" in data["data"] or "AAPL" in data["errors"]
    assert "MSFT" in data["data"] or "MSFT" in data["errors"]


def test_batch_quotes_too_many():
    """测试批量查询超过限制"""
    symbols = ",".join([f"STOCK{i}" for i in range(15)])  # 超过10个限制
    response = client.get(f"/api/v1/quote/?symbols={symbols}")
    assert response.status_code == 400


def test_get_history():
    """测试获取历史数据"""
    response = client.get("/api/v1/history/AAPL?period=5d&interval=1d")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "data" in data
    assert "timestamp" in data

    # 检查历史数据结构
    history_data = data["data"]
    assert "data" in history_data
    assert "period" in history_data
    assert "interval" in history_data
    assert "total_records" in history_data


def test_get_company_info():
    """测试获取公司信息"""
    response = client.get("/api/v1/quote/AAPL/info")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "data" in data
    assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__])
