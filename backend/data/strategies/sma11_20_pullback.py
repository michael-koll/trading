"""SMA 11/20 Pullback strategy.

Rules:
1) Trend filter: only consider longs when SMA(11) is above SMA(20).
2) Entry: wait for first pullback to SMA(11), then buy when price crosses SMA(11) from below to above.
3) Exit: close immediately once current price crosses below SMA(20) (no candle-close wait).
"""

PARAMS = {
    "fast_period": 11,
    "slow_period": 20,
    "risk_pct": 1.0,
}

INDICATORS = [
    {
        "id": "sma_fast",
        "type": "sma",
        "source": "close",
        "period_param": "fast_period",
        "label": "SMA 11",
        "color": "#ffd166",
    },
    {
        "id": "sma_slow",
        "type": "sma",
        "source": "close",
        "period_param": "slow_period",
        "label": "SMA 20",
        "color": "#60a5fa",
    },
]


def describe() -> dict:
    return {
        "name": "SMA 11/20 Pullback",
        "description": "Long-only: trend filter via SMA11>SMA20, first pullback entry via cross above SMA11, immediate exit once price crosses below SMA20.",
        "params": PARAMS,
        "rules": [
            "Only trade long when SMA(11) > SMA(20)",
            "After first pullback to SMA(11), buy on cross from below to above SMA(11)",
            "Exit immediately when current price crosses below SMA(20), without waiting for candle close",
        ],
    }


# Optional signal helper for future custom-engine support.
# `price` is intended as current/streaming price (not candle-close dependent).
def signal_state(price: float, prev_price: float, sma11: float, sma20: float, pullback_seen: bool) -> dict:
    trend_ok = sma11 > sma20
    crossed_up_sma11 = prev_price <= sma11 and price > sma11
    touched_or_below_sma11 = price <= sma11

    entry = trend_ok and pullback_seen and crossed_up_sma11
    crossed_below_sma20 = prev_price >= sma20 and price < sma20
    exit_signal = price < sma20 or crossed_below_sma20

    return {
        "trend_ok": trend_ok,
        "pullback_seen_next": pullback_seen or touched_or_below_sma11,
        "entry": entry,
        "exit": exit_signal,
    }
