from fastapi import FastAPI
import random
import requests
import os
from typing import Optional

app = FastAPI(title="Stock API - Alpha Vantage + Fallback")

# Alpha Vantage API (free tier: 25 requests/day, 5 requests/minute)
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  # Use "demo" for testing

def fetch_from_alpha_vantage(symbol: str) -> Optional[dict]:
    """Fetch real stock data from Alpha Vantage API"""
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Alpha Vantage returns data in "Global Quote" key
        quote = data.get("Global Quote", {})
        if not quote:
            return None
            
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol.upper()} Corporation",  # Alpha Vantage doesn't provide company name in this endpoint
            "price": float(quote.get("05. price", 0)),
            "previous_close": float(quote.get("08. previous close", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
            "volume": int(quote.get("06. volume", 0)),
            "52_week_high": float(quote.get("03. high", 0)),
            "52_week_low": float(quote.get("04. low", 0)),
            "source": "alpha_vantage"
        }
        
    except Exception as e:
        print(f"Alpha Vantage error for {symbol}: {e}")
        return None

# Stock database - just clean sample data
STOCK_DATA = {
    "AAPL": {
        "symbol": "AAPL", "name": "Apple Inc.", "price": 227.52,
        "previous_close": 225.77, "market_cap": 3454000000000,
        "pe_ratio": 33.44, "sector": "Technology", "industry": "Consumer Electronics",
        "52_week_high": 237.23, "52_week_low": 164.08, "dividend_yield": 0.44
    },
    "TSLA": {
        "symbol": "TSLA", "name": "Tesla, Inc.", "price": 242.68,
        "previous_close": 238.59, "market_cap": 775000000000,
        "pe_ratio": 65.32, "sector": "Consumer Cyclical", "industry": "Auto Manufacturers",
        "52_week_high": 299.29, "52_week_low": 138.80, "dividend_yield": None
    },
    "SPY": {
        "symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "price": 557.02,
        "previous_close": 554.33, "market_cap": 524000000000,
        "pe_ratio": None, "sector": "Financial Services", "industry": "Exchange Traded Fund",
        "52_week_high": 565.85, "52_week_low": 415.54, "dividend_yield": 1.23
    },
    "NVDA": {
        "symbol": "NVDA", "name": "NVIDIA Corporation", "price": 119.46,
        "previous_close": 116.91, "market_cap": 2930000000000,
        "pe_ratio": 66.12, "sector": "Technology", "industry": "Semiconductors",
        "52_week_high": 140.76, "52_week_low": 39.23, "dividend_yield": 0.03
    },
    "MSFT": {
        "symbol": "MSFT", "name": "Microsoft Corporation", "price": 425.22,
        "previous_close": 422.37, "market_cap": 3160000000000,
        "pe_ratio": 35.67, "sector": "Technology", "industry": "Software",
        "52_week_high": 468.35, "52_week_low": 362.90, "dividend_yield": 0.72
    },
    "GOOGL": {
        "symbol": "GOOGL", "name": "Alphabet Inc.", "price": 167.06,
        "previous_close": 165.34, "market_cap": 2050000000000,
        "pe_ratio": 23.45, "sector": "Communication Services", "industry": "Internet Content",
        "52_week_high": 191.75, "52_week_low": 129.40, "dividend_yield": None
    }
}

@app.get("/")
def health():
    return {
        "status": "ok", 
        "note": "Stock API with Alpha Vantage + fallback data",
        "available_tickers": list(STOCK_DATA.keys()),
        "alpha_vantage_key": "configured" if ALPHA_VANTAGE_KEY != "demo" else "using demo key"
    }

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    """Get stock info - tries Alpha Vantage first, falls back to sample data"""
    symbol = ticker.upper()
    
    # Try Alpha Vantage first
    alpha_data = fetch_from_alpha_vantage(symbol)
    if alpha_data:
        return alpha_data
    
    # Fallback to known stock data
    if symbol in STOCK_DATA:
        result = STOCK_DATA[symbol].copy()
        result["source"] = "sample_data"
        result["note"] = "Alpha Vantage unavailable, using sample data"
        return result
    
    # Generate realistic data for unknown tickers
    base_price = round(20 + random.random() * 300, 2)
    return {
        "symbol": symbol,
        "name": f"{symbol} Corporation",
        "price": base_price,
        "previous_close": round(base_price * (0.98 + random.random() * 0.04), 2),
        "change": round(base_price * (random.random() * 0.1 - 0.05), 2),
        "change_percent": round((random.random() * 10 - 5), 2),
        "market_cap": int(base_price * 1000000000 * (0.5 + random.random())),
        "pe_ratio": round(15 + random.random() * 40, 2),
        "dividend_yield": round(random.random() * 3, 2) if random.random() > 0.3 else None,
        "52_week_high": round(base_price * (1.1 + random.random() * 0.3), 2),
        "52_week_low": round(base_price * (0.6 + random.random() * 0.2), 2),
        "volume": int(1000000 + random.random() * 50000000),
        "sector": random.choice(["Technology", "Healthcare", "Financial Services", "Consumer Cyclical", "Energy"]),
        "industry": "Various",
        "source": "generated",
        "note": f"Alpha Vantage unavailable, generated sample data for {symbol}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
