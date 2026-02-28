"""New strategy."""

import backtrader as bt

PARAMS = {
    "fast_period": 10,
    "slow_period": 30,
    "risk_pct": 10.0,
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
