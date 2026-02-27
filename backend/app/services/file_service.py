from datetime import datetime
from pathlib import Path
from app.core.config import STRATEGIES_DIR


class FileService:
    @staticmethod
    def list_strategies() -> list[dict]:
        items: list[dict] = []
        for path in sorted(STRATEGIES_DIR.rglob("*.py")):
            stat = path.stat()
            items.append(
                {
                    "name": path.name,
                    "path": str(path.relative_to(STRATEGIES_DIR)),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime),
                }
            )
        return items

    @staticmethod
    def read_strategy(rel_path: str) -> str:
        path = (STRATEGIES_DIR / rel_path).resolve()
        if not str(path).startswith(str(STRATEGIES_DIR.resolve())):
            raise ValueError("Invalid path")
        if not path.exists():
            raise FileNotFoundError(rel_path)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def save_strategy(rel_path: str, content: str) -> None:
        path = (STRATEGIES_DIR / rel_path).resolve()
        if not str(path).startswith(str(STRATEGIES_DIR.resolve())):
            raise ValueError("Invalid path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
