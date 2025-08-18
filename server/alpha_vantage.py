"""
Alpha Vantage API integrations for comprehensive market data
"""
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime


class AlphaVantageClient:
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.base_url = "https://www.alphavantage.co/query"
    
    def _make_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """Make API request"""
        try:
            params["apikey"] = self.api_key
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            return data if "Error Message" not in data else None
        except:
            return None
    
    def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """Get all available data for a symbol in one unified call"""
        # We'll make individual calls but collect all data at once
        all_data = {"symbol": symbol.upper(), "timestamp": datetime.now().isoformat(), "data_sources": []}
        
        # Define all the data sources we want to fetch
        data_sources = [
            ("GLOBAL_QUOTE", "stock_quote", self._parse_stock_quote),
            ("OVERVIEW", "company_overview", self._parse_company_overview),
            ("NEWS_SENTIMENT", "news_sentiment", self._parse_news_sentiment),
            ("EARNINGS", "earnings", self._parse_earnings),
            ("CASH_FLOW", "cash_flow", self._parse_cash_flow),
            ("BALANCE_SHEET", "balance_sheet", self._parse_balance_sheet),
            ("INCOME_STATEMENT", "income_statement", self._parse_income_statement)
        ]
        
        for function, key, parser in data_sources:
            try:
                if function == "NEWS_SENTIMENT":
                    params = {"function": function, "tickers": symbol, "limit": "5"}
                else:
                    params = {"function": function, "symbol": symbol}
                
                data = self._make_request(params)
                if data:
                    parsed_data = parser(data, symbol)
                    if parsed_data:
                        all_data[key] = parsed_data
                        all_data["data_sources"].append(key)
            except Exception as e:
                # Continue with other data sources if one fails
                print(f"Failed to fetch {function} for {symbol}: {e}")
                continue
        
        return all_data
    
    def _parse_stock_quote(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse stock quote data"""
        if "Global Quote" not in data:
            return None
            
        quote = data["Global Quote"]
        return {
            "symbol": symbol.upper(),
            "price": float(quote.get("05. price", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
            "volume": int(quote.get("06. volume", 0)),
            "source": "alpha_vantage"
        }
    
    def _parse_company_overview(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse company overview data"""
        if "Symbol" not in data:
            return None
            
        return {
            "symbol": data.get("Symbol"),
            "name": data.get("Name"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "dividend_yield": data.get("DividendYield"),
            "eps": data.get("EPS"),
            "profit_margin": data.get("ProfitMargin")
        }
    
    def _parse_news_sentiment(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse news sentiment data"""
        if "feed" not in data:
            return None
            
        articles = []
        for article in data.get("feed", [])[:5]:
            articles.append({
                "title": article.get("title"),
                "summary": article.get("summary"),
                "sentiment": article.get("overall_sentiment_label"),
                "source": article.get("source")
            })
        
        return {"symbol": symbol.upper(), "articles": articles}
    
    def _parse_earnings(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse earnings data"""
        if "quarterlyEarnings" not in data:
            return None
        
        # Get the most recent quarterly earnings
        recent_earnings = data["quarterlyEarnings"][:4] if data["quarterlyEarnings"] else []
        
        return {
            "symbol": symbol.upper(),
            "recent_quarters": recent_earnings
        }
    
    def _parse_cash_flow(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse cash flow data"""
        if "quarterlyReports" not in data:
            return None
        
        # Get most recent quarter
        recent_quarter = data["quarterlyReports"][0] if data["quarterlyReports"] else {}
        
        return {
            "symbol": symbol.upper(),
            "latest_quarter": recent_quarter
        }
    
    def _parse_balance_sheet(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse balance sheet data"""
        if "quarterlyReports" not in data:
            return None
        
        # Get most recent quarter
        recent_quarter = data["quarterlyReports"][0] if data["quarterlyReports"] else {}
        
        return {
            "symbol": symbol.upper(),
            "latest_quarter": recent_quarter
        }
    
    def _parse_income_statement(self, data: Dict, symbol: str) -> Optional[Dict]:
        """Parse income statement data"""
        if "quarterlyReports" not in data:
            return None
        
        # Get most recent quarter
        recent_quarter = data["quarterlyReports"][0] if data["quarterlyReports"] else {}
        
        return {
            "symbol": symbol.upper(),
            "latest_quarter": recent_quarter
        }
    
    # Legacy methods for backward compatibility
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time stock quote"""
        params = {"function": "GLOBAL_QUOTE", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_stock_quote(data, symbol) if data else None
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """Get company fundamental data"""
        params = {"function": "OVERVIEW", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_company_overview(data, symbol) if data else None
    
    def get_news_sentiment(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """Get market news for a stock"""
        params = {"function": "NEWS_SENTIMENT", "tickers": symbol, "limit": str(limit)}
        data = self._make_request(params)
        return self._parse_news_sentiment(data, symbol) if data else None
    
    def get_earnings(self, symbol: str) -> Optional[Dict]:
        """Get earnings data"""
        params = {"function": "EARNINGS", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_earnings(data, symbol) if data else None
    
    def get_cash_flow(self, symbol: str) -> Optional[Dict]:
        """Get cash flow data"""
        params = {"function": "CASH_FLOW", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_cash_flow(data, symbol) if data else None
    
    def get_balance_sheet(self, symbol: str) -> Optional[Dict]:
        """Get balance sheet data"""
        params = {"function": "BALANCE_SHEET", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_balance_sheet(data, symbol) if data else None
    
    def get_income_statement(self, symbol: str) -> Optional[Dict]:
        """Get income statement data"""
        params = {"function": "INCOME_STATEMENT", "symbol": symbol}
        data = self._make_request(params)
        return self._parse_income_statement(data, symbol) if data else None


def create_comprehensive_context(symbol: str) -> Dict[str, Any]:
    """Create context by fetching ALL available data for a symbol in one unified call"""
    client = AlphaVantageClient()
    return client.get_comprehensive_data(symbol)


def format_context_for_llm(context: Dict[str, Any]) -> str:
    """Format comprehensive context for LLM analysis"""
    symbol = context["symbol"]
    output = [f"COMPREHENSIVE MARKET DATA FOR {symbol}"]
    output.append(f"Data Sources: {', '.join(context.get('data_sources', []))}")
    output.append("")
    
    # Current Stock Performance
    if "stock_quote" in context:
        quote = context["stock_quote"]
        output.append("📈 CURRENT PERFORMANCE:")
        output.append(f"  Price: ${quote['price']:.2f}")
        output.append(f"  Change: {quote['change_percent']}%")
        if 'volume' in quote:
            output.append(f"  Volume: {quote['volume']:,}")
        output.append("")
    
    # Company Fundamentals
    if "company_overview" in context:
        overview = context["company_overview"]
        output.append("🏢 COMPANY FUNDAMENTALS:")
        output.append(f"  Name: {overview.get('name', 'N/A')}")
        output.append(f"  Sector: {overview.get('sector', 'N/A')}")
        output.append(f"  Industry: {overview.get('industry', 'N/A')}")
        if overview.get("market_cap"):
            output.append(f"  Market Cap: ${overview['market_cap']}")
        if overview.get("pe_ratio"):
            output.append(f"  P/E Ratio: {overview['pe_ratio']}")
        if overview.get("eps"):
            output.append(f"  EPS: ${overview['eps']}")
        if overview.get("dividend_yield"):
            output.append(f"  Dividend Yield: {overview['dividend_yield']}")
        output.append("")
    
    # Recent Earnings
    if "earnings" in context:
        earnings = context["earnings"]
        if earnings.get("recent_quarters"):
            output.append("📊 RECENT EARNINGS:")
            for i, quarter in enumerate(earnings["recent_quarters"][:2]):
                quarter_date = quarter.get("fiscalDateEnding", "N/A")
                eps = quarter.get("reportedEPS", "N/A")
                output.append(f"  Q{i+1} ({quarter_date}): EPS ${eps}")
        output.append("")
    
    # Financial Health (from statements)
    if "balance_sheet" in context:
        bs = context["balance_sheet"].get("latest_quarter", {})
        output.append("💰 FINANCIAL POSITION:")
        if bs.get("totalAssets"):
            output.append(f"  Total Assets: ${bs['totalAssets']}")
        if bs.get("totalShareholderEquity"):
            output.append(f"  Shareholder Equity: ${bs['totalShareholderEquity']}")
        output.append("")
    
    if "cash_flow" in context:
        cf = context["cash_flow"].get("latest_quarter", {})
        output.append("💸 CASH FLOW:")
        if cf.get("operatingCashflow"):
            output.append(f"  Operating Cash Flow: ${cf['operatingCashflow']}")
        if cf.get("capitalExpenditures"):
            output.append(f"  Capital Expenditures: ${cf['capitalExpenditures']}")
        output.append("")
    
    if "income_statement" in context:
        income = context["income_statement"].get("latest_quarter", {})
        output.append("📈 PROFITABILITY:")
        if income.get("totalRevenue"):
            output.append(f"  Revenue: ${income['totalRevenue']}")
        if income.get("netIncome"):
            output.append(f"  Net Income: ${income['netIncome']}")
        output.append("")
    
    # Market Sentiment & News
    if "news_sentiment" in context:
        news = context["news_sentiment"]
        if news.get("articles"):
            output.append("📰 RECENT NEWS & SENTIMENT:")
            for article in news["articles"][:3]:
                title = article.get('title', 'N/A')
                sentiment = article.get('sentiment', 'Neutral')
                source = article.get('source', 'Unknown')
                output.append(f"  • {title} ({sentiment}) - {source}")
        output.append("")
    
    return "\n".join(output)
