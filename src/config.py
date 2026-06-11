import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ADO_ORG = os.getenv("ADO_ORG", "DocusignOrg")
    ADO_PAT = os.getenv("ADO_PAT")
    
    # 💥 Add this property back into the class:
    PROMETHEUS_ENDPOINT = os.getenv(
        "PROMETHEUS_ENDPOINT", 
        "https://observability-prometheusdeveus-ui23.eastus.prometheus.monitor.azure.com"
    )
    
    DATABASE_URL = "sqlite:///./greenops.db"

settings = Settings()

if not settings.ADO_PAT:
    raise ValueError("Missing ADO_PAT environment variable.")