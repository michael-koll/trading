from datetime import datetime
from pydantic import BaseModel, Field


class StrategyFile(BaseModel):
    name: str
    path: str
    updated_at: datetime


class SaveStrategyRequest(BaseModel):
    path: str = Field(min_length=1)
    content: str


class BacktestRequest(BaseModel):
    strategy_path: str
    symbol: str = "AAPL"
    interval: str = "1m"
    period: str = "5d"
    start_cash: float = 10000.0
    dataset_path: str | None = None
    params: dict[str, float | int] | None = None
    market: str = "stocks"
    exchange: str | None = None


class TradeMarker(BaseModel):
    time: str
    price: float
    side: str


class BacktestResponse(BaseModel):
    run_id: str
    final_value: float
    pnl: float
    win_rate: float
    equity_curve: list[dict]
    markers: list[TradeMarker]


class OptimizeRequest(BaseModel):
    strategy_path: str
    symbol: str = "AAPL"
    interval: str = "1m"
    period: str = "5d"
    n_trials: int = 20
    dataset_path: str | None = None
    objective: str = "pnl"
    seed: int | None = None
    ranges: dict[str, dict[str, float]] | None = None


class DatasetImportRequest(BaseModel):
    source: str
    symbol: str | None = None
    interval: str | None = None
    period: str | None = None
    csv_path: str | None = None
    timeframe: str | None = None


class PaperTradeStartRequest(BaseModel):
    strategy_path: str
    symbol: str
    interval: str = "1m"
    period: str = "7d"
    dataset_path: str | None = None
    market: str = "stocks"
    exchange: str | None = None
    starting_cash: float = 10000.0
    broker: str = "local"
