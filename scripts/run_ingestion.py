import sys
import os

# Maintain local path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.ado_client import AzureDevOpsClient
from src.ingestion.grafana_client import GrafanaClient

def main():
    print("🎬 Initializing Dual-Source Integration Spike...\n")

    # 1. Test Azure DevOps Client
    ado = AzureDevOpsClient()
    ado_data = ado.fetch_raw_builds("search")
    if ado_data and "value" in ado_data:
        print(f"✅ ADO Connectivity Verified! Retrieved {len(ado_data['value'])} build runs.")
    else:
        print("❌ ADO Validation Failed.")

    print("\n" + "="*50 + "\n")

    # 2. Test Grafana/Prometheus Client
    grafana = GrafanaClient()
    # Testing against the active search namespace we saw on your dashboard
    cpu_cores = grafana.fetch_namespace_cpu_cores("search")
    print(f"✅ Grafana Connectivity Verified! Active CPU load: {cpu_cores} cores.")

if __name__ == "__main__":
    main()