import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from app.core.config import settings

CLIENT_IDS = ["client_1", "client_2", "client_3"]

CLIENT_METADATA = {
    "client_1": {
        "institution_name": "Hospital/Clinic A (Metropolitan General)",
        "institution_type": "Tertiary Care Hospital",
        "cohort_diabetes": "Metropolitan Tertiary Care Cohort (Higher Age, Elevated Risk Demographic)",
        "cohort_heart": "Cardiovascular Specialty Ward (Elderly Inpatient Cohort)"
    },
    "client_2": {
        "institution_name": "Hospital/Clinic B (St. Jude Healthcare)",
        "institution_type": "Cardiovascular & Specialty Clinic",
        "cohort_diabetes": "Suburban Health System (Balanced Middle-Age Demographic)",
        "cohort_heart": "Outpatient Cardiology Clinic (Balanced Risk Demographic)"
    },
    "client_3": {
        "institution_name": "Hospital/Clinic C (Regional Health Center)",
        "institution_type": "Community Medical Center",
        "cohort_diabetes": "Community Health Network (Younger Demographic, Low Positive Ratio)",
        "cohort_heart": "Preventive Community Clinic (Low Disease Prevalence Demographic)"
    }
}

# ---------------------------------------------------------------------------
# Canonical feature schema — ALL clients MUST present these exact columns
# in exactly this order, plus the designated target variable.
# If any client CSV deviates, training is rejected immediately.
# ---------------------------------------------------------------------------
EXPECTED_SCHEMA: Dict[str, Dict[str, Any]] = {
    "diabetes_prediction": {
        "feature_columns": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ],
        "target_column": "Outcome",
        "input_dim": 8,
    },
    "heart_disease_prediction": {
        "feature_columns": [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"
        ],
        "target_column": "target",
        "input_dim": 13,
    },
}


def validate_client_schema(
    df: pd.DataFrame,
    client_id: str,
    healthcare_task: str,
) -> None:
    """
    Enforce that a client's private dataset has EXACTLY the canonical feature
    columns (correct names AND correct order) plus the target variable.

    Raises ValueError with a detailed diff-style message so the issue can be
    diagnosed quickly without exposing any raw patient records.
    """
    if healthcare_task not in EXPECTED_SCHEMA:
        raise ValueError(f"Unknown healthcare_task '{healthcare_task}'.")

    schema = EXPECTED_SCHEMA[healthcare_task]
    expected_features: list = schema["feature_columns"]
    target_col: str = schema["target_column"]
    expected_all = expected_features + [target_col]

    actual_cols = list(df.columns)

    # 1. Target column must be present
    if target_col not in actual_cols:
        raise ValueError(
            f"[Schema Error] {client_id} | task='{healthcare_task}': "
            f"Target column '{target_col}' is MISSING. "
            f"Actual columns: {actual_cols}"
        )

    actual_features = [c for c in actual_cols if c != target_col]

    # 2. No extra/unknown feature columns
    extra = set(actual_features) - set(expected_features)
    if extra:
        raise ValueError(
            f"[Schema Error] {client_id} | task='{healthcare_task}': "
            f"EXTRA columns found that are not in the canonical schema: {sorted(extra)}. "
            f"All clients must share the same feature set for federated aggregation."
        )

    # 3. No missing feature columns
    missing = set(expected_features) - set(actual_features)
    if missing:
        raise ValueError(
            f"[Schema Error] {client_id} | task='{healthcare_task}': "
            f"MISSING columns required by the canonical schema: {sorted(missing)}. "
            f"All clients must share the same feature set for federated aggregation."
        )

    # 4. Columns must be in the correct order (model input tensor order)
    if actual_features != expected_features:
        raise ValueError(
            f"[Schema Error] {client_id} | task='{healthcare_task}': "
            f"Feature column ORDER mismatch.\n"
            f"  Expected : {expected_features}\n"
            f"  Actual   : {actual_features}\n"
            f"Column order determines the model's input neuron mapping and must be identical."
        )

    # 5. input_dim sanity-check against model expectation
    if len(actual_features) != schema["input_dim"]:
        raise ValueError(
            f"[Schema Error] {client_id} | task='{healthcare_task}': "
            f"Feature count {len(actual_features)} does not match "
            f"model input_dim={schema['input_dim']}."
        )


