from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any


class Source(BaseModel):
    """引用元情報"""
    title: str
    link: str


class IndicatorChart(BaseModel):
    """チャート情報"""
    title: Optional[str] = None
    encodedImage: str = None


class Assets(BaseModel):
    """Assets情報"""
    indicatorCharts: Optional[List[IndicatorChart]] = None
    sourceList: Optional[List[Source]] = None


class GenerateQuery(BaseModel):
    """PPT生成クエリモデル"""
    userName: str
    conversation: List[Dict[str, Any]]
    threadId: str
    assets: Optional[Assets] = None
    generatedAt: Optional[str] = None