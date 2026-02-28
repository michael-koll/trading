"use client";

import type { CSSProperties } from "react";
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
  paramSpecs: { name: string; type: "int" | "float"; default: number }[];
  paramRanges: Record<string, { min: number; max: number; type: "int" | "float" }>;
  optimizedParams?: Record<string, number> | null;
  splitPct: number;
  trainBars: number | null;
  oosBars: number | null;
  cutoffTimestamp: string | null;
  onSelectDataset: (value: string) => void;
  onSymbolChange: (value: string) => void;
  onIntervalChange: (value: string) => void;
  onPeriodChange: (value: string) => void;
  onTrialsChange: (value: number) => void;
  onSeedChange: (value: number) => void;
  onObjectiveChange: (value: "pnl" | "final_value" | "win_rate" | "sharpe_ratio" | "max_drawdown_pct") => void;
  onSplitPctChange: (value: number) => void;
  onParamRangeChange: (name: string, field: "min" | "max", value: number) => void;
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
  paramSpecs,
  paramRanges,
  optimizedParams = null,
  splitPct,
  trainBars,
  oosBars,
  cutoffTimestamp,
  onSelectDataset,
  onSymbolChange,
  onIntervalChange,
  onPeriodChange,
  onTrialsChange,
  onSeedChange,
  onObjectiveChange,
  onSplitPctChange,
  onParamRangeChange,
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
  const splitSliderStyle = { "--split-pct": `${splitPct}%` } as CSSProperties;
  return (
    <section className="card panel backtest-view ml-view">
      <div className="panel-head">
        <div>
          <div className="section-label">ML VIEW</div>
          <h3>Optuna Hyperparameter Tuning</h3>
        </div>
        <button
          className="btn-primary icon-action-btn"
          onClick={onRun}
          disabled={loading}
          aria-label={loading ? "Running optimization" : `Run optimization for ${strategyName}`}
          title={loading ? "Running optimization" : `Run optimization for ${strategyName}`}
        >
          {loading ? (
            <span className="loading-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M8 6L18 12L8 18V6Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
            </svg>
          )}
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
      </div>

      <div className="section-label">STRATEGY PARAMETERS</div>
      {paramSpecs.length === 0 && (
        <p className="muted">No numeric strategy params found in `class ... params`.</p>
      )}
      {paramSpecs.length > 0 && (
        <div className="ml-param-grid">
          {paramSpecs.map((param) => {
            const range = paramRanges[param.name];
            const minValue = range ? range.min : param.default;
            const maxValue = range ? range.max : param.default;
            const step = param.type === "int" ? 1 : 0.01;
            return (
              <article key={param.name} className="ml-param-card">
                <div className="ml-param-head">
                  <strong>{param.name}</strong>
                  <span className="ml-param-meta">
                    <span>{param.type.toUpperCase()}</span>
                    <span>|</span>
                    <span>default {param.default}</span>
                    {optimizedParams && optimizedParams[param.name] !== undefined && (
                      <>
                        <span>|</span>
                        <span className="ml-param-best-inline">best {optimizedParams[param.name]}</span>
                      </>
                    )}
                  </span>
                </div>
                <div className="ml-param-range">
                  <label>
                    <span>Min</span>
                    <input
                      className="input-modern"
                      type="number"
                      step={step}
                      value={minValue}
                      onChange={(e) => onParamRangeChange(param.name, "min", Number(e.target.value || 0))}
                      disabled={loading}
                    />
                  </label>
                  <label>
                    <span>Max</span>
                    <input
                      className="input-modern"
                      type="number"
                      step={step}
                      value={maxValue}
                      onChange={(e) => onParamRangeChange(param.name, "max", Number(e.target.value || 0))}
                      disabled={loading}
                    />
                  </label>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <div className="section-label">BAR SPLIT</div>
      <div className="ml-split-card">
        <div className="ml-split-row">
          <span className="ml-split-value">{splitPct}%</span>
          <input
            type="range"
            min={1}
            max={99}
            step={1}
            value={splitPct}
            style={splitSliderStyle}
            onChange={(e) => onSplitPctChange(Number(e.target.value || 70))}
            disabled={loading}
          />
        </div>
        <div className="ml-split-bars">
          <span>IS Bars: {trainBars ?? "-"}</span>
          <span>OOS Bars: {oosBars ?? "-"}</span>
          <span>Cutoff Timestamp: {cutoffTimestamp || "-"}</span>
        </div>
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
              {paramSpecs.map((param) => {
                const range = paramRanges[param.name];
                return (
                  <tr key={`ctx-${param.name}`}>
                    <td>{param.name} Range</td>
                    <td>{range ? `${range.min} - ${range.max}` : "-"}</td>
                  </tr>
                );
              })}
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
