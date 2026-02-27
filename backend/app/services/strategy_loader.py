from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from app.core.config import STRATEGIES_DIR


def _resolve_strategy_path(rel_path: str) -> Path:
    path = (STRATEGIES_DIR / rel_path).resolve()
    if not str(path).startswith(str(STRATEGIES_DIR.resolve())):
        raise ValueError("Invalid strategy path")
    if not path.exists():
        raise FileNotFoundError(rel_path)
    return path


def load_strategy_module(rel_path: str) -> ModuleType:
    path = _resolve_strategy_path(rel_path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        raise ValueError("Could not load strategy module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_strategy_params(rel_path: str) -> dict:
    module = load_strategy_module(rel_path)
    params = getattr(module, "PARAMS", {})
    if not isinstance(params, dict):
        raise ValueError("PARAMS in strategy must be a dict")
    return params
