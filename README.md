# Trading Strategy Development Framework

Local-first framework for:
- Python strategy development
- Real Backtrader backtesting (OHLCV)
- Optuna hyperparameter tuning
- Live paper trading simulation
- Dataset import (`yfinance`, `csv`, `csv_tick`, `alpaca`)

## Stack
- Frontend: Next.js + TypeScript + Monaco Editor + Lightweight Charts
- Backend: FastAPI + Python 3.11 + Optuna + Backtrader
- Runtime: Docker Compose (portable for VPS / Raspberry Pi)

## Run
```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

LAN access:
- Open frontend from another device via `http://<host-lan-ip>:3000`
- Frontend API calls are proxied through Next.js (`/api -> backend`) so no hardcoded backend host is required in the browser.

## Alpaca (optional now)
To enable Alpaca data import and Alpaca paper account checks, set:
```bash
export ALPACA_API_KEY="..."
export ALPACA_API_SECRET="..."
```
Then restart backend container.

## Folder Structure
```text
backend/
  app/
    api/
    core/
    schemas/
    services/
  data/
    strategies/
    datasets/
    backtests/
frontend/
  app/
  components/
  lib/
```

## API Highlights
- `GET /api/strategies`
- `GET /api/strategies/{path}`
- `POST /api/strategies`
- `POST /api/backtests/run`
- `POST /api/optimize/run`
- `POST /api/paper/start`
- `GET /api/paper/sessions`
- `GET /api/paper/alpaca/account`
- `POST /api/datasets/import`

## Tick CSV Format (for `source=csv_tick`)
Required columns:
- `timestamp` (or `time`)
- `price`

Optional:
- `size` (defaults to 1)

The import pipeline saves raw ticks and also creates OHLCV bars in `1m` or `5m`.

## Notes
- Backtests currently run with an SMA crossover strategy scaffold that reads `PARAMS` from your strategy file.
- Paper trading runs free in local simulation mode by default and does not require API keys.
- Alpaca integration is implemented first for data/account connectivity and can be extended to order placement next.

## Strategy Indicator Auto-Plot
If a strategy defines `INDICATORS`, the backtest engine auto-computes and renders them in the price chart.

Example:
```python
INDICATORS = [
  {"id": "sma_fast", "type": "sma", "source": "close", "period_param": "fast_period", "label": "Fast SMA", "color": "#ffd166"},
  {"id": "sma_slow", "type": "sma", "source": "close", "period_param": "slow_period", "label": "Slow SMA", "color": "#60a5fa"},
]
```

Supported types in v1: `sma`, `ema`, `wma`, `rsi`.
