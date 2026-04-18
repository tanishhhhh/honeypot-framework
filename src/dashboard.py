import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import subprocess
import sys
import os
import pickle
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))
from simulation import render_simulation_mode

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000/predict")
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://admin:admin123@localhost:5432/honeypot")

# Session state initialisation
if 'sim_process' not in st.session_state:
    st.session_state['sim_process'] = None


@st.cache_resource
def load_model_cached():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'best_model.pkl')
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def _get_db_engine():
    """Create a SQLAlchemy engine (import here to avoid top-level crash if not installed)."""
    from sqlalchemy import create_engine, text  # noqa: F811
    return create_engine(DB_URL), text


def _classify_rows(df, model):
    """Extract features from raw DB rows and return model predictions."""
    import numpy as np
    X = df[['duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts']].copy()
    X['packet_count'] = df['orig_pkts'].fillna(0) + df['resp_pkts'].fillna(0)
    X['history_len'] = df['history'].astype(str).apply(len)
    # One-hot encode proto
    proto_dummies = pd.get_dummies(df['proto'], prefix='proto')
    X = pd.concat([X, proto_dummies], axis=1)
    # Align to model features
    if hasattr(model, 'feature_names_in_'):
        X = X.reindex(columns=model.feature_names_in_, fill_value=0)
    return model.predict(X)



st.set_page_config(
    page_title="Attack Analysis & Prevention Framework",
    page_icon="🛡️",
    layout="wide"
)

# Title and Description
st.title("Automated Attack Analysis and Prevention Framework")

# Sidebar
st.sidebar.header("Control Panel")
mode = st.sidebar.radio("Mode", ["Dataset Analysis", "External Simulation"])

if mode == "External Simulation":
    render_simulation_mode()
    st.stop()  # Stop execution of the rest of the script

st.markdown("""
This dashboard visualizes honeypot attack data and provides real-time classification and prevention strategies.
""")

page = st.sidebar.radio("Navigation", [
    "Real-time Analysis", "Historical Trends",
    "System Health", "Live Database Monitor"
])

auto_refresh = False  # initialised here so the auto-refresh block at the end never raises NameError

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
    st.caption("⚠️ Chart shows illustrative sample data. Connect live DB for real trends.")

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
    plt.close(fig)

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
    except Exception:
        st.error("Backend is unreachable.")

