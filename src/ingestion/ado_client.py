import requests
from src.config import settings

class AzureDevOpsClient:
    def __init__(self):
        self.org = settings.ADO_ORG
        self.pat = settings.ADO_PAT
        self.base_url = f"https://dev.azure.com/{self.org}"

    def fetch_raw_builds(self, project_name: str):
        """
        Fetches the raw list of recent builds for a specific project.
        We print this out to inspect the exact JSON keys.
        """
        url = f"{self.base_url}/{project_name}/_apis/build/builds?api-version=7.1"
        
        # Top 3 runs is plenty for a quick schema test
        params = {
            "$top": 3 
        }
        
        print(f"📡 Hitting ADO API for project: {project_name}...")
        response = requests.get(url, auth=('', self.pat), params=params)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
        return response.json()