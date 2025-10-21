from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Source(BaseModel):
    """Reference source information"""
    title: str
    link: str


class IndicatorChart(BaseModel):
    """Chart information with encoded image"""
    title: Optional[str] = None
    encodedImage: str = None


class Assets(BaseModel):
    """Assets containing charts and sources"""
    indicatorCharts: Optional[List[IndicatorChart]] = None
    sourceList: Optional[List[Source]] = None


class GenerateQuery(BaseModel):
    """Request schema for presentation generation"""
    userName: str
    conversation: List[Dict[str, Any]]
    threadId: str
    assets: Optional[Assets] = None
