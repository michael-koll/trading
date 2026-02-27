"""New strategy."""

PARAMS = {
    "fast_period": 10,
    "slow_period": 30,
    "risk_pct": 1.0,
}


def describe() -> dict:
    return {
        "name": "New Strategy",
        "description": "Describe your strategy here.",
        "params": PARAMS,
    }
