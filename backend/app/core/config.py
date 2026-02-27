from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STRATEGIES_DIR = DATA_DIR / "strategies"
DATASETS_DIR = DATA_DIR / "datasets"
BACKTESTS_DIR = DATA_DIR / "backtests"

for folder in (DATA_DIR, STRATEGIES_DIR, DATASETS_DIR, BACKTESTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)
