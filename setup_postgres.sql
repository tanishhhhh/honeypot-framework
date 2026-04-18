-- setup_postgres.sql
-- Run with: docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql
-- Or:       docker exec -it honeypot-live psql -U admin -d honeypot -f /setup_postgres.sql

DROP TABLE IF EXISTS logs;

CREATE TABLE logs (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMP DEFAULT NOW(),
    duration    FLOAT,
    orig_bytes  INT,
    resp_bytes  INT,
    orig_pkts   INT,
    resp_pkts   INT,
    proto       VARCHAR(10),
    conn_state  VARCHAR(10),
    history     VARCHAR(50)
);
