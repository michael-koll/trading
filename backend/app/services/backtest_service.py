from __future__ import annotations

import json
from collections.abc import Mapping
from inspect import isclass
from numbers import Integral, Real
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


class EquityCurveAnalyzer(bt.Analyzer):
    def start(self) -> None:
        self._curve: list[dict] = []

    def next(self) -> None:
        dt = self.strategy.data.datetime.datetime(0).isoformat()
        self._curve.append({"time": dt, "value": round(float(self.strategy.broker.getvalue()), 2)})

    def get_analysis(self) -> list[dict]:
        return self._curve


class TradeMarkerAnalyzer(bt.Analyzer):
    def start(self) -> None:
        self._markers: list[dict] = []

    def notify_order(self, order: bt.Order) -> None:
        if order.status != order.Completed:
            return
        side = "buy" if order.isbuy() else "sell"
        self._markers.append(
            {
                "time": bt.num2date(order.executed.dt).isoformat(),
                "price": round(float(order.executed.price), 4),
                "side": side,
            }
        )

    def get_analysis(self) -> list[dict]:
        return self._markers


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
    def _resolve_strategy_class(strategy_module: object) -> type[bt.Strategy]:
        # First bt.Strategy subclass declared in this module.
        module_name = getattr(strategy_module, "__name__", "")
        for candidate in vars(strategy_module).values():
            if (
                isclass(candidate)
                and issubclass(candidate, bt.Strategy)
                and candidate is not bt.Strategy
                and getattr(candidate, "__module__", None) == module_name
            ):
                return candidate

        raise ValueError(
            "Strategy module must define a Backtrader strategy class. "
            "Add `class MyStrategy(bt.Strategy): ...` to the script."
        )

    @staticmethod
    def _strategy_param_keys(strategy_class: type[bt.Strategy]) -> set[str]:
        raw_params = getattr(strategy_class, "params", None)
        if raw_params is None:
            return set()

        if hasattr(raw_params, "_getkeys"):
            try:
                return {str(key) for key in raw_params._getkeys()}
            except Exception:
                return set()

        if isinstance(raw_params, Mapping):
            return {str(key) for key in raw_params.keys()}

        if isinstance(raw_params, (list, tuple)):
            keys: set[str] = set()
            for item in raw_params:
                if isinstance(item, (list, tuple)) and item:
                    keys.add(str(item[0]))
            return keys

        return set()

    @staticmethod
    def _strategy_param_defaults(strategy_class: type[bt.Strategy]) -> dict[str, object]:
        raw_params = getattr(strategy_class, "params", None)
        if raw_params is None:
            return {}

        if hasattr(raw_params, "_getitems"):
            try:
                return {str(k): v for k, v in raw_params._getitems()}
            except Exception:
                return {}

        if isinstance(raw_params, Mapping):
            return {str(k): v for k, v in raw_params.items()}

        if isinstance(raw_params, (list, tuple)):
            out: dict[str, object] = {}
            for item in raw_params:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    out[str(item[0])] = item[1]
            return out

        return {}

    @staticmethod
    def _default_optimization_range(default_value: object) -> tuple[float | int, float | int] | None:
        if isinstance(default_value, bool):
            return None

        if isinstance(default_value, Integral):
            base = int(default_value)
            if base <= 0:
                return 1, 10
            minimum = max(1, int(base * 0.5))
            maximum = max(minimum + 1, int(base * 2))
            return minimum, maximum

        if isinstance(default_value, Real):
            base = float(default_value)
            if base <= 0:
                return 0.01, 1.0
            minimum = max(0.0001, round(base * 0.5, 6))
            maximum = max(minimum + 0.0001, round(base * 2, 6))
            return minimum, maximum

        return None

    @staticmethod
    def inspect_strategy_params(rel_path: str) -> dict:
        strategy_module = load_strategy_module(rel_path)
        strategy_class = BacktestService._resolve_strategy_class(strategy_module)
        defaults = BacktestService._strategy_param_defaults(strategy_class)

        params_out: list[dict] = []
        for name, default_value in defaults.items():
            range_values = BacktestService._default_optimization_range(default_value)
            if range_values is None:
                continue

            if isinstance(default_value, Integral) and not isinstance(default_value, bool):
                ptype = "int"
                default_numeric = int(default_value)
            else:
                ptype = "float"
                default_numeric = float(default_value)

            params_out.append(
                {
                    "name": str(name),
                    "type": ptype,
                    "default": default_numeric,
                    "suggested_min": range_values[0],
                    "suggested_max": range_values[1],
                }
            )

        return {
            "strategy_class": getattr(strategy_class, "__name__", str(strategy_class)),
            "params": sorted(params_out, key=lambda x: x["name"]),
        }

    @staticmethod
    def _filter_strategy_params(strategy_class: type[bt.Strategy], params: dict) -> tuple[dict, list[str]]:
        allowed = BacktestService._strategy_param_keys(strategy_class)
        if not allowed:
            return params, []

        filtered: dict = {}
        ignored: list[str] = []
        for key, value in params.items():
            if str(key) in allowed:
                filtered[key] = value
            else:
                ignored.append(str(key))
        return filtered, sorted(ignored)

    @staticmethod
    def _resolve_indicator_specs(strategy_module: object, params: dict) -> list[dict]:
        raw = getattr(strategy_module, "INDICATORS", None)
        if not isinstance(raw, list):
            return []

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

        return specs

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
    def _execute(
        payload: dict,
        persist: bool = True,
        params_override: dict | None = None,
        frame_override: pd.DataFrame | None = None,
    ) -> dict:
        run_id = str(uuid4())
        base = float(payload.get("start_cash", 10000.0))

        strategy_module = load_strategy_module(payload["strategy_path"])
        params = load_strategy_params(payload["strategy_path"])
        if payload.get("params"):
            params.update(payload["params"])
        if params_override:
            params.update(params_override)

        frame = frame_override if frame_override is not None else MarketDataService.get_ohlcv(payload)
        strategy_class = BacktestService._resolve_strategy_class(strategy_module)
        strategy_params, ignored_strategy_params = BacktestService._filter_strategy_params(strategy_class, params)

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(base)
        cerebro.broker.setcommission(commission=0.001)
        feed = bt.feeds.PandasData(dataname=frame)
        cerebro.adddata(feed)
        cerebro.addstrategy(strategy_class, **strategy_params)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        cerebro.addanalyzer(EquityCurveAnalyzer, _name="equitycurve")
        cerebro.addanalyzer(TradeMarkerAnalyzer, _name="trademarkers")

        try:
            result = cerebro.run()
        except TypeError as exc:
            raise ValueError(f"Invalid strategy configuration: {exc}") from exc
        strategy: bt.Strategy = result[0]

        final_value = round(float(cerebro.broker.getvalue()), 2)
        pnl = round(final_value - base, 2)
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
        win_rate = round((won_total / total_trades) if total_trades else 0.0, 3)
        gross_pnl = (trades.get("pnl", {}) or {}).get("gross", {}) or {}
        net_pnl = (trades.get("pnl", {}) or {}).get("net", {}) or {}
        equity_curve = strategy.analyzers.equitycurve.get_analysis()
        if not isinstance(equity_curve, list):
            equity_curve = []
        markers = getattr(strategy, "_markers", [])
        if not isinstance(markers, list):
            markers = []
        if not markers:
            markers = strategy.analyzers.trademarkers.get_analysis()
            if not isinstance(markers, list):
                markers = []
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
            "equity_curve": equity_curve,
            "price_bars": price_bars,
            "indicator_series": indicator_series,
            "markers": markers,
            "params": params,
            "bars": len(frame),
            "context": {
                "strategy_path": payload.get("strategy_path"),
                "strategy_class": getattr(strategy_class, "__name__", str(strategy_class)),
                "symbol": payload.get("symbol", "AAPL"),
                "market": payload.get("market", "stocks"),
                "exchange": payload.get("exchange"),
                "interval": payload.get("interval", "1m"),
                "period": payload.get("period", "5d"),
                "dataset_path": payload.get("dataset_path"),
                "dataset_source": "local" if payload.get("dataset_path") else "yfinance",
                "start_time": frame.index.min().isoformat() if len(frame) else None,
                "end_time": frame.index.max().isoformat() if len(frame) else None,
                "ignored_strategy_params": ignored_strategy_params,
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
