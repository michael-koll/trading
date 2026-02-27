from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
import yfinance as yf

from app.core.config import DATASETS_DIR
from app.services.alpaca_service import AlpacaService

ALLOWED_INTERVALS = {"1m", "5m", "15m", "1h", "1d"}
POPULAR_SYMBOLS = [
    {"symbol": "^GSPC", "name": "S&P 500", "type": "INDEX", "exchange": "INDEX"},
    {"symbol": "^NDX", "name": "NASDAQ 100", "type": "INDEX", "exchange": "INDEX"},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "type": "INDEX", "exchange": "INDEX"},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "type": "INDEX", "exchange": "INDEX"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "type": "ETF", "exchange": "NYSEARCA"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "type": "ETF", "exchange": "NASDAQ"},
    {"symbol": "AAPL", "name": "Apple Inc.", "type": "EQUITY", "exchange": "NASDAQ"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "type": "EQUITY", "exchange": "NASDAQ"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "type": "EQUITY", "exchange": "NASDAQ"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "type": "EQUITY", "exchange": "NASDAQ"},
    {"symbol": "BTC-USD", "name": "Bitcoin USD", "type": "CRYPTO", "exchange": "CCC"},
    {"symbol": "ETH-USD", "name": "Ethereum USD", "type": "CRYPTO", "exchange": "CCC"},
    {"symbol": "SOL-USD", "name": "Solana USD", "type": "CRYPTO", "exchange": "CCC"},
]


