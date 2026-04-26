# 📧 Email Alert Setup Guide

This guide explains how to configure automated email alerts for the ML Honeypot Framework.

---

## Quick Start

### 1. Gmail App Password (Recommended)

Gmail requires an **App Password** instead of your regular password when using SMTP.

**Prerequisites:** You must have **2-Factor Authentication** enabled on your Google account.

**Steps:**

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", ensure **2-Step Verification** is ON
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** as the app and **Windows Computer** as the device
5. Click **Generate**
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 2. Configure Environment Variables

Edit the `.env` file in the project root:

```env
ALERT_EMAIL_FROM=your-real-email@gmail.com
ALERT_EMAIL_TO=honeytest777@gmail.com
ALERT_EMAIL_PASSWORD=abcdefghijklmnop
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

> **Note:** Remove spaces from the App Password when pasting.

### 3. Test the Connection

Start the Flask API and send a test:

```bash
python src/app.py

# In another terminal:
curl -X POST http://localhost:5000/test-email
```

Or use the React dashboard: navigate to **Alerts** → click **Send Test Email**.

---

## Alternative SMTP Providers

### Outlook / Hotmail

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
ALERT_EMAIL_FROM=your-email@outlook.com
ALERT_EMAIL_PASSWORD=your-password
```

### SendGrid (API-based)

```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
ALERT_EMAIL_FROM=your-verified-sender@domain.com
ALERT_EMAIL_PASSWORD=SG.your-api-key-here
```

> For SendGrid, use the API key as the password and `apikey` as the username. The current module uses standard SMTP, which works with SendGrid's SMTP relay.

### AWS SES

```env
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
ALERT_EMAIL_FROM=your-verified-email@domain.com
ALERT_EMAIL_PASSWORD=your-ses-smtp-password
```

> You'll also need to set `ALERT_EMAIL_FROM` to a verified SES sender.

---

## Daily Summary Setup

The daily summary emails aggregate statistics from PostgreSQL and send a report.

### Option A: Run Continuously (Development)

```bash
python src/scheduled_tasks.py --time 08:00
```

This keeps running and sends the summary every day at 08:00.

### Option B: Windows Task Scheduler (Production)

1. Open **Task Scheduler** → Create Basic Task
2. Name: `Honeypot Daily Summary`
3. Trigger: **Daily** at 08:00
4. Action: **Start a program**
   - Program: `C:\path\to\python.exe`
   - Arguments: `src/scheduled_tasks.py --once`
   - Start in: `C:\path\to\Ml-Honeypot-Framework`
5. Click Finish

### Option C: Linux Cron

```bash
crontab -e
# Add this line:
0 8 * * * cd /path/to/Ml-Honeypot-Framework && /path/to/python src/scheduled_tasks.py --once
```

### Option D: Manual Trigger

```bash
python src/scheduled_tasks.py --once
```

---

## What Triggers an Email?

| Event | Condition | Email Type |
|-------|-----------|------------|
| Attack detected | `severity == 'HIGH'` AND `confidence > 0.9` | 🚨 Immediate alert |
| Daily schedule | Runs at configured time | 📊 Summary report |
| Manual test | `POST /test-email` API call | ✅ Test confirmation |

### Rate Limiting

To prevent email flooding during active attacks:
- **Max 1 alert per IP per 5 minutes**
- Subsequent alerts from the same IP are logged but not emailed
- The rate limit is per-process (resets on restart)

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `SMTPAuthenticationError` | Wrong password | Regenerate Gmail App Password (not regular password) |
| `Connection refused` | SMTP port blocked | Allow outbound port 587 in firewall |
| `Username and Password not accepted` | 2FA not enabled | Enable 2FA first, then create App Password |
| `SMTP timeout` | Network issue | Check internet connection, try `telnet smtp.gmail.com 587` |
| `Email not configured — skipping` | Missing env vars | Ensure `ALERT_EMAIL_FROM`, `ALERT_EMAIL_PASSWORD`, `ALERT_EMAIL_TO` are set in `.env` |
| Rate-limited suppression | Same IP attacked again | Expected behavior — wait 5 min or restart watcher |

### Debug Mode

Set `FLASK_DEBUG=true` in `.env` to see detailed SMTP logs in the console.

### Verify Environment Variables Are Loaded

```python
python -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; print(os.getenv('ALERT_EMAIL_FROM'))"
```

---

## Security Notes

- **Never commit `.env`** to version control — it's in `.gitignore`
- Use **App Passwords**, not your actual Gmail password
- For production, consider a dedicated service account email
- Alert emails are sent via **TLS-encrypted** SMTP connections
