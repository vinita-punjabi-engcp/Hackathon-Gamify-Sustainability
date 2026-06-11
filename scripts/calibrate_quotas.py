import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import func
from src.db.session import SessionLocal
from src.db.models import ClusterMetric, TeamMetricModel

def calibrate_team_quotas():
    print("⚖️ RUNNING DATA-DRIVEN QUOTA CALIBRATION")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Find the maximum cores ever used by each namespace in our telemetry history
        usage_history = db.query(
            ClusterMetric.namespace, 
            func.max(ClusterMetric.active_cores).label('peak_cores')
        ).group_by(ClusterMetric.namespace).all()
        
        if not usage_history:
            print("⚠️ No telemetry found. Run ingestion first.")
            return

        updated_count = 0
        for ns, peak_cores in usage_history:
            team = db.query(TeamMetricModel).filter(TeamMetricModel.namespace == ns).first()
            
            if team and peak_cores > 0:
                # 2. Add a 30% FinOps safety buffer to their peak usage
                # Ensure every team gets at least a 2.0 core minimum baseline
                calculated_quota = round(peak_cores * 1.3, 1)
                team.resource_quota_cpu = max(2.0, calculated_quota)
                updated_count += 1
                
        # 3. Commit the realistic quotas to the database
        db.commit()
        print(f"✅ Successfully calibrated quotas for {updated_count} teams based on actual hardware usage.")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    calibrate_team_quotas()