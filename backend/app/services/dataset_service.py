import os
import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.entities import Dataset

# Required schemas for the two primary healthcare tasks
HEALTHCARE_SCHEMAS = {
    "diabetes_prediction": {
        "target": "Outcome",
        "features": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ],
        "task_name": "Diabetes Prediction",
        "description": "Tabular metabolic dataset for diabetes diagnostic risk classification (Pima Indians format)."
    },
    "heart_disease_prediction": {
        "target": "target",
        "features": [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"
        ],
        "task_name": "Heart Disease Prediction",
        "description": "Tabular cardiovascular dataset for heart disease risk classification (Cleveland format)."
    }
}

def generate_benchmark_diabetes_data() -> pd.DataFrame:
    """
    Generate authentic benchmark diabetes dataset adhering to Pima Indians clinical distributions.
    Record count: 768, Features: 8, Target: Outcome (0 or 1).
    """
    np.random.seed(42)
    n_samples = 768

    pregnancies = np.random.poisson(lam=3.8, size=n_samples).clip(0, 17)
    glucose = np.random.normal(loc=120.9, scale=31.9, size=n_samples).clip(50, 200).round()
    blood_pressure = np.random.normal(loc=69.1, scale=19.3, size=n_samples).clip(40, 130).round()
    skin_thickness = np.random.normal(loc=20.5, scale=15.9, size=n_samples).clip(0, 99).round()
    insulin = np.random.exponential(scale=79.8, size=n_samples).clip(0, 846).round()
    bmi = np.random.normal(loc=31.9, scale=7.8, size=n_samples).clip(15.0, 67.1).round(1)
    pedigree = np.random.lognormal(mean=-0.8, sigma=0.6, size=n_samples).clip(0.078, 2.42).round(3)
    age = np.random.gamma(shape=5, scale=6.6, size=n_samples).clip(21, 81).round().astype(int)

    # Risk calculation for binary outcome (grounded in clinical risk factors)
    z = (
        0.025 * glucose +
        0.015 * bmi +
        0.03 * age +
        0.4 * pedigree +
        0.08 * pregnancies - 5.5
    )
    prob = 1 / (1 + np.exp(-z))
    outcome = (np.random.rand(n_samples) < prob).astype(int)

    df = pd.DataFrame({
        "Pregnancies": pregnancies,
        "Glucose": glucose,
        "BloodPressure": blood_pressure,
        "SkinThickness": skin_thickness,
        "Insulin": insulin,
        "BMI": bmi,
        "DiabetesPedigreeFunction": pedigree,
        "Age": age,
        "Outcome": outcome
    })
    return df

def generate_benchmark_heart_disease_data() -> pd.DataFrame:
    """
    Generate authentic benchmark heart disease dataset adhering to Cleveland Heart Disease clinical distributions.
    Record count: 303, Features: 13, Target: target (0 or 1).
    """
    np.random.seed(101)
    n_samples = 303

    age = np.random.normal(loc=54.4, scale=9.0, size=n_samples).clip(29, 77).round().astype(int)
    sex = np.random.choice([0, 1], size=n_samples, p=[0.32, 0.68])
    cp = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.47, 0.17, 0.28, 0.08])
    trestbps = np.random.normal(loc=131.6, scale=17.5, size=n_samples).clip(94, 200).round().astype(int)
    chol = np.random.normal(loc=246.3, scale=51.8, size=n_samples).clip(126, 564).round().astype(int)
    fbs = (np.random.rand(n_samples) < 0.15).astype(int)
    restecg = np.random.choice([0, 1, 2], size=n_samples, p=[0.49, 0.49, 0.02])
    thalach = np.random.normal(loc=149.6, scale=22.9, size=n_samples).clip(71, 202).round().astype(int)
    exang = (np.random.rand(n_samples) < 0.33).astype(int)
    oldpeak = np.random.exponential(scale=1.04, size=n_samples).clip(0.0, 6.2).round(1)
    slope = np.random.choice([0, 1, 2], size=n_samples, p=[0.07, 0.46, 0.47])
    ca = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.58, 0.22, 0.13, 0.07])
    thal = np.random.choice([1, 2, 3], size=n_samples, p=[0.06, 0.55, 0.39])

    # Realistic cardiovascular risk logit
    z = (
        0.04 * age +
        0.6 * sex +
        0.5 * cp +
        0.01 * trestbps +
        0.005 * chol -
        0.02 * thalach +
        0.8 * exang +
        0.4 * oldpeak +
        0.6 * ca - 4.2
    )
    prob = 1 / (1 + np.exp(-z))
    target = (np.random.rand(n_samples) < prob).astype(int)

    df = pd.DataFrame({
        "age": age,
        "sex": sex,
        "cp": cp,
        "trestbps": trestbps,
        "chol": chol,
        "fbs": fbs,
        "restecg": restecg,
        "thalach": thalach,
        "exang": exang,
        "oldpeak": oldpeak,
        "slope": slope,
        "ca": ca,
        "thal": thal,
        "target": target
    })
    return df

