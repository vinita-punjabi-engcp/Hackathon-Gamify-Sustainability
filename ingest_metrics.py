import subprocess
import re
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import the SQL model from your main app file
from app import TeamMetricModel, DATABASE_URL

# Configure your DB Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# --- 🗺️ CONFIGURATION: MAP NAMESPACES TO parent TEAMS ---
# Key: Namespace, Value: (Parent Team Name, Regional Grid Profile)
NAMESPACE_TEAM_MAP = {
    "1ds-app": ("Core Search", "westus3"),
    "1ds-api": ("Core Search", "westus3"),  # Multiple namespaces can roll up into one team
    "clm-indexing": ("CLM Lifecycle", "westeurope"),
    "query-parser": ("NLP Processing", "westus3"),
    "signing-core": ("Envelope Signing", "westeurope"),
    "esign-automation": ("esign", "westeurope"),
    "esign-insights": ("esign", "westeurope"),
    "esign-prototype": ("esign", "westeurope"),
    "esign-site-extension-1": ("esign", "westeurope"),
    "esign-site-extension-2": ("esign", "westeurope"),
    "esign-site-extension-3": ("esign", "westeurope"),
    "esign-site-extension-4": ("esign", "westeurope"),
    "esignlinuxops": ("esign", "westeurope"),
    "search": ("Search", "westus3")
}

def parse_memory_to_gb(mem_str: str) -> float:
    """Converts K8s memory string outputs (Mi, Ki, Gi) cleanly into Gigabytes (GB)."""
    digits = float(re.findall(r'\d+\.?\d*', mem_str)[0])
    if "Mi" in mem_str:
        return digits / 1024.0
    if "Gi" in mem_str:
        return digits
    if "Ki" in mem_str:
        return digits / (1024.0 * 1024.0)
    return digits / 1024.0 # Default fallback to Mi handling

def parse_cpu_to_cores(cpu_str: str) -> float:
    """Converts K8s CPU millicores (m) or whole cores cleanly to floats."""
    digits = float(re.findall(r'\d+', cpu_str)[0])
    if "m" in cpu_str:
        return digits / 1000.0  # 500m = 0.5 Cores
    return digits

def scrape_namespace_metrics(namespace: str):
    """Executes kubectl top pods and aggregates total CPU and Memory consumption."""
    try:
        # Run the native kubectl terminal command inside Python
        result = subprocess.run(
            ["kubectl", "top", "pods", "-n", namespace],
            capture_output=True, text=True, check=True
        )
        
        lines = result.stdout.strip().split("\n")
        if len(lines) <= 1:
            print(f"⚠️ No active pod telemetry found in namespace: {namespace}")
            return 0.0, 0.0

        total_cpu = 0.0
        total_mem = 0.0

        # Loop through rows, skipping the header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                # parts[0] = Pod Name, parts[1] = CPU, parts[2] = Memory
                total_cpu += parse_cpu_to_cores(parts[1])
                total_mem += parse_memory_to_gb(parts[2])

        return total_cpu, total_mem

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run kubectl for namespace '{namespace}': {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        print("❌ Error: 'kubectl' CLI tool was not found in your system PATH environment.")
        sys.exit(1)

def run_ingestion_pipeline():
    """Aggregates namespace data into teams and commits values directly to the SQL DB."""
    db = SessionLocal()
    
    # Initialize an aggregation bucket for team rollups
    team_aggregates = {}

    print("🔄 Initializing live Kubectl metric harvesting...")
    
    for namespace, (team_name, region) in NAMESPACE_TEAM_MAP.items():
        print(f"📡 Scraping pod metrics from namespace: [{namespace}]")
        metrics = scrape_namespace_metrics(namespace)
        
        if metrics is None:
            continue
            
        ns_cpu, ns_mem = metrics
        print(f"   ↳ Extracted: {round(ns_cpu, 3)} Cores, {round(ns_mem, 2)} GB RAM")

        # Initialize team bucket if it doesn't exist yet
        if team_name not in team_aggregates:
            team_aggregates[team_name] = {
                "namespace": namespace,  # Primary reference namespace
                "region": region,
                "total_cpu": 0.0,
                "total_mem": 0.0
            }
            
        # Sum everything up under the parent team name
        team_aggregates[team_name]["total_cpu"] += ns_cpu
        team_aggregates[team_name]["total_mem"] += ns_mem

    # 3. Update or Insert the aggregated data records into SQL database
    print("\n💾 Committing rolled-up metrics to the SQL Database...")
    for team_name, aggregated_data in team_aggregates.items():
        
        # Query if team record already exists via Primary Key
        team_record = db.query(TeamMetricModel).filter(TeamMetricModel.team_name == team_name).first()
        
        if team_record:
            # Update existing row parameters
            team_record.cpu_usage_cores = aggregated_data["total_cpu"]
            team_record.memory_usage_gb = aggregated_data["total_mem"]
            print(f"✅ Updated existing entry: {team_name} (CPU Cores Total: {round(aggregated_data['total_cpu'], 2)})")
        else:
            # Create a new record fallback if team doesn't exist in DB
            new_record = TeamMetricModel(
                team_name=team_name,
                namespace=aggregated_data["namespace"],
                region=aggregated_data["region"],
                cpu_usage_cores=aggregated_data["total_cpu"],
                memory_usage_gb=aggregated_data["total_mem"],
                resource_quota_cpu=aggregated_data["total_cpu"] * 2.0, # Guessing a default quota ceiling
                resource_quota_mem=aggregated_data["total_mem"] * 2.0
            )
            db.add(new_record)
            print(f"✨ Created fresh database row entry: {team_name}")

    db.commit()
    db.close()
    print("🏁 Ingestion run complete!")

if __name__ == "__main__":
    run_ingestion_pipeline()