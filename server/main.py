from fastapi import FastAPI, HTTPException
import os
import openai
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from .models import RoboAdvisorRequest, RoboAdvisorResponse, StructuredQuery, StockData
from .prompts import extract_ticker_from_text
from .alpha_vantage import AlphaVantageClient, create_comprehensive_context, format_context_for_llm

app = FastAPI(title="RoboAdvisor API")

def get_openai_response(prompt: str, max_tokens: int = 400) -> str:
    """Simple OpenAI API call"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return "I'm unable to provide analysis right now. Please check back later."
    
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Analysis temporarily unavailable: {str(e)}"

def get_stock_data(ticker: str) -> Optional[StockData]:
    """Get stock data from Alpha Vantage"""
    try:
        client = AlphaVantageClient()
        data = client.get_stock_quote(ticker)
        return StockData(**data) if data else None
    except Exception:
        return None

@app.get("/")
def health():
    return {"status": "healthy", "service": "RoboAdvisor API"}

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
    
    # Extract ticker from query
    ticker = extract_ticker_from_text(query)
    structured_query = StructuredQuery(
        ticker=ticker,
        query_type="analysis",
        time_frame="current",
        intent="Stock analysis request"
    )
    
    # Handle unknown ticker
    if ticker == "UNKNOWN":
        return RoboAdvisorResponse(
            response="I couldn't identify a specific stock. Please mention a company name or ticker symbol.",
            structured_query=structured_query,
            user_level="BEGINNER",
            stock_data=None,
            original_query=query
        )
    
    # Get stock data
    stock_data = get_stock_data(ticker)
    if not stock_data:
        return RoboAdvisorResponse(
            response=f"Sorry, I can't get current data for {ticker}. Please try another stock or check back later.",
            structured_query=structured_query,
            user_level="BEGINNER",
            stock_data=None,
            original_query=query
        )
    
    # Generate comprehensive response using ALL Alpha Vantage endpoints
    print(f"Gathering comprehensive market data for {ticker}...")
    
    try:
        # Get comprehensive context using all Alpha Vantage endpoints
        comprehensive_context = create_comprehensive_context(ticker)
        formatted_context = format_context_for_llm(comprehensive_context)
        
        prompt = f"""You are an experienced wealth advisor. A client just asked: "{query}"

Here's the comprehensive market data I've gathered for {ticker}:

{formatted_context}

Analyze this data and provide a thorough, conversational response that:
1. Answers their specific question
2. Provides insights from the price action, fundamentals, and news
3. Gives your professional opinion as a wealth advisor
4. Sounds natural and engaging, not robotic

Make it 2-3 paragraphs, professional but approachable."""

        response_text = get_openai_response(prompt, max_tokens=600)
        
    except Exception as e:
        print(f"Error creating comprehensive context: {e}")
        # Fallback to basic response
        change_pct = ((stock_data.price - stock_data.previous_close) / stock_data.previous_close * 100) if stock_data.previous_close else 0
        
        prompt = f"""You are a helpful financial advisor. Answer this user question about {stock_data.symbol}:

User Question: {query}

Current Stock Data:
- Symbol: {stock_data.symbol}
- Price: ${stock_data.price:.2f}
- Change: {change_pct:+.1f}% today
- Volume: {stock_data.volume:,} shares

Provide a helpful, conversational analysis in 2-3 paragraphs. Be informative but easy to understand."""
        
        response_text = get_openai_response(prompt)
    
    return RoboAdvisorResponse(
        response=response_text,
        structured_query=structured_query,
        user_level="INTERMEDIATE",
        stock_data=stock_data,
        original_query=query
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)