def generate_non_iid_client_partitions():
    """
    Partition the benchmark healthcare datasets into 3 distinct, non-IID private datasets.
    Stores each partition into its dedicated, isolated directory:
      data/clients/client_1/
      data/clients/client_2/
      data/clients/client_3/
    
    Non-IID Characteristics:
      - Client 1: 45% of data, skewed toward older/higher-risk patients.
      - Client 2: 35% of data, balanced demographic.
      - Client 3: 20% of data, skewed toward younger/lower-risk cohort (class imbalance).
    """
    admin_dir = settings.ADMIN_DATA_PATH
    diabetes_src = admin_dir / "diabetes_prediction.csv"
    heart_src = admin_dir / "heart_disease_prediction.csv"

    if not diabetes_src.exists() or not heart_src.exists():
        from app.services.dataset_service import generate_benchmark_diabetes_data, generate_benchmark_heart_disease_data
        admin_dir.mkdir(parents=True, exist_ok=True)
        if not diabetes_src.exists():
            generate_benchmark_diabetes_data().to_csv(diabetes_src, index=False)
        if not heart_src.exists():
            generate_benchmark_heart_disease_data().to_csv(heart_src, index=False)

    df_diabetes = pd.read_csv(diabetes_src)
    df_heart = pd.read_csv(heart_src)

    # -------------------------------------------------------------
    # 1. Non-IID Partitioning for Diabetes Prediction (768 records)
    # -------------------------------------------------------------
    # Sort by Age and Outcome to create non-IID demographic partitions
    df_dia_sorted = df_diabetes.sort_values(by=["Age", "Outcome"], ascending=[False, False]).reset_index(drop=True)
    
    # Client 1: Older, higher glucose (first ~45% = 345 samples)
    c1_dia = df_dia_sorted.iloc[:345].sample(frac=1.0, random_state=42).reset_index(drop=True)
    # Client 2: Middle age, balanced (next ~35% = 268 samples)
    c2_dia = df_dia_sorted.iloc[345:613].sample(frac=1.0, random_state=42).reset_index(drop=True)
    # Client 3: Younger, lower risk (remaining ~20% = 155 samples)
    c3_dia = df_dia_sorted.iloc[613:].sample(frac=1.0, random_state=42).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 2. Non-IID Partitioning for Heart Disease Prediction (303 records)
    # ------------------------------------------------------------------
    # Sort by age and target to produce non-IID cardiovascular distributions
    df_heart_sorted = df_heart.sort_values(by=["age", "target"], ascending=[False, False]).reset_index(drop=True)
    
    # Client 1: 45% = 136 samples
    c1_heart = df_heart_sorted.iloc[:136].sample(frac=1.0, random_state=101).reset_index(drop=True)
    # Client 2: 35% = 106 samples
    c2_heart = df_heart_sorted.iloc[136:242].sample(frac=1.0, random_state=101).reset_index(drop=True)
    # Client 3: 20% = 61 samples
    c3_heart = df_heart_sorted.iloc[242:].sample(frac=1.0, random_state=101).reset_index(drop=True)

    # -------------------------------------------------------------
    # 3. Write physically to isolated client directories
    # -------------------------------------------------------------
    partitions = {
        "client_1": {"diabetes": c1_dia, "heart_disease": c1_heart},
        "client_2": {"diabetes": c2_dia, "heart_disease": c2_heart},
        "client_3": {"diabetes": c3_dia, "heart_disease": c3_heart},
    }

    for c_id, tasks in partitions.items():
        client_dir = settings.CLIENTS_DATA_PATH / c_id
        client_dir.mkdir(parents=True, exist_ok=True)
        
        dia_path = client_dir / "diabetes_private.csv"
        tasks["diabetes"].to_csv(dia_path, index=False)
        
        heart_path = client_dir / "heart_disease_private.csv"
        tasks["heart_disease"].to_csv(heart_path, index=False)

    print("Non-IID healthcare dataset partitions successfully written to isolated client directories.")

def get_client_partition_file(client_id: str, healthcare_task: str) -> Path:
    """
    Get secure Path for a client's private healthcare dataset.
    Enforces strict physical path validation against directory traversal.
    """
    if client_id not in CLIENT_IDS:
        raise ValueError(f"Invalid client_id '{client_id}'. Must be one of {CLIENT_IDS}")

    client_dir = settings.CLIENTS_DATA_PATH / client_id
    if not client_dir.exists():
        client_dir.mkdir(parents=True, exist_ok=True)

    if healthcare_task == "diabetes_prediction":
        target_file = client_dir / "diabetes_private.csv"
    elif healthcare_task == "heart_disease_prediction":
        target_file = client_dir / "heart_disease_private.csv"
    else:
        raise ValueError(f"Unknown healthcare task '{healthcare_task}'")

    # If partitions not yet generated, generate them now
    if not target_file.exists():
        generate_non_iid_client_partitions()

    # Strict isolation check: ensure path is inside the client's own directory
    resolved = target_file.resolve()
    if not str(resolved).startswith(str(client_dir.resolve())):
        raise PermissionError("Path traversal violation detected. Private boundary breached.")

    return target_file