# ══════════════════════════════════════════════════════════════════════
#  LIVE DATABASE MONITOR PAGE
# ══════════════════════════════════════════════════════════════════════
elif page == "Live Database Monitor":
    st.header("🔴 Live Database Monitor")

    # ── Helpers ──────────────────────────────────────────────────────
    db_connected = False
    db_conn_error = ""
    engine = None
    _text = None
    try:
        engine, _text = _get_db_engine()
        with engine.connect() as conn:
            conn.execute(_text("SELECT 1"))
        db_connected = True
    except Exception as e:
        db_conn_error = str(e)

    # ── Section A — Connection status ────────────────────────────────
    if db_connected:
        try:
            with engine.connect() as conn:
                total_rows = conn.execute(_text("SELECT COUNT(*) FROM logs")).scalar()
            st.success(f"✅ PostgreSQL connected — honeypot-live database ready  |  **{total_rows:,}** rows in logs")
        except Exception as e:
            st.success("✅ PostgreSQL connected — honeypot-live database ready")
            st.warning(f"Could not read row count: {e}")
            total_rows = 0
    else:
        st.error(f"❌ PostgreSQL not running. Start with: `docker start honeypot-live`\n\nError: {db_conn_error}")
        total_rows = 0

    # ── Section B — Simulator controls ───────────────────────────────
    st.subheader("Controls")
    ctrl_left, ctrl_right = st.columns(2)

    with ctrl_left:
        st.markdown("**Simulator Controls**")
        sim_script = os.path.join(os.path.dirname(__file__), '..', 'simulate_attacks.py')

        if st.button("▶ Start Inserting Attacks"):
            try:
                proc = subprocess.Popen(
                    ['python', sim_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                st.session_state['sim_process'] = proc
                st.success("Simulator running...")
            except Exception as e:
                st.error(f"Failed to start simulator: {e}")

        if st.button("⏹ Stop Simulator"):
            proc = st.session_state.get('sim_process')
            if proc and proc.poll() is None:
                proc.terminate()
                st.info("Simulator stopped.")
                st.session_state['sim_process'] = None
            else:
                st.info("Simulator is not running.")

    with ctrl_right:
        st.markdown("**Auto-refresh**")
        auto_refresh = st.checkbox("Auto-refresh every 3 seconds")
        if st.button("🔄 Refresh Now"):
            st.rerun()

    st.markdown("---")

    # ── Section C — Live metrics row ─────────────────────────────────
    if db_connected:
        # Load model for on-the-fly classification
        model = None
        try:
            model = load_model_cached()
        except Exception as e:
            st.error(f"Model loading failed: {e}")

        # Classify last 100 rows for metrics
        attack_count = 0
        probe_count = 0
        try:
            with engine.connect() as conn:
                df_100 = pd.read_sql(
                    "SELECT * FROM logs ORDER BY id DESC LIMIT 100",
                    conn,
                )
            if not df_100.empty and model is not None:
                preds = _classify_rows(df_100, model)
                attack_count = int((preds == 1).sum())
                probe_count = int((preds == 0).sum())
        except Exception as e:
            st.warning(f"Metrics query failed: {e}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Connections", f"{total_rows:,}")
        m2.metric("Attacks Detected", attack_count, help="From last 100 rows")
        m3.metric("Probes Detected", probe_count, help="From last 100 rows")
        m4.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

        st.markdown("---")

        # ── Section D — Live connection feed ─────────────────────────
        st.subheader("Live Connection Feed (last 20)")
        df_feed = pd.DataFrame()  # initialise so the alerts section below can safely check it
        try:
            with engine.connect() as conn:
                df_feed = pd.read_sql(
                    "SELECT * FROM logs ORDER BY id DESC LIMIT 20",
                    conn,
                )
            if not df_feed.empty and model is not None:
                preds = _classify_rows(df_feed, model)
                df_feed['Classification'] = [
                    "🚨 Attack" if p == 1 else "✅ Probe" for p in preds
                ]
                display_df = df_feed[[
                    'ts', 'proto', 'orig_bytes', 'resp_bytes',
                    'orig_pkts', 'resp_pkts', 'Classification'
                ]].rename(columns={
                    'ts': 'Time', 'proto': 'Protocol',
                    'orig_bytes': 'Orig Bytes', 'resp_bytes': 'Resp Bytes',
                    'orig_pkts': 'Orig Pkts', 'resp_pkts': 'Resp Pkts',
                })
                st.dataframe(display_df, use_container_width=True)
            elif df_feed.empty:
                st.info("No rows in logs table yet. Start the simulator!")
            else:
                st.dataframe(df_feed, use_container_width=True)
        except Exception as e:
            st.warning(f"Feed query failed: {e}")

        st.markdown("---")

        # ── Section E — Protocol distribution chart ──────────────────
        st.subheader("Protocol Distribution (last 1,000 connections)")
        try:
            with engine.connect() as conn:
                df_proto = pd.read_sql(
                    "SELECT proto, COUNT(*) as count FROM "
                    "(SELECT proto FROM logs ORDER BY id DESC LIMIT 1000) sub "
                    "GROUP BY proto ORDER BY count DESC",
                    conn,
                )
            if not df_proto.empty:
                st.bar_chart(df_proto.set_index('proto'))
            else:
                st.info("No data for chart.")
        except Exception as e:
            st.warning(f"Protocol chart query failed: {e}")

        st.markdown("---")

        # ── Section F — Recent alerts panel ──────────────────────────
        st.subheader("🚨 Recent Alerts")
        try:
            if not df_feed.empty and 'Classification' in df_feed.columns:
                attacks = df_feed[df_feed['Classification'] == "🚨 Attack"]
                if not attacks.empty:
                    for _, row in attacks.iterrows():
                        st.error(
                            f"🚨 ATTACK DETECTED | {row['orig_bytes']} bytes | "
                            f"{row['proto']} | {row['conn_state']} | {row['ts']}"
                        )
                else:
                    st.success("No attacks in last 20 connections")
            else:
                st.info("No data to check for alerts.")
        except Exception as e:
            st.warning(f"Alerts failed: {e}")

    # Auto-refresh logic (must be last)
    if auto_refresh:
        time.sleep(3)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2026 Automated Attack Analysis Framework")
