"""Sample strategy file used by the editor and runtime discovery."""

PARAMS = {
    "fast_period": 10,
    "slow_period": 30,
    "risk_pct": 1.0,
}

INDICATORS = [
    {
        "id": "sma_fast",
        "type": "sma",
        "source": "close",
        "period_param": "fast_period",
        "label": "Fast SMA",
        "color": "#ffd166",
    },
    {
        "id": "sma_slow",
        "type": "sma",
        "source": "close",
        "period_param": "slow_period",
        "label": "Slow SMA",
        "color": "#60a5fa",
    },
]


def describe() -> dict:
    return {
        "name": "Example SMA",
        "description": "Simple moving average crossover baseline strategy.",
        "params": PARAMS,
    }