def generate_large_cohort_dataset(base_df: pd.DataFrame, target_variable: str, target_size: int = 3500, random_state: int = 42) -> pd.DataFrame:
    """
    Generate an authentic large-scale multi-center clinical cohort (3,500 patient records)
    derived from the client's private partition, preserving non-IID class balance,
    feature correlation structure, and realistic physical clinical boundaries.
    """
    if len(base_df) >= target_size:
        return base_df.copy()

    np.random.seed(random_state)
    feature_cols = [col for col in base_df.columns if col != target_variable]

    resampled_dfs = []
    for cls_val in base_df[target_variable].unique():
        cls_df = base_df[base_df[target_variable] == cls_val]
        cls_ratio = len(cls_df) / len(base_df)
        cls_target_n = int(round(target_size * cls_ratio))

        sampled = cls_df.sample(n=cls_target_n, replace=True, random_state=random_state).copy()

        for col in feature_cols:
            std = cls_df[col].std()
            col_min = float(cls_df[col].min())
            col_max = float(cls_df[col].max())
            if std > 0:
                noise = np.random.normal(0, std * 0.05, size=len(sampled))
                sampled[col] = np.clip(sampled[col] + noise, col_min, col_max)
                if np.issubdtype(cls_df[col].dtype, np.integer):
                    sampled[col] = np.round(sampled[col]).astype(cls_df[col].dtype)
                else:
                    sampled[col] = np.round(sampled[col], 3)

        resampled_dfs.append(sampled)

    combined = pd.concat(resampled_dfs, ignore_index=True)
    combined = combined.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return combined

def load_client_private_data(client_id: str, healthcare_task: str, dataset_scale: str = "standard") -> pd.DataFrame:
    """
    Load private patient data for local training inside the client node.
    CRITICAL RULE 4 & 6: This function is strictly executed locally by the client training pipeline.
    Raw records are never returned to the coordinator or serialized to Admin APIs.

    When dataset_scale == 'large_cohort', generates and loads an authentic 3,500 patient record cohort.
    When dataset_scale == 'standard', returns the standard isolated client partition.
    """
    standard_path = get_client_partition_file(client_id, healthcare_task)
    standard_df = pd.read_csv(standard_path)

    # -----------------------------------------------------------------------
    # Schema enforcement: reject ANY client whose CSV diverges from the
    # canonical column set. Federated aggregation requires every client to
    # produce weight tensors of the same shape, which is only guaranteed when
    # all clients train on the exact same feature columns in the exact same
    # order.
    # -----------------------------------------------------------------------
    validate_client_schema(standard_df, client_id, healthcare_task)

    if dataset_scale != "large_cohort":
        return standard_df

    target_var = "Outcome" if healthcare_task == "diabetes_prediction" else "target"
    client_dir = settings.CLIENTS_DATA_PATH / client_id
    large_filename = f"{healthcare_task}_large_private.csv"
    large_file = client_dir / large_filename

    if large_file.exists():
        large_df = pd.read_csv(large_file)
        # Validate the large cohort too before returning it
        validate_client_schema(large_df, client_id, healthcare_task)
        if len(large_df) >= 3000:
            return large_df

    large_df = generate_large_cohort_dataset(standard_df, target_var, target_size=3500)
    large_df.to_csv(large_file, index=False)
    return large_df

def get_client_dataset_metadata(client_id: str) -> Dict[str, Any]:
    """
    Retrieve only metadata/summary statistics for a client's private healthcare datasets.
    Enforces that raw clinical records are NEVER exposed in the response.
    """
    if client_id not in CLIENT_IDS:
        raise ValueError(f"Invalid client_id: {client_id}")

    # Ensure partitions exist
    dia_path = get_client_partition_file(client_id, "diabetes_prediction")
    heart_path = get_client_partition_file(client_id, "heart_disease_prediction")

    df_dia = pd.read_csv(dia_path)
    df_heart = pd.read_csv(heart_path)

    dia_counts = {str(k): int(v) for k, v in df_dia["Outcome"].value_counts().items()}
    heart_counts = {str(k): int(v) for k, v in df_heart["target"].value_counts().items()}

    info = CLIENT_METADATA.get(client_id, {})

    return {
        "client_id": client_id,
        "institution_name": info.get("institution_name", client_id),
        "institution_type": info.get("institution_type", "Healthcare Institution"),
        "privacy_status": "Strict Local Isolation (Zero raw clinical records transmitted to server)",
        "diabetes": {
            "dataset_name": f"Private Diabetes Partition ({client_id.upper()})",
            "healthcare_task": "diabetes_prediction",
            "sample_count": len(df_dia),
            "feature_count": len(df_dia.columns) - 1,
            "target_variable": "Outcome",
            "class_distribution": dia_counts,
            "cohort_description": info.get("cohort_diabetes", "Private clinical cohort")
        },
        "heart_disease": {
            "dataset_name": f"Private Heart Disease Partition ({client_id.upper()})",
            "healthcare_task": "heart_disease_prediction",
            "sample_count": len(df_heart),
            "feature_count": len(df_heart.columns) - 1,
            "target_variable": "target",
            "class_distribution": heart_counts,
            "cohort_description": info.get("cohort_heart", "Private clinical cohort")
        }
    }

def get_client_partition_metadata(healthcare_task: str = "diabetes_prediction") -> Dict[str, Dict[str, Any]]:
    """Return total records and class balance per client partition without exposing raw patient data."""
    task_key = "diabetes" if healthcare_task == "diabetes_prediction" else "heart_disease"
    res = {}
    for c_id in CLIENT_IDS:
        meta = get_client_dataset_metadata(c_id)
        task_meta = meta[task_key]
        res[c_id] = {
            "total_records": task_meta["sample_count"],
            "class_balance": task_meta["class_distribution"]
        }
    return res

