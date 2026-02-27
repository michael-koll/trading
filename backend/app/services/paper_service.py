from datetime import datetime
from uuid import uuid4

from app.services.alpaca_service import AlpacaService
from app.services.backtest_service import BacktestService


class PaperService:
    _sessions: dict[str, dict] = {}

    @classmethod
    def start_session(cls, payload: dict) -> dict:
        broker = str(payload.get("broker", "local")).lower()
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "strategy_path": payload["strategy_path"],
            "symbol": payload["symbol"],
            "interval": payload.get("interval", "1m"),
            "period": payload.get("period", "7d"),
            "dataset_path": payload.get("dataset_path"),
            "market": payload.get("market", "stocks"),
            "exchange": payload.get("exchange"),
            "cash": payload.get("starting_cash", 10000.0),
            "position": 0,
            "created_at": datetime.utcnow().isoformat(),
            "status": "running",
            "broker": broker,
        }

        if broker == "alpaca":
            account = AlpacaService.get_account()
            session["alpaca_account"] = {
                "id": account.get("id"),
                "status": account.get("status"),
                "buying_power": account.get("buying_power"),
                "currency": account.get("currency"),
            }
            session["mode"] = "paper_remote"
        else:
            session["mode"] = "paper_local"

        cls._sessions[session_id] = session
        return session

    @classmethod
    def list_sessions(cls) -> list[dict]:
        return list(cls._sessions.values())

    @classmethod
    def get_session_state(cls, session_id: str) -> dict:
        session = cls._sessions.get(session_id)
        if not session:
            raise ValueError("Paper session not found")

        payload = {
            "strategy_path": session["strategy_path"],
            "symbol": session["symbol"],
            "interval": session.get("interval", "1m"),
            "period": session.get("period", "7d"),
            "dataset_path": session.get("dataset_path"),
            "market": session.get("market", "stocks"),
            "exchange": session.get("exchange"),
            "start_cash": session.get("cash", 10000.0),
        }
        snapshot = BacktestService._execute(payload, persist=False)

        buys = len([m for m in snapshot.get("markers", []) if m.get("side") == "buy"])
        sells = len([m for m in snapshot.get("markers", []) if m.get("side") == "sell"])
        session["position"] = max(buys - sells, 0)
        session["updated_at"] = datetime.utcnow().isoformat()

        return {
            "session": session,
            "snapshot": snapshot,
        }

    @classmethod
    def alpaca_account(cls) -> dict:
        return AlpacaService.get_account()
