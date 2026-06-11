import os
import requests
from typing import List
from src.config import settings
from src.ingestion.dtos import PipelineRun

class AzureDevOpsClient:
    def __init__(self):
        self.org = settings.ADO_ORG
        self.pat = settings.ADO_PAT
        
    def fetch_recent_builds(self, project: str, top: int = 5) -> List[PipelineRun]:
        """
        Fetches the latest builds and immediately validates them into DTOs.
        """
        url = f"https://dev.azure.com/{self.org}/{project}/_apis/build/builds"
        params = {"api-version": "7.1", "$top": top}
        auth = ("", self.pat)
        
        try:
            response = requests.get(url, params=params, auth=auth, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Map the raw JSON dictionary into our strict DTO objects
            runs = []
            for item in data.get("value", []):
                run = PipelineRun(
                    build_id=item.get("id"),
                    pipeline_name=item.get("definition", {}).get("name", "Unknown"),
                    status=item.get("status"),
                    result=item.get("result"),
                    # Pydantic will automatically convert these strings to datetimes
                    start_time=item.get("startTime"),
                    finish_time=item.get("finishTime")
                )
                runs.append(run)
            return runs
            
        except Exception as e:
            print(f"❌ Failed to fetch ADO builds for {project}: {e}")
            return []