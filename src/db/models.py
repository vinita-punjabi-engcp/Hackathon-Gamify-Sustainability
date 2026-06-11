from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from src.db.session import Base

class ClusterMetric(Base):
    __tablename__ = "cluster_metrics"
    id = Column(Integer, primary_key=True, index=True)
    namespace = Column(String, index=True, nullable=False)
    active_cores = Column(Float, nullable=False)
    carbon_co2g = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class PipelineMetric(Base):
    __tablename__ = "pipeline_metrics"
    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(Integer, unique=True, index=True, nullable=False)
    pipeline_name = Column(String, nullable=False)
    duration_mins = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    result = Column(String, nullable=False)
    carbon_co2g = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class TeamMetricModel(Base):
    __tablename__ = "team_sustainability_metrics"
    team_name = Column(String, primary_key=True, index=True)
    namespace = Column(String, nullable=False, index=True)
    region = Column(String, default="eastus")
    service_name = Column(String, default="search-service")
    resource_quota_cpu = Column(Float, default=8.0)   # Default ceiling for efficiency scores
    resource_quota_mem = Column(Float, default=32.0)