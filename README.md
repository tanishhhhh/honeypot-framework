# 🛡️ Automated Attack Analysis & Prevention Framework

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![ML Framework](https://img.shields.io/badge/Model-XGBoost-orange)](https://xgboost.readthedocs.io/)
[![Framework](https://img.shields.io/badge/Frontend-Streamlit-red)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

> **A Machine Learning-powered Honeypot Intelligence System capable of detecting intrusions with 99% accuracy and generating actionable prevention strategies.**

## 📌 Project Overview
As cyberattacks become more sophisticated, manual analysis of honeypot logs is no longer scalable. This research project introduces an end-to-end framework that automates the transition from **raw log data** to **actionable threat intelligence**.

Using the **CTU HORNER dataset** as a baseline, this system employs ensemble learning (XGBoost/Random Forest) to classify attack intentions and maps them to specific security controls (e.g., "Implement Fail2Ban").

### 🚀 Key Features
* **Automated ETL Pipeline:** Parses and cleans millions of raw honeypot logs (CSV/JSON).
* **🧠 High-Fidelity ML Models:** Trained on **XGBoost** and **Random Forest**, achieving >99% accuracy in distinguishing "Intent-to-Act" vs. "Intent-to-Probe".
* **📊 Interactive SOC Dashboard:** A Streamlit-based interface for visualizing attack trends, geographic distributions, and real-time alerts.
* **🛡️ Prevention Intelligence:** Automatically suggests mitigation strategies (Firewall rules, SSH hardening) based on the classified attack type.
* **🧪 Simulation Mode:** Allows security analysts to upload **external log files** to test the model against new, unseen datasets.
* **⚡ Real-Time Ingestion:** Includes a `Watchdog` module to monitor log files and trigger alerts the instant a new attack occurs.

---

## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.9+ |
| **Data Processing** | Pandas, NumPy, Scapy |
| **Machine Learning** | Scikit-learn, XGBoost |
| **Backend API** | Flask (REST API) |
| **Frontend UI** | Streamlit |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## 📂 Project Structure
```text
honeypot-framework/
├── .github/              # CI/CD Workflows
├── src/
│   ├── app.py            # Flask API for Model Inference
│   ├── dashboard.py      # Streamlit Frontend
│   ├── data_loader.py    # Data Ingestion Logic
│   ├── feature_eng.py    # Feature Extraction Pipeline
│   ├── log_watcher.py    # Real-time Log Monitor
│   ├── prevention.py     # Mitigation Rule Engine
│   ├── train_model.py    # ML Training Script (GridSearch)
│   └── simulation.py     # External Data Testing Module
├── tests/                # Unit Tests (Pytest)
├── logs/                 # Raw Dataset (Excluded from Git)
├── Dockerfile.api        # Backend Container
├── Dockerfile.ui         # Frontend Container
├── docker-compose.yml    # Orchestration
└── requirements.txt      # Python Dependencies
````

-----

## ⚙️ Installation & Usage

### Option A: Running Locally

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/tanishhhhh/honeypot-framework.git](https://github.com/tanishhhhh/honeypot-framework.git)
    cd honeypot-framework
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Train the Model:**
    *(Note: This creates the `best_model.pkl` artifact)*

    ```bash
    python src/train_model.py
    ```

4.  **Launch the System:**

      * **Backend API:**
        ```bash
        python src/app.py
        ```
      * **Dashboard:**
        ```bash
        streamlit run src/dashboard.py
        ```

### Option B: Running with Docker (Recommended)

Build and run the entire stack with a single command:

```bash
docker-compose up --build
```

  * **Dashboard:** `http://localhost:8501`
  * **API:** `http://localhost:5000`

-----

## 📊 Results & Performance

The system was evaluated using the CTU HORNER dataset (12M+ rows).

  * **Accuracy:** 99.9% (XGBoost/Random Forest)
  * **Precision:** 1.00
  * **Recall:** 1.00
  * **Inference Speed:** \<50ms per entry

-----

## 🧪 External Simulation

The dashboard includes a **Simulation Mode** that allows researchers to upload their own `.csv` logs. The system attempts to map external columns to the model's feature set and provides a downloadable report of detected threats.

-----

## 👤 Author

**Tanish Parab**

  * M.Sc. Computer Science
  * [GitHub Profile](https://github.com/tanishhhhh)

-----

*This project is part of a Master's Research Paper on "Machine Learning Framework for Automated Attack Analysis".*

```
```
