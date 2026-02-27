"use client";

export type Strategy = {
  name: string;
  path: string;
  updated_at: string;
};

type SidebarProps = {
  strategies: Strategy[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
};

export function Sidebar({ strategies, selectedPath, onSelect }: SidebarProps) {
  return (
    <aside className="sidebar card">
      <div className="section-label">WORKSPACE</div>
      <h2>Strategies</h2>
      <div className="file-list">
        {strategies.length === 0 && <p className="muted">No strategy files yet.</p>}
        {strategies.map((item) => (
          <button
            key={item.path}
            className={`file-item ${selectedPath === item.path ? "active" : ""}`}
            onClick={() => onSelect(item.path)}
          >
            <span>{item.path}</span>
          </button>
        ))}
      </div>
      <div className="sidebar-footer muted">
        Datasets and backtests are saved in backend `data/`.
      </div>
    </aside>
  );
}
