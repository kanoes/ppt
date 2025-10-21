from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Source(BaseModel):
    title: str
    link: str


class IndicatorChart(BaseModel):
    title: Optional[str] = None
    encodedImage: str


class Assets(BaseModel):
    indicatorCharts: Optional[List[IndicatorChart]] = None
    sourceList: Optional[List[Source]] = None


class GenerateQuery(BaseModel):
    userName: str
    conversation: List[Dict[str, Any]]
    threadId: str
    assets: Optional[Assets] = None