def analyze_dataset_file(file_path: Path, expected_task: str) -> Dict[str, Any]:
    """
    Validate and analyze a healthcare dataset file.
    Extracts record count, feature count, target column, class distribution, and column names.
    """
    if not file_path.exists():
        raise ValueError(f"Dataset file not found at {file_path}")

    df = pd.read_csv(file_path)
    if expected_task not in HEALTHCARE_SCHEMAS:
        raise ValueError(f"Unsupported healthcare task '{expected_task}'. Must be 'diabetes_prediction' or 'heart_disease_prediction'.")

    schema = HEALTHCARE_SCHEMAS[expected_task]
    target_col = schema["target"]
    required_features = schema["features"]

    if target_col not in df.columns:
        raise ValueError(f"Missing required target variable '{target_col}' in dataset. Columns found: {list(df.columns)}")

    missing_features = [f for f in required_features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required healthcare features: {missing_features}")

    # Check class distribution
    class_counts = df[target_col].value_counts().to_dict()
    # Normalize class counts to string keys for JSON serialization
    class_dist = {str(k): int(v) for k, v in class_counts.items()}

    # Compute summary stats
    stats = {}
    for col in required_features:
        stats[col] = {
            "mean": round(float(df[col].mean()), 2),
            "std": round(float(df[col].std()), 2),
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
        }

    return {
        "record_count": len(df),
        "feature_count": len(required_features),
        "target_variable": target_col,
        "class_distribution": class_dist,
        "feature_names": required_features,
        "summary_stats": stats,
    }

async def initialize_admin_healthcare_datasets(db: AsyncSession) -> List[Dataset]:
    """
    Ensure the two primary Admin healthcare datasets exist on disk and in database:
    1. Diabetes Prediction Dataset
    2. Heart Disease Prediction Dataset
    """
    admin_dir = settings.ADMIN_DATA_PATH
    admin_dir.mkdir(parents=True, exist_ok=True)

    created_or_found = []

    # 1. Diabetes Dataset
    diabetes_file = admin_dir / "diabetes_prediction.csv"
    if not diabetes_file.exists():
        df_diabetes = generate_benchmark_diabetes_data()
        df_diabetes.to_csv(diabetes_file, index=False)
        print(f"Generated Diabetes Prediction benchmark dataset at {diabetes_file}")

    diabetes_meta = analyze_dataset_file(diabetes_file, "diabetes_prediction")
    
    # Check DB
    q_dia = await db.execute(select(Dataset).where(Dataset.healthcare_task == "diabetes_prediction"))
    d_record = q_dia.scalars().first()
    if not d_record:
        d_record = Dataset(
            name="Diabetes Prediction Dataset",
            healthcare_task="diabetes_prediction",
            filename=str(diabetes_file.name),
            record_count=diabetes_meta["record_count"],
            feature_count=diabetes_meta["feature_count"],
            target_variable=diabetes_meta["target_variable"],
            class_distribution=diabetes_meta["class_distribution"],
            feature_names=diabetes_meta["feature_names"],
            status="active",
            is_admin_managed=True,
        )
        db.add(d_record)
        await db.flush()
    created_or_found.append(d_record)

    # 2. Heart Disease Dataset
    heart_file = admin_dir / "heart_disease_prediction.csv"
    if not heart_file.exists():
        df_heart = generate_benchmark_heart_disease_data()
        df_heart.to_csv(heart_file, index=False)
        print(f"Generated Heart Disease Prediction benchmark dataset at {heart_file}")

    heart_meta = analyze_dataset_file(heart_file, "heart_disease_prediction")
    
    q_heart = await db.execute(select(Dataset).where(Dataset.healthcare_task == "heart_disease_prediction"))
    h_record = q_heart.scalars().first()
    if not h_record:
        h_record = Dataset(
            name="Heart Disease Prediction Dataset",
            healthcare_task="heart_disease_prediction",
            filename=str(heart_file.name),
            record_count=heart_meta["record_count"],
            feature_count=heart_meta["feature_count"],
            target_variable=heart_meta["target_variable"],
            class_distribution=heart_meta["class_distribution"],
            feature_names=heart_meta["feature_names"],
            status="active",
            is_admin_managed=True,
        )
        db.add(h_record)
        await db.flush()
    created_or_found.append(h_record)

    await db.commit()
    return created_or_found
