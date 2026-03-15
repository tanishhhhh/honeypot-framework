import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import xgboost as xgb
import pickle
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.data_loader import load_data
from src.feature_eng import FeatureEngineer

# Paths ─────────────────────────────────────────────
DB_PATH = os.getenv(
    "DB_PATH",
    r"C:\TANISH WORK\Msc CS\Semester 03\Reserach Paper\CTU Hornet 65 Niner A Network Dataset of Geographically Distributed Low-Interaction Honeypots\CTU-Hornet-65-Niner\duckdb\ctu-hornet-65-niner_v0.1.db",
)
MODEL_OUT = os.path.join(os.path.dirname(__file__), '..', 'best_model.pkl')
RESULTS_OUT = os.path.join(os.path.dirname(__file__), '..', 'training_results.json')


def train_models():
    # 1. Load Data
    df = load_data(DB_PATH)

    # 2. Feature Engineering
    fe = FeatureEngineer(df)
    X, y = fe.get_processed_data()

    print(f"Features shape: {X.shape}")
    print(f"Class distribution:\n{y.value_counts()}")
    print(f"Class ratio: 1:{int(y.value_counts()[0] / y.value_counts()[1])}")

    # 3. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(eval_metric='logloss', random_state=42),
    }

    best_model = None
    best_accuracy = 0
    best_f1 = 0

    results = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, pos_label=1)

        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[name] = {
            "accuracy": round(acc, 6),
            "f1_score": round(f1, 6),
            "classification_report": report,
            "confusion_matrix": cm,
        }

        print(f"{name}  Accuracy: {acc:.4f}  |  F1 (minority): {f1:.4f}")
        print(classification_report(y_test, y_pred))
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))

        # Select by F1 on the minority class, not accuracy
        score = f1_score(y_test, y_pred, pos_label=1)
        if score > best_f1:
            best_f1 = score
            best_accuracy = acc
            best_model = model

    # Save intermediate results from main loop
    # (saved here so results persist even if GridSearch fails)
    results_path = RESULTS_OUT
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nIntermediate results saved to training_results.json")

    # Save best model from main loop
    with open(MODEL_OUT, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"Best model saved to {MODEL_OUT}")
    print(f"  → {best_model.__class__.__name__}  F1={best_f1:.4f}")

    # XGBoost GridSearch (on stratified 10% sample to avoid memory crash on 12M rows)
    try:
        print("\nRunning GridSearch for XGBoost (stratified 10% sample)...")

        _, X_gs, _, y_gs = train_test_split(
            X_train, y_train,
            test_size=0.1,
            random_state=42,
            stratify=y_train
        )
        print(f"GridSearch sample: {len(X_gs):,} rows")

        param_grid = {
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.2],
            'n_estimators': [100, 200]
        }

        xgb_model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
        grid_search = GridSearchCV(
            xgb_model,
            param_grid,
            cv=3,
            scoring='f1',
            n_jobs=1,
            verbose=1
        )
        grid_search.fit(X_gs, y_gs)
        print(f"Best XGBoost Params: {grid_search.best_params_}")

        # Re-train best params on FULL training set for final evaluation
        best_xgb = xgb.XGBClassifier(
            **grid_search.best_params_,
            eval_metric='logloss',
            random_state=42
        )
        print("Re-training optimized XGBoost on full training set...")
        best_xgb.fit(X_train, y_train)

        y_pred_xgb = best_xgb.predict(X_test)
        f1_xgb = f1_score(y_test, y_pred_xgb, pos_label=1)
        acc_xgb = accuracy_score(y_test, y_pred_xgb)
        print(f"Optimized XGBoost — Accuracy: {acc_xgb:.4f}  |  F1: {f1_xgb:.4f}")
        print(classification_report(y_test, y_pred_xgb))
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred_xgb))

        # Update results and best model if improved
        results['XGBoost_optimized'] = {
            'accuracy': float(acc_xgb),
            'f1_score': float(f1_xgb),
            'best_params': grid_search.best_params_,
            'classification_report': classification_report(
                y_test, y_pred_xgb, output_dict=True
            ),
            'confusion_matrix': confusion_matrix(y_test, y_pred_xgb).tolist()
        }

        if f1_xgb > best_f1:
            best_model = best_xgb
            best_f1 = f1_xgb
            best_accuracy = acc_xgb

            # Re-save improved model
            with open(MODEL_OUT, 'wb') as f:
                pickle.dump(best_model, f)
            print(f"Best model updated: {best_model.__class__.__name__}  F1={best_f1:.4f}")

        # Update results file with GridSearch results
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("training_results.json updated with GridSearch results.")

    except MemoryError as e:
        print(f"\nGridSearch skipped — insufficient memory: {e}")
        print("Best model from main loop will be used instead.")
    except Exception as e:
        print(f"\nGridSearch failed: {e}")
        print("Best model from main loop will be used instead.")


if __name__ == "__main__":
    train_models()
