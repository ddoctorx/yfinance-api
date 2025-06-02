"""
历史数据API路由
提供K线数据、股息、拆股等历史信息
"""

from typing import Optional
from fastapi import APIRouter, Query, Depends

from app.core.logging import get_logger
from app.models.base import BaseResponse
from app.models.history import HistoryData, HistoryParams, ActionsData
from app.services.yfinance_service import yfinance_service
from app.utils.exceptions import InvalidParameterError

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{symbol}", response_model=BaseResponse[dict])
async def get_history(
    symbol: str,
    period: Optional[str] = Query(
        "1y", description="数据周期", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: Optional[str] = Query(
        "1d", description="数据间隔", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"),
    start: Optional[str] = Query(
        None, description="开始日期 (YYYY-MM-DD)", pattern="^\\d{4}-\\d{2}-\\d{2}$"),
    end: Optional[str] = Query(
        None, description="结束日期 (YYYY-MM-DD)", pattern="^\\d{4}-\\d{2}-\\d{2}$"),
    auto_adjust: bool = Query(True, description="是否自动调整价格"),
    prepost: bool = Query(False, description="是否包含盘前盘后数据"),
    actions: bool = Query(True, description="是否包含分红和拆股信息")
):
    """
    获取股票历史数据

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)
    - **period**: 数据周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    - **interval**: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    - **start**: 开始日期，格式 YYYY-MM-DD
    - **end**: 结束日期，格式 YYYY-MM-DD
    - **auto_adjust**: 是否自动调整价格(除权除息)
    - **prepost**: 是否包含盘前盘后数据
    - **actions**: 是否包含分红和拆股信息

    注意：使用start/end参数时会忽略period参数
    """
    logger.info("获取历史数据", symbol=symbol, period=period, interval=interval)

    # 验证股票代码
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()

    # 验证日期参数
    if start and end:
        from datetime import datetime
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            if end_date <= start_date:
                raise InvalidParameterError("end", "结束日期必须晚于开始日期")
        except ValueError:
            raise InvalidParameterError("date", "日期格式必须是 YYYY-MM-DD")

    # 获取历史数据
    history_data = await yfinance_service.get_history(
        symbol=symbol,
        period=period,
        interval=interval,
        start=start,
        end=end,
        auto_adjust=auto_adjust,
        prepost=prepost,
        actions=actions
    )

    return BaseResponse(
        symbol=symbol,
        data=history_data
    )


@router.get("/{symbol}/dividends", response_model=BaseResponse[list])
async def get_dividends(symbol: str):
    """
    获取股票股息历史

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回历史股息分配记录
    """
    logger.info("获取股息历史", symbol=symbol)

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()

    # 这里应该调用 yfinance_service 的股息方法
    # 暂时返回空数据作为占位符
    dividends_data = []

    return BaseResponse(
        symbol=symbol,
        data=dividends_data
    )


@router.get("/{symbol}/splits", response_model=BaseResponse[list])
async def get_splits(symbol: str):
    """
    获取股票拆股历史

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回历史拆股记录
    """
    logger.info("获取拆股历史", symbol=symbol)

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()

    # 这里应该调用 yfinance_service 的拆股方法
    # 暂时返回空数据作为占位符
    splits_data = []

    return BaseResponse(
        symbol=symbol,
        data=splits_data
    )


@router.get("/{symbol}/actions", response_model=BaseResponse[dict])
async def get_actions(symbol: str):
    """
    获取股票行动历史(股息+拆股)

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回股息和拆股的综合记录
    """
    logger.info("获取行动历史", symbol=symbol)

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()

    # 这里应该调用 yfinance_service 的行动方法
    # 暂时返回空数据作为占位符
    actions_data = {
        "dividends": [],
        "splits": []
    }

    return BaseResponse(
        symbol=symbol,
        data=actions_data
    )
