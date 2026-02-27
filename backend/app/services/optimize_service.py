from __future__ import annotations

import optuna
from optuna.trial import TrialState
from optuna.samplers import TPESampler

from app.services.backtest_service import BacktestService
from app.services.market_data_service import MarketDataService


class OptimizeService:
    MAX_OPT_BARS = 5000
    SUPPORTED_OBJECTIVES = {"pnl", "final_value", "win_rate", "sharpe_ratio", "max_drawdown_pct"}

    @staticmethod
    def _range_int(ranges: dict, key: str, default_min: int, default_max: int) -> tuple[int, int]:
        node = ranges.get(key, {}) if isinstance(ranges, dict) else {}
        min_v = int(node.get("min", default_min))
        max_v = int(node.get("max", default_max))
        if min_v >= max_v:
            raise ValueError(f"Invalid range for {key}: min must be < max")
        return min_v, max_v

    @staticmethod
    def _range_float(
        ranges: dict, key: str, default_min: float, default_max: float
    ) -> tuple[float, float]:
        node = ranges.get(key, {}) if isinstance(ranges, dict) else {}
        min_v = float(node.get("min", default_min))
        max_v = float(node.get("max", default_max))
        if min_v >= max_v:
            raise ValueError(f"Invalid range for {key}: min must be < max")
        return min_v, max_v

    @staticmethod
    def _objective_value(result: dict, objective: str) -> float:
        if objective == "pnl":
            return float(result["pnl"])
        if objective == "final_value":
            return float(result["final_value"])
        if objective == "win_rate":
            return float(result["win_rate"])
        if objective == "sharpe_ratio":
            return float(((result.get("analytics", {}) or {}).get("performance", {}) or {}).get("sharpe_ratio", 0.0))
        if objective == "max_drawdown_pct":
            return float(((result.get("analytics", {}) or {}).get("risk", {}) or {}).get("max_drawdown_pct", 0.0))
        raise ValueError(f"Unsupported optimization objective '{objective}'")

    @staticmethod
    def run_optimization(payload: dict) -> dict:
        n_trials = int(payload.get("n_trials", 20))
        ranges = payload.get("ranges") or {}
        objective_name = str(payload.get("objective", "pnl")).strip().lower()
        if objective_name not in OptimizeService.SUPPORTED_OBJECTIVES:
            raise ValueError(
                "Unsupported objective. Use one of: pnl, final_value, win_rate, sharpe_ratio, max_drawdown_pct"
            )
        direction = "minimize" if objective_name == "max_drawdown_pct" else "maximize"
        seed = payload.get("seed")
        sampler = TPESampler(seed=int(seed)) if seed is not None else TPESampler()

        fast_min, fast_max = OptimizeService._range_int(ranges, "fast_period", 5, 40)
        slow_min, slow_max = OptimizeService._range_int(ranges, "slow_period", 20, 120)
        risk_min, risk_max = OptimizeService._range_float(ranges, "risk_pct", 0.1, 3.0)

        frame = MarketDataService.get_ohlcv(payload)
        if len(frame) > OptimizeService.MAX_OPT_BARS:
            frame = frame.tail(OptimizeService.MAX_OPT_BARS).copy()
        failed_trials = 0

        def objective(trial: optuna.Trial) -> float:
            nonlocal failed_trials
            params = {
                "fast_period": trial.suggest_int("fast_period", fast_min, fast_max),
                "slow_period": trial.suggest_int("slow_period", slow_min, slow_max),
                "risk_pct": trial.suggest_float("risk_pct", risk_min, risk_max),
            }
            if params["slow_period"] <= params["fast_period"]:
                raise optuna.TrialPruned("slow_period must be greater than fast_period")

            try:
                result = BacktestService._execute(
                    payload,
                    persist=False,
                    params_override=params,
                    frame_override=frame,
                )
                return OptimizeService._objective_value(result, objective_name)
            except Exception:
                failed_trials += 1
                raise optuna.TrialPruned("Trial failed while executing backtest")

        study = optuna.create_study(direction=direction, sampler=sampler)
        study.optimize(objective, n_trials=n_trials)

        completed = study.get_trials(states=(TrialState.COMPLETE,))
        if not completed:
            raise ValueError("No successful optimization trial was completed.")

        best = BacktestService._execute(
            payload,
            persist=False,
            params_override=study.best_params,
            frame_override=frame,
        )
        best_params = {str(k): float(v) if isinstance(v, float) else int(v) for k, v in study.best_params.items()}
        return {
            "best_value": float(study.best_value),
            "best_params": best_params,
            "trials": int(n_trials),
            "failed_trials": int(failed_trials),
            "objective": objective_name,
            "direction": direction,
            "seed": int(seed) if seed is not None else None,
            "search_space": {
                "fast_period": {"min": fast_min, "max": fast_max},
                "slow_period": {"min": slow_min, "max": slow_max},
                "risk_pct": {"min": risk_min, "max": risk_max},
            },
            "best_metrics": {
                "final_value": float(best["final_value"]),
                "pnl": float(best["pnl"]),
                "win_rate": float(best["win_rate"]),
                "bars": int(best["bars"]),
            },
            "data_bars_used": int(len(frame)),
        }
