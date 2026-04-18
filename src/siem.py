"""
SIEM Integration Module for ML Honeypot Framework.

Supports:
  - Splunk HTTP Event Collector (HEC) — primary
  - Elasticsearch — fallback

Configured via environment variables; graceful no-op if not configured.
"""

import os
import json
import threading
import time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None


# ── Configuration ────────────────────────────────────────────

def _splunk_config():
    return {
        "hec_url": os.getenv("SPLUNK_HEC_URL"),
        "hec_token": os.getenv("SPLUNK_HEC_TOKEN"),
    }


def _elastic_config():
    return {
        "url": os.getenv("ELASTIC_URL", "http://localhost:9200"),
        "index": os.getenv("ELASTIC_INDEX", "honeypot-alerts"),
    }


def splunk_configured():
    cfg = _splunk_config()
    return bool(cfg["hec_url"] and cfg["hec_token"])


def elastic_configured():
    return bool(os.getenv("ELASTIC_URL"))


# ── Splunk HEC ───────────────────────────────────────────────

def _send_to_splunk(event_data: dict):
    """Send event to Splunk via HTTP Event Collector."""
    if requests is None:
        print("[SIEM] 'requests' library not available — cannot send to Splunk.")
        return

    cfg = _splunk_config()

    payload = {
        "time": int(time.time()),
        "source": "ml-honeypot",
        "sourcetype": "security:event",
        "event": {
            "severity": event_data.get("severity", "UNKNOWN"),
            "attack_type": event_data.get("attack_type", "Unknown"),
            "confidence": event_data.get("confidence", 0),
            "class_name": event_data.get("class_name", ""),
            "mitigation": event_data.get("mitigation", []),
            "timestamp": event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "prediction": event_data.get("prediction", -1),
        },
    }

    try:
        resp = requests.post(
            cfg["hec_url"],
            headers={
                "Authorization": f"Splunk {cfg['hec_token']}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=5,
        )
        if resp.status_code in (200, 201):
            print(f"[SIEM] Splunk event sent — {event_data.get('attack_type')}")
        else:
            print(f"[SIEM] Splunk returned {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[SIEM] Splunk send failed: {e}")


# ── Elasticsearch ────────────────────────────────────────────

def _send_to_elastic(event_data: dict):
    """Send event to Elasticsearch."""
    if requests is None:
        print("[SIEM] 'requests' library not available — cannot send to Elasticsearch.")
        return

    cfg = _elastic_config()
    url = f"{cfg['url']}/{cfg['index']}/_doc"

    doc = {
        "severity": event_data.get("severity", "UNKNOWN"),
        "attack_type": event_data.get("attack_type", "Unknown"),
        "confidence": event_data.get("confidence", 0),
        "class_name": event_data.get("class_name", ""),
        "mitigation": event_data.get("mitigation", []),
        "prediction": event_data.get("prediction", -1),
        "timestamp": event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }

    try:
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(doc),
            timeout=5,
        )
        if resp.status_code in (200, 201):
            print(f"[SIEM] Elasticsearch event indexed — {event_data.get('attack_type')}")
        else:
            print(f"[SIEM] Elasticsearch returned {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[SIEM] Elasticsearch send failed: {e}")


# ── Public API ───────────────────────────────────────────────

def send_to_siem(event_data: dict):
    """
    Non-blocking SIEM dispatch.

    Tries Splunk first (if configured), then Elasticsearch (if configured).
    Runs in a daemon thread so it does not block the API response.

    Args:
        event_data: dict with keys like attack_type, confidence, severity,
                    class_name, mitigation, timestamp, prediction.
    """
    def _dispatch():
        sent = False
        if splunk_configured():
            _send_to_splunk(event_data)
            sent = True
        if elastic_configured():
            _send_to_elastic(event_data)
            sent = True
        if not sent:
            print("[SIEM] No SIEM backend configured — skipping event.")

    thread = threading.Thread(target=_dispatch, daemon=True)
    thread.start()
