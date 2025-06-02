"""
报价API路由
提供实时报价、公司信息等接口
支持多数据源降级机制
"""

from typing import List, Dict
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.base import BaseResponse, BatchRequest, BatchResponse
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.services.data_source_manager import DataSourceManager
from app.utils.exceptions import InvalidParameterError

logger = get_logger(__name__)
router = APIRouter()


def get_data_source_manager() -> DataSourceManager:
    """获取数据源管理器实例（本地引用以避免循环导入）"""
    from app.main import get_data_source_manager
    return get_data_source_manager()


@router.get("/{symbol}", response_model=BaseResponse[FastQuoteData])
async def get_quote(
    symbol: str,
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    获取股票实时报价

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    支持多数据源降级：主数据源失败时自动切换到备用数据源
    """
    logger.info("获取股票报价", symbol=symbol)

    # 验证股票代码格式
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    quote_data = await manager.get_fast_quote(symbol)

    # 在响应中添加数据源信息
    response = BaseResponse(
        symbol=symbol,
        data=quote_data
    )

    # 如果数据中包含数据源信息，添加到响应中
    if hasattr(quote_data, '__dict__') and 'data_source' in quote_data.__dict__:
        response.data_source = quote_data.data_source
        response.is_fallback = getattr(quote_data, 'is_fallback', False)

    return response


@router.get("/{symbol}/detailed", response_model=BaseResponse[QuoteData])
async def get_detailed_quote(
    symbol: str,
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    获取股票详细报价信息

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    包含更详细的财务指标、估值数据等
    支持多数据源降级机制
    """
    logger.info("获取详细股票报价", symbol=symbol)

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    quote_data = await manager.get_detailed_quote(symbol)

    response = BaseResponse(
        symbol=symbol,
        data=quote_data
    )

    # 添加数据源信息
    if hasattr(quote_data, '__dict__') and 'data_source' in quote_data.__dict__:
        response.data_source = quote_data.data_source
        response.is_fallback = getattr(quote_data, 'is_fallback', False)

    return response


@router.get("/{symbol}/info", response_model=BaseResponse[CompanyInfo])
async def get_company_info(
    symbol: str,
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    获取公司基本信息

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    包含公司名称、行业、国家、员工数等基本信息
    支持多数据源降级机制
    """
    logger.info("获取公司信息", symbol=symbol)

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    company_info = await manager.get_company_info(symbol)

    response = BaseResponse(
        symbol=symbol,
        data=company_info
    )

    # 添加数据源信息
    if hasattr(company_info, '__dict__') and 'data_source' in company_info.__dict__:
        response.data_source = company_info.data_source
        response.is_fallback = getattr(company_info, 'is_fallback', False)

    return response


@router.post("/batch", response_model=BatchResponse[FastQuoteData])
async def get_batch_quotes(
    request: BatchRequest,
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    批量获取股票报价

    - **symbols**: 股票代码列表，最多10个

    返回成功获取的报价数据和失败的错误信息
    支持多数据源降级机制
    """
    logger.info("批量获取股票报价", symbols=request.symbols,
                count=len(request.symbols))

    # 验证股票代码
    valid_symbols = []
    for symbol in request.symbols:
        if symbol and len(symbol.strip()) > 0:
            valid_symbols.append(symbol.upper().strip())

    if not valid_symbols:
        raise InvalidParameterError("symbols", request.symbols)

    # 获取批量报价
    quotes = await manager.get_batch_quotes(valid_symbols)

    # 构建响应
    errors = {}
    for symbol in valid_symbols:
        if symbol not in quotes:
            errors[symbol] = "获取报价失败"

    return BatchResponse(
        data=quotes,
        errors=errors
    )


@router.get("/", response_model=BatchResponse[FastQuoteData])
async def get_quotes_by_symbols(
    symbols: str = Query(..., description="逗号分隔的股票代码列表",
                         example="AAPL,MSFT,GOOGL"),
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    通过查询参数批量获取股票报价

    - **symbols**: 逗号分隔的股票代码列表，最多10个

    例如: ?symbols=AAPL,MSFT,GOOGL
    支持多数据源降级机制
    """
    # 解析股票代码
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    if not symbol_list:
        raise InvalidParameterError("symbols", symbols)

    if len(symbol_list) > 10:
        raise InvalidParameterError(
            "symbols", f"最多支持10个股票代码，当前提供了{len(symbol_list)}个")

    logger.info("通过查询参数批量获取股票报价", symbols=symbol_list, count=len(symbol_list))

    # 获取批量报价
    quotes = await manager.get_batch_quotes(symbol_list)

    # 构建响应
    errors = {}
    for symbol in symbol_list:
        if symbol not in quotes:
            errors[symbol] = "获取报价失败"

    return BatchResponse(
        data=quotes,
        errors=errors
    )
