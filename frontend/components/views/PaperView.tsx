"use client";

type PaperViewProps = {
  strategyName: string;
  sessionId: string;
  error: string;
  onStartLocal: () => void;
  onStartAlpaca: () => void;
};

export function PaperView({ strategyName, sessionId, error, onStartLocal, onStartAlpaca }: PaperViewProps) {
  return (
    <section className="card panel">
      <div className="panel-head">
        <div>
          <div className="section-label">LIVE PAPER TRADING VIEW</div>
          <h3>Paper Trading Session</h3>
        </div>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onStartLocal}>Start Local Paper</button>
          <button className="btn-secondary" onClick={onStartAlpaca}>Start Alpaca Paper</button>
        </div>
      </div>
      <p className="muted">Running strategy: <code>{strategyName}</code></p>
      <p className="muted">Session id: <code>{sessionId || "not started"}</code></p>
      {error && <p className="muted">Alpaca error: {error}</p>}
      <p className="muted">Local paper mode is key-free. Alpaca paper mode requires `ALPACA_API_KEY` and `ALPACA_API_SECRET`.</p>
    </section>
  );
}
