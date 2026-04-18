"""
simulate_attacks.py — Generates random honeypot-style network connection
records and inserts them into a PostgreSQL ``logs`` table.

Run alongside run_live_demo.py to see the ML model classify each
connection in real time.
"""

import random
import time
import psycopg2

# ── PostgreSQL connection settings ──────────────────────────────────
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "honeypot"
DB_USER = "admin"
DB_PASS = "admin123"

# ── Attack profiles ─────────────────────────────────────────────────
PROFILES = {
    "SSH Brute Force": {
        "duration": 0.1,
        "orig_bytes": lambda: random.randint(5000, 50000),
        "resp_bytes": lambda: random.randint(3000, 30000),
        "orig_pkts": lambda: random.randint(100, 500),
        "resp_pkts": lambda: random.randint(80, 400),
        "proto": "tcp",
        "conn_state": "SF",
        "history": "ShAdDaF",
    },
    "Port Scan": {
        "duration": 0.01,
        "orig_bytes": lambda: random.randint(20, 60),
        "resp_bytes": lambda: random.randint(0, 20),
        "orig_pkts": 1,
        "resp_pkts": 0,
        "proto": "tcp",
        "conn_state": "S0",
        "history": "S",
    },
    "Data Exfiltration": {
        "duration": 45.0,
        "orig_bytes": lambda: random.randint(100000, 500000),
        "resp_bytes": lambda: random.randint(50000, 200000),
        "orig_pkts": lambda: random.randint(500, 2000),
        "resp_pkts": lambda: random.randint(300, 1500),
        "proto": "tcp",
        "conn_state": "SF",
        "history": "ShAdDaFf",
    },
    "Benign Browse": {
        "duration": 1.5,
        "orig_bytes": lambda: random.randint(200, 800),
        "resp_bytes": lambda: random.randint(1000, 5000),
        "orig_pkts": lambda: random.randint(5, 15),
        "resp_pkts": lambda: random.randint(8, 20),
        "proto": "tcp",
        "conn_state": "SF",
        "history": "ShADadf",
    },
}


def resolve(value):
    """If value is a callable (lambda), call it; otherwise return as-is."""
    return value() if callable(value) else value


def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        conn.autocommit = True
        cur = conn.cursor()
        print(f"Connected to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
    except psycopg2.OperationalError as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        print("\nMake sure PostgreSQL is running. Quick start:")
        print("  docker run --name honeypot-live \\")
        print("    -e POSTGRES_DB=honeypot \\")
        print("    -e POSTGRES_USER=admin \\")
        print("    -e POSTGRES_PASSWORD=admin123 \\")
        print("    -p 5432:5432 -d postgres:15")
        print("\nThen create the table:")
        print("  docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql")
        return

    INSERT_SQL = """
        INSERT INTO logs (duration, orig_bytes, resp_bytes, orig_pkts, resp_pkts,
                          proto, conn_state, history)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    profile_names = list(PROFILES.keys())
    print("Simulation started — press Ctrl+C to stop.\n")

    try:
        while True:
            name = random.choice(profile_names)
            p = PROFILES[name]

            row = (
                resolve(p["duration"]),
                resolve(p["orig_bytes"]),
                resolve(p["resp_bytes"]),
                resolve(p["orig_pkts"]),
                resolve(p["resp_pkts"]),
                p["proto"],
                p["conn_state"],
                p["history"],
            )

            cur.execute(INSERT_SQL, row)
            print(f"Inserted: {name} | bytes={row[1]} | state={p['conn_state']}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
