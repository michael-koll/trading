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
    def _build_param_specs(payload: dict, ranges: dict) -> list[dict]:
        if not isinstance(ranges, dict) or not ranges:
            raise ValueError("Optimization ranges are required")

        strategy_path = str(payload.get("strategy_path") or "").strip()
        if not strategy_path:
            raise ValueError("strategy_path is required")

        strategy_info = BacktestService.inspect_strategy_params(strategy_path)
        numeric_params = {
            str(item["name"]): item
            for item in strategy_info.get("params", [])
            if isinstance(item, dict) and item.get("type") in {"int", "float"}
        }

        specs: list[dict] = []
        for key, node in ranges.items():
            name = str(key)
            if name not in numeric_params:
                raise ValueError(f"Range parameter '{name}' is not defined in strategy params")
            if not isinstance(node, dict):
                raise ValueError(f"Range for '{name}' must be an object with min/max")

            param_type = str(numeric_params[name].get("type"))
            try:
                if param_type == "int":
                    min_v = int(node.get("min"))
                    max_v = int(node.get("max"))
                else:
                    min_v = float(node.get("min"))
                    max_v = float(node.get("max"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Range for '{name}' must include numeric min/max values") from exc

            if min_v >= max_v:
                raise ValueError(f"Invalid range for {name}: min must be < max")

            specs.append({"name": name, "type": param_type, "min": min_v, "max": max_v})

        if not specs:
            raise ValueError("No optimization parameters configured")
        return specs

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
        param_specs = OptimizeService._build_param_specs(payload, ranges)

        frame = MarketDataService.get_ohlcv(payload)
        if len(frame) > OptimizeService.MAX_OPT_BARS:
            frame = frame.tail(OptimizeService.MAX_OPT_BARS).copy()
        failed_trials = 0

        def objective(trial: optuna.Trial) -> float:
            nonlocal failed_trials
            params: dict[str, float | int] = {}
            for spec in param_specs:
                if spec["type"] == "int":
                    params[spec["name"]] = trial.suggest_int(spec["name"], int(spec["min"]), int(spec["max"]))
                else:
                    params[spec["name"]] = trial.suggest_float(spec["name"], float(spec["min"]), float(spec["max"]))

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
            "search_space": {spec["name"]: {"min": spec["min"], "max": spec["max"], "type": spec["type"]} for spec in param_specs},
            "best_metrics": {
                "final_value": float(best["final_value"]),
                "pnl": float(best["pnl"]),
                "win_rate": float(best["win_rate"]),
                "bars": int(best["bars"]),
            },
            "data_bars_used": int(len(frame)),
        }
