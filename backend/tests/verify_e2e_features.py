"""
End-to-end integration test for:
1. Model workspace fetching
2. Client training with standard dataset
3. Client training with large_cohort (~3,500 records)
4. Offline starter kit ZIP export with standard and large_cohort scale
5. Checkpoint weights download (.pt)
6. Offline update submission
"""
import io
import os
import sys
import zipfile

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_workspace_flow():
    model_id = "diabetes_prediction"
    client_id = "hospital_a"
    headers = {"x-client-id": client_id}

    # 1. Fetch workspace
    res = client.get(f"/api/v1/client/models/{model_id}/workspace", headers=headers)
    assert res.status_code == 200, f"Workspace failed: {res.text}"
    ws = res.json()
    print(f"✓ Workspace loaded: {ws['name']} ({ws['healthcare_task']})")
    assert ws['client_private_data'] is not None

    # 2. Train on standard dataset
    res_std = client.post(
        f"/api/v1/client/models/{model_id}/train",
        json={"local_epochs": 2, "learning_rate": 0.01, "batch_size": 16, "dataset_scale": "standard"},
        headers=headers
    )
    assert res_std.status_code == 200, f"Standard train failed: {res_std.text}"
    std_data = res_std.json()
    print(f"✓ Standard Train complete: {std_data['train_samples']} train samples, Loss: {std_data['final_loss']:.4f}, Acc: {std_data['accuracy']*100:.1f}%, Scale: {std_data['dataset_scale']}")
    assert std_data['train_samples'] < 500
    assert std_data['dataset_scale'] == "standard"

    # 3. Train on large_cohort (~3,500 records)
    res_large = client.post(
        f"/api/v1/client/models/{model_id}/train",
        json={"local_epochs": 2, "learning_rate": 0.01, "batch_size": 32, "dataset_scale": "large_cohort"},
        headers=headers
    )
    assert res_large.status_code == 200, f"Large cohort train failed: {res_large.text}"
    large_data = res_large.json()
    print(f"✓ Large Cohort Train complete: {large_data['sample_count']} total records ({large_data['train_samples']} train / {large_data['val_samples']} val), Loss: {large_data['final_loss']:.4f}, Acc: {large_data['accuracy']*100:.1f}%, Scale: {large_data['dataset_scale']}")
    assert large_data['sample_count'] >= 3000
    assert large_data['train_samples'] >= 2400
    assert large_data['dataset_scale'] == "large_cohort"
    assert len(large_data['loss_history']) == 2
    assert large_data['l2_norm'] > 0

    # 4. Download Starter Kit for standard and large_cohort
    for scale in ["standard", "large_cohort"]:
        res_kit = client.get(
            f"/api/v1/client/models/{model_id}/export-package?dataset_scale={scale}",
            headers=headers
        )
        assert res_kit.status_code == 200, f"Export kit failed for {scale}: {res_kit.text}"
        assert res_kit.headers["content-type"] == "application/zip"
        
        # Verify ZIP contains valid files
        zf = zipfile.ZipFile(io.BytesIO(res_kit.content))
        file_list = zf.namelist()
        print(f"✓ ZIP bundle ({scale}) contents: {file_list} (Size: {len(res_kit.content):,} bytes)")
        assert "train_local.py" in file_list
        assert "global_weights.pt" in file_list
        assert "local_dataset.csv" in file_list
        assert "README.md" in file_list
        
        # Read dataset in ZIP to check record count
        csv_bytes = zf.read("local_dataset.csv").decode("utf-8")
        csv_lines = [l for l in csv_bytes.split("\n") if l.strip()]
        line_count = len(csv_lines) - 1 # exclude header
        print(f"  -> local_dataset.csv has {line_count:,} records for scale='{scale}'")
        if scale == "large_cohort":
            assert line_count >= 3000
        else:
            assert line_count < 500

    # 5. Download model checkpoint (.pt)
    res_pt = client.get(f"/api/v1/client/models/{model_id}/download-model", headers=headers)
    assert res_pt.status_code == 200, f"Download model failed: {res_pt.text}"
    assert len(res_pt.content) > 0
    print(f"✓ Model weights (.pt) downloaded successfully ({len(res_pt.content):,} bytes)")

    # 6. Offline update submission using output from large_cohort
    sub_payload = {
        "sample_count": large_data["sample_count"],
        "epochs_trained": large_data["epochs_trained"],
        "accuracy": large_data["accuracy"],
        "loss": large_data["final_loss"],
        "l2_norm": large_data["l2_norm"],
        "update_size_kb": large_data["update_size_kb"],
        "training_time_ms": large_data["training_time_ms"],
        "delta_base64": large_data["delta_base64"],
        "loss_history": large_data["loss_history"],
        "val_loss_history": large_data.get("val_loss_history"),
        "val_accuracy_history": large_data.get("val_accuracy_history"),
        "gradient_steps": large_data.get("gradient_steps"),
    }
    res_sub = client.post(f"/api/v1/client/models/{model_id}/submit-update", json=sub_payload, headers=headers)
    assert res_sub.status_code == 200, f"Submit update failed: {res_sub.text}"
    sub_resp = res_sub.json()
    print(f"✓ Submit update accepted: {sub_resp['message']} (Round: {sub_resp['fl_round']}, Staged: {sub_resp['staged_updates']})")

    print("\n=========================================")
    print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_full_workspace_flow()
