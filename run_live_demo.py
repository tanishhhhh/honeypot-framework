"""
run_live_demo.py — Starts the live PostgreSQL database monitor.

Loads the trained ML model and polls the PostgreSQL ``logs`` table for
new rows, classifying each connection as Attack or Probe in real time.

Usage:
    python run_live_demo.py
"""

import pickle
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from log_watcher import watch_postgres

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_model.pkl')
DB_URL = os.getenv("DB_URL", "postgresql://admin:admin123@localhost:5432/honeypot")


def main():
    print("=" * 60)
    print("  ML Honeypot Framework — Live Database Monitor")
    print("=" * 60)
    print(f"  Connecting to: {DB_URL}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        print(f"\nModel loaded: {type(model).__name__}")
    except FileNotFoundError:
        print("ERROR: best_model.pkl not found. Run train_model.py first.")
        return

    watch_postgres(model, DB_URL)


if __name__ == "__main__":
    main()
