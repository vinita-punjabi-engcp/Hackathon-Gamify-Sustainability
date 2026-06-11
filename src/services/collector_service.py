from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.db.models import ClusterMetric, PipelineMetric
from src.ingestion.ado_client import AzureDevOpsClient
from src.ingestion.prometheus_client import PrometheusClient
from src.core.carbon_math import CarbonMath

class MetricsCollectorService:
    """
    Facade Orchestrator that coordinates pulling data from clients,
    calculating carbon footprint values, and persisting results safely.
    """

    def collect_and_persist_pipeline_metrics(self, project: str) -> None:
        """Fetches latest CI/CD runs, filters duplicates, computes carbon, and stores them."""
        print(f"🤖 Starting Pipeline metrics ingestion for project: {project}")
        ado_client = AzureDevOpsClient()
        runs = ado_client.fetch_recent_builds(project=project)

        if not runs:
            print(f"⚠️ No active or recent runs retrieved for project: {project}")
            return

        db: Session = SessionLocal()
        try:
            for run in runs:
                # Deduplication check
                exists = db.query(PipelineMetric).filter(PipelineMetric.build_id == run.build_id).first()
                if exists:
                    print(f"⏭️ Build ID {run.build_id} ({run.pipeline_name}) already processed. Skipping.")
                    continue

                # Carbon Calculation (Math engine takes seconds: mins * 60)
                duration_seconds = run.duration_mins * 60
                carbon_score = CarbonMath.calculate_pipeline_co2(duration_seconds=duration_seconds)

                metric_record = PipelineMetric(
                    build_id=run.build_id,
                    pipeline_name=run.pipeline_name,
                    duration_mins=run.duration_mins,
                    status=run.status,
                    result=run.result,
                    carbon_co2g=carbon_score
                )
                db.add(metric_record)
                print(f"➕ Prepared Build ID {run.build_id} | Carbon: {carbon_score}g CO2")

            db.commit()
            print(f"💾 Successfully committed new pipeline records for '{project}' to database.")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Database Transaction Failed for pipelines: {e}")
            raise e
        finally:
            db.close()

    def collect_and_persist_cluster_metrics(self, namespace: str) -> None:
        """Fetches instant namespace core load, computes daily footprint, and stores it."""
        print(f"🤖 Starting Cluster utilization ingestion for namespace: {namespace}")
        prom_client = PrometheusClient()
        metrics = prom_client.fetch_namespace_metrics(namespace=namespace)

        db: Session = SessionLocal()
        try:
            # Carbon Calculation (Assumes standard 24-hour baseline projection)
            carbon_score = CarbonMath.calculate_cluster_co2(
                active_cores=metrics.active_cores, 
                duration_hours=24.0
            )

            metric_record = ClusterMetric(
                namespace=metrics.namespace,
                active_cores=metrics.active_cores,
                carbon_co2g=carbon_score
            )
            db.add(metric_record)
            db.commit()
            print(f"💾 Successfully logged cluster snapshot for '{namespace}' | Carbon: {carbon_score}g CO2")

        except Exception as e:
            db.rollback()
            print(f"❌ Database Transaction Failed for cluster tracking: {e}")
            raise e
        finally:
            db.close()