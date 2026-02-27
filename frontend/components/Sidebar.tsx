"use client";

import { useEffect, useMemo, useState } from "react";

export type Strategy = {
  name: string;
  path: string;
  updated_at: string;
};

type SidebarProps = {
  strategies: Strategy[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
  onCreate: () => Promise<string>;
  onRename: (oldPath: string, newPath: string) => Promise<void>;
  onDelete: (path: string) => Promise<void>;
};

const FAVORITES_KEY = "strategy_favorites_v1";

function baseName(path: string): string {
  return path.split("/").pop() || path;
}

export function Sidebar({ strategies, selectedPath, onSelect, onCreate, onRename, onDelete }: SidebarProps) {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [editingPath, setEditingPath] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(FAVORITES_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setFavorites(parsed.filter((v) => typeof v === "string"));
      }
    } catch {
      setFavorites([]);
    }
  }, []);

  useEffect(() => {
    if (strategies.length === 0) return;
    const valid = new Set(strategies.map((s) => s.path));
    const next = favorites.filter((p) => valid.has(p));
    if (next.length !== favorites.length) {
      setFavorites(next);
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(next));
    }
  }, [strategies, favorites]);

  const favoriteSet = useMemo(() => new Set(favorites), [favorites]);
  const favoriteItems = strategies.filter((s) => favoriteSet.has(s.path));
  const otherItems = strategies.filter((s) => !favoriteSet.has(s.path));

  function toggleFavorite(path: string) {
    const next = favoriteSet.has(path) ? favorites.filter((p) => p !== path) : [path, ...favorites];
    setFavorites(next);
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(next));
  }

  async function handleCreate() {
    try {
      const createdPath = await onCreate();
      onSelect(createdPath);
    } catch (err) {
      alert(String((err as Error).message || err));
    }
  }

  async function commitRename() {
    if (!editingPath) return;
    const oldPath = editingPath;
    const oldName = baseName(oldPath);
    const clean = editingName.trim();
    setEditingPath(null);
    if (!clean || clean === oldName) return;
    const newName = clean.endsWith(".py") ? clean : `${clean}.py`;
    const dir = oldPath.includes("/") ? oldPath.slice(0, oldPath.lastIndexOf("/") + 1) : "";
    const newPath = `${dir}${newName}`;
    try {
      await onRename(oldPath, newPath);
      if (selectedPath === oldPath) onSelect(newPath);
      if (favoriteSet.has(oldPath)) {
        const next = favorites.map((p) => (p === oldPath ? newPath : p));
        setFavorites(next);
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(next));
      }
    } catch (err) {
      alert(String((err as Error).message || err));
    }
  }

  function renderItem(item: Strategy) {
    const isEditing = editingPath === item.path;
    return (
      <div
        key={item.path}
        className={`file-item-row ${selectedPath === item.path ? "active" : ""}`}
      >
        <button
          className={`file-star ${favoriteSet.has(item.path) ? "active" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            toggleFavorite(item.path);
          }}
          title={favoriteSet.has(item.path) ? "Unfavorite" : "Favorite"}
        >
          {favoriteSet.has(item.path) ? "★" : "☆"}
        </button>
        {!isEditing ? (
          <>
            <button
              className={`file-item ${selectedPath === item.path ? "active" : ""}`}
              onClick={() => onSelect(item.path)}
              onDoubleClick={() => {
                setEditingPath(item.path);
                setEditingName(baseName(item.path));
              }}
              title={item.path}
            >
              <span>{item.path}</span>
            </button>
            <button
              className="file-delete"
              title="Delete strategy"
              onClick={async (e) => {
                e.stopPropagation();
                const fileName = baseName(item.path);
                const typed = prompt(`Type the script name to delete:\n${fileName}`, "");
                if (typed === null) return;
                if (typed.trim() !== fileName) {
                  alert("Name mismatch. File was not deleted.");
                  return;
                }
                try {
                  await onDelete(item.path);
                } catch (err) {
                  alert(String((err as Error).message || err));
                }
              }}
            >
              x
            </button>
          </>
        ) : (
          <input
            className="file-rename-input input-modern"
            value={editingName}
            autoFocus
            onChange={(e) => setEditingName(e.target.value)}
            onBlur={() => commitRename().catch(console.error)}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename().catch(console.error);
              if (e.key === "Escape") setEditingPath(null);
            }}
          />
        )}
      </div>
    );
  }

  return (
    <aside className="sidebar card">
      <div className="section-label">WORKSPACE</div>
      <div className="sidebar-head">
        <h2>Strategies</h2>
        <button className="sidebar-plus" onClick={handleCreate} title="New strategy">
          +
        </button>
      </div>

      <div className="section-label">FAVORITES</div>
      <div className="file-list sidebar-block sidebar-block-favorites">
        {favoriteItems.length === 0 && <p className="muted">No favorites yet.</p>}
        {favoriteItems.map(renderItem)}
      </div>

      <div className="section-label">ALL STRATEGIES</div>
      <div className="file-list sidebar-block sidebar-block-main">
        {strategies.length === 0 && <p className="muted">No strategy files yet.</p>}
        {otherItems.map(renderItem)}
      </div>

      <div className="sidebar-footer muted">
        Datasets and backtests are saved in backend `data/`.
      </div>
    </aside>
  );
}
