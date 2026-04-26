# 🛡️ ML Honeypot Framework

An automated attack analysis and prevention framework that uses machine learning to classify honeypot network traffic as **Intent-to-act** (attack) or **Intent-to-probe** (reconnaissance) in real time.

## Tech Stack

| Layer             | Technology                                          |
| ----------------- | --------------------------------------------------- |
| Language          | Python 3.9+                                         |
| Data Processing   | Pandas, NumPy, DuckDB                               |
| Machine Learning  | Scikit-learn, XGBoost                                |
| Backend API       | Flask (REST), Flask-CORS                             |

| React Frontend    | React 19, Vite 8, Tailwind CSS 4, Recharts          |
| Live Database     | PostgreSQL 15, SQLAlchemy, psycopg2                  |
| Alerting & SIEM   | SMTP Email, Splunk HEC, Elasticsearch                |
| DevOps            | Docker, Docker Compose, GitHub Actions               |

---

## Project Structure

```
Ml-Honeypot-Framework/
├── src/
│   ├── app.py              # Flask REST API (prediction endpoint)
│   ├── alerting.py          # Email alerting module (SMTP)

│   ├── data_loader.py       # DuckDB data ingestion
│   ├── feature_eng.py       # Feature engineering pipeline
│   ├── log_watcher.py       # Real-time log & PostgreSQL monitor
│   ├── prevention.py        # Mitigation rule engine
│   ├── siem.py              # SIEM integration (Splunk / Elasticsearch)

│   └── train_model.py       # ML training script (GridSearchCV)
├── frontend/                # React SOC Dashboard (Vite + Tailwind)
│   ├── src/
│   │   ├── App.jsx          # Router & layout
│   │   ├── pages/           # Dashboard, Monitoring, ManualInput, Alerts, Health
│   │   ├── services/api.js  # Axios API client
│   │   └── context/         # PredictionContext (shared state)
│   ├── package.json
│   └── vite.config.js
├── tests/                   # Unit tests (Pytest)
├── Dockerfile.api           # Backend container

├── Dockerfile.frontend      # React production container (nginx)
├── docker-compose.yml       # Full stack orchestration
├── setup_postgres.sql       # PostgreSQL schema for live demo
├── simulate_attacks.py      # Attack traffic generator (PostgreSQL)
├── run_live_demo.py         # Live PostgreSQL classification monitor
├── run.bat                  # Windows quick-start (API + React)
├── best_model.pkl           # Trained model artifact
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

---

## Prerequisites

- **Python 3.9+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) (only for the React frontend)
- **Docker & Docker Compose** — [docker.com](https://www.docker.com/) (only for containerized/live-demo mode)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## 🚀 Quick Start (Automated Orchestration)

The easiest way to launch the full honeypot stack, including Docker containers, the database, the ML pipeline, and the React dashboard, is using the automated orchestrator.

> **Architecture Note:** The React dashboard now runs via Vite dev server (port 5173) for improved hot-reload, theme preservation, and direct email alert integration. Docker Compose now orchestrates only backend, database, and honeypot services.

**Note:** You must run the orchestrator as **Administrator** on Windows to allow the automated firewall mitigation module to function.

1. **Right-click** `run.bat` in your project folder and select **"Run as Administrator"**.
2. **The script will automatically:**
   - Validate your Python, Docker, and Node.js environment.
   - Check for email `.env` configuration.
   - Boot PostgreSQL and the Flask API via Docker Compose.
   - Create required database tables dynamically if they don't exist.
   - Launch the real-time Python `cowrie_watcher` in a new window.
   - Start the Vite dev server and open the SOC Dashboard at `http://localhost:5173`.
   - Prompt you to optionally start a live SSH/Telnet attack simulation against the container.

### Shutting Down
To gracefully stop all services and automatically wipe the temporary Windows Firewall blocking rules created by the honeypot:
1. **Right-click** `stop.bat` and select **"Run as Administrator"**.
2. Close any remaining "Live SOC Watcher" or "Attack Simulation" terminal windows manually.

### 🛠️ Troubleshooting `run.bat`

| Symptom | Cause | Fix |
|---------|-------|-----|
| Script crashes immediately | Pasted into PowerShell | **Double-click** `run.bat` or run `cmd /c run.bat` from PowerShell |
| `) was unexpected at this time` | Inline SQL parentheses | Fixed — DB init now uses external `scripts/init_db.sql` |
| Docker fails to start | Docker Desktop not running | Start Docker Desktop first |
| Vite fails to launch | Missing `node_modules` | Script runs `npm install` automatically on first launch |
| Watcher crashes | Missing model or `.env` | Ensure `best_model.pkl` exists (run `python src/train_model.py`) |

**Manual startup** (if `run.bat` fails):
```bash
docker compose up -d                  # 1. Start backend, Cowrie, DB
# Wait 30 seconds for healthchecks
docker compose cp scripts/init_db.sql db:/tmp/init_db.sql
docker compose exec -T db psql -U admin -d honeypot -f /tmp/init_db.sql
python src\watchers\cowrie_watcher.py  # 3. Start watcher (Admin terminal)
cd frontend && npm run dev            # 4. Start Vite frontend
# Open http://localhost:5173
```
---

