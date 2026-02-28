"""UT Bot Alerts (TradingView Pine v4) port for Backtrader."""

import math

import backtrader as bt


PARAMS = {
    "key_value": 1.0,
    "atr_period": 10,
    "use_heikin_ashi": 0,
}


class Strategy(bt.Strategy):
    params = (
        ("key_value", PARAMS["key_value"]),
        ("atr_period", PARAMS["atr_period"]),
        ("use_heikin_ashi", PARAMS["use_heikin_ashi"]),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=int(self.p.atr_period))
        self._trail = None
        self._prev_src = None

    def _src(self) -> float:
        if int(self.p.use_heikin_ashi):
            # Heikin-Ashi close approximation for current bar.
            return float(
                (self.data.open[0] + self.data.high[0] + self.data.low[0] + self.data.close[0]) / 4.0
            )
        return float(self.data.close[0])

    def next(self):
        atr_now = float(self.atr[0])
        if math.isnan(atr_now) or atr_now <= 0:
            return

        src = self._src()
        nloss = float(self.p.key_value) * atr_now

        prev_trail = self._trail if self._trail is not None else 0.0
        prev_src = self._prev_src if self._prev_src is not None else src

        # Pine equivalent:
        # xATRTrailingStop := iff(src > prev and src[1] > prev, max(prev, src - nLoss),
        #    iff(src < prev and src[1] < prev, min(prev, src + nLoss),
        #    iff(src > prev, src - nLoss, src + nLoss)))
        if src > prev_trail and prev_src > prev_trail:
            trail = max(prev_trail, src - nloss)
        elif src < prev_trail and prev_src < prev_trail:
            trail = min(prev_trail, src + nloss)
        elif src > prev_trail:
            trail = src - nloss
        else:
            trail = src + nloss

        above = prev_src <= prev_trail and src > trail
        below = prev_src >= prev_trail and src < trail
        buy = src > trail and above
        sell = src < trail and below

        if buy and not self.position:
            self.buy()
        elif sell and self.position:
            self.close()

        self._prev_src = src
        self._trail = trail


def describe() -> dict:
    return {
        "name": "UT Bot Alerts (TV Port)",
        "description": "TradingView UT Bot Alerts strategy ported to Backtrader.",
        "params": PARAMS,
    }
