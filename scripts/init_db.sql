-- scripts/init_db.sql
-- Idempotent database schema initialization for the ML Honeypot Framework.
-- Executed automatically by run.bat or manually via:
--   docker compose exec -T db psql -U admin -d honeypot -f /scripts/init_db.sql

CREATE TABLE IF NOT EXISTS logs (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_ip   VARCHAR(45),
    proto       VARCHAR(10),
    conn_state  VARCHAR(10),
    duration    FLOAT,
    orig_bytes  INTEGER,
    orig_pkts   INTEGER,
    resp_pkts   INTEGER,
    attack_type VARCHAR(100),
    prediction  INTEGER,
    class_name  VARCHAR(50),
    confidence  FLOAT,
    severity    VARCHAR(20),
    mitigation  TEXT
);

CREATE TABLE IF NOT EXISTS mitigation_log (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_ip   VARCHAR(45),
    action      VARCHAR(50),
    reason      TEXT,
    status      VARCHAR(20)
);