### 📧 Email Alerting Troubleshooting

**Dashboard shows "Not Configured":**

1. Verify `.env` file exists in project root with **real** credentials:
   ```env
   ALERT_EMAIL_FROM=your-real-email@gmail.com
   ALERT_EMAIL_TO=recipient@gmail.com
   ALERT_EMAIL_PASSWORD=your-16-char-app-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```
2. Ensure `docker-compose.yml` has `env_file: - .env` under the `backend` service
3. Restart backend: `docker compose up -d --force-recreate backend`
4. Verify: `curl http://localhost:5000/email-status` should return `"configured": true`
5. Test: `curl -X POST http://localhost:5000/test-email`

> See [EMAIL_SETUP.md](EMAIL_SETUP.md) for generating a Gmail App Password.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/tanishhhhh/honeypot-framework.git
cd honeypot-framework
```

### 2. Create & Activate a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set the Dataset Path

The training script reads data from a DuckDB database file. Set the `DB_PATH` environment variable to point to your dataset:

```bash
# Windows (PowerShell)
$env:DB_PATH = "C:\path\to\your\dataset.db"

# macOS / Linux
export DB_PATH="/path/to/your/dataset.db"
```

> **Note:** If `DB_PATH` is not set, the script falls back to the hardcoded default path in `src/data_loader.py`.

### 5. Train the Model

```bash
python src/train_model.py
```

This will:
- Load the dataset from DuckDB
- Run feature engineering (leakage-free)
- Train Logistic Regression, Random Forest, and XGBoost
- Run GridSearchCV on XGBoost (10% stratified sample)
- Save `best_model.pkl` and `training_results.json` to the project root

### 6. Launch the System

#### Option A — Windows Quick Start

Double-click `run.bat` or run in terminal:

```bash
.\run.bat
```

This starts the Docker services (backend, database, Cowrie) and launches the Vite frontend in a separate window.

#### Option B — Manual Start (React Frontend)

```bash
# Terminal 1 — Flask API (must be running)
python src/app.py

# Terminal 2 — React dev server
cd frontend
npm install
npm run dev
```

| Service              | URL                         |
| -------------------- | --------------------------- |
| Flask API            | http://localhost:5000        |
| React SOC Dashboard  | http://localhost:5173        |

---

## Docker Setup (Full Stack)

### 1. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your SMTP, SIEM, and DB credentials (all optional)
```

### 2. Build & Start All Services

```bash
docker compose up --build -d
```

This starts **three containers** (frontend runs natively via Vite):
- `backend` — Flask API on port `5000`
- `cowrie-live` — Cowrie honeypot on ports `2222` (SSH) / `2223` (Telnet)
- `db` — PostgreSQL 15 on port `5432`

To start the frontend separately:
```bash
cd frontend && npm install && npm run dev
# Dashboard available at http://localhost:5173
```

### 3. Create the Logs Table (first time only)

```bash
docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql
```

### 4. Stop All Services

```bash`
docker compose down
```

---

## Live Attack Simulation (PostgreSQL)

> Requires a running PostgreSQL instance (via Docker or standalone).

### 1. Start PostgreSQL

```bash
docker run --name honeypot-live \
  -e POSTGRES_DB=honeypot \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin123 \
  -p 5432:5432 -d postgres:15
```

### 2. Create the Schema

```bash
docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql
```

### 3. Run the Attack Simulator

```bash
python simulate_attacks.py
```

### 4. Start the Live Monitor (separate terminal)

```bash
python run_live_demo.py
```

The monitor polls the database every 5 seconds and classifies each new connection using the trained model.

> See [LIVE_DEMO.md](LIVE_DEMO.md) for more details.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Environment Variables

All optional — the system runs with sensible defaults if not configured.

| Variable              | Description                          | Default                     |
| --------------------- | ------------------------------------ | --------------------------- |
| `DB_PATH`             | Path to DuckDB dataset file          | Hardcoded in data_loader.py |
| `DB_URL`              | PostgreSQL connection URL            | `postgresql://admin:admin123@localhost:5432/honeypot` |
| `FLASK_DEBUG`         | Enable Flask debug mode              | `false`                     |
| `ALERT_EMAIL_FROM`    | Sender email for alerts              | *(disabled)*                |
| `ALERT_EMAIL_TO`      | Recipient email for alerts           | *(disabled)*                |
| `ALERT_EMAIL_PASSWORD`| Sender email app password            | *(disabled)*                |
| `SMTP_SERVER`         | SMTP server host                     | `smtp.gmail.com`            |
| `SMTP_PORT`           | SMTP server port                     | `587`                       |
| `SPLUNK_HEC_URL`      | Splunk HTTP Event Collector URL      | *(disabled)*                |
| `SPLUNK_HEC_TOKEN`    | Splunk HEC token                     | *(disabled)*                |
| `ELASTIC_URL`         | Elasticsearch base URL               | *(disabled)*                |
| `ELASTIC_INDEX`       | Elasticsearch index name             | `honeypot-alerts`           |

