import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import engine, Base
from src.services.collector_service import MetricsCollectorService

def main():
    print("🎬 INITIALIZING AUTOMATED GREENOPS BULK INGESTION")
    print("=" * 60)
    
    Base.metadata.create_all(bind=engine)
    collector = MetricsCollectorService()
    
    # 1. BULK PROMETHEUS SCRAPE & INGESTION (1 API Call, 1 DB Transaction)
    target_namespaces = collector.collect_and_persist_bulk_cluster_metrics()
    
    if not target_namespaces:
        print("⚠️ No namespaces retrieved. Check Prometheus connection/token.")
        return
        
    print("-" * 60)
    
    # 2. BULK TEAM METADATA SYNC (1 DB Transaction)
    collector.sync_team_metadata(namespaces=target_namespaces)
    print("-" * 60)
    
    # 3. ADO PIPELINES 
    # ADO requires project-by-project calls, so we exclude backend infrastructure 
    # to avoid wasting API calls on namespaces that don't write code.
    system_keywords = ["system", "kube", "observability", "cert-manager", "ingress", "default", "prom", "optimizely", "scaleops"]
    ado_projects = [ns for ns in target_namespaces if not any(k in ns.lower() for k in system_keywords)]
    
    print(f"🚀 Gathering ADO pipelines for {len(ado_projects)} engineering projects...")
    for namespace in ado_projects:
        try:
            collector.collect_and_persist_pipeline_metrics(project=namespace)
        except Exception:
            pass
        # Safe throttling exclusively for ADO since it lacks a bulk endpoint
        time.sleep(0.2)
    
    print("=" * 60)
    print("🏁 BULK INGESTION COMPLETE: Infrastructure fully synchronized.")

if __name__ == "__main__":
    main()