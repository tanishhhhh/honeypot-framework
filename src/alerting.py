"""
Email Alerting Module for ML Honeypot Framework.

Production-grade email alerting with:
  - Immediate HIGH-severity attack alerts
  - Daily summary reports (PostgreSQL stats)
  - Per-IP rate limiting (1 alert per IP per 5 minutes)
  - Background thread dispatch (non-blocking)
  - Graceful no-op when SMTP is not configured

Configured via environment variables; see EMAIL_SETUP.md.
"""

import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger("alerting")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# ─── Rate-limit tracking (module-level so it survives across calls) ───
_rate_limit_lock = threading.Lock()
_rate_limit_cache: dict[str, datetime] = {}   # ip -> last_alert_time
RATE_LIMIT_SECONDS = 300  # 5 minutes


class EmailAlerter:
    """
    Handles all email alert operations for the honeypot framework.

    Usage::

        alerter = EmailAlerter()
        if alerter.is_configured():
            alerter.send_high_severity_alert(event_data)
    """

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.from_email = os.getenv("ALERT_EMAIL_FROM", "")
        self.password = os.getenv("ALERT_EMAIL_PASSWORD", "")
        self.to_email = os.getenv("ALERT_EMAIL_TO", "")

        # Track emails sent in current process lifetime
        self._emails_sent = 0
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────
    # Configuration helpers
    # ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Return True when all required SMTP credentials are present."""
        return all([self.from_email, self.password, self.to_email])

    def get_status(self) -> dict:
        """Return a JSON-safe status snapshot."""
        return {
            "configured": self.is_configured(),
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "from_email": self.from_email or "(not set)",
            "to_email": self.to_email or "(not set)",
            "emails_sent_session": self._emails_sent,
            "rate_limit_cache_size": len(_rate_limit_cache),
        }

    # ──────────────────────────────────────────────
    # Test connection
    # ──────────────────────────────────────────────

    def test_email_connection(self) -> bool:
        """
        Send a lightweight test email to verify SMTP credentials.
        Returns True on success, False on failure.
        """
        if not self.is_configured():
            logger.warning("Email not configured — cannot send test.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "✅ ML Honeypot Framework — Email Test"
            msg["From"] = self.from_email
            msg["To"] = self.to_email

            html = """
            <html>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px;">
                <div style="max-width: 560px; margin: 0 auto; background: #16213e;
                            border-radius: 8px; padding: 24px; border-left: 4px solid #22c55e;">
                    <h2 style="color: #22c55e; margin-top: 0;">✅ Email Alert Test Successful</h2>
                    <p style="color: #f8fafc;">
                        Your SMTP configuration is working correctly.<br>
                        The ML Honeypot Framework will now send alerts to this address
                        when HIGH-severity attacks are detected.
                    </p>
                    <hr style="border: 1px solid #334155; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">SMTP Server</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{server}:{port}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Sender</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{sender}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Recipient</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{recipient}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Timestamp</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{ts}</td>
                        </tr>
                    </table>
                    <hr style="border: 1px solid #334155; margin: 20px 0;">
                    <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
                        ML Honeypot Framework — Automated Security Alerting
                    </p>
                </div>
            </body>
            </html>
            """.format(
                server=self.smtp_server,
                port=self.smtp_port,
                sender=self.from_email,
                recipient=self.to_email,
                ts=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            )
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            logger.info("Test email sent successfully to %s", self.to_email)
            with self._lock:
                self._emails_sent += 1
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed — check your App Password: %s", e)
            return False
        except smtplib.SMTPConnectError as e:
            logger.error("Could not connect to SMTP server %s:%s — %s",
                         self.smtp_server, self.smtp_port, e)
            return False
        except Exception as e:
            logger.error("Test email failed: %s", e)
            return False

    # ──────────────────────────────────────────────
    # HIGH-severity alert
    # ──────────────────────────────────────────────

    def send_high_severity_alert(self, event_data: dict) -> bool:
        """
        Send an immediate email alert for a HIGH-severity event.

        Rate-limited: max 1 email per source IP per 5 minutes.

        Args:
            event_data: dict with keys: attack_type, class_name, confidence,
                        severity, source_ip (or src_ip), timestamp (or ts),
                        proto, duration, orig_bytes, resp_bytes, orig_pkts,
                        resp_pkts, mitigation (list).

        Returns:
            True if email was dispatched, False if skipped or failed.
        """
        if not self.is_configured():
            logger.debug("Email not configured — skipping HIGH alert.")
            return False

        # Normalise source_ip key
        src_ip = event_data.get("source_ip") or event_data.get("src_ip", "unknown")

        # ── Rate-limit check ─────────────────────────
        now = datetime.now(timezone.utc)
        with _rate_limit_lock:
            last_sent = _rate_limit_cache.get(src_ip)
            if last_sent and (now - last_sent).total_seconds() < RATE_LIMIT_SECONDS:
                logger.info("Rate-limited: suppressing alert for %s (sent %ds ago)",
                            src_ip, int((now - last_sent).total_seconds()))
                return False
            _rate_limit_cache[src_ip] = now

        # ── Dispatch in background thread ────────────
        thread = threading.Thread(
            target=self._send_high_severity_email,
            args=(event_data, src_ip),
            daemon=True,
        )
        thread.start()
        return True

    def _send_high_severity_email(self, event_data: dict, src_ip: str):
        """Internal: build and send the HIGH-severity email (runs in thread)."""
        try:
            attack_type = event_data.get("attack_type", "Unknown Attack")
            ts = event_data.get("timestamp") or event_data.get("ts", "N/A")
            confidence = event_data.get("confidence", 0)
            severity = event_data.get("severity", "HIGH")
            class_name = event_data.get("class_name", "Intent-to-act")
            proto = event_data.get("proto", "tcp")
            duration = event_data.get("duration", "N/A")
            orig_bytes = event_data.get("orig_bytes", 0)
            resp_bytes = event_data.get("resp_bytes", 0)
            orig_pkts = event_data.get("orig_pkts", 0)
            resp_pkts = event_data.get("resp_pkts", 0)

            # Build mitigation list
            mitigations = event_data.get("mitigation", [
                "Immediate IP Block via Firewall",
                "Terminate Active Sessions",
                "Trigger SIEM Alert (High Severity)",
                "Snapshot System State for Forensics",
            ])
            mitigation_html = "".join(
                f'<li style="margin: 4px 0; color: #f8fafc;">{m}</li>' for m in mitigations
            )

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px;">
                <div style="max-width: 620px; margin: 0 auto; background: #16213e;
                            border-radius: 8px; padding: 24px; border-left: 4px solid #e74c3c;">

                    <h2 style="color: #e74c3c; margin-top: 0;">
                        🚨 HIGH SEVERITY: {attack_type} from {src_ip}
                    </h2>

                    <!-- Attack Details -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Attack Details</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8; width: 140px;">Attack Type</td>
                            <td style="padding: 6px 8px; font-weight: bold; color: #f8fafc;">{attack_type}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Classification</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{class_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Confidence</td>
                            <td style="padding: 6px 8px; color: #e74c3c; font-weight: bold;">{confidence:.1%}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Severity</td>
                            <td style="padding: 6px 8px; color: #e74c3c; font-weight: bold;">{severity}</td>
                        </tr>
                    </table>

                    <!-- Source Information -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Source Information</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8; width: 140px;">Source IP</td>
                            <td style="padding: 6px 8px; font-weight: bold; color: #f8fafc;">{src_ip}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Timestamp</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{ts}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Protocol</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{proto}</td>
                        </tr>
                    </table>

                    <!-- Connection Metrics -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Connection Metrics</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Duration</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{duration}s</td>
                            <td style="padding: 6px 8px; color: #94a3b8;">Orig Bytes</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{orig_bytes}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Resp Bytes</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{resp_bytes}</td>
                            <td style="padding: 6px 8px; color: #94a3b8;">Orig Pkts</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{orig_pkts}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Resp Pkts</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{resp_pkts}</td>
                            <td style="padding: 6px 8px; color: #94a3b8;"></td>
                            <td style="padding: 6px 8px; color: #f8fafc;"></td>
                        </tr>
                    </table>

                    <!-- Automated Actions -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">🛡️ Automated Actions Taken</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #22c55e;">✅ IP blocked via Windows Firewall</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #22c55e;">✅ Event logged to PostgreSQL</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #22c55e;">✅ Email alert dispatched</td>
                        </tr>
                    </table>

                    <!-- Recommended Actions -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">📋 Recommended SOC Actions</h3>
                    <ul style="padding-left: 20px;">{mitigation_html}</ul>

                    <hr style="border: 1px solid #334155; margin: 20px 0;">
                    <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
                        ML Honeypot Framework — Automated Security Alert<br>
                        Dashboard: <a href="http://localhost:5173" style="color: #64b5f6;">http://localhost:5173</a>
                    </p>
                </div>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 HIGH SEVERITY: {attack_type} from {src_ip}"
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            with self._lock:
                self._emails_sent += 1
            logger.info("HIGH-severity alert sent for %s → %s", src_ip, self.to_email)

        except Exception as e:
            logger.error("Failed to send HIGH-severity alert: %s", e)

    # ──────────────────────────────────────────────
    # Daily summary
    # ──────────────────────────────────────────────

    def send_daily_summary(self, db_url: str = None) -> bool:
        """
        Query PostgreSQL for today's event statistics and email a summary.

        Args:
            db_url: SQLAlchemy connection string. Falls back to DB_URL env var.

        Returns:
            True on success, False on failure.
        """
        if not self.is_configured():
            logger.warning("Email not configured — skipping daily summary.")
            return False

        try:
            from sqlalchemy import create_engine, text

            if db_url is None:
                db_url = os.getenv("DB_URL", "postgresql://admin:admin123@localhost:5432/honeypot")
                # Ensure localhost for local runs
                if "db:5432" in db_url:
                    db_url = db_url.replace("db:5432", "localhost:5432")

            engine = create_engine(db_url)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            with engine.connect() as conn:
                # Total events
                total = conn.execute(text("SELECT COUNT(*) FROM logs")).scalar() or 0

                # Severity breakdown
                sev_rows = conn.execute(text(
                    "SELECT severity, COUNT(*) as cnt FROM logs "
                    "WHERE severity IS NOT NULL GROUP BY severity"
                )).fetchall()
                severity_map = {row[0]: row[1] for row in sev_rows} if sev_rows else {}

                # Unique source IPs
                unique_ips = conn.execute(text(
                    "SELECT COUNT(DISTINCT src_ip) FROM logs WHERE src_ip IS NOT NULL"
                )).scalar() or 0

                # Top 5 source IPs by event count
                top_ips = conn.execute(text(
                    "SELECT src_ip, COUNT(*) as cnt FROM logs "
                    "WHERE src_ip IS NOT NULL GROUP BY src_ip "
                    "ORDER BY cnt DESC LIMIT 5"
                )).fetchall()

                # Attack vs probe breakdown
                attacks = conn.execute(text(
                    "SELECT COUNT(*) FROM logs WHERE prediction = 1"
                )).scalar() or 0
                probes = conn.execute(text(
                    "SELECT COUNT(*) FROM logs WHERE prediction = 0"
                )).scalar() or 0

            # Build top IPs HTML rows
            top_ip_rows = ""
            for i, row in enumerate(top_ips or []):
                bg = 'background: #1a1a2e;' if i % 2 == 1 else ''
                top_ip_rows += f'''
                <tr style="{bg}">
                    <td style="padding: 6px 8px; color: #f8fafc;">{row[0]}</td>
                    <td style="padding: 6px 8px; color: #f8fafc; text-align: center;">{row[1]}</td>
                </tr>'''

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px;">
                <div style="max-width: 620px; margin: 0 auto; background: #16213e;
                            border-radius: 8px; padding: 24px; border-left: 4px solid #3b82f6;">

                    <h2 style="color: #3b82f6; margin-top: 0;">
                        📊 Daily Security Summary — {today}
                    </h2>

                    <!-- Overview -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Overview</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Total Events</td>
                            <td style="padding: 6px 8px; font-weight: bold; color: #f8fafc;">{total}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Attacks (Intent-to-act)</td>
                            <td style="padding: 6px 8px; color: #e74c3c; font-weight: bold;">{attacks}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #94a3b8;">Probes (Intent-to-probe)</td>
                            <td style="padding: 6px 8px; color: #f59e0b; font-weight: bold;">{probes}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #94a3b8;">Unique Source IPs</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{unique_ips}</td>
                        </tr>
                    </table>

                    <!-- Severity Breakdown -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Severity Breakdown</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #e74c3c; font-weight: bold;">🔴 HIGH</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{severity_map.get('HIGH', 0)}</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #f59e0b; font-weight: bold;">🟡 MEDIUM</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{severity_map.get('MEDIUM', 0)}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #22c55e; font-weight: bold;">🟢 LOW</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">{severity_map.get('LOW', 0)}</td>
                        </tr>
                    </table>

                    <!-- Top Source IPs -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">Top 5 Source IPs</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr style="background: #0f172a;">
                            <th style="padding: 6px 8px; color: #94a3b8; text-align: left;">IP Address</th>
                            <th style="padding: 6px 8px; color: #94a3b8; text-align: center;">Events</th>
                        </tr>
                        {top_ip_rows if top_ip_rows else '<tr><td style="padding: 6px 8px; color: #64748b;" colspan="2">No data</td></tr>'}
                    </table>

                    <!-- System Health -->
                    <h3 style="color: #64b5f6; margin-bottom: 8px;">System Health</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                        <tr>
                            <td style="padding: 6px 8px; color: #22c55e;">✅ ML Classifier</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">Operational</td>
                        </tr>
                        <tr style="background: #1a1a2e;">
                            <td style="padding: 6px 8px; color: #22c55e;">✅ PostgreSQL</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">Connected</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; color: #22c55e;">✅ Email Alerts</td>
                            <td style="padding: 6px 8px; color: #f8fafc;">Active</td>
                        </tr>
                    </table>

                    <hr style="border: 1px solid #334155; margin: 20px 0;">
                    <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
                        ML Honeypot Framework — Daily Summary Report<br>
                        Dashboard: <a href="http://localhost:5173" style="color: #64b5f6;">http://localhost:5173</a>
                    </p>
                </div>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📊 Daily Security Summary — {today}"
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            with self._lock:
                self._emails_sent += 1
            logger.info("Daily summary sent to %s", self.to_email)
            return True

        except Exception as e:
            logger.error("Failed to send daily summary: %s", e)
            return False


# ──────────────────────────────────────────────────
# Backward-compatible wrapper (used by app.py)
# ──────────────────────────────────────────────────

_default_alerter = None


def _get_default_alerter() -> EmailAlerter:
    global _default_alerter
    if _default_alerter is None:
        _default_alerter = EmailAlerter()
    return _default_alerter


def is_configured() -> bool:
    """Legacy helper — check if email alerting is configured."""
    return _get_default_alerter().is_configured()


def send_email_alert(alert_data: dict):
    """
    Legacy wrapper — send an email alert in a background thread (non-blocking).

    This preserves backward compatibility with the existing app.py call::

        from alerting import send_email_alert
        send_email_alert(alert_data)
    """
    alerter = _get_default_alerter()
    if not alerter.is_configured():
        logger.info("Email not configured — skipping alert.")
        return

    alerter.send_high_severity_alert(alert_data)
