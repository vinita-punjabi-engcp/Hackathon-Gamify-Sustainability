"""
Pluggable efficiency-scoring strategies (Strategy pattern).

Each scorer maps a single namespace's telemetry to a 0-100 "efficiency" score
that the leaderboard ranks on. Scoring philosophies are interchangeable: adding
a new one means subclassing EfficiencyScorer and registering it here — the
service and routes stay untouched.

Active default: AverageUtilizationScorer.
Retained for derivative use cases: GreenScoreScorer.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import ClusterMetric


@dataclass
class ScoringContext:
    """Everything a scorer may need to evaluate one namespace.

    Carrying a context object (rather than a long arg list) keeps the
    EfficiencyScorer.score signature stable as new strategies need new inputs.
    """
    db: Session
    namespace: str
    active_cores: float  # latest telemetry snapshot
    quota_cpu: float


class EfficiencyScorer(ABC):
    """Strategy interface: telemetry -> efficiency score in [0, 100]."""

    #: Stable identifier used for registration and selection.
    name: str = "base"

    @abstractmethod
    def score(self, ctx: ScoringContext) -> float:
        """Return this namespace's efficiency score in the range [0, 100]."""
        raise NotImplementedError


class AverageUtilizationScorer(EfficiencyScorer):
    """Average utilization of the reserved CPU quota.

    A low score means the team reserves far more than it uses on average
    (over-provisioned / wasteful). This is the active default metric.
    """

    name = "average_utilization"

    def score(self, ctx: ScoringContext) -> float:
        if ctx.quota_cpu <= 0:
            return 0.0
        avg_cores = (
            ctx.db.query(func.avg(ClusterMetric.active_cores))
            .filter(ClusterMetric.namespace == ctx.namespace)
            .scalar()
        ) or 0.0
        return min(100.0, round((float(avg_cores) / ctx.quota_cpu) * 100, 1))


class GreenScoreScorer(EfficiencyScorer):
    """Percentile rank: percentage of namespaces consuming MORE cores on average.

    Higher means a lighter consumer relative to peers. Quota-independent, so it
    is useful for peer-relative carbon views even though it does not reflect
    provisioning efficiency.
    """

    name = "green_score"

    def score(self, ctx: ScoringContext) -> float:
        subq = (
            ctx.db.query(func.avg(ClusterMetric.active_cores).label("avg_cores"))
            .group_by(ClusterMetric.namespace)
            .subquery()
        )
        total = ctx.db.query(func.count()).select_from(subq).scalar() or 1
        heavier = (
            ctx.db.query(func.count())
            .select_from(subq)
            .filter(subq.c.avg_cores > ctx.active_cores)
            .scalar()
        ) or 0
        return round((heavier / total) * 100, 1)


# --- registry -------------------------------------------------------------
DEFAULT_SCORER = "average_utilization"

_SCORERS = {
    scorer.name: scorer
    for scorer in (AverageUtilizationScorer(), GreenScoreScorer())
}


def get_scorer(name: str = DEFAULT_SCORER) -> EfficiencyScorer:
    """Resolve a scorer by name, falling back to the default strategy."""
    return _SCORERS.get(name, _SCORERS[DEFAULT_SCORER])


def available_scorers() -> List[str]:
    """Names of all registered scoring strategies."""
    return list(_SCORERS)
