from database import SessionLocal
from services.analysis import compute_all_stats
import json

def run_test():
    db = SessionLocal()
    try:
        # Use the hardcoded demo UUID we made in init.sql and seed.py
        user_id = "00000000-0000-0000-0000-000000000001"
        stats = compute_all_stats(user_id, db)
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"Analysis engine failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
