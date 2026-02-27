from __future__ import annotations

import os
from datetime import datetime, timezone
import requests

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"


class AlpacaService:
    @staticmethod
    def _headers() -> dict[str, str]:
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_API_SECRET")
        if not key or not secret:
            raise ValueError("Missing ALPACA_API_KEY or ALPACA_API_SECRET environment variables")
        return {
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
        }

    @classmethod
    def get_account(cls) -> dict:
        response = requests.get(f"{PAPER_BASE_URL}/v2/account", headers=cls._headers(), timeout=15)
        response.raise_for_status()
        return response.json()

    @classmethod
    def fetch_bars(
        cls,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        feed: str = "iex",
        adjustment: str = "raw",
        limit: int = 10000,
    ) -> dict:
        params = {
            "symbols": symbol,
            "timeframe": timeframe,
            "start": start.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "end": end.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "limit": str(limit),
            "adjustment": adjustment,
            "feed": feed,
        }
        response = requests.get(
            f"{DATA_BASE_URL}/v2/stocks/bars",
            headers=cls._headers(),
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
