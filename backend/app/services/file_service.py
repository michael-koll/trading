from datetime import datetime
from pathlib import Path
from app.core.config import STRATEGIES_DIR


class FileService:
    DEFAULT_TEMPLATE = '''"""New strategy."""

import backtrader as bt

PARAMS = {
    "fast_period": 10,
    "slow_period": 30,
    "risk_pct": 1.0,
}


class Strategy(bt.Strategy):
    params = dict(
        fast_period=PARAMS["fast_period"],
        slow_period=PARAMS["slow_period"],
        risk_pct=PARAMS["risk_pct"],
    )

    def __init__(self):
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.p.fast_period))
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.p.slow_period))
        self.cross = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        if not self.position and self.cross > 0:
            close = float(self.data.close[0])
            risk_cash = float(self.broker.getcash()) * (float(self.p.risk_pct) / 100.0)
            size = max(int(risk_cash / close), 1)
            self.buy(size=size)
        elif self.position and self.cross < 0:
            self.close()


def describe() -> dict:
    return {
        "name": "New Strategy",
        "description": "Editable Backtrader strategy.",
        "params": PARAMS,
    }
'''

    @staticmethod
    def _resolve_strategy_path(rel_path: str) -> Path:
        path = (STRATEGIES_DIR / rel_path).resolve()
        if not str(path).startswith(str(STRATEGIES_DIR.resolve())):
            raise ValueError("Invalid path")
        return path

    @staticmethod
    def list_strategies() -> list[dict]:
        items: list[dict] = []
        for path in sorted(STRATEGIES_DIR.rglob("*.py")):
            stat = path.stat()
            items.append(
                {
                    "name": path.name,
                    "path": str(path.relative_to(STRATEGIES_DIR)),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime),
                }
            )
        return items

    @staticmethod
    def read_strategy(rel_path: str) -> str:
        path = FileService._resolve_strategy_path(rel_path)
        if not path.exists():
            raise FileNotFoundError(rel_path)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def save_strategy(rel_path: str, content: str) -> None:
        path = FileService._resolve_strategy_path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def create_strategy(rel_path: str = "new_strategy.py") -> str:
        base_rel = (rel_path or "new_strategy.py").strip()
        if not base_rel:
            base_rel = "new_strategy.py"
        if not base_rel.endswith(".py"):
            base_rel = f"{base_rel}.py"

        base_path = FileService._resolve_strategy_path(base_rel)
        if base_path.suffix != ".py":
            raise ValueError("Strategy file must use .py extension")

        candidate = base_path
        if candidate.exists():
            stem = candidate.stem
            suffix = candidate.suffix
            parent = candidate.parent
            i = 1
            while True:
                numbered = parent / f"{stem}{i}{suffix}"
                if not numbered.exists():
                    candidate = numbered
                    break
                i += 1

        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(FileService.DEFAULT_TEMPLATE, encoding="utf-8")
        return str(candidate.relative_to(STRATEGIES_DIR))

    @staticmethod
    def rename_strategy(old_rel_path: str, new_rel_path: str) -> None:
        old_path = FileService._resolve_strategy_path(old_rel_path)
        new_path = FileService._resolve_strategy_path(new_rel_path)
        if old_path.suffix != ".py" or new_path.suffix != ".py":
            raise ValueError("Strategy files must use .py extension")
        if not old_path.exists():
            raise FileNotFoundError(old_rel_path)
        if new_path.exists():
            raise ValueError("Target strategy file already exists")
        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)

    @staticmethod
    def delete_strategy(rel_path: str) -> None:
        path = FileService._resolve_strategy_path(rel_path)
        if path.suffix != ".py":
            raise ValueError("Strategy file must use .py extension")
        if not path.exists():
            raise FileNotFoundError(rel_path)
        path.unlink()
