import os
import requests
from azure.identity import DefaultAzureCredential

class GrafanaClient:
    def __init__(self):
        # Fallback to the known Dev endpoint if missing from .env
        self.api_url = os.getenv(
            "PROMETHEUS_ENDPOINT",
            "https://observability-prometheusdeveus-ui23.eastus.prometheus.monitor.azure.com"
        )

    def _get_access_token(self) -> str:
        """
        Generates a token specifically scoped for Azure Monitor Workspace / Prometheus
        using the user's active local az cli login.
        """
        print("🔑 Fetching Prometheus scoped access token via Azure Identity...")
        credential = DefaultAzureCredential(exclude_managed_identity_credential=True)
        resource = "https://prometheus.monitor.azure.com/.default"
        access_token = credential.get_token(resource).token
        return f"Bearer {access_token}"

    def fetch_namespace_cpu_cores(self, namespace: str) -> float:
        """
        Queries Azure Prometheus directly to get active CPU cores.
        """
        try:
            token = self._get_access_token()
        except Exception as e:
            print(f"❌ Failed to generate Azure credential: {e}")
            return 0.0

        headers = {
            "Authorization": token,
            "Accept": "application/json"
        }

        promql_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!=""}}[24h]))'

        # Direct Azure Monitor endpoint structure
        query_url = f"{self.api_url}/api/v1/query"
        params = {"query": promql_query}

        print(f"📡 Querying Azure Prometheus directly for namespace: {namespace}...")

        try:
            response = requests.get(query_url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = data.get("data", {}).get("result", [])
                if results:
                    return float(results[0]["value"][1])
                else:
                    print(f"⚠️ No metrics found for {namespace}.")
                    return 0.0
            else:
                print(f"❌ Prometheus Error {response.status_code}: {response.text}")
                return 0.0

        except Exception as e:
            print(f"❌ Connection issue: {e}")
            return 0.0