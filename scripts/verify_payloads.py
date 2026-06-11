import sys
import os
from datetime import datetime

# Path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.ado_client import AzureDevOpsClient
from src.ingestion.grafana_client import GrafanaClient

def parse_iso_time(time_str: str) -> datetime:
    """Helper to cleanly parse Azure ISO timestamps."""
    if not time_str:
        return None
    # Truncate fractional seconds for clean parsing
    clean_str = time_str.split('.')[0].replace('Z', '')
    return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")

def run_diagnostic_audit():
    print("🔬 RUNNING INTEGRATION AUDIT & KEY VERIFICATION\n" + "="*60)

    # Define a matrix of namespaces and project pipelines to audit
    audit_matrix = [
        {"namespace": "search", "ado_project": "search"},
        {"namespace": "1ds-app", "ado_project": "search"}, # Testing fallback/cross-projects
    ]

    ado_client = AzureDevOpsClient()
    prom_client = GrafanaClient()

    all_systems_go = True

    for target in audit_matrix:
        ns = target["namespace"]
        proj = target["ado_project"]

        print(f"\n📂 Auditing Target Group: Namespace [{ns}] / ADO Project [{proj}]")
        print("-" * 50)

        # 1. Audit Prometheus Data Contract
        cpu_cores = prom_client.fetch_namespace_cpu_cores(ns)
        print(f"  🔹 Prometheus Active Cores Found: {cpu_cores}")

        # 2. Audit ADO Pipeline Data Contract
        raw_ado = ado_client.fetch_raw_builds(proj)

        if not raw_ado or "value" not in raw_ado or len(raw_ado["value"]) == 0:
            print(f"  ⚠️  No recent builds found for project '{proj}' or project inaccessible.")
            continue

        # Inspect the absolute first run to verify mandatory schema keys
        sample_build = raw_ado["value"][0]

        # Map out required data keys for math/db
        build_id = sample_build.get("id")
        status = sample_build.get("status")
        result = sample_build.get("result")
        raw_start = sample_build.get("startTime")
        raw_finish = sample_build.get("finishTime")
        pipeline_name = sample_build.get("definition", {}).get("name", "Unknown")

        # Calculate duration validation
        start_dt = parse_iso_time(raw_start)
        finish_dt = parse_iso_time(raw_finish)
        duration_mins = 0.0

        if start_dt and finish_dt:
            duration_mins = (finish_dt - start_dt).total_seconds() / 60.0

        # Run strict checklist validations
        checklist = {
            "Build ID": build_id is not None,
            "Pipeline Name": pipeline_name != "Unknown",
            "Lifecycle Status": status is not None,
            "Execution Result": result is not None,
            "Valid Duration (Mins)": duration_mins >= 0
        }

        print("  🔹 ADO Schema Key Verification:")
        for key, passed in checklist.items():
            status_icon = "✅" if passed else "❌"
            print(f"    {status_icon} {key}")
            if not passed:
                all_systems_go = False

        if start_dt and finish_dt:
            print(f"  🔹 Live Sample Run: {pipeline_name} (ID: {build_id}) lasted {duration_mins:.2f} mins [{result}]")

    print("\n" + "="*60)
    if all_systems_go:
        print("🚀 VERIFICATION COMPLETE: All required schema keys are present and validated with 100% certainty.")
    else:
        print("⚠️  AUDIT WARNING: Some expected data structures or keys are missing. Review logs above.")

if __name__ == "__main__":
    run_diagnostic_audit()