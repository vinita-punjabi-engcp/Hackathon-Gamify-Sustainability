import sys
import os

# Maintain local path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.ado_client import AzureDevOpsClient
from src.ingestion.prometheus_client import PrometheusClient

def main():
    print("🎬 Initializing Dual-Source Integration Spike...\n")

    # 1. Test Refactored ADO
    ado = AzureDevOpsClient()
    recent_runs = ado.fetch_recent_builds("search", top=1)
    for run in recent_runs:
        print(f"✅ ADO Run: {run.pipeline_name} (ID: {run.build_id}) lasted {run.duration_mins:.2f} mins")

    print("\n" + "="*50 + "\n")

    # 2. Test Refactored Prometheus
    prom = PrometheusClient()
    metrics = prom.fetch_namespace_metrics("search")
    print(f"✅ Prometheus: {metrics.namespace} is using {metrics.active_cores:.2f} cores.")

if __name__ == "__main__":
    main()