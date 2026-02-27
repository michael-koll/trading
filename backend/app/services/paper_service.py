from datetime import datetime
from uuid import uuid4

from app.services.alpaca_service import AlpacaService


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
    def alpaca_account(cls) -> dict:
        return AlpacaService.get_account()
