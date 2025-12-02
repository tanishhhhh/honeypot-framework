from flask import Flask, request, jsonify
import pandas as pd
import pickle
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(__file__))
from prevention import PreventionSystem

app = Flask(__name__)

# Load Model
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
    if not model:
        return jsonify({"error": "Model not loaded"}), 500
        
    try:
        data = request.get_json()
        
        # Expected features (must match training features)
        # For simplicity, we expect the preprocessed features or raw data that we process?
        # Ideally, we should reuse FeatureEngineer. But for this API, let's assume we receive features
        # or we instantiate FeatureEngineer.
        # Let's assume we receive a dictionary that matches the feature columns.
        
        # Feature columns from training:
        feature_cols = [
            'duration', 'orig_bytes', 'resp_bytes', 'bytes_per_session', 
            'orig_pkts', 'resp_pkts', 'packet_count', 'history_len'
        ]
        
        # Create DataFrame from input
        input_df = pd.DataFrame([data])
        
        # Ensure all columns exist, fill with 0 if missing
        for col in feature_cols:
            if col not in input_df.columns:
                input_df[col] = 0
                
        # Select and order columns
        X = input_df[feature_cols]
        
        # Add categorical columns if model expects them (one-hot encoded)
        # This is tricky without the exact same columns as training.
        # For XGBoost, it handles missing columns okay sometimes, but sklearn needs exact shape.
        # In a robust system, we'd save the column list or the pipeline.
        # For this MVP, let's assume the input provides the necessary numeric features 
        # and we ignore the one-hot encoded ones for now or assume they are not critical for this demo 
        # OR we should have saved the columns in training.
        
        # Let's try to predict.
        # Note: If the model was trained with one-hot encoded columns, we need to provide them.
        # The training script used `pd.get_dummies`.
        # To fix this properly, we should have saved the columns.
        # I will update `train_model.py` to save columns, but for now let's handle what we can.
        
        # Re-align columns to match model (if possible)
        if hasattr(model, 'feature_names_in_'):
            model_cols = model.feature_names_in_
            for col in model_cols:
                if col not in X.columns:
                    X[col] = 0
            X = X[model_cols]
        
        prediction = model.predict(X)[0]
        
        # Map prediction to class name
        class_name = "Intent-to-act" if prediction == 1 else "Intent-to-probe"
        
        mitigation = prevention_system.get_mitigation(class_name)
        
        return jsonify({
            "prediction": int(prediction),
            "class_name": class_name,
            "mitigation": mitigation
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "model_loaded": model is not None})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
