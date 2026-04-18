# Live Attack Simulation Demo

## Prerequisites
- Docker Desktop running
- Project dependencies installed (`pip install -r requirements.txt`)

## Step 1 — Start PostgreSQL

```bash
docker run --name honeypot-live \
  -e POSTGRES_DB=honeypot \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin123 \
  -p 5432:5432 \
  -d postgres:15
```

## Step 2 — Create the logs table

```bash
docker exec -i honeypot-live psql -U admin -d honeypot < setup_postgres.sql
```

## Step 3 — Start the live monitor (Terminal 1)

```bash
python run_live_demo.py
```

## Step 4 — Start attack simulation (Terminal 2)

```bash
python simulate_attacks.py
```

## Step 5 — Watch detections appear in Terminal 1

Expected output:
```
  🚨 ATTACK | bytes=23451 | proto=tcp | state=SF
  ✅ Probe  | bytes=45    | proto=tcp | state=S0
  🚨 ATTACK | bytes=345210 | proto=tcp | state=SF
  ✅ Probe  | bytes=542   | proto=tcp | state=SF
```

## What each attack profile means

| Profile | Bytes | Duration | conn_state | Meaning |
|---------|-------|----------|------------|---------|
| SSH Brute Force | 5K–50K | 0.1s | SF | Successful connection, high throughput |
| Port Scan | 20–60 | 0.01s | S0 | No response — classic reconnaissance |
| Data Exfiltration | 100K–500K | 45s | SF | Very high bytes, long duration — active threat |
| Benign Browse | 200–800 | 1.5s | SF | Normal traffic patterns — should classify as probe |

## Stopping the demo

Press `Ctrl+C` in both terminals, then:

```bash
docker stop honeypot-live
docker rm honeypot-live
```
