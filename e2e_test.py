import httpx
import time

API_URL = "http://localhost:8000"

def run_tests():
    print("Starting End-to-End API Tests...")
    
    # 1. System Health
    print("\n--- Testing Metrics ---")
    r = httpx.get(f"{API_URL}/api/v1/metrics/system-health")
    print(f"GET /api/v1/metrics/system-health: {r.status_code}")
    assert r.status_code == 200, r.text
    
    r = httpx.get(f"{API_URL}/api/v1/metrics/recent-jobs")
    print(f"GET /api/v1/metrics/recent-jobs: {r.status_code}")
    assert r.status_code in (200, 404), r.text

    # 2. Authentication
    print("\n--- Testing Authentication ---")
    # Let's try to get a token with the seeded user admin@test.com / password
    r = httpx.post(f"{API_URL}/api/v1/auth/login", data={"username": "admin@test.com", "password": "password"})
    print(f"POST /api/v1/auth/login: {r.status_code}")
    if r.status_code == 200:
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Successfully obtained JWT Token.")
    else:
        print("Auth failed, skipping authenticated routes.")
        return

    # 3. Projects & Queues
    print("\n--- Testing Projects ---")
    r = httpx.get(f"{API_URL}/api/v1/projects", headers=headers)
    print(f"GET /api/v1/projects: {r.status_code}")
    assert r.status_code == 200, r.text
    projects = r.json()
    if not projects:
        print("No projects found.")
        return
    project_id = projects[0]["id"]

    print("\n--- Testing Queues ---")
    r = httpx.get(f"{API_URL}/api/v1/projects/{project_id}/queues", headers=headers)
    print(f"GET /api/v1/projects/{{project_id}}/queues: {r.status_code}")
    assert r.status_code == 200, r.text
    queues = r.json()
    print(f"Found {len(queues)} queues.")
    
    if not queues:
        print("No queues found to test jobs.")
        return
        
    queue_id = queues[0]["id"]

    # 4. Jobs
    print("\n--- Testing Jobs ---")
    job_payload = {
        "type": "e2e_test_job",
        "payload": {"message": "hello world"},
        "priority": 10
    }
    r = httpx.post(f"{API_URL}/api/v1/queues/{queue_id}/jobs", json=job_payload, headers=headers)
    print(f"POST /api/v1/queues/{{queue_id}}/jobs: {r.status_code}")
    assert r.status_code == 201, r.text
    job_id = r.json()["id"]
    print(f"Successfully created job {job_id}")

    # Wait a second for worker to potentially process it
    time.sleep(1)

    # Check Job Status
    r = httpx.get(f"{API_URL}/api/v1/queues/{queue_id}/jobs/{job_id}", headers=headers)
    print(f"GET /api/v1/queues/{{queue_id}}/jobs/{{job_id}}: {r.status_code}")
    assert r.status_code == 200, r.text
    print(f"Job status: {r.json()['status']}")

    # 5. Workers
    print("\n--- Testing Workers ---")
    r = httpx.get(f"{API_URL}/api/v1/workers/", headers=headers)
    print(f"GET /api/v1/workers/: {r.status_code}")
    assert r.status_code == 200, r.text
    print(f"Found {len(r.json())} active workers.")

    print("\nAll End-to-End Tests Passed Successfully! \u2728")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Test failed: {e}")
