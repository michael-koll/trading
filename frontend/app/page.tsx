"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Sidebar, Strategy } from "@/components/Sidebar";
import { CodingView } from "@/components/views/CodingView";
import { BacktestingView } from "@/components/views/BacktestingView";
import { MlView } from "@/components/views/MlView";
import { PaperView } from "@/components/views/PaperView";

type BacktestResult = {
  run_id: string;
  final_value: number;
  pnl: number;
  pnl_pct?: number;
  win_rate: number;
  bars?: number;
  context?: {
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
  analytics?: {
    performance?: Record<string, number>;
    risk?: Record<string, number>;
    trades?: Record<string, number>;
  };
  analyzers_raw?: Record<string, unknown>;
  equity_curve: { time: string; value: number }[];
  price_bars?: { time: string; open: number; high: number; low: number; close: number }[];
  markers?: { time: string; price: number; side: "buy" | "sell" }[];
  indicator_series?: Record<string, { time: string; value: number }[]>;
};

type WorkspaceView = "coding" | "backtesting" | "ml" | "paper";
type DatasetItem = {
  name: string;
  path: string;
  rows: number | null;
  start: string | null;
  end: string | null;
  columns: string[];
};

export default function HomePage() {
  const [view, setView] = useState<WorkspaceView>("coding");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [optuna, setOptuna] = useState<string>("");
  const [paperSession, setPaperSession] = useState<string>("");
  const [paperError, setPaperError] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [symbol, setSymbol] = useState<string>("AAPL");
  const [market, setMarket] = useState<string>("stocks");
  const [exchange, setExchange] = useState<string>("NASDAQ");
  const [interval, setInterval] = useState<string>("1m");
  const [period, setPeriod] = useState<string>("7d");
  const [startCash, setStartCash] = useState<number>(10000);

  async function reloadStrategies() {
    const files = await apiGet<Strategy[]>("/strategies");
    setStrategies(files);
    if (!selectedPath && files.length > 0) {
      setSelectedPath(files[0].path);
    }
  }

  useEffect(() => {
    reloadStrategies().catch(console.error);
    apiGet<DatasetItem[]>("/datasets").then(setDatasets).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedPath) return;
    apiGet<{ content: string }>(`/strategies/${selectedPath}`)
      .then((res) => setCode(res.content))
      .catch(console.error);
  }, [selectedPath]);

  useEffect(() => {
    if (view !== "backtesting") return;
    apiGet<DatasetItem[]>("/datasets").then(setDatasets).catch(console.error);
  }, [view]);

  const activeName = selectedPath || "Select strategy";
  const activeFileName = selectedPath ? selectedPath.split("/").pop() || selectedPath : "no_strategy.py";

  async function saveStrategy() {
    if (!selectedPath) return;
    await apiPost("/strategies", { path: selectedPath, content: code });
    await reloadStrategies();
  }

  async function runBacktest() {
    if (!selectedPath) return;
    const backtest = await apiPost<BacktestResult>("/backtests/run", {
      strategy_path: selectedPath,
      symbol,
      market,
      exchange,
      interval,
      period,
      start_cash: startCash,
      dataset_path: selectedDataset || null,
    });
    setResult(backtest);
  }

  async function runOptimization() {
    if (!selectedPath) return;
    const res = await apiPost<{ best_value: number; best_params: Record<string, number> }>("/optimize/run", {
      strategy_path: selectedPath,
      symbol,
      interval,
      period,
      dataset_path: selectedDataset || null,
      n_trials: 20,
    });
    setOptuna(JSON.stringify(res, null, 2));
  }

  async function startPaper(broker: "local" | "alpaca" = "local") {
    if (!selectedPath) return;
    setPaperError("");
    const res = await apiPost<{ session_id: string }>("/paper/start", {
      strategy_path: selectedPath,
      symbol,
      interval,
      starting_cash: startCash,
      broker,
    });
    setPaperSession(res.session_id);
  }

  return (
    <main className="shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <div className="ambient ambient-c" />

      <Sidebar strategies={strategies} selectedPath={selectedPath} onSelect={setSelectedPath} />

      <section className="content">
        <header className="taskbar">
          <nav className="view-switch" aria-label="Workspace Views">
            <button className={view === "coding" ? "active" : ""} onClick={() => setView("coding")}>Coding</button>
            <button className={view === "backtesting" ? "active" : ""} onClick={() => setView("backtesting")}>Backtesting</button>
            <button className={view === "ml" ? "active" : ""} onClick={() => setView("ml")}>ML Optimization</button>
            <button className={view === "paper" ? "active" : ""} onClick={() => setView("paper")}>Live Paper Trading</button>
          </nav>
          <div className="taskbar-strategy" title={activeName}>
            <span className="taskbar-strategy-label">Strategy</span>
            <strong>{activeFileName}</strong>
          </div>
        </header>

        <div className="view-stage">
          {view === "coding" && (
            <CodingView title={activeName} code={code} onChange={setCode} onSave={saveStrategy} />
          )}

          {view === "backtesting" && (
            <BacktestingView
              strategyName={activeName}
              result={result}
              datasets={datasets}
              selectedDataset={selectedDataset}
              symbol={symbol}
              market={market}
              exchange={exchange}
              interval={interval}
              period={period}
              startCash={startCash}
              onSelectDataset={setSelectedDataset}
              onSymbolChange={setSymbol}
              onMarketChange={setMarket}
              onExchangeChange={setExchange}
              onIntervalChange={setInterval}
              onPeriodChange={setPeriod}
              onStartCashChange={setStartCash}
              onRun={runBacktest}
            />
          )}

          {view === "ml" && (
            <MlView strategyName={activeName} resultText={optuna} onRun={runOptimization} />
          )}

          {view === "paper" && (
            <PaperView
              strategyName={activeName}
              sessionId={paperSession}
              error={paperError}
              onStartLocal={() => startPaper("local")}
              onStartAlpaca={() => startPaper("alpaca").catch((err) => setPaperError(String(err.message || err)))}
            />
          )}
        </div>
      </section>
    </main>
  );
}
