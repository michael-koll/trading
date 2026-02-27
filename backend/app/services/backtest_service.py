from __future__ import annotations

import json
from collections.abc import Mapping
from uuid import uuid4

import backtrader as bt
import pandas as pd

from app.core.config import BACKTESTS_DIR
from app.services.market_data_service import MarketDataService
from app.services.strategy_loader import load_strategy_module, load_strategy_params


class SmaCrossStrategy(bt.Strategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
        ("risk_pct", 1.0),
    )

    def __init__(self) -> None:
        self._markers: list[dict] = []
        self._equity_curve: list[dict] = []
        self._wins = 0
        self._closed = 0

        fast = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.fast_period))
        slow = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.slow_period))
        self.cross = bt.indicators.CrossOver(fast, slow)

    def next(self) -> None:
        dt = self.data.datetime.datetime(0).isoformat()
        self._equity_curve.append({"time": dt, "value": round(float(self.broker.getvalue()), 2)})

        if not self.position and self.cross > 0:
            close = float(self.data.close[0])
            risk_cash = float(self.broker.getcash()) * (float(self.params.risk_pct) / 100.0)
            size = max(int(risk_cash / close), 1)
            self.buy(size=size)
        elif self.position and self.cross < 0:
            self.close()

    def notify_order(self, order: bt.Order) -> None:
        if order.status != order.Completed:
            return

        side = "buy" if order.isbuy() else "sell"
        self._markers.append(
            {
                "time": self.data.datetime.datetime(0).isoformat(),
                "price": round(float(order.executed.price), 4),
                "side": side,
            }
        )

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return
        self._closed += 1
        if trade.pnlcomm > 0:
            self._wins += 1


