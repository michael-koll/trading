from fastapi import APIRouter, HTTPException
import requests
from app.schemas.models import (
    BacktestRequest,
    DatasetImportRequest,
    OptimizeRequest,
    PaperTradeStartRequest,
    SaveStrategyRequest,
)
from app.services.backtest_service import BacktestService
from app.services.dataset_service import DatasetService
from app.services.file_service import FileService
from app.services.optimize_service import OptimizeService
from app.services.paper_service import PaperService

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


@router.get("/paper/alpaca/account")
def alpaca_account() -> dict:
    try:
        return PaperService.alpaca_account()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Broker error: {exc}")
