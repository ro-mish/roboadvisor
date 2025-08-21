# Roboadvisor App

A minimal FastAPI server that fetches stock data from Alpha Vantage Finance API.

## Setup

1. **Install dependencies:**
```bash
scripts/setup.sh
```

2. **Configure environment variables:**
Create a `.env` file in the project root with the following variables:

```env
# Required: OpenAI API Key for AI analysis
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Alpha Vantage API Key (defaults to "demo" with limited functionality)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Optional: API Base URL (defaults to http://localhost:8000)
API_BASE_URL=http://localhost:8000
```

**Getting API Keys:**
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Alpha Vantage API Key**: Get free key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)

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
./venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload &
./venv/bin/python -m streamlit run app/streamlit_app.py --server.port 8501
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

**Chat with the AI Wealth Advisor (main endpoint):**
```bash
# Natural language queries
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me how Tesla is doing today"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Apple stock price?"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How has NVDA performed recently?"}'

# Pretty print with jq
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Tesla"}' | jq
```

## Testing

**Run system tests:**
```bash
source venv/bin/activate
./venv/bin/python scripts/test_system.py
```



## API Endpoints

- `POST /chat` - **Main endpoint**: Natural language query → intelligent response

## Environment Variables

Required for full functionality:
- `ALPHA_VANTAGE_API_KEY` - For real stock data (required)
- `OPENAI_API_KEY` - For intelligent analysis (required)