class BacktestService:
    SUPPORTED_INDICATORS = {"sma", "ema", "wma", "rsi"}

    @staticmethod
    def _to_float(value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_value(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(k): BacktestService._normalize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [BacktestService._normalize_value(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        try:
            return float(value)  # e.g. Decimal
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _default_indicator_specs(params: dict) -> list[dict]:
        return [
            {
                "id": "sma_fast",
                "type": "sma",
                "source": "close",
                "period": int(params.get("fast_period", 10)),
                "label": f"SMA({int(params.get('fast_period', 10))})",
                "color": "#ffd166",
            },
            {
                "id": "sma_slow",
                "type": "sma",
                "source": "close",
                "period": int(params.get("slow_period", 30)),
                "label": f"SMA({int(params.get('slow_period', 30))})",
                "color": "#60a5fa",
            },
        ]

    @staticmethod
    def _resolve_indicator_specs(strategy_module: object, params: dict) -> list[dict]:
        raw = getattr(strategy_module, "INDICATORS", None)
        if not isinstance(raw, list):
            return BacktestService._default_indicator_specs(params)

        specs: list[dict] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                continue

            itype = str(item.get("type", "")).lower().strip()
            if itype not in BacktestService.SUPPORTED_INDICATORS:
                continue

            indicator_id = str(item.get("id") or f"{itype}_{i}").strip()
            source = str(item.get("source", "close")).strip().lower()
            if not indicator_id:
                continue

            period_value = item.get("period")
            period_param = item.get("period_param")
            if period_value is None and isinstance(period_param, str):
                period_value = params.get(period_param)

            try:
                period = int(period_value) if period_value is not None else None
            except (TypeError, ValueError):
                period = None

            if itype != "rsi" and (period is None or period <= 0):
                continue
            if itype == "rsi" and (period is None or period <= 0):
                period = 14

            specs.append(
                {
                    "id": indicator_id,
                    "type": itype,
                    "source": source,
                    "period": period,
                    "label": str(item.get("label") or f"{itype.upper()}({period})"),
                    "color": str(item.get("color") or ""),
                }
            )

        return specs or BacktestService._default_indicator_specs(params)

    @staticmethod
    def _compute_indicator(frame: pd.DataFrame, spec: dict) -> pd.Series:
        source = spec.get("source", "close")
        if source not in frame.columns:
            raise ValueError(f"Indicator source column '{source}' not found")

        series = frame[source].astype(float)
        period = int(spec.get("period", 14))
        itype = spec.get("type")

        if itype == "sma":
            return series.rolling(window=period, min_periods=period).mean()
        if itype == "ema":
            return series.ewm(span=period, adjust=False).mean()
        if itype == "wma":
            weights = pd.Series(range(1, period + 1), dtype="float64")
            return series.rolling(period).apply(
                lambda values: (values * weights).sum() / weights.sum(), raw=False
            )
        if itype == "rsi":
            delta = series.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, pd.NA)
            return 100 - (100 / (1 + rs))

        raise ValueError(f"Unsupported indicator type '{itype}'")

    @staticmethod
    def _execute(payload: dict, persist: bool = True, params_override: dict | None = None) -> dict:
        run_id = str(uuid4())
        base = float(payload.get("start_cash", 10000.0))

        strategy_module = load_strategy_module(payload["strategy_path"])
        params = load_strategy_params(payload["strategy_path"])
        if payload.get("params"):
            params.update(payload["params"])
        if params_override:
            params.update(params_override)

        frame = MarketDataService.get_ohlcv(payload)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(base)
        cerebro.broker.setcommission(commission=0.001)
        feed = bt.feeds.PandasData(dataname=frame)
        cerebro.adddata(feed)
        cerebro.addstrategy(SmaCrossStrategy, **params)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

        result = cerebro.run()
        strategy: SmaCrossStrategy = result[0]

        final_value = round(float(cerebro.broker.getvalue()), 2)
        pnl = round(final_value - base, 2)
        win_rate = round((strategy._wins / strategy._closed) if strategy._closed else 0.0, 3)
        pnl_pct = round((pnl / base) * 100.0 if base else 0.0, 4)

        drawdown = strategy.analyzers.drawdown.get_analysis()
        sharpe = strategy.analyzers.sharpe.get_analysis()
        returns = strategy.analyzers.returns.get_analysis()
        trades = strategy.analyzers.trades.get_analysis()
        sqn = strategy.analyzers.sqn.get_analysis()
        analyzers_raw = {
            "drawdown": BacktestService._normalize_value(drawdown),
            "sharpe": BacktestService._normalize_value(sharpe),
            "returns": BacktestService._normalize_value(returns),
            "trades": BacktestService._normalize_value(trades),
            "sqn": BacktestService._normalize_value(sqn),
        }

        total_trades = int((trades.get("total", {}) or {}).get("closed", 0) or 0)
        won_total = int((trades.get("won", {}) or {}).get("total", 0) or 0)
        lost_total = int((trades.get("lost", {}) or {}).get("total", 0) or 0)
        gross_pnl = (trades.get("pnl", {}) or {}).get("gross", {}) or {}
        net_pnl = (trades.get("pnl", {}) or {}).get("net", {}) or {}
        price_bars = [
            {
                "time": idx.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
            for idx, row in frame.iterrows()
        ]
        indicator_specs = BacktestService._resolve_indicator_specs(strategy_module, params)
        indicator_series: dict[str, list[dict]] = {}
        indicator_labels: dict[str, str] = {}
        indicator_colors: dict[str, str] = {}
        indicator_warnings: list[str] = []

        for spec in indicator_specs:
            iid = str(spec["id"])
            try:
                values = BacktestService._compute_indicator(frame, spec)
            except Exception as exc:
                indicator_warnings.append(f"{iid}: {exc}")
                continue

            indicator_series[iid] = [
                {"time": idx.isoformat(), "value": float(v)}
                for idx, v in values.items()
                if v == v
            ]
            indicator_labels[iid] = str(spec.get("label") or iid)
            if str(spec.get("color") or "").strip():
                indicator_colors[iid] = str(spec["color"]).strip()

        out = {
            "run_id": run_id,
            "final_value": final_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "win_rate": win_rate,
            "equity_curve": strategy._equity_curve,
            "price_bars": price_bars,
            "indicator_series": indicator_series,
            "markers": strategy._markers,
            "params": params,
            "bars": len(frame),
            "context": {
                "strategy_path": payload.get("strategy_path"),
                "symbol": payload.get("symbol", "AAPL"),
                "market": payload.get("market", "stocks"),
                "exchange": payload.get("exchange"),
                "interval": payload.get("interval", "1m"),
                "period": payload.get("period", "5d"),
                "dataset_path": payload.get("dataset_path"),
                "dataset_source": "local" if payload.get("dataset_path") else "yfinance",
                "start_time": frame.index.min().isoformat() if len(frame) else None,
                "end_time": frame.index.max().isoformat() if len(frame) else None,
                "indicator_labels": indicator_labels,
                "indicator_colors": indicator_colors,
                "indicator_warnings": indicator_warnings,
            },
            "analytics": {
                "performance": {
                    "start_cash": round(base, 2),
                    "final_value": final_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "returns_rtot": round(BacktestService._to_float(returns.get("rtot")), 6),
                    "returns_rnorm": round(BacktestService._to_float(returns.get("rnorm")), 6),
                    "returns_rnorm100": round(BacktestService._to_float(returns.get("rnorm100")), 4),
                    "sharpe_ratio": round(BacktestService._to_float(sharpe.get("sharperatio")), 6),
                    "sqn": round(BacktestService._to_float(sqn.get("sqn")), 6),
                },
                "risk": {
                    "max_drawdown_pct": round(BacktestService._to_float((drawdown.get("max", {}) or {}).get("drawdown")), 4),
                    "max_drawdown_money": round(BacktestService._to_float((drawdown.get("max", {}) or {}).get("moneydown")), 4),
                    "current_drawdown_pct": round(BacktestService._to_float(drawdown.get("drawdown")), 4),
                    "current_drawdown_money": round(BacktestService._to_float(drawdown.get("moneydown")), 4),
                },
                "trades": {
                    "total_closed": total_trades,
                    "won": won_total,
                    "lost": lost_total,
                    "win_rate_pct": round((won_total / total_trades) * 100.0 if total_trades else 0.0, 4),
                    "avg_net_pnl": round(BacktestService._to_float(net_pnl.get("average")), 6),
                    "total_net_pnl": round(BacktestService._to_float(net_pnl.get("total")), 6),
                    "avg_gross_pnl": round(BacktestService._to_float(gross_pnl.get("average")), 6),
                    "total_gross_pnl": round(BacktestService._to_float(gross_pnl.get("total")), 6),
                },
            },
            "analyzers_raw": analyzers_raw,
        }

        if persist:
            (BACKTESTS_DIR / f"{run_id}.json").write_text(json.dumps(out), encoding="utf-8")
        return out

    @classmethod
    def run_backtest(cls, payload: dict) -> dict:
        return cls._execute(payload, persist=True)
