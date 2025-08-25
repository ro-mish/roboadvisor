from fastapi import FastAPI, HTTPException
import os
import openai
import re
import unicodedata
from typing import Optional, List, Dict
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

from .models import RoboAdvisorRequest, RoboAdvisorResponse, StructuredQuery, StockData, ConversationEntry
from .prompts import extract_ticker_from_text, create_single_stock_analysis_prompt, create_fallback_single_stock_prompt, create_general_query_prompt
from .alpha_vantage import AlphaVantageClient, create_comprehensive_context, format_context_for_llm

app = FastAPI(title="RoboAdvisor API")

# In-memory conversation storage (in production, use a database)
conversation_memory: Dict[str, List[ConversationEntry]] = {}

def validate_environment_variables():
    """Validate that all required environment variables are set"""
    print("Checking environment variables...")
    
    # Check OpenAI API Key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        if openai_key.startswith(('sk-', 'sk-proj-')):
            print(f"OpenAI API Key: {openai_key[:8]}...")
        else:
            print("WARNING: OpenAI API Key format appears invalid")
    else:
        print("ERROR: OpenAI API Key not set")
    
    # Check Alpha Vantage API Key
    alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    if alpha_key == "demo":
        print("WARNING: Alpha Vantage API Key using demo (limited functionality)")
    else:
        print(f"Alpha Vantage API Key: {alpha_key[:8]}...")
    
    # Check API Base URL
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"API Base URL: {api_url}")
    
    print("Environment validation complete\n")

# Validate environment on startup
validate_environment_variables()

