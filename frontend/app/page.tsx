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
type ObjectiveKey = "pnl" | "final_value" | "win_rate" | "sharpe_ratio" | "max_drawdown_pct";
type PaperStateResponse = {
  session: {
    session_id: string;
    strategy_path: string;
    symbol: string;
    interval: string;
    period: string;
    dataset_path?: string | null;
    market?: string;
    exchange?: string | null;
    cash: number;
    position: number;
    status: string;
    broker: string;
    updated_at?: string;
  };
  snapshot: BacktestResult;
};
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
  const [mlBestResult, setMlBestResult] = useState<BacktestResult | null>(null);
  const [optuna, setOptuna] = useState<string>("");
  const [mlLoading, setMlLoading] = useState<boolean>(false);
  const [mlError, setMlError] = useState<string>("");
  const [mlTrials, setMlTrials] = useState<number>(8);
  const [mlSeed, setMlSeed] = useState<number>(42);
  const [mlObjective, setMlObjective] = useState<ObjectiveKey>("pnl");
  const [mlFastMin, setMlFastMin] = useState<number>(5);
  const [mlFastMax, setMlFastMax] = useState<number>(40);
  const [mlSlowMin, setMlSlowMin] = useState<number>(20);
  const [mlSlowMax, setMlSlowMax] = useState<number>(120);
  const [mlRiskMin, setMlRiskMin] = useState<number>(0.1);
  const [mlRiskMax, setMlRiskMax] = useState<number>(3.0);
  const [paperSession, setPaperSession] = useState<string>("");
  const [paperError, setPaperError] = useState<string>("");
  const [paperState, setPaperState] = useState<PaperStateResponse | null>(null);
  const [paperLoading, setPaperLoading] = useState<boolean>(false);
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
    if (files.length === 0) {
      setSelectedPath(null);
      return;
    }
    if (!selectedPath || !files.some((f) => f.path === selectedPath)) {
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

  async function createStrategy(): Promise<string> {
    const res = await apiPost<{ path: string }>("/strategies/create", { path: "new_strategy.py" });
    await reloadStrategies();
    return res.path;
  }

  async function renameStrategy(oldPath: string, newPath: string) {
    await apiPost("/strategies/rename", { old_path: oldPath, new_path: newPath });
    await reloadStrategies();
  }

  async function deleteStrategy(path: string) {
    await apiPost("/strategies/delete", { path });
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
    setMlLoading(true);
    setMlError("");
    setMlBestResult(null);
    try {
      const res = await apiPost<{
        best_value: number;
        best_params: Record<string, number>;
      }>("/optimize/run", {
        strategy_path: selectedPath,
        symbol,
        interval,
        period,
        dataset_path: selectedDataset || null,
        n_trials: mlTrials,
        seed: mlSeed,
        objective: mlObjective,
        ranges: {
          fast_period: { min: mlFastMin, max: mlFastMax },
          slow_period: { min: mlSlowMin, max: mlSlowMax },
          risk_pct: { min: mlRiskMin, max: mlRiskMax },
        },
      });
      setOptuna(JSON.stringify(res, null, 2));

      const bestRun = await apiPost<BacktestResult>("/backtests/run", {
        strategy_path: selectedPath,
        symbol,
        market,
        exchange,
        interval,
        period,
        start_cash: startCash,
        dataset_path: selectedDataset || null,
        params: res.best_params,
      });
      setMlBestResult(bestRun);
    } catch (err) {
      setMlError(String((err as Error).message || err));
    } finally {
      setMlLoading(false);
    }
  }

  async function startPaper(broker: "local" | "alpaca" = "local") {
    if (!selectedPath) return;
    setPaperError("");
    setPaperState(null);
    const res = await apiPost<{ session_id: string }>("/paper/start", {
      strategy_path: selectedPath,
      symbol,
      interval,
      period,
      dataset_path: selectedDataset || null,
      market,
      exchange,
      starting_cash: startCash,
      broker,
    });
    setPaperSession(res.session_id);
  }

  async function refreshPaperState() {
    if (!paperSession) return;
    setPaperLoading(true);
    try {
      const state = await apiGet<PaperStateResponse>(`/paper/sessions/${paperSession}/state`);
      setPaperState(state);
      setPaperError("");
    } catch (err) {
      setPaperError(String((err as Error).message || err));
    } finally {
      setPaperLoading(false);
    }
  }

  useEffect(() => {
    if (view !== "paper" || !paperSession) return;
    refreshPaperState().catch((err) => setPaperError(String((err as Error).message || err)));
    const timer = setInterval(() => {
      refreshPaperState().catch((err) => setPaperError(String((err as Error).message || err)));
    }, 10000);
    return () => clearInterval(timer);
  }, [view, paperSession]);

  return (
    <main className="shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <div className="ambient ambient-c" />

      <Sidebar
        strategies={strategies}
        selectedPath={selectedPath}
        onSelect={setSelectedPath}
        onCreate={createStrategy}
        onRename={renameStrategy}
        onDelete={deleteStrategy}
      />

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
            <MlView
              strategyName={activeName}
              resultText={optuna}
              loading={mlLoading}
              error={mlError}
              datasets={datasets}
              selectedDataset={selectedDataset}
              symbol={symbol}
              interval={interval}
              period={period}
              trials={mlTrials}
              onTrialsChange={setMlTrials}
              onSelectDataset={setSelectedDataset}
              onSymbolChange={setSymbol}
              onIntervalChange={setInterval}
              onPeriodChange={setPeriod}
              seed={mlSeed}
              onSeedChange={setMlSeed}
              objective={mlObjective}
              onObjectiveChange={setMlObjective}
              bestRun={mlBestResult}
              fastMin={mlFastMin}
              fastMax={mlFastMax}
              onFastMinChange={setMlFastMin}
              onFastMaxChange={setMlFastMax}
              slowMin={mlSlowMin}
              slowMax={mlSlowMax}
              onSlowMinChange={setMlSlowMin}
              onSlowMaxChange={setMlSlowMax}
              riskMin={mlRiskMin}
              riskMax={mlRiskMax}
              onRiskMinChange={setMlRiskMin}
              onRiskMaxChange={setMlRiskMax}
              onRun={runOptimization}
            />
          )}

          {view === "paper" && (
            <PaperView
              strategyName={activeName}
              sessionId={paperSession}
              error={paperError}
              loading={paperLoading}
              state={paperState}
              onStartLocal={() => startPaper("local")}
              onStartAlpaca={() => startPaper("alpaca").catch((err) => setPaperError(String(err.message || err)))}
              onRefresh={() => refreshPaperState().catch((err) => setPaperError(String((err as Error).message || err)))}
            />
          )}
        </div>
      </section>
    </main>
  );
}