class MarketDataService:
    @staticmethod
    def _fallback_symbol_search(query: str, limit: int) -> list[dict]:
        q = query.lower().strip()
        ranked: list[dict] = []
        for item in POPULAR_SYMBOLS:
            symbol = str(item.get("symbol", ""))
            name = str(item.get("name", ""))
            hay = f"{symbol} {name}".lower()
            if q in hay:
                ranked.append(item)
        return ranked[:limit]

    @staticmethod
    def search_symbols(query: str, limit: int = 8) -> list[dict]:
        q = (query or "").strip()
        if len(q) < 1:
            return []
        safe_limit = max(1, min(int(limit), 20))

        out: list[dict] = []
        seen: set[str] = set()

        try:
            response = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/search",
                params={
                    "q": q,
                    "quotesCount": safe_limit,
                    "newsCount": 0,
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                },
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json() or {}
            quotes = payload.get("quotes", []) or []

            for item in quotes:
                symbol = str(item.get("symbol") or "").strip()
                if not symbol or symbol in seen:
                    continue
                seen.add(symbol)
                out.append(
                    {
                        "symbol": symbol,
                        "name": str(item.get("shortname") or item.get("longname") or symbol),
                        "type": str(item.get("quoteType") or ""),
                        "exchange": str(item.get("exchDisp") or item.get("exchange") or ""),
                    }
                )
                if len(out) >= safe_limit:
                    return out
        except requests.RequestException:
            pass

        for item in MarketDataService._fallback_symbol_search(q, safe_limit):
            symbol = str(item.get("symbol") or "").strip()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            out.append(item)
            if len(out) >= safe_limit:
                break

        return out

    @staticmethod
    def list_datasets() -> list[dict]:
        items: list[dict] = []
        for path in sorted(DATASETS_DIR.glob("*.csv")):
            try:
                sample = pd.read_csv(path, nrows=5000)
            except Exception:
                continue

            rows = None
            start = None
            end = None
            for tcol in ("datetime", "timestamp", "time", "date"):
                if tcol in sample.columns:
                    ts = pd.to_datetime(sample[tcol], errors="coerce")
                    ts = ts.dropna()
                    if not ts.empty:
                        start = str(ts.min())
                        end = str(ts.max())
                    break

            try:
                rows = sum(1 for _ in open(path, "r", encoding="utf-8")) - 1
            except Exception:
                rows = None

            stat = path.stat()
            items.append(
                {
                    "name": path.name,
                    "path": path.name,
                    "size_bytes": stat.st_size,
                    "updated_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
                    "rows": rows,
                    "start": start,
                    "end": end,
                    "columns": [str(c) for c in sample.columns],
                }
            )
        return items

    @staticmethod
    def _normalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            raise ValueError("Dataset is empty")

        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)

        lower_map = {c: str(c).strip().lower() for c in frame.columns}
        frame = frame.rename(columns={orig: mapped for orig, mapped in lower_map.items()})

        index_name = str(frame.index.name or "").lower()
        if "date" in frame.columns:
            frame["datetime"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
            frame = frame.drop(columns=["date"])
        elif "datetime" in frame.columns:
            frame["datetime"] = pd.to_datetime(frame["datetime"], utc=True, errors="coerce")
        elif "timestamp" in frame.columns:
            frame["datetime"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        elif "time" in frame.columns:
            frame["datetime"] = pd.to_datetime(frame["time"], utc=True, errors="coerce")
        elif index_name in {"date", "datetime", "timestamp", "time"}:
            frame["datetime"] = pd.to_datetime(frame.index, utc=True, errors="coerce")
        else:
            raise ValueError("Could not determine datetime column")

        required = ["open", "high", "low", "close"]
        for col in required:
            if col not in frame.columns:
                raise ValueError(f"Missing required column: {col}")

        if "volume" not in frame.columns:
            frame["volume"] = 0

        clean = frame[["datetime", "open", "high", "low", "close", "volume"]].copy()
        clean = clean.dropna(subset=["datetime", "open", "high", "low", "close"])
        clean = clean.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
        clean = clean.set_index("datetime")
        clean.index = clean.index.tz_convert(None)

        for col in ["open", "high", "low", "close", "volume"]:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")

        clean = clean.dropna(subset=["open", "high", "low", "close"])
        if clean.empty:
            raise ValueError("No valid OHLCV rows after normalization")
        return clean

    @staticmethod
    def _ticks_to_ohlcv(frame: pd.DataFrame, timeframe: str = "1m") -> pd.DataFrame:
        if timeframe not in {"1m", "5m"}:
            raise ValueError("Tick resampling supports only 1m and 5m")

        lower_map = {c: str(c).strip().lower() for c in frame.columns}
        frame = frame.rename(columns={orig: mapped for orig, mapped in lower_map.items()})
        if "timestamp" not in frame.columns and "time" not in frame.columns:
            raise ValueError("Tick CSV needs timestamp or time column")

        tcol = "timestamp" if "timestamp" in frame.columns else "time"
        frame["datetime"] = pd.to_datetime(frame[tcol], utc=True, errors="coerce")
        if "price" not in frame.columns:
            raise ValueError("Tick CSV needs price column")
        if "size" not in frame.columns:
            frame["size"] = 1

        ticks = frame[["datetime", "price", "size"]].dropna(subset=["datetime", "price"]).copy()
        ticks = ticks.sort_values("datetime").set_index("datetime")

        rule = "1min" if timeframe == "1m" else "5min"
        ohlc = ticks["price"].resample(rule).ohlc()
        vol = ticks["size"].resample(rule).sum().rename("volume")
        out = pd.concat([ohlc, vol], axis=1).dropna(subset=["open", "high", "low", "close"])
        out.index = out.index.tz_convert(None)
        if out.empty:
            raise ValueError("Tick conversion produced no bars")
        return out

    @staticmethod
    def _load_local_dataset(dataset_path: str) -> pd.DataFrame:
        src = Path(dataset_path)
        if not src.is_absolute():
            src = (DATASETS_DIR / dataset_path).resolve()
        if not src.exists():
            raise FileNotFoundError(str(src))
        frame = pd.read_csv(src)
        return MarketDataService._normalize_ohlcv(frame)

    @staticmethod
    def get_ohlcv(payload: dict) -> pd.DataFrame:
        interval = payload.get("interval", "1m")
        if interval not in ALLOWED_INTERVALS:
            raise ValueError("Supported intervals: 1m, 5m, 15m, 1h, 1d")

        dataset_path = payload.get("dataset_path")
        if dataset_path:
            return MarketDataService._load_local_dataset(dataset_path)

        symbol = payload.get("symbol", "AAPL")
        period = payload.get("period", "5d")
        frame = yf.download(symbol, interval=interval, period=period, auto_adjust=True)
        return MarketDataService._normalize_ohlcv(frame)

    @staticmethod
    def import_dataset(payload: dict) -> dict:
        source = payload.get("source", "").lower()
        timeframe = payload.get("timeframe") or payload.get("interval") or "1m"
        stamp = int(datetime.utcnow().timestamp())

        if source == "yfinance":
            symbol = payload.get("symbol") or "AAPL"
            interval = payload.get("interval") or timeframe
            period = payload.get("period") or "5d"
            frame = yf.download(symbol, interval=interval, period=period, auto_adjust=True)
            clean = MarketDataService._normalize_ohlcv(frame)
            name = f"{symbol}_{interval}_{period}_{stamp}.csv"
            target = DATASETS_DIR / name
            clean.reset_index().to_csv(target, index=False)
            return {"source": source, "kind": "ohlcv", "path": str(target), "rows": len(clean)}

        if source == "csv":
            csv_path = payload.get("csv_path")
            if not csv_path:
                raise ValueError("csv_path is required for source=csv")
            frame = pd.read_csv(Path(csv_path).expanduser().resolve())
            clean = MarketDataService._normalize_ohlcv(frame)
            name = f"ohlcv_import_{stamp}.csv"
            target = DATASETS_DIR / name
            clean.reset_index().to_csv(target, index=False)
            return {"source": source, "kind": "ohlcv", "path": str(target), "rows": len(clean)}

        if source == "csv_tick":
            csv_path = payload.get("csv_path")
            if not csv_path:
                raise ValueError("csv_path is required for source=csv_tick")
            frame = pd.read_csv(Path(csv_path).expanduser().resolve())
            ticks_name = f"ticks_raw_{stamp}.csv"
            ticks_target = DATASETS_DIR / ticks_name
            frame.to_csv(ticks_target, index=False)

            bars = MarketDataService._ticks_to_ohlcv(frame, timeframe=timeframe)
            bars_name = f"ticks_to_{timeframe}_{stamp}.csv"
            bars_target = DATASETS_DIR / bars_name
            bars.reset_index().to_csv(bars_target, index=False)
            return {
                "source": source,
                "kind": "tick+ohlcv",
                "tick_path": str(ticks_target),
                "path": str(bars_target),
                "rows": len(bars),
                "timeframe": timeframe,
            }

        if source == "alpaca":
            symbol = payload.get("symbol") or "AAPL"
            interval = payload.get("interval") or timeframe
            if interval not in {"1m", "5m"}:
                raise ValueError("Alpaca import supports 1m/5m in v2")

            now = datetime.utcnow()
            start = now - timedelta(days=5)
            tf = "1Min" if interval == "1m" else "5Min"
            response = AlpacaService.fetch_bars(symbol=symbol, timeframe=tf, start=start, end=now)
            bars = response.get("bars", {}).get(symbol, [])
            if not bars:
                raise ValueError("No bars returned from Alpaca")

            frame = pd.DataFrame(
                {
                    "datetime": [bar["t"] for bar in bars],
                    "open": [bar["o"] for bar in bars],
                    "high": [bar["h"] for bar in bars],
                    "low": [bar["l"] for bar in bars],
                    "close": [bar["c"] for bar in bars],
                    "volume": [bar["v"] for bar in bars],
                }
            )
            clean = MarketDataService._normalize_ohlcv(frame)
            name = f"alpaca_{symbol}_{interval}_{stamp}.csv"
            target = DATASETS_DIR / name
            clean.reset_index().to_csv(target, index=False)
            return {"source": source, "kind": "ohlcv", "path": str(target), "rows": len(clean)}

        if source == "polymarket":
            return {
                "source": source,
                "status": "connector_stub",
                "message": "Polymarket connector is planned after Alpaca integration.",
            }

        raise ValueError("Unsupported source")
