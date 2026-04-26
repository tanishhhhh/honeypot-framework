import os
import sys
import time
import json
import subprocess
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

# Add src to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_eng import FeatureEngineer
from app import load_model, model
from alerting import EmailAlerter

def block_ip_windows(ip):
    check = subprocess.run(f'netsh advfirewall firewall show rule name="Honeypot_Block_{ip}"', shell=True, capture_output=True)
    if b"No rules match" in check.stdout:
        subprocess.run(f'netsh advfirewall firewall add rule name="Honeypot_Block_{ip}" dir=in action=block remoteip={ip}', shell=True)
        print(f"🛡️  Firewall rule created for {ip}")

def ensure_columns(engine):
    """Ensure the logs table has the new ML columns."""
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE logs ADD COLUMN prediction INT;"))
            conn.execute(text("ALTER TABLE logs ADD COLUMN class_name TEXT;"))
            conn.execute(text("ALTER TABLE logs ADD COLUMN confidence FLOAT;"))
            conn.execute(text("ALTER TABLE logs ADD COLUMN severity TEXT;"))
            conn.execute(text("ALTER TABLE logs ADD COLUMN src_ip TEXT;"))
            print("Added ML columns to DB.")
        except Exception:
            pass # Columns likely exist

def insert_and_predict(engine, session_id, src_ip, duration, orig_bytes, resp_bytes, orig_pkts, resp_pkts, proto, conn_state, history_str, email_alerter=None):
    # Construct DF for FeatureEngineer
    data = {
        'duration': duration,
        'orig_bytes': orig_bytes,
        'resp_bytes': resp_bytes,
        'orig_pkts': orig_pkts,
        'resp_pkts': resp_pkts,
        'proto': proto,
        'conn_state': conn_state,
        'history': history_str
    }
    df = pd.DataFrame([data])
    fe = FeatureEngineer(df)
    X = fe.get_inference_features()

    if hasattr(model, 'feature_names_in_'):
        X = X.reindex(columns=model.feature_names_in_, fill_value=0)

    prediction = int(model.predict(X)[0])
    
    confidence = 0.5
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X)[0]
        confidence = float(np.max(proba))
    
    if confidence > 0.9:
        severity = "HIGH"
    elif confidence > 0.7:
        severity = "MEDIUM"
    else:
        severity = "LOW"
        
    class_name = "Intent-to-act" if prediction == 1 else "Intent-to-probe"

    with engine.begin() as conn:
        query = text("""
            INSERT INTO logs (duration, orig_bytes, resp_bytes, orig_pkts, resp_pkts, proto, conn_state, history, prediction, class_name, confidence, severity, src_ip)
            VALUES (:duration, :orig_bytes, :resp_bytes, :orig_pkts, :resp_pkts, :proto, :conn_state, :history, :prediction, :class_name, :confidence, :severity, :src_ip)
        """)
        conn.execute(query, {
            "duration": duration, "orig_bytes": orig_bytes, "resp_bytes": resp_bytes,
            "orig_pkts": orig_pkts, "resp_pkts": resp_pkts, "proto": proto,
            "conn_state": conn_state, "history": history_str,
            "prediction": prediction, "class_name": class_name,
            "confidence": confidence, "severity": severity, "src_ip": src_ip
        })

    print(f"{'🚨 BLOCKED' if prediction == 1 else '✅ LOGGED'} {src_ip} | Class: {class_name} | Conf: {confidence:.2f}")

    if prediction == 1:
        block_ip_windows(src_ip)

    # ── Email alert for HIGH-severity attacks ──────────
    if severity == "HIGH" and email_alerter is not None:
        try:
            # Infer attack type from features (same heuristic as app.py)
            if prediction == 1:
                if resp_bytes > orig_bytes * 3:
                    attack_type = "Data Exfiltration"
                elif duration > 60:
                    attack_type = "Command & Control"
                elif orig_pkts > 20:
                    attack_type = "Lateral Movement"
                else:
                    attack_type = "Credential Theft"
            else:
                attack_type = "Network Scan"

            event_data = {
                "attack_type": attack_type,
                "class_name": class_name,
                "confidence": confidence,
                "severity": severity,
                "source_ip": src_ip,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "proto": proto,
                "duration": duration,
                "orig_bytes": orig_bytes,
                "resp_bytes": resp_bytes,
                "orig_pkts": orig_pkts,
                "resp_pkts": resp_pkts,
                "mitigation": [
                    "Immediate IP Block via Firewall",
                    "Terminate Active Sessions",
                    "Trigger SIEM Alert (High Severity)",
                    "Snapshot System State for Forensics",
                ],
            }
            email_alerter.send_high_severity_alert(event_data)
        except Exception as e:
            print(f"[EMAIL] Alert dispatch error (non-fatal): {e}")

def tail_file(filename):
    while not os.path.exists(filename):
        print(f"Waiting for {filename} to be created...", end='\r')
        time.sleep(2)
    print(f"                                                ", end='\r')
        
    try:
        with open(filename, 'r') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                yield line
    except Exception as e:
        print(f"Error reading file: {e}")

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    # If using local running windows, we want DB on localhost
    db_url = os.environ.get("DB_URL", "postgresql://admin:admin123@localhost:5432/honeypot")
    if "db:5432" in db_url:
        db_url = db_url.replace("db:5432", "localhost:5432")

    engine = create_engine(db_url)
    ensure_columns(engine)
    
    load_model()
    if model is None:
        print("Failed to load model. Exiting.")
        return

    # ── Initialise email alerter ──────────────────
    email_alerter = EmailAlerter()
    if email_alerter.is_configured():
        print("📧 Email alerting is ACTIVE — alerts will be sent to:", email_alerter.to_email)
    else:
        print("📧 Email alerting is DISABLED — set ALERT_EMAIL_FROM/PASSWORD/TO in .env to enable.")

    log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'honeypots', 'cowrie', 'logs', 'cowrie.json')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    print(f"Starting to watch {log_path}...")
    
    sessions = {}
    
    for line in tail_file(log_path):
        try:
            event = json.loads(line)
            event_id = event.get('eventid')
            session_id = event.get('session')
            src_ip = event.get('src_ip')
            
            if event_id == 'cowrie.session.connect':
                sessions[session_id] = {
                    'src_ip': src_ip,
                    'start_time': time.time(),
                    'inputs': [],
                    'inputs_count': 0
                }
            elif event_id == 'cowrie.command.input':
                if session_id in sessions:
                    sessions[session_id]['inputs'].append(event.get('input', ''))
                    sessions[session_id]['inputs_count'] += 1
            elif event_id == 'cowrie.session.closed':
                if session_id in sessions:
                    s = sessions[session_id]
                    duration = event.get('duration', time.time() - s['start_time'])
                    history_str = " ".join(s['inputs'])[:50]
                    orig_bytes = s['inputs_count'] * 64
                    resp_bytes = s['inputs_count'] * 128
                    orig_pkts = s['inputs_count']
                    resp_pkts = s['inputs_count']
                    proto = 'tcp'
                    conn_state = 'SF' if s['inputs_count'] > 0 else 'S0'
                    
                    insert_and_predict(engine, session_id, s['src_ip'], duration, orig_bytes, resp_bytes, orig_pkts, resp_pkts, proto, conn_state, history_str, email_alerter=email_alerter)
                    
                    del sessions[session_id]
            elif event_id == 'cowrie.login.success':
                if session_id in sessions:
                    sessions[session_id]['login_success'] = True
                
        except json.JSONDecodeError:
            print("JSON parse error")
        except Exception as e:
            print(f"Error processing event: {e}")

if __name__ == "__main__":
    main()
