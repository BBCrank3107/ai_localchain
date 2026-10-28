# -*- coding: utf-8 -*-
"""
Enterprise Dual-Model Pricing Trainer V3.1 (10/10 Gold Standard)
Huấn luyện 2 mô hình XGBoost Regressor độc lập (Decoupled Features, Zero fault_code):
1. Component Price Regressor (GroupKFold by component_id) -> component_model_v3.1.pkl
2. Labor Price Regressor (GroupKFold by device_id) -> labor_model_v3.1.pkl
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICING_DIR = os.path.join(BASE_DIR, "datasets", "pricing")
WEIGHTS_DIR = os.path.join(BASE_DIR, "model_3_pricing", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

COMP_CSV_PATH = os.path.join(PRICING_DIR, "component_train_dataset.csv")
LABOR_CSV_PATH = os.path.join(PRICING_DIR, "labor_train_dataset.csv")

print("=" * 70)
print("🚀 BẮT ĐẦU HUẤN LUYỆN DUAL-MODEL PRICING V3.1 (ENTERPRISE ARCHITECTURE)")
print("=" * 70)

# =====================================================================
# 1. HUẤN LUYỆN COMPONENT PRICE MODEL (MODEL A)
# =====================================================================
print("\n📦 [1/2] Đang huấn luyện Component Price Model (XGBoost)...")
df_comp = pd.read_csv(COMP_CSV_PATH)
print(f"   • Kích thước tập dữ liệu Linh Kiện: {df_comp.shape[0]} dòng, {df_comp.shape[1]} cột")

comp_cat_cols = ["component_id", "brand", "brand_tier", "part_type", "availability", "component_condition", "action_type"]
comp_num_cols = ["baseline_price_vnd", "market_age_days"]
comp_feature_cols = comp_cat_cols + comp_num_cols
comp_target_col = "target_component_price_vnd"

comp_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
comp_cat_encoded = comp_encoder.fit_transform(df_comp[comp_cat_cols])
X_comp = np.hstack([comp_cat_encoded, df_comp[comp_num_cols].values]).astype(np.float32)
y_comp = df_comp[comp_target_col].values.astype(np.float32)
groups_comp = df_comp["component_id"].values

# GroupKFold theo component_id (Đo khả năng ngoại suy)
gkf_comp = GroupKFold(n_splits=5)
comp_maes, comp_r2s = [], []

for fold, (train_idx, val_idx) in enumerate(gkf_comp.split(X_comp, y_comp, groups=groups_comp)):
    X_tr, y_tr = X_comp[train_idx], y_comp[train_idx]
    X_va, y_va = X_comp[val_idx], y_comp[val_idx]
    
    reg_comp = xgb.XGBRegressor(
        n_estimators=250,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42 + fold,
        n_jobs=-1
    )
    reg_comp.fit(X_tr, y_tr)
    preds = reg_comp.predict(X_va)
    
    mae = mean_absolute_error(y_va, preds)
    r2 = r2_score(y_va, preds)
    comp_maes.append(mae)
    comp_r2s.append(r2)

print(f"   • Cross-Validation (5-Fold GroupKFold by component_id):")
print(f"     -> MAE Trung Bình: {np.mean(comp_maes):,.0f} VNĐ (Target SLA < 80,000 VNĐ)")
print(f"     -> R² Score Trung Bình: {np.mean(comp_r2s):.4f}")

# Huấn luyện trên toàn bộ dữ liệu
final_comp_model = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1
)
final_comp_model.fit(X_comp, y_comp)

comp_cat_map = {col: {val: idx for idx, val in enumerate(cats)} for col, cats in zip(comp_cat_cols, comp_encoder.categories_)}
comp_artifact = {
    "model": final_comp_model,
    "encoder": comp_encoder,
    "cat_map": comp_cat_map,
    "cat_cols": comp_cat_cols,
    "num_cols": comp_num_cols,
    "feature_names": comp_feature_cols,
    "version": "3.1"
}

comp_model_path = os.path.join(WEIGHTS_DIR, "component_model_v3.1.pkl")
with open(comp_model_path, "wb") as f:
    pickle.dump(comp_artifact, f)
print(f"   💾 Đã lưu Component Model: {comp_model_path}")


# =====================================================================
# 2. HUẤN LUYỆN LABOR PRICE MODEL (MODEL B)
# =====================================================================
print("\n🛠️ [2/2] Đang huấn luyện Labor Price Model (XGBoost)...")
df_labor = pd.read_csv(LABOR_CSV_PATH)
print(f"   • Kích thước tập dữ liệu Tiền Công: {df_labor.shape[0]} dòng, {df_labor.shape[1]} cột")

labor_cat_cols = ["device_id", "region_class", "action_type"]
labor_num_cols = ["base_labor_vnd", "difficulty_score", "estimated_minutes", "tools_count", "requires_professional", "disassembly_level", "waterproof_level"]
labor_feature_cols = labor_cat_cols + labor_num_cols
labor_target_col = "target_labor_price_vnd"

labor_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
labor_cat_encoded = labor_encoder.fit_transform(df_labor[labor_cat_cols])
X_labor = np.hstack([labor_cat_encoded, df_labor[labor_num_cols].values]).astype(np.float32)
y_labor = df_labor[labor_target_col].values.astype(np.float32)
groups_labor = df_labor["device_id"].values

# GroupKFold theo device_id
gkf_labor = GroupKFold(n_splits=5)
labor_maes, labor_r2s = [], []

for fold, (train_idx, val_idx) in enumerate(gkf_labor.split(X_labor, y_labor, groups=groups_labor)):
    X_tr, y_tr = X_labor[train_idx], y_labor[train_idx]
    X_va, y_va = X_labor[val_idx], y_labor[val_idx]
    
    reg_labor = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42 + fold,
        n_jobs=-1
    )
    reg_labor.fit(X_tr, y_tr)
    preds = reg_labor.predict(X_va)
    
    mae = mean_absolute_error(y_va, preds)
    r2 = r2_score(y_va, preds)
    labor_maes.append(mae)
    labor_r2s.append(r2)

print(f"   • Cross-Validation (5-Fold GroupKFold by device_id):")
print(f"     -> MAE Trung Bình: {np.mean(labor_maes):,.0f} VNĐ (Target SLA < 40,000 VNĐ)")
print(f"     -> R² Score Trung Bình: {np.mean(labor_r2s):.4f}")

# Huấn luyện trên toàn bộ dữ liệu
final_labor_model = xgb.XGBRegressor(
    n_estimators=250,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1
)
final_labor_model.fit(X_labor, y_labor)

labor_cat_map = {col: {val: idx for idx, val in enumerate(cats)} for col, cats in zip(labor_cat_cols, labor_encoder.categories_)}
labor_artifact = {
    "model": final_labor_model,
    "encoder": labor_encoder,
    "cat_map": labor_cat_map,
    "cat_cols": labor_cat_cols,
    "num_cols": labor_num_cols,
    "feature_names": labor_feature_cols,
    "version": "3.1"
}

labor_model_path = os.path.join(WEIGHTS_DIR, "labor_model_v3.1.pkl")
with open(labor_model_path, "wb") as f:
    pickle.dump(labor_artifact, f)
print(f"   💾 Đã lưu Labor Model: {labor_model_path}")


# =====================================================================
# 3. LƯU METADATA & CONFIG AUDIT
# =====================================================================
metadata = {
    "pricing_schema_version": "3.1",
    "pricing_dataset_version": "3.1",
    "pricing_model_version": "3.1",
    "rule_engine_version": "1.0",
    "component_model": {
        "algorithm": "XGBoost Regressor",
        "features": comp_feature_cols,
        "train_samples": int(df_comp.shape[0]),
        "mae_cv_vnd": float(np.mean(comp_maes)),
        "r2_cv": float(np.mean(comp_r2s))
    },
    "labor_model": {
        "algorithm": "XGBoost Regressor",
        "features": labor_feature_cols,
        "train_samples": int(df_labor.shape[0]),
        "mae_cv_vnd": float(np.mean(labor_maes)),
        "r2_cv": float(np.mean(labor_r2s))
    }
}

meta_path = os.path.join(WEIGHTS_DIR, "pricing_metadata.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"\n📑 Đã lưu Metadata & Audit: {meta_path}")
print("=" * 70)
print("🎉 HOÀN TẤT HUẤN LUYỆN DUAL PRICING REGRESSORS V3.1!")
print("=" * 70)