def clean_text_response(text: str) -> str:
    """Clean and normalize text response to fix formatting issues"""
    if not text:
        return text
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove any non-printable characters except newlines and tabs
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    
    # Fix multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Fix line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def get_openai_response(prompt: str, max_tokens: int = 400) -> str:
    """Simple OpenAI API call"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return "I'm unable to provide analysis right now. Please set the OPENAI_API_KEY environment variable."
    
    # Validate API key format
    if not openai_api_key.startswith(('sk-', 'sk-proj-')):
        print("WARNING: OpenAI API key format seems invalid")
        return "OpenAI API key appears to be invalid. Please check your OPENAI_API_KEY environment variable."
    
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens
        )
        response_text = response.choices[0].message.content.strip()
        return clean_text_response(response_text)
    except Exception as e:
        return f"Analysis temporarily unavailable: {str(e)}"

def extract_tickers_from_text(text: str) -> List[str]:
    """Extract multiple ticker symbols from text"""
    # First try the existing single ticker extraction
    single_ticker = extract_ticker_from_text(text)
    if single_ticker != "UNKNOWN":
        tickers = [single_ticker]
    else:
        tickers = []
    
    # Look for additional ticker patterns
    # Common patterns: $AAPL, AAPL, (AAPL), ticker symbols in caps
    ticker_patterns = [
        r'\$([A-Z]{1,5})\b',  # $AAPL format
        r'\b([A-Z]{2,5})\b',  # 2-5 letter caps (but be selective)
        r'\(([A-Z]{1,5})\)',  # (AAPL) format
    ]
    
    # Known company name to ticker mappings for common stocks
    company_mappings = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
        'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META', 'facebook': 'META',
        'nvidia': 'NVDA', 'netflix': 'NFLX', 'disney': 'DIS', 'walmart': 'WMT',
        'coca cola': 'KO', 'coca-cola': 'KO', 'pepsi': 'PEP', 'mcdonalds': 'MCD',
        'visa': 'V', 'mastercard': 'MA', 'paypal': 'PYPL', 'intel': 'INTC',
        'amd': 'AMD', 'boeing': 'BA', 'ge': 'GE', 'general electric': 'GE'
    }
    
    text_lower = text.lower()
    
    # Check for company names
    for company, ticker in company_mappings.items():
        if company in text_lower and ticker not in tickers:
            tickers.append(ticker)
    
    # Extract ticker patterns
    for pattern in ticker_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            ticker = match.upper()
            # Filter out common English words that might match ticker pattern
            if ticker not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'USE', 'MAN', 'NEW', 'NOW', 'WAY', 'MAY', 'SAY', 'WHAT', 'WHEN', 'WHERE', 'WHO', 'WHY', 'HOW', 'SOME', 'GOOD', 'BEST', 'TOP', 'ANY', 'WILL', 'SHOULD', 'COULD', 'WOULD'] and ticker not in tickers:
                tickers.append(ticker)
    
    # Remove duplicates while preserving order
    unique_tickers = []
    for ticker in tickers:
        if ticker not in unique_tickers:
            unique_tickers.append(ticker)
    
    return unique_tickers if unique_tickers else ["UNKNOWN"]

def get_stock_data(ticker: str) -> Optional[StockData]:
    """Get stock data from Alpha Vantage"""
    try:
        client = AlphaVantageClient()
        data = client.get_stock_quote(ticker)
        return StockData(**data) if data else None
    except Exception:
        return None

def get_conversation_history(session_id: str, max_entries: int = 5) -> str:
    """Get formatted conversation history for context"""
    if session_id not in conversation_memory:
        return ""
    
    entries = conversation_memory[session_id][-max_entries:]  # Get last N entries
    if not entries:
        return ""
    
    history_lines = []
    for entry in entries:
        history_lines.append(f"Previous Query: {entry.query}")
        history_lines.append(f"Response: {entry.response}")
        history_lines.append(f"Stock: {entry.ticker}")
        history_lines.append("---")
    
    return "\n".join(history_lines)

def save_conversation_entry(session_id: str, query: str, response: str, ticker: str):
    """Save a conversation entry to memory"""
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
    
    entry = ConversationEntry(
        timestamp=datetime.now(),
        query=query,
        response=response,
        ticker=ticker
    )
    
    conversation_memory[session_id].append(entry)
    
    # Keep only last 20 entries per session to prevent memory overflow
    if len(conversation_memory[session_id]) > 20:
        conversation_memory[session_id] = conversation_memory[session_id][-20:]

@app.get("/")
def health():
    return {"status": "healthy", "service": "RoboAdvisor API"}

@app.get("/env-status")
def environment_status():
    """Check environment variable status"""
    status = {
        "openai_api_key": {
            "configured": bool(os.getenv("OPENAI_API_KEY")),
            "valid_format": False
        },
        "alpha_vantage_api_key": {
            "configured": os.getenv("ALPHA_VANTAGE_API_KEY", "demo") != "demo",
            "using_demo": os.getenv("ALPHA_VANTAGE_API_KEY", "demo") == "demo"
        },
        "api_base_url": os.getenv("API_BASE_URL", "http://localhost:8000")
    }
    
    # Check OpenAI key format if present
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        status["openai_api_key"]["valid_format"] = openai_key.startswith(('sk-', 'sk-proj-'))
    
    return status

@app.get("/context/{symbol}")
def debug_comprehensive_context(symbol: str):
    """Debug endpoint to see what comprehensive context looks like"""
    try:
        context = create_comprehensive_context(symbol)
        formatted = format_context_for_llm(context)
        
        return {
            "symbol": symbol.upper(),
            "raw_context": context,
            "formatted_for_llm": formatted,
            "data_sources": context.get("data_sources", [])
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@app.post("/chat", response_model=RoboAdvisorResponse)
def chat_roboadvisor(request: RoboAdvisorRequest) -> RoboAdvisorResponse:
    query = request.query
    session_id = request.session_id or str(uuid.uuid4())  # Generate session ID if not provided
    
    # Extract ticker from query (single stock only)
    tickers = extract_tickers_from_text(query)
    primary_ticker = tickers[0] if tickers else "UNKNOWN"
    
    structured_query = StructuredQuery(
        ticker=primary_ticker if primary_ticker != "UNKNOWN" else "",
        query_type="analysis",
        time_frame="current",
        intent="Stock analysis request"
    )
    
    # Handle unknown ticker - use general query prompt
    if primary_ticker == "UNKNOWN":
        # Get conversation history
        conversation_history = get_conversation_history(session_id)
        
        # Use general query prompt to let LLM handle the response
        prompt = create_general_query_prompt(query, conversation_history)
        response_text = get_openai_response(prompt, max_tokens=600)
        
        save_conversation_entry(session_id, query, response_text, "")
        return RoboAdvisorResponse(
            response=response_text,
            structured_query=structured_query,
            user_level="BEGINNER",
            stock_data=None,
            original_query=query,
            session_id=session_id
        )
    
    # Get stock data
    stock_data = get_stock_data(primary_ticker)
    
    if not stock_data:
        response_text = f"Sorry, I can't get current data for {primary_ticker}. Please try another stock or check back later."
        save_conversation_entry(session_id, query, response_text, primary_ticker)
        return RoboAdvisorResponse(
            response=response_text,
            structured_query=structured_query,
            user_level="BEGINNER",
            stock_data=None,
            original_query=query,
            session_id=session_id
        )
    
    # Get conversation history
    conversation_history = get_conversation_history(session_id)
    
# Removed verbose print statement
    
    comprehensive_context = None
    response_text = ""
    
    try:
        # Single stock analysis with conversation history
        comprehensive_context = create_comprehensive_context(primary_ticker)
        formatted_context = format_context_for_llm(comprehensive_context)
        
        prompt = create_single_stock_analysis_prompt(query, primary_ticker, formatted_context, conversation_history)
        response_text = get_openai_response(prompt, max_tokens=800)
        
    except Exception as e:
        print(f"Error creating comprehensive context: {e}")
        # Fallback to basic response
        prompt = create_fallback_single_stock_prompt(query, stock_data, conversation_history)
        response_text = get_openai_response(prompt)
    
    # Save conversation entry (only the LLM response)
    save_conversation_entry(session_id, query, response_text, primary_ticker)
    
    # Ensure stock_data is properly formatted
    if stock_data:
        # Convert to dict to ensure proper serialization
        stock_data_dict = stock_data.dict() if hasattr(stock_data, 'dict') else stock_data.model_dump() if hasattr(stock_data, 'model_dump') else stock_data
        # Create new StockData object with clean values
        clean_stock_data = StockData(
            symbol=stock_data_dict.get('symbol', ''),
            name=stock_data_dict.get('name'),
            price=stock_data_dict.get('price', 0),
            previous_close=stock_data_dict.get('previous_close', 0),
            change=stock_data_dict.get('change', 0),
            change_percent=str(stock_data_dict.get('change_percent', 'N/A')),
            volume=stock_data_dict.get('volume', 0),
            market_cap=stock_data_dict.get('market_cap'),
            pe_ratio=stock_data_dict.get('pe_ratio'),
            dividend_yield=stock_data_dict.get('dividend_yield'),
            week_52_high=stock_data_dict.get('week_52_high'),
            week_52_low=stock_data_dict.get('week_52_low'),
            sector=stock_data_dict.get('sector'),
            industry=stock_data_dict.get('industry'),
            source=str(stock_data_dict.get('source', 'N/A')),
            note=stock_data_dict.get('note')
        )
    else:
        clean_stock_data = None
    
    return RoboAdvisorResponse(
        response=response_text,
        structured_query=structured_query,
        user_level="INTERMEDIATE",
        stock_data=clean_stock_data,
        comprehensive_context=comprehensive_context,
        original_query=query,
        session_id=session_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)