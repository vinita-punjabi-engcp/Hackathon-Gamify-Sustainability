from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime

class NamespaceMetrics(BaseModel):
    """The strict data contract for Kubernetes namespace utilization."""
    namespace: str
    active_cores: float = Field(default=0.0, ge=0.0) # Must be greater than or equal to 0

class PipelineRun(BaseModel):
    """The strict data contract for a single CI/CD pipeline execution."""
    build_id: int
    pipeline_name: str
    status: str
    result: Optional[str] = "unknown"
    
    # We use datetime objects so Pydantic automatically parses the ISO strings!
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None

    @computed_field
    @property
    def duration_mins(self) -> float:
        """Dynamically calculates duration whenever the object is created."""
        if self.start_time and self.finish_time:
            duration_seconds = (self.finish_time - self.start_time).total_seconds()
            return max(0.0, duration_seconds / 60.0)
        return 0.0