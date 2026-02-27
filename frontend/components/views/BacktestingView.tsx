"use client";

import { useEffect, useMemo, useState } from "react";
import { ChartPane } from "@/components/ChartPane";
import { TradeChartPane } from "@/components/TradeChartPane";
import { apiGet } from "@/lib/api";

type DatasetItem = {
  name: string;
  path: string;
  rows: number | null;
  start: string | null;
  end: string | null;
  columns: string[];
};

type BacktestContext = {
  strategy_path?: string;
  symbol?: string;
  market?: string;
  exchange?: string | null;
  interval?: string;
  period?: string;
  dataset_path?: string | null;
  dataset_source?: string;
  start_time?: string | null;
  end_time?: string | null;
  indicator_labels?: Record<string, string>;
  indicator_colors?: Record<string, string>;
  indicator_warnings?: string[];
};

type BacktestAnalytics = {
  performance?: Record<string, number>;
  risk?: Record<string, number>;
  trades?: Record<string, number>;
};

type BacktestResult = {
  final_value: number;
  pnl: number;
  pnl_pct?: number;
  win_rate: number;
  bars?: number;
  context?: BacktestContext;
  analytics?: BacktestAnalytics;
  analyzers_raw?: Record<string, unknown>;
  equity_curve: { time: string; value: number }[];
  price_bars?: { time: string; open: number; high: number; low: number; close: number }[];
  markers?: { time: string; price: number; side: "buy" | "sell" }[];
  indicator_series?: Record<string, { time: string; value: number }[]>;
};

type BacktestingViewProps = {
  strategyName: string;
  result: BacktestResult | null;
  datasets: DatasetItem[];
  selectedDataset: string;
  symbol: string;
  market: string;
  exchange: string;
  interval: string;
  period: string;
  startCash: number;
  onSelectDataset: (value: string) => void;
  onSymbolChange: (value: string) => void;
  onMarketChange: (value: string) => void;
  onExchangeChange: (value: string) => void;
  onIntervalChange: (value: string) => void;
  onPeriodChange: (value: string) => void;
  onStartCashChange: (value: number) => void;
  onRun: () => void;
};

type SymbolSearchItem = {
  symbol: string;
  name: string;
  type: string;
  exchange: string;
};

const PERIOD_OPTIONS = [
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "60d", label: "60 Days" },
  { value: "6mo", label: "6 Months" },
  { value: "1y", label: "1 Year" },
];

const INTERVAL_OPTIONS = [
  { value: "1m", label: "1 Minute" },
  { value: "5m", label: "5 Minutes" },
  { value: "15m", label: "15 Minutes" },
  { value: "1h", label: "1 Hour" },
  { value: "1d", label: "1 Day" },
];

function fmt(v: unknown): string {
  if (v === null || v === undefined || Number.isNaN(v as number)) return "-";
  if (typeof v === "number") return Number.isInteger(v) ? `${v}` : v.toFixed(6);
  return String(v);
}

const METRIC_LABELS: Record<string, string> = {
  start_cash: "Starting Cash",
  final_value: "Final Portfolio Value",
  pnl: "Net Profit / Loss",
  pnl_pct: "Net Profit / Loss (%)",
  returns_rtot: "Total Return (Log)",
  returns_rnorm: "Normalized Return",
  returns_rnorm100: "Annualized Return (%)",
  sharpe_ratio: "Sharpe Ratio",
  sqn: "System Quality Number (SQN)",
  max_drawdown_pct: "Max Drawdown (%)",
  max_drawdown_money: "Max Drawdown (Currency)",
  current_drawdown_pct: "Current Drawdown (%)",
  current_drawdown_money: "Current Drawdown (Currency)",
  total_closed: "Closed Trades",
  won: "Winning Trades",
  lost: "Losing Trades",
  win_rate_pct: "Win Rate (%)",
  avg_net_pnl: "Average Net P/L per Trade",
  total_net_pnl: "Total Net P/L",
  avg_gross_pnl: "Average Gross P/L per Trade",
  total_gross_pnl: "Total Gross P/L",
};

