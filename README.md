--Tech Stack:
Language = Python 3.9+ 
Data Processing = Pandas, NumPy, Scapy 
Machine Learning = Scikit-learn, XGBoost 
Backend API = Flask (REST API) 
Frontend UI = Streamlit 
DevOps = Docker, Docker Compose, GitHub Actions 

--Project Structure:

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

--Installation:

1.  Clone the repository:
git clone [https://github.com/tanishhhhh/honeypot-framework.git](https://github.com/tanishhhhh/honeypot-framework.git)
cd honeypot-framework

2.  Install dependencies
pip install -r requirements.t

3.  Train the Model:
python src/train_model.p

4. Launch the System
Windows Quick Start:
Double-click `run.bat` or run in terminal:
.\run.bat

Manual Start:
Backend API: `python src/app.py`
Dashboard: `streamlit run src/dashboard.py`

Dashboard: http://localhost:8501
API: http://localhost:5000

--Results: 
Accuracy: 99.9% (XGBoost/Random Forest)
Precision: 1.00
Recall: 1.00
Inference Speed: <50ms per entry
