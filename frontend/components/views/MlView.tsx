"use client";

type MlViewProps = {
  strategyName: string;
  resultText: string;
  onRun: () => void;
};

export function MlView({ strategyName, resultText, onRun }: MlViewProps) {
  return (
    <section className="card panel">
      <div className="panel-head">
        <div>
          <div className="section-label">ML VIEW</div>
          <h3>Optuna Hyperparameter Tuning</h3>
        </div>
        <button className="btn-primary" onClick={onRun}>Run Optimization for {strategyName}</button>
      </div>
      <p className="muted">Using selected strategy: <code>{strategyName}</code></p>
      {!resultText && <p className="muted">Run optimization to see best parameters.</p>}
      {resultText && <pre className="json-box">{resultText}</pre>}
    </section>
  );
}
