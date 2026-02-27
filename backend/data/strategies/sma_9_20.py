def __init__(self):

    self.sma9 = bt.ind.SMA(self.data.close, period=9)
    self.sma20 = bt.ind.SMA(self.data.close, period=20)

    self.cross_sma9 = bt.ind.CrossOver(self.data.close, self.sma9)
    self.cross_sma20 = bt.ind.CrossOver(self.data.close, self.sma20)

    self.pullback_seen = False


def next(self):

    # =========================
    # EXIT LOGIK
    # =========================
    if self.position:
        # Close kreuzt SMA20 nach unten
        if self.cross_sma20[0] < 0:
            self.close()
        return


    # =========================
    # TREND FILTER
    # =========================
    trend_up = (
        self.sma9[0] > self.sma20[0] and
        self.sma20[0] > self.sma20[-1]  # SMA20 steigt
    )

    if not trend_up:
        self.pullback_seen = False
        return


    # =========================
    # PULLBACK ERKENNEN
    # =========================
    # erster Pullback = Close unter SMA9
    if self.data.close[0] < self.sma9[0]:
        self.pullback_seen = True


    # =========================
    # ENTRY
    # =========================
    # Nach Pullback kreuzt Close SMA9 nach oben
    if self.pullback_seen and self.cross_sma9[0] > 0:
        self.buy()
        self.pullback_seen = False