"""Pydantic V2 response schemas for the EcoTrace AI API."""
from typing import List

from pydantic import BaseModel, ConfigDict


class TeamMetricsResponse(BaseModel):
    """Detailed sustainability profile for a single team / namespace."""
    model_config = ConfigDict(from_attributes=True)

    team_name: str
    namespace: str
    region: str
    service_name: str
    cpu_usage_cores: float
    memory_usage_gb: float
    resource_quota_cpu: float
    resource_quota_mem: float
    efficiency_score_pct: float
    yesterday_carbon_kg: float
    wasted_carbon_kg: float
    waste_ratio: float
    ai_mitigation_strategies: List[str]


class SearchResultEntry(BaseModel):
    """Mirrors a leaderboard row so the UI dropdown can render results identically."""
    team_name: str
    namespace: str
    region: str
    efficiency_score_pct: float
    yesterday_carbon_kg: float
    wasted_carbon_kg: float
    waste_ratio: float
    rank_placement: int


class SearchResponse(BaseModel):
    query: str
    total_matches_found: int
    results: List[SearchResultEntry]
