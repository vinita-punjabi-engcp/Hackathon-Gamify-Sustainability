"""
Business-logic layer for GreenOps sustainability analytics.

Merges live telemetry (ClusterMetric) with team configuration
(TeamMetricModel) to produce per-team metrics, the aggregated leaderboard,
and server-side search results. Routes stay thin by delegating here.
"""
import datetime
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.db.models import ClusterMetric, TeamMetricModel

# Carbon model constants (10W per core * 24h * Azure PUE * grid intensity).
_WATTS_PER_CORE = 10
_HOURS_PER_DAY = 24
_AZURE_PUE = 1.15
_GRID_INTENSITY_KG_PER_KWH = 0.350

# Seed profiles used by the admin mock-database endpoint.
_MOCK_TEAMS = [
    {"team_name": "Core Search Engine", "namespace": "search", "region": "eastus", "resource_quota_cpu": 8.0},
    {"team_name": "1DS Collection Unit", "namespace": "1ds-app", "region": "eastus", "resource_quota_cpu": 16.0},
]


class SustainabilityService:
    """Stateless-per-request service bound to a single SQLAlchemy session."""

    def __init__(self, db: Session):
        self.db = db

    # --- internal helpers -------------------------------------------------
    def _green_score(self, active_cores: float) -> float:
        """Percentile rank: % of namespaces consuming MORE cores. Higher = greener."""
        subq = (
            self.db.query(func.avg(ClusterMetric.active_cores).label("avg_cores"))
            .group_by(ClusterMetric.namespace)
            .subquery()
        )
        total = self.db.query(func.count()).select_from(subq).scalar() or 1
        heavier = self.db.query(func.count()).select_from(subq).filter(subq.c.avg_cores > active_cores).scalar() or 0
        return round((heavier / total) * 100, 1)

    def _meta_for(self, namespace: str) -> Optional[TeamMetricModel]:
        return (
            self.db.query(TeamMetricModel)
            .filter(TeamMetricModel.namespace == namespace)
            .first()
        )

    def compute_live_metrics(self, namespace: str, team_meta: Optional[TeamMetricModel] = None) -> dict:
        """
        Dynamically merges configuration limits with live telemetry data
        for ANY namespace discovered by the system.
        """
        # 1. Fetch the absolute latest snapshot from the Prometheus tracking table
        latest_snapshot = (
            self.db.query(ClusterMetric)
            .filter(ClusterMetric.namespace == namespace)
            .order_by(desc(ClusterMetric.recorded_at))
            .first()
        )

        active_cores = latest_snapshot.active_cores if latest_snapshot else 0.0
        yesterday_carbon_kg = round((latest_snapshot.carbon_co2g / 1000.0), 4) if latest_snapshot else 0.0

        # 2. Extract quotas or fall back to default constraints if unconfigured
        team_name = team_meta.team_name if team_meta else f"{namespace.capitalize()}"
        region = team_meta.region if team_meta else "eastus"
        service_name = team_meta.service_name if team_meta else f"{namespace}-service"
        quota_cpu = team_meta.resource_quota_cpu if team_meta else 8.0
        quota_mem = team_meta.resource_quota_mem if team_meta else 32.0

        # 3. Calculate operational sustainability math
        green_score = self._green_score(active_cores)
        wasted_cores = max(0.0, quota_cpu - active_cores)
        wasted_carbon_kg = round(
            (wasted_cores * _WATTS_PER_CORE * _HOURS_PER_DAY * _AZURE_PUE * _GRID_INTENSITY_KG_PER_KWH) / 1000.0,
            4,
        )
        total_carbon = yesterday_carbon_kg + wasted_carbon_kg
        waste_ratio = round(wasted_carbon_kg / total_carbon, 3) if total_carbon > 0 else 0.0

        return {
            "team_name": team_name,
            "namespace": namespace,
            "region": region,
            "service_name": service_name,
            "cpu_usage_cores": active_cores,
            "memory_usage_gb": 16.0,  # Placeholder telemetry
            "resource_quota_cpu": quota_cpu,
            "resource_quota_mem": quota_mem,
            "efficiency_score_pct": green_score,
            "yesterday_carbon_kg": yesterday_carbon_kg,
            "wasted_carbon_kg": wasted_carbon_kg,
            "waste_ratio": waste_ratio,
        }

    def _rank(self, metrics_list: List[dict], sort_by: str) -> List[dict]:
        """Sorts a metrics list by the chosen criteria and stamps rank_placement."""
        if sort_by == "carbon":
            metrics_list.sort(key=lambda x: x["yesterday_carbon_kg"])
        else:
            metrics_list.sort(key=lambda x: x["efficiency_score_pct"], reverse=True)

        for index, item in enumerate(metrics_list, start=1):
            item["rank_placement"] = index
        return metrics_list

    def _ranked_namespaces(self, sort_by: str = "efficiency") -> List[dict]:
        """One unique row per active namespace, ranked. Source of truth for search."""
        unique_namespaces = self.db.query(ClusterMetric.namespace).distinct().all()

        processed_list = []
        seen = set()
        for (ns,) in unique_namespaces:
            if ns in seen:
                continue
            seen.add(ns)
            processed_list.append(self.compute_live_metrics(namespace=ns, team_meta=self._meta_for(ns)))

        return self._rank(processed_list, sort_by)

    # --- public API used by routes ---------------------------------------
    def get_team_metrics(self, team_name: str) -> dict:
        """Looks up a profile by name (fallback by namespace) and attaches AI guidance."""
        meta_record = (
            self.db.query(TeamMetricModel)
            .filter((TeamMetricModel.team_name == team_name) | (TeamMetricModel.namespace == team_name))
            .first()
        )
        target_namespace = meta_record.namespace if meta_record else team_name
        data = self.compute_live_metrics(namespace=target_namespace, team_meta=meta_record)

        strategies = []
        if data["efficiency_score_pct"] < 50.0:
            strategies.append(
                f"HIGH EMITTER: This service is in the bottom 50% of peers with a green score of {data['efficiency_score_pct']}%. "
                f"Reducing active core consumption will improve your standing and save up to {data['wasted_carbon_kg']}kg of idle CO2."
            )
        else:
            strategies.append(f"GREEN ZONE: This service scores {data['efficiency_score_pct']}% — lighter than most peers on carbon footprint.")

        data["ai_mitigation_strategies"] = strategies
        return data

    def get_leaderboard(self, sort_by: str = "efficiency") -> dict:
        """Discovers ALL active namespaces in telemetry history and aggregates a leaderboard."""
        unique_namespaces = self.db.query(ClusterMetric.namespace).distinct().all()

        processed_list = []
        for (ns,) in unique_namespaces:
            metrics_computed = self.compute_live_metrics(namespace=ns, team_meta=self._meta_for(ns))
            # NOTE: pre-existing behavior — active namespaces are appended twice.
            if metrics_computed["cpu_usage_cores"] > 0.1:
                processed_list.append(metrics_computed)
            processed_list.append(metrics_computed)

        total_carbon = sum(item["yesterday_carbon_kg"] for item in processed_list)
        total_wasted = sum(item["wasted_carbon_kg"] for item in processed_list)
        avg_efficiency = (
            round(sum(item["efficiency_score_pct"] for item in processed_list) / len(processed_list), 1)
            if processed_list else 0.0
        )

        self._rank(processed_list, sort_by)

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
                "avg_efficiency_pct": avg_efficiency,
            },
            "top_performers_green_zone": top_five,
            "bottom_performers_action_required": bottom_five,
        }

    def search(self, query: str, sort_by: str = "efficiency") -> dict:
        """
        Server-side search over the live namespace metrics that back the leaderboard.
        Matches the query against namespace and team_name, returning full ranked rows.
        """
        if not query.strip():
            return {"query": query, "total_matches_found": 0, "results": []}

        term = query.lower().strip()
        matches = [
            item for item in self._ranked_namespaces(sort_by=sort_by)
            if term in item["namespace"].lower() or term in item["team_name"].lower()
        ]
        return {"query": query, "total_matches_found": len(matches), "results": matches}

    def seed_mock_metadata(self) -> dict:
        """Attaches friendly team profiles to ingestion targets for demos/tests."""
        self.db.query(TeamMetricModel).delete()
        self.db.add_all([TeamMetricModel(**team) for team in _MOCK_TEAMS])
        self.db.commit()
        return {"status": "Registry metadata linked successfully."}
