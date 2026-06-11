import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import engine, Base
from src.ingestion.prometheus_client import PrometheusClient
from src.services.collector_service import MetricsCollectorService

def main():
    print("🎬 INITIALIZING AUTOMATED GREENOPS PRODUCTION SWEEP")
    print("=" * 60)
    
    Base.metadata.create_all(bind=engine)
    collector = MetricsCollectorService()
    
    # 💥 Look here: Instantiate the client to fetch all active cluster namespaces dynamically
    prom_client = PrometheusClient()
    target_namespaces = prom_client.discover_all_active_namespaces()
    print(f"✅ Dynamic Discovery Complete! Found {len(target_namespaces)} operational namespaces.")
    print("-" * 60)
    
    print("🚀 Gathering Azure DevOps pipeline history...")
    collector.collect_and_persist_pipeline_metrics(project="search")
    print("-" * 60)
    
    print(f"📡 Sweeping live telemetry across all {len(target_namespaces)} namespaces...")
    for namespace in target_namespaces:
        try:
            collector.collect_and_persist_cluster_metrics(namespace=namespace)
        except Exception as e:
            print(f"⚠️ Skipping namespace '{namespace}': {e}")
    
    print("=" * 60)
    print("🏁 INGESTION COMPLETE: All corporate components synchronized.")

if __name__ == "__main__":
    main()