from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

def test_endpoints():
    print("Testing /api/health...")
    health = client.get("/api/health")
    assert health.status_code == 200
    print("Health check OK!")

    print("\nTesting /api/stats...")
    stats = client.get(f"/api/stats/{DEMO_USER_ID}")
    assert stats.status_code == 200
    
    # Check if the structure returned from the Web Server matches what compute_all_stats outputted
    json_data = stats.json()
    assert "trigger_correlations" in json_data
    assert "temporal_patterns" in json_data
    assert "severity_trends" in json_data
    print("Stats API returned valid JSON structure!")

    print("\nTesting /api/entries...")
    entries = client.get(f"/api/entries/{DEMO_USER_ID}?limit=2")
    assert entries.status_code == 200
    assert isinstance(entries.json(), list)
    assert len(entries.json()) == 2
    print("Entries API returned valid list of history!")
        
if __name__ == "__main__":
    test_endpoints()
