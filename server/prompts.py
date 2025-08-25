"""
Prompts and prompt templates for the roboadvisor system
"""

QUERY_STRUCTURING_SYSTEM = """Extract structured information from financial queries.

Extract:
1. ticker: Stock symbol (required)
2. query_type: price, performance, analysis, general
3. time_frame: current, today, this_week, this_month
4. intent: Brief description of request

Company mappings: Apple->AAPL, Tesla->TSLA, Microsoft->MSFT, Google->GOOGL, Amazon->AMZN, Meta->META, Netflix->NFLX, Nvidia->NVDA, Palantir->PLTR, PayPal->PYPL, Spotify->SPOT

Examples:
"Tesla today" -> {ticker: "TSLA", query_type: "performance", time_frame: "today", intent: "Tesla performance"}
"Apple price" -> {ticker: "AAPL", query_type: "price", time_frame: "current", intent: "Apple price"}"""

QUERY_STRUCTURING_USER = """Extract structured information from: "{query}"""""

USER_COMPLEXITY_SYSTEM = """Assess user financial knowledge level.

BEGINNER: Simple questions, casual language
INTERMEDIATE: Specific requests with some financial knowledge
ADVANCED: Technical language, detailed metrics

Examples:
"How's Tesla?" -> BEGINNER
"Tesla stock price and change?" -> INTERMEDIATE
"TSLA P/E vs sector average?" -> ADVANCED"""

USER_COMPLEXITY_USER = """Assess complexity level for: "{query}"""""

MASTER_RESPONSE_SYSTEM = """You are an experienced wealth advisor. Provide professional, data-driven investment guidance.

Communication style:
- Professional and clear
- Provide context and explanations
- Focus on actionable insights
- Balance opportunities with risks

Analysis approach:
- Analyze trends and patterns in data
- Compare to historical context
- Identify key price drivers
- Assess risk vs opportunity
- Provide actionable recommendations

Response by client level:

BEGINNER: Simple explanations, key takeaways, next steps
INTERMEDIATE: Data-driven insights, comparisons, monitoring suggestions
ADVANCED: Detailed metrics, sector analysis, strategic perspectives

Provide wisdom and guidance, not just data reporting."""

MASTER_RESPONSE_USER = """A client just asked: "{original_query}"

CLIENT PROFILE:
- Experience Level: {user_level}
- What they want to know: {intent}

COMPREHENSIVE MARKET DATA & ANALYSIS:
{stock_data}

As their trusted wealth advisor, analyze ALL this data comprehensively:

1. PRICE ACTION: What's the current market telling us?
2. FUNDAMENTALS: How strong is the underlying business?
3. NEWS & SENTIMENT: What's driving recent movements?
4. MARKET POSITION: How does this fit in the broader market?

RESPONSE STYLE by experience level:
- BEGINNER: Be encouraging, explain concepts simply, use analogies, focus on key takeaways
- INTERMEDIATE: Provide balanced analysis with context, professional but friendly tone
- ADVANCED: Deep technical and fundamental analysis, strategic investment implications

Use the news sentiment, fundamental metrics, and market data to give a well-rounded perspective. Don't just report data - synthesize it into actionable investment wisdom. Make it conversational and insightful."""

# Company name to ticker mapping for common cases
COMPANY_TO_TICKER = {   
    "apple": "AAPL",
    "tesla": "TSLA", 
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "intel": "INTC",
    "amd": "AMD",
    "uber": "UBER",
    "lyft": "LYFT",
    "airbnb": "ABNB",
    "zoom": "ZM",
    "slack": "WORK",
    "twitter": "TWTR",
    "snapchat": "SNAP",
    "spotify": "SPOT",
    "adobe": "ADBE",
    "paypal": "PYPL",
    "palantir": "PLTR",
    "square": "SQ",
    "robinhood": "HOOD",
    "coinbase": "COIN",
    "s&p 500": "SPY",
    "spy": "SPY",
    "nasdaq": "QQQ",
    "qqq": "QQQ",
    "dow": "DIA",
    "russell": "IWM"
}

def extract_ticker_from_text(query: str) -> str:
    """
    Simple fallback ticker extraction using keyword matching
    """
    query_lower = query.lower()
    
    english_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'USE', 'MAN', 'NEW', 'NOW', 'WAY', 'MAY', 'SAY', 'WHAT', 'WHEN', 'WHERE', 'WHO', 'WHY', 'HOW', 'SOME', 'GOOD', 'BEST', 'TOP', 'ANY', 'WILL', 'SHOULD', 'COULD', 'WOULD'}
    
    # Check for exact ticker mentions (3-5 uppercase letters)
    import re
    ticker_pattern = r'\b([A-Z]{2,5})\b'
    matches = re.findall(ticker_pattern, query)
    if matches:
        # Filter out common English words
        for match in matches:
            if match not in english_words:
                return match
    
    # Check company name mappings
    for company, ticker in COMPANY_TO_TICKER.items():
        if company in query_lower:
            return ticker
    
    return "UNKNOWN"

def create_single_stock_analysis_prompt(query: str, ticker: str, context: str, conversation_history: str = None) -> str:
    """Create comprehensive stock analysis prompt"""
    history_section = ""
    if conversation_history:
        history_section = f"\n\nPrevious context:\n{conversation_history}"
    
    return f"""System: {MASTER_RESPONSE_SYSTEM}

Query: "{query}"
Ticker: {ticker}
Experience Level: INTERMEDIATE

Market Data:
{context}{history_section}

Analyze:
1. Price action and trends
2. Business fundamentals
3. News sentiment impact
4. Market positioning

Provide actionable investment insights."""

def create_fallback_single_stock_prompt(query: str, stock_data, conversation_history: str = None) -> str:
    """Create basic stock prompt when comprehensive data unavailable"""
    history_section = ""
    if conversation_history:
        history_section = f"\n\nPrevious context:\n{conversation_history}"
    
    return f"""Financial advisor analysis.

Query: "{query}"
Stock data: {stock_data}{history_section}

Provide clear analysis based on available information."""

def create_general_query_prompt(query: str, conversation_history: str = None) -> str:
    """Create prompt for general financial queries"""
    history_section = ""
    if conversation_history:
        history_section = f"\n\nPrevious context:\n{conversation_history}"
    
    return f"""Experienced wealth advisor responding to general financial query.

Query: "{query}"{history_section}

Respond appropriately:
1. Provide general financial advice/market outlook if applicable
2. Ask for specific ticker if stock query lacks company name
3. Request clarification if too vague

Be professional and guide toward specific questions when needed."""


