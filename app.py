import datetime
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.db.session import engine, SessionLocal, Base
from src.db.models import ClusterMetric, PipelineMetric, TeamMetricModel

# Compile all structural tables cleanly on startup
Base.metadata.create_all(bind=engine)

# --- 🧮 HYBRID SUSTAINABILITY LOGIC ENGINE ---
def compute_live_metrics(namespace: str, db: Session, team_meta: Optional[TeamMetricModel] = None) -> dict:
    """
    Dynamically merges configuration limits with live telemetry data 
    for ANY namespace discovered by the system.
    """
    # 1. Fetch the absolute latest snapshot from our Prometheus tracking table
    latest_snapshot = db.query(ClusterMetric)\
                        .filter(ClusterMetric.namespace == namespace)\
                        .order_by(desc(ClusterMetric.recorded_at))\
                        .first()
    
    active_cores = latest_snapshot.active_cores if latest_snapshot else 0.0
    yesterday_carbon_kg = round((latest_snapshot.carbon_co2g / 1000.0), 4) if latest_snapshot else 0.0

    # 2. Extract quotas or fall back to default constraints if unconfigured
    team_name = team_meta.team_name if team_meta else f"{namespace.capitalize()}"
    region = team_meta.region if team_meta else "eastus"
    service_name = team_meta.service_name if team_meta else f"{namespace}-service"
    quota_cpu = team_meta.resource_quota_cpu if team_meta else 8.0
    quota_mem = team_meta.resource_quota_mem if team_meta else 32.0

    # 3. Calculate operational sustainability math
    efficiency_score = round((active_cores / quota_cpu) * 100, 1) if quota_cpu > 0 else 0.0
    wasted_cores = max(0.0, quota_cpu - active_cores)
    
    # 10W per core * 24 Hours * 1.15 PUE * 350g Carbon Intensity / 1000g to get kg
    wasted_carbon_kg = round(((wasted_cores * 10 * 24 * 1.15 * 0.350) / 1000.0), 4)
    total_carbon = yesterday_carbon_kg + wasted_carbon_kg
    waste_ratio = round(wasted_carbon_kg / total_carbon, 3) if total_carbon > 0 else 0.0

    return {
        "team_name": team_name,
        "namespace": namespace,
        "region": region,
        "service_name": service_name,
        "cpu_usage_cores": active_cores,
        "memory_usage_gb": 16.0, # Placeholder telemetry
        "resource_quota_cpu": quota_cpu,
        "resource_quota_mem": quota_mem,
        "efficiency_score_pct": min(100.0, efficiency_score),
        "yesterday_carbon_kg": yesterday_carbon_kg,
        "wasted_carbon_kg": wasted_carbon_kg,
        "waste_ratio": waste_ratio
    }

