import requests

def test_api():
    res = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'admin@flplatform.org', 'password': 'admin123'})
    token = res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 1. List experiments
    exps = requests.get('http://127.0.0.1:8000/api/v1/admin/experiments', headers=headers).json()
    print(f"Total active experiments in API: {len(exps)}")
    for e in exps:
        print(f" - ID {e['id']}: {e['name']} (Task: {e['healthcare_task']}, Status: {e['status']})")

    # 2. Create a temporary test experiment
    model_id = exps[0]['model_id'] if exps else 1
    create_res = requests.post('http://127.0.0.1:8000/api/v1/admin/experiments', json={
        "name": "Temporary Test Exp to Verify Delete",
        "healthcare_task": "diabetes_prediction",
        "model_id": 1,
        "total_rounds": 2,
        "local_epochs": 1,
        "learning_rate": 0.01,
        "batch_size": 16
    }, headers=headers)
    new_exp = create_res.json()
    print(f"\nCreated temporary experiment ID {new_exp['id']}: '{new_exp['name']}'")

    # 3. Test DELETE endpoint
    del_res = requests.delete(f"http://127.0.0.1:8000/api/v1/admin/experiments/{new_exp['id']}", headers=headers)
    print(f"DELETE status code: {del_res.status_code}, response: {del_res.json()}")

    # 4. Confirm it was deleted
    exps_after = requests.get('http://127.0.0.1:8000/api/v1/admin/experiments', headers=headers).json()
    print(f"Total experiments after deletion: {len(exps_after)}")
    ids_after = [e['id'] for e in exps_after]
    assert new_exp['id'] not in ids_after, "Deleted experiment still found!"
    print("Delete verification test PASSED cleanly!")

if __name__ == "__main__":
    test_api()
