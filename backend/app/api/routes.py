from fastapi import APIRouter, HTTPException, Query
import requests
from app.schemas.models import (
    BacktestRequest,
    CreateStrategyRequest,
    DeleteStrategyRequest,
    DatasetImportRequest,
    OptimizeRequest,
    PaperTradeStartRequest,
    RenameStrategyRequest,
    SaveStrategyRequest,
)
from app.services.backtest_service import BacktestService
from app.services.dataset_service import DatasetService
from app.services.file_service import FileService
from app.services.optimize_service import OptimizeService
from app.services.paper_service import PaperService
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/strategies")
def list_strategies() -> list[dict]:
    return FileService.list_strategies()


@router.get("/strategies/{path:path}")
def read_strategy(path: str) -> dict:
    try:
        content = FileService.read_strategy(path)
        return {"path": path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/strategies")
def save_strategy(payload: SaveStrategyRequest) -> dict:
    try:
        FileService.save_strategy(payload.path, payload.content)
        return {"status": "saved", "path": payload.path}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/strategies/create")
def create_strategy(payload: CreateStrategyRequest) -> dict:
    try:
        created = FileService.create_strategy(payload.path)
        return {"status": "created", "path": created}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/strategies/rename")
def rename_strategy(payload: RenameStrategyRequest) -> dict:
    try:
        FileService.rename_strategy(payload.old_path, payload.new_path)
        return {"status": "renamed", "old_path": payload.old_path, "new_path": payload.new_path}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/strategies/delete")
def delete_strategy(payload: DeleteStrategyRequest) -> dict:
    try:
        FileService.delete_strategy(payload.path)
        return {"status": "deleted", "path": payload.path}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/backtests/run")
def run_backtest(payload: BacktestRequest) -> dict:
    try:
        return BacktestService.run_backtest(payload.model_dump())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/optimize/run")
def run_optimize(payload: OptimizeRequest) -> dict:
    try:
        return OptimizeService.run_optimization(payload.model_dump())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Remote data provider error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {exc}")


@router.post("/datasets/import")
def import_dataset(payload: DatasetImportRequest) -> dict:
    try:
        return DatasetService.import_dataset(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Remote data provider error: {exc}")


@router.get("/datasets")
def list_datasets() -> list[dict]:
    return DatasetService.list_datasets()


@router.get("/symbols/search")
def search_symbols(q: str = Query(default="", min_length=1), limit: int = 8) -> list[dict]:
    try:
        return MarketDataService.search_symbols(q, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Remote data provider error: {exc}")


@router.post("/paper/start")
def start_paper(payload: PaperTradeStartRequest) -> dict:
    try:
        return PaperService.start_session(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Broker error: {exc}")


@router.get("/paper/sessions")
def list_paper_sessions() -> list[dict]:
    return PaperService.list_sessions()


@router.get("/paper/sessions/{session_id}/state")
def paper_session_state(session_id: str) -> dict:
    try:
        return PaperService.get_session_state(session_id)
    except ValueError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Remote data provider error: {exc}")


@router.get("/paper/alpaca/account")
def alpaca_account() -> dict:
    try:
        return PaperService.alpaca_account()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Broker error: {exc}")
