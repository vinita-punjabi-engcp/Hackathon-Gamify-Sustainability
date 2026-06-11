import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings:
    # ADO Config
    ADO_ORG = os.getenv("ADO_ORG", "DocusignOrg")
    ADO_PAT = os.getenv("ADO_PAT")

    # Grafana Config
    GRAFANA_API_URL = os.getenv("GRAFANA_API_URL")
    GRAFANA_BEARER_TOKEN = os.getenv("GRAFANA_BEARER_TOKEN")

    # DB Config
    DATABASE_URL = "sqlite:///./greenops.db"

# ⚠️ THIS LINE IS MISSING OR TYPO'D CRITICAL FIX:
settings = Settings()

# Fast-fail if critical secrets are missing
if not settings.ADO_PAT:
    raise ValueError("Missing critical environment variables. Check your .env file.")