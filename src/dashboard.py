import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(__file__))
from simulation import render_simulation_mode

# Configuration
API_URL = "http://127.0.0.1:5000/predict"

st.set_page_config(
    page_title="Attack Analysis & Prevention Framework",
    page_icon="🛡️",
    layout="wide"
)

# Title and Description
st.title("🛡️ Automated Attack Analysis and Prevention Framework")

# Sidebar
st.sidebar.header("Control Panel")
mode = st.sidebar.radio("Mode", ["Dataset Analysis", "External Simulation"])

if mode == "External Simulation":
    render_simulation_mode()
    st.stop() # Stop execution of the rest of the script

st.markdown("""
This dashboard visualizes honeypot attack data and provides real-time classification and prevention strategies.
""")

page = st.sidebar.radio("Navigation", ["Real-time Analysis", "Historical Trends", "System Health"])

if page == "Real-time Analysis":
    st.header("Real-time Attack Classification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Network Parameters")
        duration = st.number_input("Duration", min_value=0.0, value=1.5)
        orig_bytes = st.number_input("Origin Bytes", min_value=0, value=120)
        resp_bytes = st.number_input("Response Bytes", min_value=0, value=500)
        orig_pkts = st.number_input("Origin Packets", min_value=0, value=5)
        resp_pkts = st.number_input("Response Packets", min_value=0, value=8)
        
    with col2:
        st.subheader("Derived Features")
        bytes_per_session = orig_bytes + resp_bytes
        packet_count = orig_pkts + resp_pkts
        history_len = st.slider("History Length (Proxy)", 0, 20, 5)
        
        st.metric("Bytes per Session", bytes_per_session)
        st.metric("Packet Count", packet_count)
        
    if st.button("Analyze Traffic"):
        payload = {
            "duration": duration,
            "orig_bytes": orig_bytes,
            "resp_bytes": resp_bytes,
            "bytes_per_session": bytes_per_session,
            "orig_pkts": orig_pkts,
            "resp_pkts": resp_pkts,
            "packet_count": packet_count,
            "history_len": history_len
        }
        
        try:
            with st.spinner("Analyzing..."):
                response = requests.post(API_URL, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                prediction = result['class_name']
                mitigation = result['mitigation']
                
                st.success(f"Prediction: **{prediction}**")
                
                st.subheader("Recommended Mitigation Strategies")
                for strategy in mitigation:
                    st.info(f"👉 {strategy}")
            else:
                st.error(f"Error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend API. Is it running?")

elif page == "Historical Trends":
    st.header("Historical Attack Trends")
    st.write("Visualizing trends from the CTU HORNER dataset.")
    
    # Placeholder for visualizations
    # In a real app, this would query a database or load the processed CSV
    
    # Mock Data
    data = {
        'Date': pd.date_range(start='1/1/2024', periods=10),
        'Attacks': [5, 12, 8, 15, 20, 18, 25, 30, 22, 10],
        'Probes': [50, 45, 60, 55, 70, 65, 80, 75, 60, 50]
    }
    df_trends = pd.DataFrame(data)
    
    st.line_chart(df_trends.set_index('Date'))
    
    st.subheader("Attack Distribution")
    fig, ax = plt.subplots()
    sns.barplot(x=['Intent-to-act', 'Intent-to-probe'], y=[78884, 12398280], ax=ax, palette="viridis")
    ax.set_yscale("log")
    st.pyplot(fig)

elif page == "System Health":
    st.header("System Health")
    try:
        response = requests.get("http://127.0.0.1:5000/health")
        if response.status_code == 200:
            status = response.json()
            st.json(status)
            if status.get("model_loaded"):
                st.success("Model is loaded and ready.")
            else:
                st.warning("Model is NOT loaded.")
        else:
            st.error("Backend is unreachable.")
    except:
        st.error("Backend is unreachable.")

# Footer
st.markdown("---")
st.markdown("© 2025 Automated Attack Analysis Framework")