---

## API Endpoints

| Method | Endpoint   | Description                        |
| ------ | ---------- | ---------------------------------- |
| `GET`  | `/`        | API info & available endpoints     |
| `GET`  | `/health`  | System health & model status       |
| `POST` | `/predict` | Classify a network flow            |

### Example — Predict

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"duration":5.0,"orig_bytes":5000,"resp_bytes":3000,"orig_pkts":20,"resp_pkts":15,"history_len":10}'
```

Response:

```json
{
  "prediction": 1,
  "class_name": "Intent-to-act",
  "attack_type": "Lateral Movement",
  "confidence": 0.9832,
  "severity": "HIGH",
  "mitigation": [
    "Immediate IP Block via Firewall",
    "Terminate Active Sessions",
    "Trigger SIEM Alert (High Severity)",
    "Snapshot System State for Forensics"
  ],
  "timestamp": "2026-04-14T15:30:00+00:00"
}
```

---

## Results

| Metric           | Score       |
| ---------------- | ----------- |
| Accuracy         | 99.9%       |
| Precision        | 1.00        |
| Recall           | 1.00        |
| F1 Score         | 1.00        |
| Inference Speed  | < 50 ms     |

---

## 🔴 LIVE HONEYPOT MODE

This project supports swapping out the simulated data stream with a live network honeypot (Cowrie). Attackers connecting to Cowrie on port 2222 will be recorded to `cowrie.json`. A watcher script tails this log, parses each event using the ML Model feature logic, uploads it to PostgreSQL, and triggers real-time responses. **If an intent-to-act is confidently detected, it automatically blocks the IP address dynamically via Windows Firewall (`netsh`)**.

### 1. Requirements

Ensure Docker Desktop and PostgreSQL are running, and an elevated (Admin) PowerShell prompt if you wish to block IPs via firewall. 

### 2. Start Cowrie

Run this in a regular PowerShell window. It creates the honeypot network intercept on ports 2222 (SSH) and 2223 (Telnet).

```bash
docker compose -f docker-compose.cowrie.yml up -d
```

### 3. Launch the Watcher (Requires Admin)

**Open a NEW PowerShell terminal AS ADMINISTRATOR.**
The watcher monitors the real-time logs and adds the dynamic Firewall rules to mitigate detected threats.

```bash
python src/watchers/cowrie_watcher.py
```

### 4. Execute the Simulation Payload

**Open a NEW PowerShell terminal.**
Send simulated brute-force SSH attacks locally to trigger the alerts.

```bash
powershell .\attacks\test_cowrie_attacks.ps1
```

### 5. Verify the Defense 

- The `cowrie_watcher.py` log should emit `🚨 BLOCKED 127.0.0.1` and `🛡️  Firewall rule created for 127.0.0.1`
- The React dashboard should update with Live metrics and the High-Severity alert.

> **Rollback instructions for Windows Firewall**:
> To undo the automatic IP bans and test again, remove the rules via the following admin command:
> ```powershell
> netsh advfirewall firewall delete rule name=all | Select-String "Honeypot_Block_"
> ```

---

## 📧 Email Alerts

The framework supports automated email alerts for HIGH-severity attacks and scheduled daily summary reports.

### Quick Setup

1. **Generate a Gmail App Password** — see [EMAIL_SETUP.md](EMAIL_SETUP.md) for step-by-step instructions
2. **Configure environment variables** in `.env`:

```env
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_TO=honeytest777@gmail.com
ALERT_EMAIL_PASSWORD=your-16-char-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

3. **Test the connection:**

```bash
# Via API
curl -X POST http://localhost:5000/test-email

# Or via the React dashboard → Alerts page → "Send Test Email" button
```

### What Gets Emailed?

| Trigger | Condition | Email Type |
| ------- | --------- | ---------- |
| Attack detected | `severity == HIGH` and `confidence > 90%` | 🚨 Immediate alert with full event details |
| Scheduled | Daily at 08:00 (configurable) | 📊 Summary with stats from PostgreSQL |
| Manual test | `POST /test-email` | ✅ Connection verification |

### Rate Limiting

To prevent inbox flooding during active attacks:
- Max **1 email per source IP per 5 minutes**
- Subsequent detections are logged but not emailed
- Rate limit resets when the watcher process restarts

### Daily Summary Reports

```bash
# Run continuously (sends at 08:00 daily)
python src/scheduled_tasks.py

# Custom time
python src/scheduled_tasks.py --time 18:00

# One-shot (for cron / Task Scheduler)
python src/scheduled_tasks.py --once
```

### Email API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/test-email` | Send a test email to verify SMTP config |
| `GET` | `/email-status` | Get email alerting config and status |

> See [EMAIL_SETUP.md](EMAIL_SETUP.md) for full setup guide, alternative SMTP providers, and troubleshooting.

---

## License

© 2026 Automated Attack Analysis and Prevention Framework
