"""
SMA 9/20/50 Pullback Strategy (Backtrader editor/runtime discovery)
moserdan
Logic:
1) Trend filter: SMA20 > SMA50
2) First pullback: Close dips below SMA9 at least once while trend filter holds
3) Entry: After that pullback, Close crosses SMA9 upward -> BUY
4) Exit: Close crosses SMA20 downward -> SELL
"""

PARAMS = {
    "sma9_period": 9,
    "sma20_period": 20,
    "sma50_period": 50,
    "risk_pct": 1.0,
}

INDICATORS = [
    {
        "id": "sma9",
        "type": "sma",
        "source": "close",
        "period_param": "sma9_period",
        "label": "SMA 9",
        "color": "#facc15",
    },
    {
        "id": "sma20",
        "type": "sma",
        "source": "close",
        "period_param": "sma20_period",
        "label": "SMA 20",
        "color": "#60a5fa",
    },
    {
        "id": "sma50",
        "type": "sma",
        "source": "close",
        "period_param": "sma50_period",
        "label": "SMA 50",
        "color": "#ef4444",
    },
]


def describe() -> dict:
    return {
        "name": "SMA Pullback 9/20 with 20>50 Filter",
        "description": (
            "Trend filter: SMA20 > SMA50. Entry on first pullback below SMA9, "
            "then buy when Close crosses SMA9 upward. Exit when Close crosses SMA20 downward."
        ),
        "params": PARAMS,
    }


# --- Strategy logic (Backtrader) ---
import backtrader as bt


class Strategy(bt.Strategy):
    params = dict(
        sma9_period=PARAMS["sma9_period"],
        sma20_period=PARAMS["sma20_period"],
        sma50_period=PARAMS["sma50_period"],
        risk_pct=PARAMS["risk_pct"],
    )

    def __init__(self):
        self.sma9 = bt.ind.SMA(self.data.close, period=self.p.sma9_period)
        self.sma20 = bt.ind.SMA(self.data.close, period=self.p.sma20_period)
        self.sma50 = bt.ind.SMA(self.data.close, period=self.p.sma50_period)

        # Cross: +1 up, -1 down
        self.cross_sma9 = bt.ind.CrossOver(self.data.close, self.sma9)
        self.cross_sma20 = bt.ind.CrossOver(self.data.close, self.sma20)

        self.pullback_seen = False
        self.order = None

    def notify_order(self, order):
        if order.status in (order.Completed, order.Canceled, order.Rejected):
            self.order = None

    def next(self):
        if self.order:
            return

        # 4) Exit: Close crosses SMA20 down
        if self.position:
            if self.cross_sma20[0] < 0:
                self.order = self.close()
            return

        # 1) Trend filter: SMA20 > SMA50
        trend_up = self.sma20[0] > self.sma50[0]
        if not trend_up:
            self.pullback_seen = False
            return

        # 2) First pullback: Close below SMA9
        if self.data.close[0] < self.sma9[0]:
            self.pullback_seen = True

        # 3) Entry: after pullback, Close crosses SMA9 up
        if self.pullback_seen and self.cross_sma9[0] > 0:
            # Simple sizing placeholder:
            # If your runtime provides a risk-based sizer, use it.
            # Otherwise, buy 1 unit.
            self.order = self.buy(size=1)
            self.pullback_seen = False