# --- 🧪 DATABASE DEPENDENCY INJECTION ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 🌐 FASTAPI APPLICATION ---
app = FastAPI(title="EcoTrace AI - Auto-Scaling GreenOps Engine", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🗂️ MODERN PYDANTIC SCHEMAS (V2 COMPLIANT) ---
class TeamMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Modern Pydantic V2 Syntax
    
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

# --- 🌐 REST API ENDPOINTS ---

@app.get("/api/team-metrics", response_model=TeamMetricsResponse)
def get_team_metrics(team_name: str = Query(..., description="Target configuration identifier"), db: Session = Depends(get_db)):
    """Looks up a profile by name, fallback checks by namespace, and extracts dynamic calculations."""
    # Try finding configuration limits by Team Name or directly by Namespace match
    meta_record = db.query(TeamMetricModel).filter(
        (TeamMetricModel.team_name == team_name) | (TeamMetricModel.namespace == team_name)
    ).first()
    
    target_namespace = meta_record.namespace if meta_record else team_name
    
    # Run core analytics calculations
    data = compute_live_metrics(namespace=target_namespace, db=db, team_meta=meta_record)

    strategies = []
    if data["efficiency_score_pct"] < 40.0:
        strategies.append(
            f"POTENTIAL OVER-PROVISIONING: System is running at {data['efficiency_score_pct']}% efficiency. "
            f"Reducing resource limits closer to your active load will save up to {data['wasted_carbon_kg']}kg of idle CO2."
        )
    else:
        strategies.append("OPTIMAL TARGET BOUNDS: Allocation metrics match sustainability standards.")

    return TeamMetricsResponse(**data, ai_mitigation_strategies=strategies)


@app.get("/api/leaderboard")
def get_leaderboard(sort_by: str = Query("efficiency", description="Criteria: 'efficiency' or 'carbon'"), db: Session = Depends(get_db)):
    """Discovers ALL active namespaces in telemetry history and formats an aggregated leaderboard."""
    # Dynamic Discovery: Find every single unique namespace currently saved in your tracking tables
    unique_namespaces = db.query(ClusterMetric.namespace).distinct().all()
    
    processed_list = []
    for (ns,) in unique_namespaces:
        meta_record = db.query(TeamMetricModel).filter(TeamMetricModel.namespace == ns).first()
        metrics_computed = compute_live_metrics(namespace=ns, db=db, team_meta=meta_record)
        if metrics_computed["cpu_usage_cores"] > 0.1:
            processed_list.append(metrics_computed)
        processed_list.append(metrics_computed)

    # Compute Global Shared Aggregates for UI Header Panels
    total_carbon = sum(item["yesterday_carbon_kg"] for item in processed_list)
    total_wasted = sum(item["wasted_carbon_kg"] for item in processed_list)
    avg_efficiency = round(sum(item["efficiency_score_pct"] for item in processed_list) / len(processed_list), 1) if processed_list else 0.0

    if sort_by == "carbon":
        processed_list.sort(key=lambda x: x["yesterday_carbon_kg"])
    else:
        processed_list.sort(key=lambda x: x["efficiency_score_pct"], reverse=True)

    for index, item in enumerate(processed_list, start=1):
        item["rank_placement"] = index

    top_five = processed_list[:5]
    bottom_five = processed_list[-5:] if len(processed_list) > 5 else []
    bottom_five.reverse()

    return {
        "metadata": {
            "total_teams_logged": len(processed_list),
            "sorting_metric": sort_by,
            "retrieved_at": datetime.datetime.utcnow().isoformat(),
            "total_carbon_kg": round(total_carbon, 3),
            "total_wasted_kg": round(total_wasted, 3),
            "avg_efficiency_pct": avg_efficiency
        },
        "top_performers_green_zone": top_five,
        "bottom_performers_action_required": bottom_five
    }

@app.post("/api/admin/seed-mock-database", tags=["Admin Tools"])
def seed_database(db: Session = Depends(get_db)):
    """Optional meta mapper to attach friendly team profiles to ingestion targets."""
    test_teams = [
        TeamMetricModel(team_name="Core Search Engine", namespace="search", region="eastus", resource_quota_cpu=8.0),
        TeamMetricModel(team_name="1DS Collection Unit", namespace="1ds-app", region="eastus", resource_quota_cpu=16.0)
    ]
    db.query(TeamMetricModel).delete()
    db.add_all(test_teams)
    db.commit()
    return {"status": "Registry metadata linked successfully."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)


class SearchSuggestion(BaseModel):
    team_name: str
    namespace: str

class SearchResponse(BaseModel):
    query_string: str
    total_matches_found: int
    options: List[SearchSuggestion]

@app.get("/api/search", response_model=SearchResponse)
def search_teams_only(
    query: str = Query(..., description="Case-insensitive search string targeting Team Names only"),
    db: Session = Depends(get_db)
):
    """
    Scans the database columns matching 'team_name' against partial user inputs.
    Returns clean key-value pairs to populate frontend interactive dropdown menus.
    """
    if not query.strip():
        return {"query_string": query, "total_matches_found": 0, "options": []}

    # Format query for case-insensitive SQL matching (e.g., "%1ds%")
    search_term = f"%{query.lower()}%"

    # Query strictly against the team_name column
    matched_records = db.query(TeamMetricModel).filter(
        TeamMetricModel.team_name.cast(String).ilike(search_term)
    ).all()

    # Format the payload to supply options for the user interface dropdown
    dropdown_options = [
        SearchSuggestion(team_name=record.team_name, namespace=record.namespace)
        for record in matched_records
    ]

    return SearchResponse(
        query_string=query,
        total_matches_found=len(dropdown_options),
        options=dropdown_options
    )