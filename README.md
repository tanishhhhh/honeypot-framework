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

This starts both the Flask API and the React dashboard in separate windows.

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

This starts **three containers**:
- `backend` — Flask API on port `5000`
- `react-frontend` — React app (nginx) on port `3000`
- `db` — PostgreSQL 15 on port `5432`

### 3. Create the Logs Table (first time only)

```bash
docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql
```

### 4. Stop All Services

```bash
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

## License

© 2026 Automated Attack Analysis and Prevention Framework
