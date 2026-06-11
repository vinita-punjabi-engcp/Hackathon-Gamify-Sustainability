import os
from azure.identity import DefaultAzureCredential
from src.core.http_client import BaseHttpClient
from src.config import settings

# 💥 The missing import!
from src.ingestion.dtos import NamespaceMetrics

class PrometheusClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.PROMETHEUS_ENDPOINT)

    def _get_access_token(self) -> str:
        """Generates an Azure Monitor Workspace scoped token."""
        print("🔑 Fetching Prometheus scoped access token via Azure Identity...")
        credential = DefaultAzureCredential(exclude_managed_identity_credential=True)
        resource = "https://prometheus.monitor.azure.com/.default"
        access_token = credential.get_token(resource).token
        return f"Bearer {access_token}"
    
    def discover_all_active_namespaces(self) -> list[str]:
        """Queries Prometheus metadata to dynamically discover every active namespace."""
        print("📡 Discovering active cluster namespaces via Prometheus metadata...")
        promql_query = "count(container_cpu_usage_seconds_total) by (namespace)"
        
        try:
            token = self._get_access_token()
            headers = {"Authorization": token, "Accept": "application/json"}
            
            data = self.get(endpoint="/api/v1/query", headers=headers, params={"query": promql_query})
            results = data.get("data", {}).get("result", [])
            
            namespaces = [
                item["metric"]["namespace"] 
                for item in results 
                if "namespace" in item["metric"] and item["metric"]["namespace"] != "kube-system"
            ]
            return namespaces
        except Exception as e:
            print(f"⚠️ Dynamic discovery failed: {e}. Falling back to default scope.")
            return ["search", "1ds-app"]

    def fetch_namespace_metrics(self, namespace: str) -> NamespaceMetrics:
        """Queries Azure Prometheus and returns a validated DTO."""
        try:
            token = self._get_access_token()
        except Exception as e:
            print(f"❌ Failed to generate Azure credential: {e}")
            return NamespaceMetrics(namespace=namespace, active_cores=0.0)

        headers = {"Authorization": token, "Accept": "application/json"}
        promql_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!=""}}[24h]))'
        params = {"query": promql_query}
        
        print(f"📡 Querying Azure Prometheus directly for namespace: {namespace}...")
        
        try:
            data = self.get(endpoint="/api/v1/query", headers=headers, params=params)
            results = data.get("data", {}).get("result", [])
            
            cores = float(results[0]["value"][1]) if results else 0.0
            return NamespaceMetrics(namespace=namespace, active_cores=cores)
                
        except Exception as e:
            print(f"❌ Connection issue: {e}")
            return NamespaceMetrics(namespace=namespace, active_cores=0.0)
        
    def get_bulk_cluster_metrics(self) -> dict:
        """Fetches CPU usage for ALL namespaces in a single API call."""
        print("📡 Fetching bulk telemetry for all namespaces from Prometheus...")
        
        # PromQL: Sums up the active CPU cores across the cluster, grouped by namespace
        promql_query = "sum(rate(container_cpu_usage_seconds_total[5m])) by (namespace)"
        
        try:
            token = self._get_access_token()
            headers = {"Authorization": token, "Accept": "application/json"}
            
            data = self.get(endpoint="/api/v1/query", headers=headers, params={"query": promql_query})
            results = data.get("data", {}).get("result", [])
            
            metrics_map = {}
            for item in results:
                ns = item["metric"].get("namespace")
                if ns and ns != "kube-system":
                    # PromQL returns value as [timestamp, "string_value"]
                    core_value = float(item["value"][1])
                    metrics_map[ns] = core_value
                    
            return metrics_map
        except Exception as e:
            print(f"⚠️ Bulk telemetry fetch failed: {e}")
            return {}