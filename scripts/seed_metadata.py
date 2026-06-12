import sys
import os

# Ensure python can find the 'src' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import SessionLocal, Base, engine
from src.db.models import ClusterMetric, TeamMetricModel

def seed_metadata():
    print("🌱 RUNNING ONE-TIME METADATA SEEDER")
    print("=" * 60)
    
    # Ensure tables exist just in case
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Fetch all unique namespaces already successfully ingested
        unique_namespaces = db.query(ClusterMetric.namespace).distinct().all()
        print(f"🔍 Found {len(unique_namespaces)} unique namespaces in telemetry.")
        
        if not unique_namespaces:
            print("⚠️ No telemetry data found to base metadata on.")
            return

        added_count = 0
        
        # 2. Generate a default configuration profile for each
        for (ns,) in unique_namespaces:
            exists = db.query(TeamMetricModel).filter(TeamMetricModel.namespace == ns).first()
            if not exists:
                # Format "clm-indexing" into "Clm Indexing"
                clean_name = ns.replace("-", " ").title()
                
                new_team = TeamMetricModel(
                    team_name=clean_name,
                    namespace=ns,
                    region="eastus",
                    resource_quota_cpu=8.0,  # Baseline allocation
                    resource_quota_mem=32.0
                )
                db.add(new_team)
                added_count += 1
        
        # 3. Commit everything to SQLite
        db.commit()
        print(f"✅ Successfully seeded {added_count} new team profiles into 'team_sustainability_metrics'.")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_metadata()