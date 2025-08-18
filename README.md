# Roboadvisor App

A minimal FastAPI server that fetches stock data from Alpha Vantage Finance API.

## Setup

```bash
scripts/setup.sh
```

## Run

**Start API server:**
```bash
scripts/run_server.sh
# Server runs on http://localhost:8000
```

**Start Streamlit UI (in another terminal):**
```bash
scripts/run_ui.sh
# UI runs on http://localhost:8501
```

**Manual run:**
```bash
source venv/bin/activate
python -m server.main &
streamlit run app/streamlit_app.py
```

## Setup Alpha Vantage (Optional)

For real stock data, get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key):

```bash
export ALPHA_VANTAGE_API_KEY=your_key_here
```

Without a key, it uses the demo key (limited) and falls back to sample data.

## Test Commands

**Health check:**
```bash
curl http://localhost:8000/
```

**Get stock data:**
```bash
# Apple (tries real data first, falls back to sample)
curl http://localhost:8000/stock/AAPL

# Tesla  
curl http://localhost:8000/stock/TSLA

# Any ticker (generates data if unknown)
curl http://localhost:8000/stock/NVDA

# Pretty print with jq
curl -s http://localhost:8000/stock/AAPL | jq
```

## API Endpoints

- `GET /` - Health check
- `GET /stock/{ticker}` - Get stock info for ticker symbol
