from flask import Flask, request, jsonify
import pandas as pd
import pickle
import os
import sys

sys.path.append(os.path.dirname(__file__))
from prevention import PreventionSystem

app = Flask(__name__)

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
        
        class_name = "Intent-to-act" if prediction == 1 else "Intent-to-probe"
        
        mitigation = prevention_system.get_mitigation(class_name)
        
        return jsonify({
            "prediction": int(prediction),
            "class_name": class_name,
            "mitigation": mitigation
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "ML Honeypot Framework API is running",
        "endpoints": {
            "predict": "/predict (POST)",
            "health": "/health (GET)",
            "dashboard": "http://localhost:8501"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "model_loaded": model is not None})

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5000)
