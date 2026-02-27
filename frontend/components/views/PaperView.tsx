"use client";

import { ChartPane } from "@/components/ChartPane";
import { TradeChartPane } from "@/components/TradeChartPane";

type PaperSnapshot = {
  final_value: number;
  pnl: number;
  pnl_pct?: number;
  win_rate: number;
  context?: {
    indicator_colors?: Record<string, string>;
  };
  equity_curve: { time: string; value: number }[];
  price_bars?: { time: string; open: number; high: number; low: number; close: number }[];
  markers?: { time: string; price: number; side: "buy" | "sell" }[];
  indicator_series?: Record<string, { time: string; value: number }[]>;
};

type PaperState = {
  session: {
    session_id: string;
    symbol: string;
    interval: string;
    period: string;
    dataset_path?: string | null;
    status: string;
    broker: string;
    position: number;
    updated_at?: string;
  };
  snapshot: PaperSnapshot;
};

type PaperViewProps = {
  strategyName: string;
  sessionId: string;
  error: string;
  loading: boolean;
  state: PaperState | null;
  onStartLocal: () => void;
  onStartAlpaca: () => void;
  onRefresh: () => void;
};

export function PaperView({
  strategyName,
  sessionId,
  error,
  loading,
  state,
  onStartLocal,
  onStartAlpaca,
  onRefresh,
}: PaperViewProps) {
  const snapshot = state?.snapshot;
  const session = state?.session;

  return (
    <section className="card panel backtest-view">
      <div className="panel-head">
        <div>
          <div className="section-label">LIVE PAPER TRADING VIEW</div>
          <h3>Paper Trading Session</h3>
        </div>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onStartLocal}>Start Local Paper</button>
          <button className="btn-secondary" onClick={onStartAlpaca}>Start Alpaca Paper</button>
          <button className="btn-secondary" onClick={onRefresh} disabled={!sessionId || loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <div className="section-label">RUN CONTEXT</div>
          <table className="metric-table">
            <tbody>
              <tr><td>Strategy File</td><td>{strategyName}</td></tr>
              <tr><td>Session ID</td><td>{sessionId || "not started"}</td></tr>
              <tr><td>Broker</td><td>{session?.broker || "-"}</td></tr>
              <tr><td>Status</td><td>{session?.status || "-"}</td></tr>
              <tr><td>Symbol</td><td>{session?.symbol || "-"}</td></tr>
              <tr><td>Interval</td><td>{session?.interval || "-"}</td></tr>
              <tr><td>Period</td><td>{session?.period || "-"}</td></tr>
              <tr><td>Dataset</td><td>{session?.dataset_path || "(live yfinance)"}</td></tr>
              <tr><td>Open Position (units)</td><td>{session?.position ?? "-"}</td></tr>
              <tr><td>Last Update</td><td>{session?.updated_at || "-"}</td></tr>
            </tbody>
          </table>
        </div>
        <div className="detail-card">
          <div className="section-label">NOTES</div>
          <p className="muted">Charts are rendered using TradingView lightweight-charts with live refresh.</p>
          <p className="muted">Entries/Exits and strategy indicators are displayed like in Backtesting view.</p>
          <p className="muted">Local paper mode is key-free. Alpaca paper mode requires `ALPACA_API_KEY` and `ALPACA_API_SECRET`.</p>
          {error && <p className="error-text">{error}</p>}
        </div>
      </div>

      {snapshot && (
        <>
          <div className="stats-row">
            <div className="stat">
              <span>Final Value</span>
              <strong className={snapshot.pnl > 0 ? "value-positive" : snapshot.pnl < 0 ? "value-negative" : ""}>
                ${snapshot.final_value.toFixed(2)}
              </strong>
            </div>
            <div className="stat">
              <span>PnL</span>
              <strong className={snapshot.pnl > 0 ? "value-positive" : snapshot.pnl < 0 ? "value-negative" : ""}>
                ${snapshot.pnl.toFixed(2)}
              </strong>
            </div>
            <div className="stat">
              <span>PnL %</span>
              <strong className={(snapshot.pnl_pct || 0) > 0 ? "value-positive" : (snapshot.pnl_pct || 0) < 0 ? "value-negative" : ""}>
                {snapshot.pnl_pct !== undefined ? `${snapshot.pnl_pct.toFixed(3)}%` : "-"}
              </strong>
            </div>
            <div className="stat">
              <span>Win Rate</span>
              <strong>{`${(snapshot.win_rate * 100).toFixed(1)}%`}</strong>
            </div>
          </div>

          <div className="section-label">LIVE EQUITY CURVE</div>
          <ChartPane points={snapshot.equity_curve || []} />
          <div className="section-label">LIVE PRICE CHART WITH ENTRIES / EXITS / INDICATORS</div>
          <TradeChartPane
            bars={snapshot.price_bars || []}
            markers={snapshot.markers || []}
            indicators={snapshot.indicator_series || {}}
            indicatorColors={snapshot.context?.indicator_colors || {}}
          />
        </>
      )}
    </section>
  );
}