function metricLabel(key: string): string {
  if (METRIC_LABELS[key]) return METRIC_LABELS[key];
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

const PROFIT_LOSS_KEYS = new Set([
  "pnl",
  "pnl_pct",
  "returns_rtot",
  "returns_rnorm",
  "returns_rnorm100",
  "sharpe_ratio",
  "sqn",
  "avg_net_pnl",
  "total_net_pnl",
  "avg_gross_pnl",
  "total_gross_pnl",
]);

function profitLossClass(key: string, value: unknown): string {
  if (!PROFIT_LOSS_KEYS.has(key) || typeof value !== "number" || Number.isNaN(value)) return "";
  if (value > 0) return "value-positive";
  if (value < 0) return "value-negative";
  return "";
}

export function BacktestingView({
  strategyName,
  result,
  datasets,
  selectedDataset,
  symbol,
  market,
  exchange,
  interval,
  period,
  startCash,
  onSelectDataset,
  onSymbolChange,
  onMarketChange,
  onExchangeChange,
  onIntervalChange,
  onPeriodChange,
  onStartCashChange,
  onRun,
}: BacktestingViewProps) {
  const context = result?.context;
  const analytics = result?.analytics;
  const [symbolQuery, setSymbolQuery] = useState(symbol);
  const [symbolResults, setSymbolResults] = useState<SymbolSearchItem[]>([]);
  const [symbolOpen, setSymbolOpen] = useState(false);
  const [symbolLoading, setSymbolLoading] = useState(false);

  useEffect(() => {
    setSymbolQuery(symbol);
  }, [symbol]);

  const trimmedQuery = useMemo(() => symbolQuery.trim(), [symbolQuery]);

  useEffect(() => {
    if (trimmedQuery.length < 1) {
      setSymbolResults([]);
      return;
    }

    const timer = setTimeout(() => {
      setSymbolLoading(true);
      apiGet<SymbolSearchItem[]>(`/symbols/search?q=${encodeURIComponent(trimmedQuery)}&limit=8`)
        .then((items) => setSymbolResults(items))
        .catch(() => setSymbolResults([]))
        .finally(() => setSymbolLoading(false));
    }, 250);

    return () => clearTimeout(timer);
  }, [trimmedQuery]);

  return (
    <section className="card panel backtest-view">
      <div className="panel-head">
        <div>
          <div className="section-label">BACKTESTING VIEW</div>
          <h3>Backtest Runner</h3>
        </div>
        <button className="btn-primary" onClick={onRun}>Run Backtest</button>
      </div>

      <div className="backtest-controls">
        <label>
          <span>Dataset</span>
          <div className="select-wrap select-modern">
            <select value={selectedDataset} onChange={(e) => onSelectDataset(e.target.value)}>
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
          <div className="symbol-search">
            <input
              className="input-modern"
              value={symbolQuery}
              onFocus={() => setSymbolOpen(true)}
              onBlur={() => setTimeout(() => setSymbolOpen(false), 120)}
              onChange={(e) => {
                const value = e.target.value;
                setSymbolQuery(value);
                onSymbolChange(value);
              }}
              placeholder="Search symbol (e.g. AAPL, BTC-USD, ^GSPC)"
            />
            {symbolOpen && (symbolLoading || symbolResults.length > 0 || trimmedQuery.length > 0) && (
              <div className="symbol-results">
                {symbolLoading && <div className="symbol-results-hint">Searching...</div>}
                {!symbolLoading && symbolResults.length === 0 && (
                  <div className="symbol-results-hint">No results for "{trimmedQuery}"</div>
                )}
                {symbolResults.map((item) => (
                  <button
                    key={`${item.symbol}-${item.exchange}`}
                    type="button"
                    className="symbol-result-item"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      setSymbolQuery(item.symbol);
                      onSymbolChange(item.symbol);
                      setSymbolOpen(false);
                    }}
                  >
                    <span className="symbol-main">
                      <strong>{item.symbol}</strong>
                      <em>{item.name}</em>
                    </span>
                    <span className="symbol-meta">{[item.type, item.exchange].filter(Boolean).join(" · ")}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </label>
        <label>
          <span>Market</span>
          <input
            className="input-modern"
            value={market}
            onChange={(e) => onMarketChange(e.target.value)}
            placeholder="stocks / crypto"
          />
        </label>
        <label>
          <span>Exchange</span>
          <input
            className="input-modern"
            value={exchange}
            onChange={(e) => onExchangeChange(e.target.value)}
            placeholder="NASDAQ / BINANCE"
          />
        </label>
        <label>
          <span>Interval</span>
          <div className="select-wrap select-modern">
            <select value={interval} onChange={(e) => onIntervalChange(e.target.value)}>
              {INTERVAL_OPTIONS.map((opt) => (
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
            <select value={period} onChange={(e) => onPeriodChange(e.target.value)}>
              {PERIOD_OPTIONS.map((opt) => (
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
          <span>Start Cash</span>
          <input
            className="input-modern"
            type="number"
            value={startCash}
            onChange={(e) => onStartCashChange(Number(e.target.value || 0))}
            min={0}
            step={100}
          />
        </label>
      </div>
      <div className="stats-row">
        <div className="stat"><span>Final Value</span><strong className={result && (result.final_value - startCash) > 0 ? "value-positive" : result && (result.final_value - startCash) < 0 ? "value-negative" : ""}>{result ? `$${result.final_value.toFixed(2)}` : "-"}</strong></div>
        <div className="stat"><span>PnL</span><strong className={result && result.pnl > 0 ? "value-positive" : result && result.pnl < 0 ? "value-negative" : ""}>{result ? `$${result.pnl.toFixed(2)}` : "-"}</strong></div>
        <div className="stat"><span>PnL %</span><strong className={result && (result.pnl_pct || 0) > 0 ? "value-positive" : result && (result.pnl_pct || 0) < 0 ? "value-negative" : ""}>{result?.pnl_pct !== undefined ? `${result.pnl_pct.toFixed(3)}%` : "-"}</strong></div>
        <div className="stat"><span>Win Rate</span><strong>{result ? `${(result.win_rate * 100).toFixed(1)}%` : "-"}</strong></div>
      </div>

      {result && (
        <>
          <div className="section-label">EQUITY CURVE</div>
          <ChartPane points={result.equity_curve} />
          <div className="section-label">PRICE CHART (TRADINGVIEW STYLE) WITH ENTRIES / EXITS</div>
          <TradeChartPane
            bars={result.price_bars || []}
            markers={result.markers || []}
            indicators={result.indicator_series || {}}
            indicatorColors={context?.indicator_colors || {}}
          />
          {(context?.indicator_labels && Object.keys(context.indicator_labels).length > 0) && (
            <p className="muted">
              Indicators on chart: {Object.values(context.indicator_labels).join(", ")}
            </p>
          )}
          {(context?.indicator_warnings && context.indicator_warnings.length > 0) && (
            <p className="muted">Indicator warnings: {context.indicator_warnings.join(" | ")}</p>
          )}
        </>
      )}

      <div className="detail-grid">
        <div className="detail-card">
          <div className="section-label">RUN CONTEXT</div>
          <table className="metric-table">
            <tbody>
              <tr><td>Strategy File</td><td>{context?.strategy_path || strategyName}</td></tr>
              <tr><td>Dataset Source</td><td>{context?.dataset_source || "-"}</td></tr>
              <tr><td>Dataset Path</td><td>{context?.dataset_path || "(live)"}</td></tr>
              <tr><td>Symbol / Pair</td><td>{context?.symbol || symbol}</td></tr>
              <tr><td>Market</td><td>{context?.market || market}</td></tr>
              <tr><td>Exchange</td><td>{context?.exchange || exchange || "-"}</td></tr>
              <tr><td>Interval</td><td>{context?.interval || interval}</td></tr>
              <tr><td>Period</td><td>{context?.period || period}</td></tr>
              <tr><td>Bars Used</td><td>{fmt(result?.bars)}</td></tr>
              <tr><td>Start Time</td><td>{context?.start_time || "-"}</td></tr>
              <tr><td>End Time</td><td>{context?.end_time || "-"}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="detail-card">
          <div className="section-label">PERFORMANCE & RISK</div>
          <table className="metric-table">
            <tbody>
              {Object.entries(analytics?.performance || {}).map(([k, v]) => (
                <tr key={`p-${k}`}><td>{metricLabel(k)}</td><td className={profitLossClass(k, v)}>{fmt(v)}</td></tr>
              ))}
              {Object.entries(analytics?.risk || {}).map(([k, v]) => (
                <tr key={`r-${k}`}><td>{metricLabel(k)}</td><td>{fmt(v)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="detail-card">
          <div className="section-label">TRADE ANALYTICS</div>
          <table className="metric-table">
            <tbody>
              {Object.entries(analytics?.trades || {}).map(([k, v]) => (
                <tr key={`t-${k}`}><td>{metricLabel(k)}</td><td className={profitLossClass(k, v)}>{fmt(v)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="detail-card">
          <div className="section-label">AVAILABLE DATASETS</div>
          <table className="metric-table">
            <tbody>
              {datasets.slice(0, 10).map((d) => (
                <tr key={d.path}><td>{d.name}</td><td>{d.rows ?? "-"} rows</td></tr>
              ))}
              {datasets.length === 0 && <tr><td colSpan={2}>No local datasets found.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="detail-card">
        <div className="section-label">RAW BACKTRADER ANALYZER OUTPUT</div>
        <pre className="json-box">{JSON.stringify(result?.analyzers_raw || {}, null, 2)}</pre>
      </div>
    </section>
  );
}
