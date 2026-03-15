import streamlit as st
import pandas as pd
import pickle
import os
import numpy as np

def render_simulation_mode():
    st.header("External Simulation Mode")
    st.markdown("""
    Upload external honeypot logs (CSV) to test the detection model on new data.
    The system will attempt to align your data with the model's expected features.
    """)

    # 1. Load Model
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'best_model.pkl')
    model = None
    
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    if model is None:
        st.warning("Model not found. Please train the model first.")
        return

    # 2. File Uploader
    uploaded_file = st.file_uploader("Upload CSV Log File", type=["csv"])

    if uploaded_file is not None:
        try:
            
            df = pd.read_csv(uploaded_file, nrows=10000)
            
            st.write(f"**Loaded:** {len(df)} rows (capped at 10,000 for performance)")
            
            if st.button("Run Detection"):
                with st.spinner("Aligning features and running inference..."):
                    # 3. Feature Alignment
                    if hasattr(model, 'feature_names_in_'):
                        expected_features = model.feature_names_in_
                    else:
                        st.error("Model does not have feature names. Cannot align data.")
                        return

                    # Create a copy for processing
                    X = df.copy()
                    
                    #  Feature Engineering 
                    if 'orig_bytes' in X.columns and 'resp_bytes' in X.columns:
                        X['bytes_per_session'] = X['orig_bytes'] + X['resp_bytes']
                    
                    if 'orig_pkts' in X.columns and 'resp_pkts' in X.columns:
                        X['packet_count'] = X['orig_pkts'] + X['resp_pkts']
                        
                    if 'history' in X.columns:
                        X['history_len'] = X['history'].astype(str).apply(len)

                    # Ensure all expected columns exist
                    missing_cols = []
                    for col in expected_features:
                        if col not in X.columns:
                           
                            if col.startswith('proto_') and 'proto' in X.columns:
                                val = col[len('proto_'):]
                                X[col] = (X['proto'] == val).astype(int)
                            elif col.startswith('conn_state_') and 'conn_state' in X.columns:
                                val = col[len('conn_state_'):]
                                X[col] = (X['conn_state'] == val).astype(int)
                            else:
                                # Fallback: Fill with 0
                                X[col] = 0
                                missing_cols.append(col)

                    if missing_cols:
                        st.warning(
                            f"{len(missing_cols)} feature(s) not found in uploaded data "
                            f"and were zero-filled: {', '.join(missing_cols[:5])}"
                            f"{'...' if len(missing_cols) > 5 else ''}. "
                            f"Results may be less accurate."
                        )

                    # Reorder to match model expectation
                    X_final = X[expected_features]
                    
                    # 4. Inference
                    predictions = model.predict(X_final)
                    
                    # Add predictions to original dataframe
                    df['predicted_label'] = predictions
                    df['prediction_class'] = df['predicted_label'].map({1: 'Attack', 0: 'Benign/Probe'})
                    
                    # 5. Visuals
                    attack_count = np.sum(predictions == 1)
                    detection_rate = (attack_count / len(df)) * 100
                    
                    st.metric("Detection Rate (Attacks)", f"{detection_rate:.2f}%", f"{attack_count} detected")
                    
                    st.subheader("Detected Attack Traffic")
                    attacks_df = df[df['predicted_label'] == 1]
                    
                    if not attacks_df.empty:
                        st.dataframe(attacks_df)
                        
                        # Download Button
                        csv = attacks_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Attack Report",
                            csv,
                            "attack_report.csv",
                            "text/csv",
                            key='download-csv'
                        )
                    else:
                        st.success("No attacks detected in this sample.")
                        
        except Exception as e:
            st.error(f"Error processing file: {e}")
