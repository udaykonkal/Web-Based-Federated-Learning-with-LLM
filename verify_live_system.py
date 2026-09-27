import requests
import json
import time

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://127.0.0.1:8000/api/v1"
PROXY_URL = "http://localhost:5173/api/v1"

report = []

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")
    report.append({"status": status, "message": msg})

def test_full_system():
    log("=== 1. Testing Frontend Static Server & Proxy ===")
    try:
        r = requests.get(FRONTEND_URL)
        if r.status_code == 200 and "html" in r.text.lower():
            log(f"Frontend index.html loads successfully (status={r.status_code})", "PASS")
        else:
            log(f"Frontend failed to load: {r.status_code}", "FAIL")
    except Exception as e:
        log(f"Frontend connection error: {e}", "FAIL")

    try:
        r = requests.get("http://127.0.0.1:8000/health")
        if r.status_code == 200:
            log(f"Backend health check responds healthy (status={r.status_code})", "PASS")
        else:
            log(f"Backend health check returned {r.status_code}", "FAIL")
    except Exception as e:
        log(f"Backend connection error: {e}", "FAIL")

    try:
        r = requests.get(f"{PROXY_URL}/admin/health")
        # should be 401 unauth without token, meaning proxy forwards correctly
        if r.status_code in [401, 403]:
            log(f"Vite /api proxy correctly routes to FastAPI (status={r.status_code})", "PASS")
        else:
            log(f"Vite proxy unexpected status: {r.status_code}", "WARN")
    except Exception as e:
        log(f"Vite proxy error: {e}", "FAIL")

    log("\n=== 2. Testing Authentication (Admin & Clients) ===")
    admin_token = None
    client_tokens = {}

    # Admin Login
    try:
        r = requests.post(f"{BACKEND_URL}/auth/login", json={"email": "admin@flplatform.org", "password": "admin123"})
        if r.status_code == 200 and "access_token" in r.json():
            admin_token = r.json()["access_token"]
            log("Admin login successful", "PASS")
        else:
            log(f"Admin login failed: {r.text}", "FAIL")
    except Exception as e:
        log(f"Admin login error: {e}", "FAIL")

    # Client Logins
    for cid, email, pwd in [("client_1", "hospital_a@flplatform.org", "client1pass"),
                            ("client_2", "hospital_b@flplatform.org", "client2pass"),
                            ("client_3", "hospital_c@flplatform.org", "client3pass")]:
        try:
            r = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": pwd})
            if r.status_code == 200 and "access_token" in r.json():
                client_tokens[cid] = r.json()["access_token"]
                log(f"{cid} ({email}) login successful", "PASS")
            else:
                log(f"{cid} login failed: {r.text}", "FAIL")
        except Exception as e:
            log(f"{cid} login error: {e}", "FAIL")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    c1_headers = {"Authorization": f"Bearer {client_tokens.get('client_1')}"}

    log("\n=== 3. Testing Model Lifecycle (Draft -> Uploaded -> Published -> Active) ===")
    # Initialize defaults if needed
    init_r = requests.post(f"{BACKEND_URL}/admin/models/initialize-defaults", headers=admin_headers)
    models = requests.get(f"{BACKEND_URL}/admin/models", headers=admin_headers).json()
    dia_model = next((m for m in models if m["healthcare_task"] == "diabetes_prediction"), None)
    if not dia_model:
        log("Diabetes model not found in admin registry", "FAIL")
        return
    
    mid = dia_model["id"]
    log(f"Testing model ID {mid} (Name: {dia_model['name']})")

    # 3a. Set to DRAFT
    requests.patch(f"{BACKEND_URL}/admin/models/{mid}/status", json={"status": "draft"}, headers=admin_headers)
    c_models = requests.get(f"{BACKEND_URL}/client/models", headers=c1_headers).json()
    if not any(m["id"] == mid for m in c_models):
        log("DRAFT model invisible to clients on /client/models", "PASS")
    else:
        log("DRAFT model leaked to /client/models", "FAIL")

    r_direct = requests.get(f"{BACKEND_URL}/client/models/{mid}", headers=c1_headers)
    if r_direct.status_code == 403:
        log("Direct GET /client/models/{id} on DRAFT model rejected with 403 Forbidden", "PASS")
    else:
        log(f"Direct GET on DRAFT model returned {r_direct.status_code}", "FAIL")

    # 3b. Set to UPLOADED
    requests.patch(f"{BACKEND_URL}/admin/models/{mid}/status", json={"status": "uploaded"}, headers=admin_headers)
    c_models = requests.get(f"{BACKEND_URL}/client/models", headers=c1_headers).json()
    if not any(m["id"] == mid for m in c_models):
        log("UPLOADED model invisible to clients", "PASS")
    else:
        log("UPLOADED model leaked to clients", "FAIL")

    # 3c. Set to PUBLISHED (still pending activation)
    requests.patch(f"{BACKEND_URL}/admin/models/{mid}/status", json={"status": "published"}, headers=admin_headers)
    c_models = requests.get(f"{BACKEND_URL}/client/models", headers=c1_headers).json()
    if not any(m["id"] == mid for m in c_models):
        log("PUBLISHED model (without active) invisible to clients", "PASS")
    else:
        log("PUBLISHED model visible before activation", "FAIL")

    r_direct = requests.get(f"{BACKEND_URL}/client/models/{mid}", headers=c1_headers)
    if r_direct.status_code == 403:
        log("Direct GET on PUBLISHED model rejected with 403 Forbidden", "PASS")
    else:
        log(f"Direct GET on PUBLISHED model returned {r_direct.status_code}", "FAIL")

    # 3d. Set to ACTIVE
    requests.patch(f"{BACKEND_URL}/admin/models/{mid}/status", json={"status": "active"}, headers=admin_headers)
    c_models = requests.get(f"{BACKEND_URL}/client/models", headers=c1_headers).json()
    if any(m["id"] == mid for m in c_models):
        log("ACTIVE model is visible to clients on /client/models", "PASS")
    else:
        log("ACTIVE model not returned to clients", "FAIL")

    # Also activate heart disease model
    heart_model = next((m for m in models if m["healthcare_task"] == "heart_disease_prediction"), None)
    if heart_model:
        requests.patch(f"{BACKEND_URL}/admin/models/{heart_model['id']}/status", json={"status": "active"}, headers=admin_headers)

    log("\n=== 4. Testing Client Workspace & START TRAINING Flow ===")
    # 4a. Opening workspace (GET only) -> zero training
    ws_r = requests.get(f"{BACKEND_URL}/client/models/{mid}", headers=c1_headers)
    if ws_r.status_code == 200:
        ws = ws_r.json()
        log(f"Client workspace opened (Model: {ws['name']}, Client: {ws['client_id']}, Local Records: {ws['client_private_data']['sample_count']})", "PASS")
    else:
        log(f"Client workspace GET failed: {ws_r.status_code}", "FAIL")

    # 4b. Explicit START TRAINING trigger (POST /train)
    t_start = time.time()
    tr_r = requests.post(f"{BACKEND_URL}/client/models/{mid}/train",
                         json={"local_epochs": 3, "learning_rate": 0.01, "batch_size": 16},
                         headers=c1_headers)
    dur = time.time() - t_start
    if tr_r.status_code == 200:
        tr = tr_r.json()
        log(f"START TRAINING executed in {dur:.2f}s: Samples={tr['sample_count']}, Acc={tr['accuracy']:.4f}, Initial Loss={tr['initial_loss']:.4f}, Final Loss={tr['final_loss']:.4f}, L2 Norm={tr['l2_norm']:.4f}, Update Size={tr['update_size_kb']} KB", "PASS")
    else:
        log(f"START TRAINING failed: {tr_r.text}", "FAIL")

    # 4c. Submit update to coordinator
    sub_r = requests.post(f"{BACKEND_URL}/client/models/{mid}/submit-update",
                          json={
                              "sample_count": tr["sample_count"],
                              "epochs_trained": tr["epochs_trained"],
                              "accuracy": tr["accuracy"],
                              "l2_norm": tr["l2_norm"],
                              "update_size_kb": tr["update_size_kb"],
                              "delta_base64": tr["delta_base64"],
                              "loss_history": tr["loss_history"]
                          },
                          headers=c1_headers)
    if sub_r.status_code == 200:
        sub = sub_r.json()
        log(f"Submit update response: {sub['message']} (Privacy: {sub['privacy_guarantee']})", "PASS")
    else:
        log(f"Submit update failed: {sub_r.text}", "FAIL")

    log("\n=== 5. Testing Admin FL Experiments & Stepping ===")
    exp_r = requests.post(f"{BACKEND_URL}/admin/experiments",
                          json={
                              "name": "Live Browser Verification FL Experiment",
                              "healthcare_task": "diabetes_prediction",
                              "model_id": mid,
                              "total_rounds": 3,
                              "strategy": "FedAvg",
                              "client_selection_mode": "adaptive",
                              "local_epochs": 3,
                              "learning_rate": 0.01
                          },
                          headers=admin_headers)
    if exp_r.status_code == 200:
        exp = exp_r.json()
        exp_id = exp["id"]
        log(f"Created FL experiment ID {exp_id} ({exp['name']})", "PASS")
    else:
        log(f"Failed to create experiment: {exp_r.text}", "FAIL")
        return

    # Step Round 1
    step_r = requests.post(f"{BACKEND_URL}/admin/experiments/{exp_id}/step", headers=admin_headers)
    if step_r.status_code == 200:
        r1 = step_r.json()
        log(f"Stepped Round 1: Global Acc={r1['global_accuracy']:.4f}, Loss={r1['global_loss']:.4f}, Clients={r1['participating_clients']}", "PASS")
    else:
        log(f"Step Round 1 failed: {step_r.text}", "FAIL")

    # Step Round 2
    step_r2 = requests.post(f"{BACKEND_URL}/admin/experiments/{exp_id}/step", headers=admin_headers)
    if step_r2.status_code == 200:
        r2 = step_r2.json()
        log(f"Stepped Round 2: Global Acc={r2['global_accuracy']:.4f}, Loss={r2['global_loss']:.4f}", "PASS")
    else:
        log(f"Step Round 2 failed: {step_r2.text}", "FAIL")

    # 5b. Check Contributions Endpoint
    contrib_r = requests.get(f"{BACKEND_URL}/admin/experiments/{exp_id}/contributions", headers=admin_headers)
    if contrib_r.status_code == 200:
        contribs = contrib_r.json()
        log(f"GET /admin/experiments/{exp_id}/contributions returned {len(contribs)} rounds of contributions", "PASS")
        for rc in contribs:
            log(f"  Round {rc['round_number']}: {len(rc['contributions'])} clients recorded")
            for c in rc["contributions"]:
                log(f"    - {c['client_id']} ({c['institution_name']}): samples={c['local_sample_count']}, acc={c['local_accuracy']}, status={c['training_status']}, weight={c['aggregation_weight']:.4f}, verified={c['update_verified']}")
    else:
        log(f"GET contributions failed: {contrib_r.text}", "FAIL")

    # 5c. Check Adaptive Client Scores
    scores_r = requests.get(f"{BACKEND_URL}/admin/experiments/{exp_id}/client-scores", headers=admin_headers)
    if scores_r.status_code == 200:
        scores = scores_r.json()
        log(f"Adaptive Client Scores returned for {list(scores.keys())}", "PASS")
        for cid, sc in scores.items():
            log(f"  - {cid}: Composite Score={sc['composite_score']}, Factors={sc['factors']}")
    else:
        log(f"Client scores failed: {scores_r.text}", "FAIL")

    log("\n=== 6. Testing Security, Communication, LLM, Analytics Endpoints ===")
    sec_r = requests.get(f"{BACKEND_URL}/admin/security/overview", headers=admin_headers)
    log(f"Security overview: screened={sec_r.json().get('total_screened_updates')}, flagged={sec_r.json().get('anomalous_updates_flagged')}", "PASS" if sec_r.status_code == 200 else "FAIL")

    comm_r = requests.get(f"{BACKEND_URL}/admin/communication/stats", headers=admin_headers)
    log(f"Communication stats: updates={comm_r.json().get('total_updates_transmitted')}, bandwidth saved={comm_r.json().get('bandwidth_saved_mb')} MB, reduction={comm_r.json().get('bandwidth_reduction_percent')}%", "PASS" if comm_r.status_code == 200 else "FAIL")

    llm_r = requests.post(f"{BACKEND_URL}/admin/llm/client-selection-advisor", json={"healthcare_task": "diabetes_prediction"}, headers=admin_headers)
    log(f"LLM Client Selection Advisory: source={llm_r.json().get('source')}, recommendations={llm_r.json().get('rationale')[:60]}...", "PASS" if llm_r.status_code == 200 else "FAIL")

    ana_r = requests.get(f"{BACKEND_URL}/admin/analytics/comparison?task=diabetes_prediction", headers=admin_headers)
    log(f"Analytics Comparison: proposed acc={ana_r.json().get('metrics_summary', {}).get('final_accuracy', {}).get('proposed')}", "PASS" if ana_r.status_code == 200 else "FAIL")

    telem_r = requests.get(f"{BACKEND_URL}/telemetry/recent", headers=admin_headers)
    log(f"Telemetry Recent Events count: {len(telem_r.json())}", "PASS" if telem_r.status_code == 200 else "FAIL")

    print("\n=== COMPLETE VERIFICATION SUMMARY ===")
    passes = [r for r in report if r["status"] == "PASS"]
    fails = [r for r in report if r["status"] == "FAIL"]
    print(f"Total Tests Run: {len(report)} | Passed: {len(passes)} | Failed: {len(fails)}")

if __name__ == "__main__":
    test_full_system()
