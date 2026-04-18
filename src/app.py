from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from prevention import PreventionSystem
from alerting import send_email_alert
from siem import send_to_siem

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from React frontend

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'best_model.pkl')
model = None

def load_model():
    global model
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            print("Model loaded successfully.")
        else:
            print("Model not found. Please train the model first.")
    except Exception as e:
        print(f"Error loading model: {e}")

load_model()
prevention_system = PreventionSystem()

# ── Attack-type mapping (heuristic from feature profile) ────
ATTACK_TYPES = {
    1: [
        "Data Exfiltration",
        "Command & Control",
        "Lateral Movement",
        "Credential Theft",
    ],
    0: [
        "Network Scan",
        "Port Sweep",
        "Service Enumeration",
        "Vulnerability Probe",
    ],
}


def _infer_attack_type(prediction: int, features: dict) -> str:
    """Pick a specific attack type label based on feature heuristics."""
    if prediction == 1:
        orig = features.get("orig_bytes", 0)
        resp = features.get("resp_bytes", 0)
        if resp > orig * 3:
            return "Data Exfiltration"
        if features.get("duration", 0) > 60:
            return "Command & Control"
        if features.get("orig_pkts", 0) > 20:
            return "Lateral Movement"
        return "Credential Theft"
    else:
        if features.get("orig_pkts", 0) > 10:
            return "Port Sweep"
        if features.get("duration", 0) < 1:
            return "Service Enumeration"
        return "Network Scan"


@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
        
    try:
        data = request.get_json()
                
        feature_cols = [
            'duration', 'orig_bytes', 'resp_bytes',
            'orig_pkts', 'resp_pkts', 'packet_count', 'history_len'
        ]
        
        input_df = pd.DataFrame([data])
        
        for col in feature_cols:
            if col not in input_df.columns:
                input_df[col] = 0
                
        X = input_df[feature_cols]
                       
        if hasattr(model, 'feature_names_in_'):
            X = X.reindex(columns=model.feature_names_in_, fill_value=0)
        
        prediction = model.predict(X)[0]
        
        # ── Confidence score ────────────────────────────
        confidence = 0.5
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X)[0]
            confidence = float(np.max(proba))
        elif hasattr(model, 'decision_function'):
            decision = abs(float(model.decision_function(X)[0]))
            confidence = min(decision / 2.0, 1.0)  # rough normalisation

        # ── Severity level ──────────────────────────────
        if confidence > 0.9:
            severity = "HIGH"
        elif confidence > 0.7:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        class_name = "Intent-to-act" if prediction == 1 else "Intent-to-probe"
        attack_type = _infer_attack_type(int(prediction), data)
        mitigation = prevention_system.get_mitigation(class_name)
        timestamp = datetime.now(timezone.utc).isoformat()

        response_payload = {
            "prediction": int(prediction),
            "class_name": class_name,
            "attack_type": attack_type,
            "confidence": round(confidence, 4),
            "severity": severity,
            "mitigation": mitigation,
            "timestamp": timestamp,
        }

        # ── Non-blocking alerting & SIEM ────────────────
        alert_data = {
            **response_payload,
            "features": {
                "duration": data.get("duration", 0),
                "orig_bytes": data.get("orig_bytes", 0),
                "resp_bytes": data.get("resp_bytes", 0),
                "orig_pkts": data.get("orig_pkts", 0),
                "resp_pkts": data.get("resp_pkts", 0),
                "history_len": data.get("history_len", 0),
            },
        }

        try:
            if prediction == 1 and confidence > 0.9:
                send_email_alert(alert_data)
        except Exception as e:
            print(f"[ALERTING] Error: {e}")

        try:
            if prediction == 1:
                send_to_siem(alert_data)
        except Exception as e:
            print(f"[SIEM] Error: {e}")

        return jsonify(response_payload)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "ML Honeypot Framework API is running",
        "endpoints": {
            "predict": "/predict (POST)",
            "health": "/health (GET)",
            "dashboard": "http://localhost:5173"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5000)
