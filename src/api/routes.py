"""HTTP route definitions. Routes are thin and delegate to the service layer."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas import SearchResponse, TeamMetricsResponse
from src.services.sustainability_service import SustainabilityService

router = APIRouter(prefix="/api")


@router.get("/team-metrics", response_model=TeamMetricsResponse)
def get_team_metrics(
    team_name: str = Query(..., description="Target configuration identifier"),
    db: Session = Depends(get_db),
):
    """Detailed metrics and AI mitigation guidance for a single team / namespace."""
    return SustainabilityService(db).get_team_metrics(team_name)


@router.get("/leaderboard")
def get_leaderboard(
    sort_by: str = Query("efficiency", description="Criteria: 'efficiency' or 'carbon'"),
    db: Session = Depends(get_db),
):
    """Aggregated leaderboard across all active namespaces."""
    return SustainabilityService(db).get_leaderboard(sort_by)


@router.get("/search", response_model=SearchResponse)
def search(
    query: str = Query(..., description="Case-insensitive search across namespace and team name"),
    sort_by: str = Query("efficiency", description="Ranking criteria: 'efficiency' or 'carbon'"),
    db: Session = Depends(get_db),
):
    """Server-side namespace search returning full leaderboard rows for the UI dropdown."""
    return SustainabilityService(db).search(query, sort_by)


@router.post("/admin/seed-mock-database", tags=["Admin Tools"])
def seed_database(db: Session = Depends(get_db)):
    """Optional meta mapper to attach friendly team profiles to ingestion targets."""
    return SustainabilityService(db).seed_mock_metadata()
