from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime


class ConversationEntry(BaseModel):
    timestamp: datetime
    query: str
    response: str
    ticker: str
    
class RoboAdvisorRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None


# Structured output schemas for OpenAI
class QueryStructure(BaseModel):
    ticker: str
    query_type: str
    time_frame: str
    intent: str


class UserLevel(BaseModel):
    level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]


class StructuredQuery(BaseModel):
    ticker: str
    query_type: str
    time_frame: str
    intent: str


class StockData(BaseModel):
    symbol: str
    name: Optional[str] = None
    price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[str] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = Field(None, alias="52_week_high")
    week_52_low: Optional[float] = Field(None, alias="52_week_low")
    sector: Optional[str] = None
    industry: Optional[str] = None
    source: str
    note: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            float: lambda v: v if v is not None else 0,
            int: lambda v: v if v is not None else 0,
            str: lambda v: v if v is not None else "N/A"
        }


class RoboAdvisorResponse(BaseModel):
    response: str
    structured_query: StructuredQuery
    user_level: str
    stock_data: Optional[StockData] = None
    comprehensive_context: Optional[Dict[str, Any]] = None
    original_query: str
    session_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            float: lambda v: v if v is not None else 0,
            int: lambda v: v if v is not None else 0,
            str: lambda v: v if v is not None else "N/A"
        }
