import requests
from src.config import settings

def find_prometheus():
    # Hit the base datasources API
    url = "https://dev-obs-grafana-e5g6h4awgpb4cedq.eus.grafana.azure.com/api/datasources"
    headers = {"Authorization": f"Bearer {settings.GRAFANA_BEARER_TOKEN}"}

    print("🔍 Searching for Prometheus datasources...")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            # Look for any datasource with Prometheus in the name or type
            if "prometheus" in ds.get("type", "").lower() or "prometheus" in ds.get("name", "").lower():
                print(f"✅ Found! Name: {ds['name']} | UID: {ds['uid']} | ID: {ds['id']}")
    else:
        print(f"❌ Failed to fetch: {response.status_code} - {response.text}")

if __name__ == "__main__":
    find_prometheus()