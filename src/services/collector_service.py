from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.db.models import ClusterMetric, PipelineMetric, TeamMetricModel
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
                    result=run.result if run.result is not None else "pending",
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

    def sync_team_metadata(self, namespaces: list[str]) -> None:
        """Auto-generates UI configuration profiles for newly discovered namespaces."""
        print(f"🤖 Synchronizing metadata registry for {len(namespaces)} namespaces...")
        db: Session = SessionLocal()
        try:
            added_count = 0
            for ns in namespaces:
                exists = db.query(TeamMetricModel).filter(TeamMetricModel.namespace == ns).first()
                if not exists:
                    clean_name = ns.replace("-", " ").title()
                    new_team = TeamMetricModel(
                        team_name=clean_name,
                        namespace=ns,
                        region="eastus",
                        resource_quota_cpu=8.0,
                        resource_quota_mem=32.0
                    )
                    db.add(new_team)
                    added_count += 1
            
            db.commit()
            if added_count > 0:
                print(f"💾 Successfully registered {added_count} new team profiles for the UI.")
            else:
                print("⏭️ All teams already registered in metadata. Skipping.")
                
        except Exception as e:
            db.rollback()
            print(f"❌ Database Transaction Failed for metadata sync: {e}")
        finally:
            db.close()

    
    def collect_and_persist_bulk_cluster_metrics(self) -> list[str]:
        """Processes and saves cluster metrics in a single bulk database transaction."""
        prom_client = PrometheusClient()
        metrics_map = prom_client.get_bulk_cluster_metrics()
        
        if not metrics_map:
            return []
            
        db: Session = SessionLocal()
        try:
            records_to_insert = []
            namespaces_found = list(metrics_map.keys())
            
            for ns, cores in metrics_map.items():
                carbon_score = CarbonMath.calculate_cluster_co2(active_cores=cores)
                
                record = ClusterMetric(
                    namespace=ns,
                    active_cores=cores,
                    carbon_co2g=carbon_score
                )
                records_to_insert.append(record)
            
            # 💥 BULK INSERT: Saves hundreds of rows in 1 millisecond
            db.add_all(records_to_insert)
            db.commit()
            
            print(f"💾 Bulk committed {len(records_to_insert)} cluster metrics to database.")
            return namespaces_found
            
        except Exception as e:
            db.rollback()
            print(f"❌ Bulk DB Insert Failed: {e}")
            return []
        finally:
            db.close()