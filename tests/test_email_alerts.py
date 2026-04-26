"""
Tests for the Email Alerting Module.

Run with:
    pytest tests/test_email_alerts.py -v

Integration tests (require real SMTP credentials) are skipped by default.
Set the SMTP env vars to run them.
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from alerting import EmailAlerter, _rate_limit_cache, _rate_limit_lock, RATE_LIMIT_SECONDS


# ── Fixtures ────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    """Clear the rate-limit cache before each test."""
    with _rate_limit_lock:
        _rate_limit_cache.clear()
    yield
    with _rate_limit_lock:
        _rate_limit_cache.clear()


@pytest.fixture
def alerter_unconfigured():
    """An EmailAlerter with no credentials set."""
    with patch.dict(os.environ, {
        "ALERT_EMAIL_FROM": "",
        "ALERT_EMAIL_TO": "",
        "ALERT_EMAIL_PASSWORD": "",
    }, clear=False):
        return EmailAlerter()


@pytest.fixture
def alerter_configured():
    """An EmailAlerter with mock credentials."""
    with patch.dict(os.environ, {
        "ALERT_EMAIL_FROM": "test@gmail.com",
        "ALERT_EMAIL_TO": "honeytest777@gmail.com",
        "ALERT_EMAIL_PASSWORD": "arjqlnjyjhnicqag",  
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
    }, clear=False):
        return EmailAlerter()


@pytest.fixture
def sample_event():
    """Sample HIGH-severity event data."""
    return {
        "attack_type": "SSH Brute Force",
        "class_name": "Intent-to-act",
        "confidence": 0.95,
        "severity": "HIGH",
        "source_ip": "192.168.1.100",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proto": "tcp",
        "duration": 12.5,
        "orig_bytes": 5000,
        "resp_bytes": 3000,
        "orig_pkts": 20,
        "resp_pkts": 15,
        "mitigation": [
            "Immediate IP Block via Firewall",
            "Terminate Active Sessions",
        ],
    }


# ── Unit Tests ──────────────────────────────────────

class TestEmailAlerterInit:
    def test_loads_defaults(self, alerter_configured):
        assert alerter_configured.smtp_server == "smtp.gmail.com"
        assert alerter_configured.smtp_port == 587
        assert alerter_configured.from_email == "test@gmail.com"
        assert alerter_configured.to_email == "honeytest777@gmail.com"

    def test_is_configured_true(self, alerter_configured):
        assert alerter_configured.is_configured() is True

    def test_is_configured_false(self, alerter_unconfigured):
        assert alerter_unconfigured.is_configured() is False


class TestGetStatus:
    def test_status_keys(self, alerter_configured):
        status = alerter_configured.get_status()
        assert "configured" in status
        assert "smtp_server" in status
        assert "emails_sent_session" in status
        assert "rate_limit_cache_size" in status
        assert status["configured"] is True


class TestRateLimiting:
    def test_first_alert_passes(self, alerter_configured, sample_event):
        """First alert for an IP should be dispatched."""
        with patch.object(alerter_configured, '_send_high_severity_email'):
            result = alerter_configured.send_high_severity_alert(sample_event)
            assert result is True

    def test_duplicate_ip_is_rate_limited(self, alerter_configured, sample_event):
        """Second alert for same IP within 5 min should be suppressed."""
        with patch.object(alerter_configured, '_send_high_severity_email'):
            first = alerter_configured.send_high_severity_alert(sample_event)
            second = alerter_configured.send_high_severity_alert(sample_event)
            assert first is True
            assert second is False

    def test_different_ips_not_limited(self, alerter_configured, sample_event):
        """Alerts for different IPs should both pass."""
        with patch.object(alerter_configured, '_send_high_severity_email'):
            event2 = {**sample_event, "source_ip": "10.0.0.1"}
            first = alerter_configured.send_high_severity_alert(sample_event)
            second = alerter_configured.send_high_severity_alert(event2)
            assert first is True
            assert second is True


class TestHighSeverityAlert:
    def test_unconfigured_returns_false(self, alerter_unconfigured, sample_event):
        result = alerter_unconfigured.send_high_severity_alert(sample_event)
        assert result is False

    def test_configured_dispatches_thread(self, alerter_configured, sample_event):
        with patch.object(alerter_configured, '_send_high_severity_email') as mock_send:
            result = alerter_configured.send_high_severity_alert(sample_event)
            assert result is True
            # Give the background thread a moment to start
            time.sleep(0.1)


class TestTestConnection:
    def test_unconfigured_returns_false(self, alerter_unconfigured):
        assert alerter_unconfigured.test_email_connection() is False

    @patch('smtplib.SMTP')
    def test_configured_sends_test(self, mock_smtp_class, alerter_configured):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = alerter_configured.test_email_connection()
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()


class TestDailySummary:
    def test_unconfigured_returns_false(self, alerter_unconfigured):
        assert alerter_unconfigured.send_daily_summary() is False


# ── Integration tests (skipped without real credentials) ────

@pytest.mark.skipif(
    not os.getenv("ALERT_EMAIL_FROM") or not os.getenv("ALERT_EMAIL_PASSWORD"),
    reason="SMTP credentials not set — skipping live email test"
)
class TestLiveEmail:
    def test_live_test_email(self):
        """Actually send a test email (requires real credentials in env)."""
        alerter = EmailAlerter()
        assert alerter.test_email_connection() is True

    def test_live_high_severity(self):
        alerter = EmailAlerter()
        event = {
            "attack_type": "Test Attack",
            "class_name": "Intent-to-act",
            "confidence": 0.99,
            "severity": "HIGH",
            "source_ip": "192.168.1.200",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proto": "tcp",
            "duration": 5.0,
            "orig_bytes": 1024,
            "resp_bytes": 2048,
            "orig_pkts": 10,
            "resp_pkts": 8,
        }
        result = alerter.send_high_severity_alert(event)
        assert result is True
