from __future__ import annotations

import optuna

from app.services.backtest_service import BacktestService


class OptimizeService:
    @staticmethod
    def run_optimization(payload: dict) -> dict:
        n_trials = int(payload.get("n_trials", 20))

        def objective(trial: optuna.Trial) -> float:
            params = {
                "fast_period": trial.suggest_int("fast_period", 5, 40),
                "slow_period": trial.suggest_int("slow_period", 20, 120),
                "risk_pct": trial.suggest_float("risk_pct", 0.1, 3.0),
            }
            if params["slow_period"] <= params["fast_period"]:
                raise optuna.TrialPruned("slow_period must be greater than fast_period")

            result = BacktestService._execute(payload, persist=False, params_override=params)
            return float(result["pnl"])

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)

        best = BacktestService._execute(payload, persist=False, params_override=study.best_params)
        return {
            "best_value": study.best_value,
            "best_params": study.best_params,
            "trials": n_trials,
            "best_metrics": {
                "final_value": best["final_value"],
                "pnl": best["pnl"],
                "win_rate": best["win_rate"],
                "bars": best["bars"],
            },
        }
