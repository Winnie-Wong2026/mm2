from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Market = Literal["cn", "hk"]
Frequency = Literal["daily", "weekly"]
Role = Literal["admin", "researcher", "viewer"]
RiskLevel = Literal["低", "中", "中高", "高"]


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserPublic(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: Role


class WatchlistCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    note: Optional[str] = None


class RankingItem(BaseModel):
    symbol: str
    name: str
    market: Market
    exchange: str
    industry: str
    rank: int
    score: float
    risk_level: RiskLevel
    horizon: str
    reason_summary: str
    positive_factors: List[str]
    negative_factors: List[str]
    updated_at: str


class StrategySummary(BaseModel):
    strategy_id: str
    name: str
    description: str
    model_type: str
    frequency: Frequency
    markets: List[Market]
    enabled: bool
    is_default: bool


class FactorSummary(BaseModel):
    factor_name: str
    factor_label: str
    score: float
    explanation: str


class PricePoint(BaseModel):
    trade_date: str
    close: float
    amount: float


class StockDetail(BaseModel):
    symbol: str
    name: str
    market: Market
    exchange: str
    industry: str
    score: float
    rank: int
    risk_level: RiskLevel
    horizon: str
    reason_summary: str
    advantages: List[str]
    risks: List[str]
    recent_performance: Dict[str, float]
    factor_summary: List[FactorSummary]
    price_series: List[PricePoint]
    updated_at: str


class WatchlistItem(BaseModel):
    symbol: str
    name: str
    market: Market
    risk_level: RiskLevel
    latest_rank: Optional[int]
    latest_score: Optional[float]
    still_on_ranking: bool
    note: Optional[str]
    created_at: str


class ReportSummary(BaseModel):
    report_id: str
    title: str
    frequency: Frequency
    markets: List[Market]
    summary: str
    published_at: str


class ReportSection(BaseModel):
    heading: str
    content: str


class ReportDetail(ReportSummary):
    sections: List[ReportSection]
    risk_notice: str


class TaskItem(BaseModel):
    task_id: str
    task_name: str
    status: str
    started_at: Optional[str]
    finished_at: Optional[str]
    message: str


class TaskStatus(BaseModel):
    as_of: str
    latest_data_update_at: str
    latest_ranking_generated_at: str
    latest_report_generated_at: str
    tasks: List[TaskItem]
    failed_tasks: List[Dict[str, Any]]
