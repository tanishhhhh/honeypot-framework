"""
Email Alerting Module for ML Honeypot Framework.

Sends SMTP email alerts when high-confidence attacks are detected.
Configured via environment variables; graceful no-op if not configured.
"""

import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def _get_config():
    """Load email configuration from environment variables."""
    return {
        "from_email": os.getenv("ALERT_EMAIL_FROM"),
        "to_email": os.getenv("ALERT_EMAIL_TO"),
        "password": os.getenv("ALERT_EMAIL_PASSWORD"),
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    }


def is_configured():
    """Check if email alerting is properly configured."""
    config = _get_config()
    return all([config["from_email"], config["to_email"], config["password"]])


def _build_email_body(alert_data: dict) -> str:
    """Build HTML email body from alert data."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 8px; padding: 24px; border-left: 4px solid #e74c3c;">
            <h2 style="color: #e74c3c; margin-top: 0;">🚨 Security Alert — ML Honeypot Framework</h2>

            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px; color: #94a3b8; width: 140px;">Attack Type</td>
                    <td style="padding: 8px; font-weight: bold; color: #f8fafc;">{alert_data.get('attack_type', 'Unknown')}</td>
                </tr>
                <tr style="background: #1a1a2e;">
                    <td style="padding: 8px; color: #94a3b8;">Severity</td>
                    <td style="padding: 8px; font-weight: bold; color: #e74c3c;">{alert_data.get('severity', 'HIGH')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #94a3b8;">Confidence</td>
                    <td style="padding: 8px; color: #f8fafc;">{alert_data.get('confidence', 0):.1%}</td>
                </tr>
                <tr style="background: #1a1a2e;">
                    <td style="padding: 8px; color: #94a3b8;">Timestamp</td>
                    <td style="padding: 8px; color: #f8fafc;">{alert_data.get('timestamp', 'N/A')}</td>
                </tr>
            </table>

            <h3 style="color: #64b5f6;">Key Features</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 8px 0;">
                <tr>
                    <td style="padding: 4px 8px; color: #94a3b8;">Duration</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('duration', 'N/A')}</td>
                    <td style="padding: 4px 8px; color: #94a3b8;">Orig Bytes</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('orig_bytes', 'N/A')}</td>
                </tr>
                <tr style="background: #1a1a2e;">
                    <td style="padding: 4px 8px; color: #94a3b8;">Resp Bytes</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('resp_bytes', 'N/A')}</td>
                    <td style="padding: 4px 8px; color: #94a3b8;">Orig Pkts</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('orig_pkts', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #94a3b8;">Resp Pkts</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('resp_pkts', 'N/A')}</td>
                    <td style="padding: 4px 8px; color: #94a3b8;">History Len</td>
                    <td style="padding: 4px 8px; color: #f8fafc;">{alert_data.get('features', {}).get('history_len', 'N/A')}</td>
                </tr>
            </table>

            <h3 style="color: #64b5f6;">Recommended Mitigation</h3>
            <ul style="color: #f8fafc; padding-left: 20px;">
                {"".join(f'<li style="margin: 4px 0;">{m}</li>' for m in alert_data.get('mitigation', ['Analyze manually']))}
            </ul>

            <hr style="border: 1px solid #334155; margin: 20px 0;">
            <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
                ML Honeypot Framework — Automated Security Alert
            </p>
        </div>
    </body>
    </html>
    """


def _send_email(alert_data: dict):
    """Internal: send email (runs in background thread)."""
    config = _get_config()

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[SECURITY ALERT] {alert_data.get('attack_type', 'Attack Detected')}"
        msg["From"] = config["from_email"]
        msg["To"] = config["to_email"]

        html_body = _build_email_body(alert_data)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["from_email"], config["password"])
            server.send_message(msg)

        print(f"[ALERTING] Email alert sent for {alert_data.get('attack_type')}")

    except Exception as e:
        print(f"[ALERTING] Failed to send email: {e}")


def send_email_alert(alert_data: dict):
    """
    Send an email alert in a background thread (non-blocking).

    Args:
        alert_data: dict with keys: attack_type, confidence, severity,
                    timestamp, features (dict), mitigation (list)
    """
    if not is_configured():
        print("[ALERTING] Email not configured — skipping alert.")
        return

    thread = threading.Thread(target=_send_email, args=(alert_data,), daemon=True)
    thread.start()
