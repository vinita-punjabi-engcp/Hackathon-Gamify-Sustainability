import datetime
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 🔌 SQL DATABASE CONFIGURATION ---
# Using a local SQLite file 'greenops.db' for easy hackathon portability.
# For SQL Server/Postgres, swap out the string to: "postgresql://user:pass@localhost/db"
DATABASE_URL = "sqlite:///./greenops.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 🗄️ SQL DATA MODEL DEFINITION ---
class TeamMetricModel(Base):
    __tablename__ = "team_sustainability_metrics"

    # User specified constraints
    team_name = Column(String, primary_key=True, index=True) # Primary Key
    namespace = Column(String, nullable=False)
    region = Column(String, default="westus3")
    service_name = Column(String, default="search-service")
    
    # Telemetry Input Columns
    cpu_usage_cores = Column(Float, default=0.0)      # Raw telemetry CPU
    memory_usage_gb = Column(Float, default=0.0)      # Raw telemetry RAM
    resource_quota_cpu = Column(Float, default=1.0)   # Requested/Allocated Ceiling
    resource_quota_mem = Column(Float, default=4.0)   
    
    # Calculated Output Columns (Stored for high performance dashboards)
    efficiency_score_pct = Column(Float, default=0.0)
    yesterday_carbon_kg = Column(Float, default=0.0)
    wasted_carbon_kg = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)


# Automatically create the database file and tables on app launch
Base.metadata.create_all(bind=engine)


# --- 🧮 GREENOPS CARBON ENGINE ---
REGIONAL_CARBON_INTENSITY = {"westus3": 0.35, "westeurope": 0.22, "default": 0.30}

def run_sustainability_math(model: TeamMetricModel) -> TeamMetricModel:
    """Mutates the SQL model instance with fresh carbon and efficiency scores."""
    intensity = REGIONAL_CARBON_INTENSITY.get(model.region, REGIONAL_CARBON_INTENSITY["default"])

    # Daily Carbon = Cores * Core Power (5W) * 24h / 1000 * regional grid intensity
    model.yesterday_carbon_kg = round(((model.cpu_usage_cores * 5 * 24) / 1000) * intensity, 3)

    # Calculate Wasted Carbon from Over-provisioning
    wasted_cores = max(0, model.resource_quota_cpu - model.cpu_usage_cores)
    model.wasted_carbon_kg = round(((wasted_cores * 5 * 24) / 1000) * intensity, 3)

    # Efficiency % = (Used Cores / Quota Cores) * 100
    model.efficiency_score_pct = round((model.cpu_usage_cores / model.resource_quota_cpu) * 100, 1) if model.resource_quota_cpu > 0 else 0.0
    model.last_updated = datetime.datetime.utcnow()
    return model


