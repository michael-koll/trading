"use client";

import { ChartPane } from "@/components/ChartPane";
import { TradeChartPane } from "@/components/TradeChartPane";

type MlBacktestResult = {
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

type MlViewProps = {
  strategyName: string;
  resultText: string;
  loading?: boolean;
  error?: string;
  bestRun: MlBacktestResult | null;
  datasets: { name: string; path: string }[];
  selectedDataset: string;
  symbol: string;
  interval: string;
  period: string;
  trials: number;
  seed: number;
  objective: "pnl" | "final_value" | "win_rate" | "sharpe_ratio" | "max_drawdown_pct";
  fastMin: number;
  fastMax: number;
  slowMin: number;
  slowMax: number;
  riskMin: number;
  riskMax: number;
  onSelectDataset: (value: string) => void;
  onSymbolChange: (value: string) => void;
  onIntervalChange: (value: string) => void;
  onPeriodChange: (value: string) => void;
  onTrialsChange: (value: number) => void;
  onSeedChange: (value: number) => void;
  onObjectiveChange: (value: "pnl" | "final_value" | "win_rate" | "sharpe_ratio" | "max_drawdown_pct") => void;
  onFastMinChange: (value: number) => void;
  onFastMaxChange: (value: number) => void;
  onSlowMinChange: (value: number) => void;
  onSlowMaxChange: (value: number) => void;
  onRiskMinChange: (value: number) => void;
  onRiskMaxChange: (value: number) => void;
  onRun: () => void;
};

export function MlView({
  strategyName,
  resultText,
  loading = false,
  error = "",
  bestRun,
  datasets,
  selectedDataset,
  symbol,
  interval,
  period,
  trials,
  seed,
  objective,
  fastMin,
  fastMax,
  slowMin,
  slowMax,
  riskMin,
  riskMax,
  onSelectDataset,
  onSymbolChange,
  onIntervalChange,
  onPeriodChange,
  onTrialsChange,
  onSeedChange,
  onObjectiveChange,
  onFastMinChange,
  onFastMaxChange,
  onSlowMinChange,
  onSlowMaxChange,
  onRiskMinChange,
  onRiskMaxChange,
  onRun,
}: MlViewProps) {
  const intervalOptions = [
    { value: "1m", label: "1 Minute" },
    { value: "5m", label: "5 Minutes" },
    { value: "15m", label: "15 Minutes" },
    { value: "1h", label: "1 Hour" },
    { value: "1d", label: "1 Day" },
  ];
  const periodOptions = [
    { value: "7d", label: "7 Days" },
    { value: "30d", label: "30 Days" },
    { value: "60d", label: "60 Days" },
    { value: "6mo", label: "6 Months" },
    { value: "1y", label: "1 Year" },
  ];

  return (
    <section className="card panel backtest-view ml-view">
      <div className="panel-head">
        <div>
          <div className="section-label">ML VIEW</div>
          <h3>Optuna Hyperparameter Tuning</h3>
        </div>
        <button className="btn-primary" onClick={onRun} disabled={loading}>
          {loading ? "Running..." : `Run Optimization for ${strategyName}`}
        </button>
      </div>

      <div className="section-label">DATA SETTINGS</div>
      <div className="backtest-controls ml-controls">
        <label>
          <span>Dataset</span>
          <div className="select-wrap select-modern">
            <select value={selectedDataset} onChange={(e) => onSelectDataset(e.target.value)} disabled={loading}>
              <option value="">Live source (yfinance)</option>
              {datasets.map((d) => (
                <option key={d.path} value={d.path}>{d.name}</option>
              ))}
            </select>
            <span className="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M5.5 7.5L10 12l4.5-4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </div>
        </label>
        <label>
          <span>Symbol / Pair</span>
          <input className="input-modern" value={symbol} onChange={(e) => onSymbolChange(e.target.value)} disabled={loading} />
        </label>
        <label>
          <span>Interval</span>
          <div className="select-wrap select-modern">
            <select value={interval} onChange={(e) => onIntervalChange(e.target.value)} disabled={loading}>
              {intervalOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <span className="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M5.5 7.5L10 12l4.5-4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </div>
        </label>
        <label>
          <span>Period</span>
          <div className="select-wrap select-modern">
            <select value={period} onChange={(e) => onPeriodChange(e.target.value)} disabled={loading}>
              {periodOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <span className="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M5.5 7.5L10 12l4.5-4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </div>
        </label>
      </div>

      <div className="section-label">OPTIMIZATION SETTINGS</div>
      <div className="backtest-controls ml-controls">
        <label>
          <span>Objective</span>
          <div className="select-wrap select-modern">
            <select
              value={objective}
              onChange={(e) => onObjectiveChange(e.target.value as MlViewProps["objective"])}
              disabled={loading}
            >
              <option value="pnl">PnL (maximize)</option>
              <option value="final_value">Final Value (maximize)</option>
              <option value="win_rate">Win Rate (maximize)</option>
              <option value="sharpe_ratio">Sharpe Ratio (maximize)</option>
              <option value="max_drawdown_pct">Max Drawdown % (minimize)</option>
            </select>
            <span className="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M5.5 7.5L10 12l4.5-4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </div>
        </label>

        <label>
          <span>Trials</span>
          <input
            className="input-modern"
            type="number"
            min={1}
            max={300}
            value={trials}
            onChange={(e) => onTrialsChange(Math.max(1, Number(e.target.value || 1)))}
            disabled={loading}
          />
        </label>

        <label>
          <span>Seed</span>
          <input
            className="input-modern"
            type="number"
            value={seed}
            onChange={(e) => onSeedChange(Number(e.target.value || 0))}
            disabled={loading}
          />
        </label>

        <label>
          <span>Fast Period Min</span>
          <input className="input-modern" type="number" min={1} value={fastMin} onChange={(e) => onFastMinChange(Number(e.target.value || 1))} disabled={loading} />
        </label>
        <label>
          <span>Fast Period Max</span>
          <input className="input-modern" type="number" min={2} value={fastMax} onChange={(e) => onFastMaxChange(Number(e.target.value || 2))} disabled={loading} />
        </label>
        <label>
          <span>Slow Period Min</span>
          <input className="input-modern" type="number" min={2} value={slowMin} onChange={(e) => onSlowMinChange(Number(e.target.value || 2))} disabled={loading} />
        </label>
        <label>
          <span>Slow Period Max</span>
          <input className="input-modern" type="number" min={3} value={slowMax} onChange={(e) => onSlowMaxChange(Number(e.target.value || 3))} disabled={loading} />
        </label>
        <label>
          <span>Risk % Min</span>
          <input className="input-modern" type="number" min={0.01} step={0.01} value={riskMin} onChange={(e) => onRiskMinChange(Number(e.target.value || 0.01))} disabled={loading} />
        </label>
        <label>
          <span>Risk % Max</span>
          <input className="input-modern" type="number" min={0.02} step={0.01} value={riskMax} onChange={(e) => onRiskMaxChange(Number(e.target.value || 0.02))} disabled={loading} />
        </label>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="detail-grid">
        <div className="detail-card">
          <div className="section-label">RUN CONTEXT</div>
          <table className="metric-table">
            <tbody>
              <tr><td>Strategy File</td><td>{strategyName}</td></tr>
              <tr><td>Dataset</td><td>{selectedDataset || "(live yfinance)"}</td></tr>
              <tr><td>Symbol</td><td>{symbol}</td></tr>
              <tr><td>Interval</td><td>{interval}</td></tr>
              <tr><td>Period</td><td>{period}</td></tr>
              <tr><td>Objective</td><td>{objective}</td></tr>
              <tr><td>Trials</td><td>{trials}</td></tr>
              <tr><td>Seed</td><td>{seed}</td></tr>
              <tr><td>Fast Period Range</td><td>{fastMin} - {fastMax}</td></tr>
              <tr><td>Slow Period Range</td><td>{slowMin} - {slowMax}</td></tr>
              <tr><td>Risk % Range</td><td>{riskMin} - {riskMax}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="detail-card">
          <div className="section-label">OPTIMIZATION OUTPUT</div>
          {!resultText && <p className="muted">Run optimization to see best parameters.</p>}
          {resultText && <pre className="json-box">{resultText}</pre>}
        </div>
      </div>

      {bestRun && (
        <>
          <div className="stats-row">
            <div className="stat">
              <span>Final Value</span>
              <strong className={bestRun.pnl > 0 ? "value-positive" : bestRun.pnl < 0 ? "value-negative" : ""}>
                ${bestRun.final_value.toFixed(2)}
              </strong>
            </div>
            <div className="stat">
              <span>PnL</span>
              <strong className={bestRun.pnl > 0 ? "value-positive" : bestRun.pnl < 0 ? "value-negative" : ""}>
                ${bestRun.pnl.toFixed(2)}
              </strong>
            </div>
            <div className="stat">
              <span>PnL %</span>
              <strong className={(bestRun.pnl_pct || 0) > 0 ? "value-positive" : (bestRun.pnl_pct || 0) < 0 ? "value-negative" : ""}>
                {bestRun.pnl_pct !== undefined ? `${bestRun.pnl_pct.toFixed(3)}%` : "-"}
              </strong>
            </div>
            <div className="stat">
              <span>Win Rate</span>
              <strong>{`${(bestRun.win_rate * 100).toFixed(1)}%`}</strong>
            </div>
          </div>
          <div className="section-label">BEST PARAMS BACKTEST - EQUITY CURVE</div>
          <ChartPane points={bestRun.equity_curve || []} />
          <div className="section-label">BEST PARAMS BACKTEST - PRICE CHART</div>
          <TradeChartPane
            bars={bestRun.price_bars || []}
            markers={bestRun.markers || []}
            indicators={bestRun.indicator_series || {}}
            indicatorColors={bestRun.context?.indicator_colors || {}}
          />
        </>
      )}
    </section>
  );
}