# --- 🧪 DATABASE DEPENDENCY INJECTION ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 🌐 FASTAPI APPLICATION ---
app = FastAPI(title="EcoTrace AI - SQL Integrated GreenOps Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 🗂️ PYDANTIC RESPONSE SCHEMAS ---
class TeamMetricsResponse(BaseModel):
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

    class Config:
        from_attributes = True


class LeaderboardMetadata(BaseModel):
    total_teams_logged: int
    sorting_metric: str
    retrieved_at: str
    total_carbon_kg: float
    total_wasted_kg: float
    avg_efficiency_pct: float

    class Config:
        from_attributes = True


# --- 🌐 API ENDPOINTS ---

# API 1: Granular Team Inspection API
# API 1: Granular Team Inspection API (FIXED)
@app.get("/api/team-metrics", response_model=TeamMetricsResponse)
def get_team_metrics(team_name: str = Query(..., description="Primary Key identifier"), db: Session = Depends(get_db)):
    """Fetches a team's real-time dataset from the SQL database and attaches localized mitigation logs."""
    team_record = db.query(TeamMetricModel).filter(TeamMetricModel.team_name == team_name).first()
    
    if not team_record:
        raise HTTPException(status_code=404, detail=f"Team record '{team_name}' not found in the SQL Database.")

    # Always ensure math engine processes the state cleanly and save it to the DB
    processed = run_sustainability_math(team_record)
    db.commit()

    # 1. Generate dynamic prompt heuristics based on the freshly calculated metrics
    strategies = []
    if processed.efficiency_score_pct < 30.0:
        strategies.append(
            f"CRITICAL INEFFICIENCY: Operating at {processed.efficiency_score_pct}%. "
            f"Truncate resource quotas by {round(processed.resource_quota_cpu - processed.cpu_usage_cores, 1)} cores "
            f"to mitigate unnecessary emissions."
        )
    else:
        strategies.append("OPTIMAL BOUNDS: Current allocation meets green target criteria smoothly.")

    # Calculate waste ratio
    total_carbon = processed.yesterday_carbon_kg + processed.wasted_carbon_kg
    waste_ratio = round(processed.wasted_carbon_kg / total_carbon, 3) if total_carbon > 0 else 0.0

    # 2. FIXED LOGIC: Manually assemble the Pydantic response model to cleanly bridge 
    # the SQL table columns with our runtime dynamic strategy list
    return TeamMetricsResponse(
        team_name=processed.team_name,
        namespace=processed.namespace,
        region=processed.region,
        service_name=processed.service_name,
        cpu_usage_cores=processed.cpu_usage_cores,
        memory_usage_gb=processed.memory_usage_gb,
        resource_quota_cpu=processed.resource_quota_cpu,
        resource_quota_mem=processed.resource_quota_mem,
        efficiency_score_pct=processed.efficiency_score_pct,
        yesterday_carbon_kg=processed.yesterday_carbon_kg,
        wasted_carbon_kg=processed.wasted_carbon_kg,
        waste_ratio=waste_ratio,
        ai_mitigation_strategies=strategies  # Clean injection without schema validation crashes!
    )

# API 2: Leaderboard API (Top 5 & Bottom 5 from DB)
@app.get("/api/leaderboard")
def get_leaderboard(sort_by: str = Query("efficiency", description="Sort criteria: 'efficiency' or 'carbon'"), db: Session = Depends(get_db)):
    """Queries the SQL backend to render partitioned Top 5 and Bottom 5 arrays."""
    all_records = db.query(TeamMetricModel).all()
    
    # Refresh sustainability variables for consistency
    processed_list = []
    for record in all_records:
        mutated = run_sustainability_math(record)
        total_carbon = mutated.yesterday_carbon_kg + mutated.wasted_carbon_kg
        waste_ratio = round(mutated.wasted_carbon_kg / total_carbon, 3) if total_carbon > 0 else 0.0
        processed_list.append({
            "team_name": mutated.team_name,
            "namespace": mutated.namespace,
            "region": mutated.region,
            "efficiency_score_pct": mutated.efficiency_score_pct,
            "yesterday_carbon_kg": mutated.yesterday_carbon_kg,
            "wasted_carbon_kg": mutated.wasted_carbon_kg,
            "waste_ratio": waste_ratio
        })
    db.commit()

    # Calculate aggregates BEFORE sorting
    total_carbon = sum(item["yesterday_carbon_kg"] for item in processed_list)
    total_wasted = sum(item["wasted_carbon_kg"] for item in processed_list)
    avg_efficiency = round(sum(item["efficiency_score_pct"] for item in processed_list) / len(processed_list), 1) if processed_list else 0.0

    # Sort logic
    if sort_by == "carbon":
        processed_list.sort(key=lambda x: x["yesterday_carbon_kg"])
    else:
        processed_list.sort(key=lambda x: x["efficiency_score_pct"], reverse=True)

    # Inject static rankings
    for index, item in enumerate(processed_list, start=1):
        item["rank_placement"] = index

    top_five = processed_list[:5]
    bottom_five = processed_list[-5:] if len(processed_list) > 5 else []
    bottom_five.reverse() # Show lowest performer at base of list

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


# --- 🧪 OPTIONAL: SEED SCRIPT FOR HACKATHON DEMO ---
@app.post("/api/admin/seed-mock-database", tags=["Admin Tools"])
def seed_database(db: Session = Depends(get_db)):
    """Helper route to instantly populate your empty SQL file with test metrics."""
    test_teams = [
        TeamMetricModel(team_name="Core Search", namespace="1ds-app", region="westus3", cpu_usage_cores=4.2, memory_usage_gb=16.0, resource_quota_cpu=12.0, resource_quota_mem=32.0),
        TeamMetricModel(team_name="CLM Lifecycle", namespace="clm-indexing", region="westeurope", cpu_usage_cores=7.8, memory_usage_gb=28.5, resource_quota_cpu=8.0, resource_quota_mem=32.0),
        TeamMetricModel(team_name="NLP Processing", namespace="query-parser", region="westus3", cpu_usage_cores=0.5, memory_usage_gb=4.0, resource_quota_cpu=6.0, resource_quota_mem=16.0),
        TeamMetricModel(team_name="Envelope Signing", namespace="signing-core", region="westeurope", cpu_usage_cores=45.2, memory_usage_gb=128.0, resource_quota_cpu=50.0, resource_quota_mem=256.0),
        TeamMetricModel(team_name="Identity Broker", namespace="identity-auth", region="westeurope", cpu_usage_cores=14.1, memory_usage_gb=32.0, resource_quota_cpu=20.0, resource_quota_mem=64.0),
        TeamMetricModel(team_name="Connect Publisher", namespace="webhooks-pub", region="westus3", cpu_usage_cores=1.2, memory_usage_gb=4.0, resource_quota_cpu=16.0, resource_quota_mem=32.0)
    ]
    
    # Wipe old test states if any exist to avoid constraint duplication conflicts
    db.query(TeamMetricModel).delete()
    db.add_all(test_teams)
    db.commit()
    return {"status": "Database successfully populated with relational search-domain records!"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)