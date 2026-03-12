# 🚀 Quick Start — CogniWatch

Get CogniWatch running in **5 minutes** and discover your first AI agent.

---

## 📋 Prerequisites

Choose **one** of these setup paths:

### Option A: Docker (Recommended ⭐)
- Docker 20.10+
- Docker Compose 2.0+

### Option B: Python pip
- Python 3.12+
- pip 24.0+

### Option C: From Source
- Python 3.12+
- Git
- Node.js 18+ (for Web UI)

---

## 🐳 Option A: Docker (3 Commands)

**Best for:** Production deployments, quick setup, isolated environment

```bash
# 1. Clone and enter directory
git clone https://github.com/neo/cogniwatch.git && cd cogniwatch

# 2. Start all services
docker compose up -d

# 3. Open dashboard
open http://localhost:3000
```

**What's running:**
- `cogniwatch-webui` — React dashboard (port 3000)
- `cogniwatch-scanner` — Discovery engine (runs every 15 min)
- `cogniwatch-db` — SQLite database (persistent volume)

**Stop services:** `docker compose down`

---

## 🐍 Option B: Python pip (4 Commands)

**Best for:** Development, custom configurations

```bash
# 1. Install package
pip install cogniwatch

# 2. Initialize configuration
cogniwatch init

# 3. Start the server
cogniwatch server

# 4. Run scanner (separate terminal)
cogniwatch scan --network 192.168.1.0/24
```

**Open dashboard:** http://localhost:3000

---

## 💻 Option C: From Source (5 Commands)

**Best for:** Contributors, custom modifications

```bash
# 1. Clone repository
git clone https://github.com/neo/cogniwatch.git && cd cogniwatch

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python -m database.init_db

# 5. Start services
python -m webui.server &  # Dashboard
python -m scanner.discover  # Scanner (runs continuously)
```

**Open dashboard:** http://localhost:3000

---

## 🎯 Your First Scan

### Run a Network Scan

```bash
# Scan your local network (adjust CIDR for your network)
curl -X POST http://localhost:3000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"network": "192.168.1.0/24"}'
```

### Check Scan Status

```bash
curl http://localhost:3000/api/scan/status
```

### View Discovered Agents

```bash
curl http://localhost:3000/api/agents
```

**Example Response:**
```json
{
  "agents": [
    {
      "id": "ag_7k2m9n4p",
      "ip": "192.168.1.100",
      "port": 8080,
      "framework": "OpenClaw",
      "confidence": 0.94,
      "confidence_level": "HIGH",
      "detected_at": "2026-03-07T00:25:00Z",
      "last_seen": "2026-03-07T00:30:00Z",
      "status": "active"
    }
  ],
  "total": 1
}
```

---

## 📊 Understanding Results

### Confidence Scores

CogniWatch uses **Bayesian inference** across multiple detection layers:

| Level | Score Range | Meaning |
|-------|-------------|---------|
| 🔴 **Critical** | 95-100% | Multiple strong signals, confirmed framework |
| 🟠 **High** | 75-94% | Strong signals, very likely agent |
| 🟡 **Medium** | 50-74% | Some signals, possible agent |
| ⚪ **Low** | <50% | Weak signals, needs verification |

### Detection Layers

Confidence is calculated from:

1. **HTTP Headers** — Framework-specific headers (e.g., `X-OpenClaw-Version`)
2. **API Endpoints** — Known paths (e.g., `/api/v1/agents`, `/chat/completions`)
3. **WebSocket** — Handshake patterns and message structures
4. **TLS/JA3** — Fingerprint matching for encrypted connections
5. **Behavioral** — Request patterns, timing, response structures

### Example: How Confidence is Calculated

```
Agent at 192.168.1.100:8080

Layer 1: HTTP Headers
  └─ Found: "X-OpenClaw-Version: 1.0" (+30 points)

Layer 2: API Endpoints
  └─ Found: /api/v1/gateway/status (+25 points)

Layer 3: WebSocket
  └─ WebSocket at /ws/agent with OpenClaw handshake (+20 points)

Layer 4: TLS/JA3
  └─ JA3 hash matches known OpenClaw fingerprint (+15 points)

Layer 5: Behavioral
  └─ Request patterns match OpenClaw agent behavior (+4 points)

═══════════════════════════════════════
Total Confidence: 94% → HIGH
═══════════════════════════════════════
```

---

## 🔮 Next Steps

### Enable Telemetry

Track agent behavior in real-time:

```bash
# Start telemetry collector
python -m telemetry.collector --agent-id ag_7k2m9n4p
```

**Dashboard:** Navigate to **Telemetry** tab for live metrics.

### Configure Alerts

Get notified when new agents are discovered:

```bash
# Edit config/alerts.yaml
alerts:
  email:
    enabled: true
    recipient: security@example.com
  slack:
    enabled: true
    webhook: https://hooks.slack.com/xxx
```

### Access the API

 Programmatically manage CogniWatch:

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:3000/api"

# List all agents
response = requests.get(f"{BASE_URL}/agents", 
                       headers={"Authorization": f"Bearer {API_KEY}"})
agents = response.json()

# Trigger new scan
response = requests.post(f"{BASE_URL}/scan",
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        json={"network": "10.0.0.0/8"})
```

See [API.md](API.md) for complete endpoint reference.

---

## 🆘 Troubleshooting

### Docker container won't start

```bash
# Check logs
docker compose logs cogniwatch-webui

# Common fix: remove volumes and restart
docker compose down -v
docker compose up -d
```

### Port 3000 already in use

```bash
# Edit docker-compose.yml, change:
ports:
  - "3001:3000"  # Use 3001 instead

# Or set environment variable
export COGNIWATCH_PORT=3001
```

### Scanner not discovering agents

1. **Check network range:** Ensure CIDR matches your network
2. **Firewall rules:** Allow outbound connections from scanner
3. **Run manually:** `python -m scanner.discover --verbose`

### Database errors

```bash
# Reset database (WARNING: deletes all data)
rm data/cogniwatch.db
python -m database.init_db
```

---

## 📚 Learn More

- [Deployment Guide](DEPLOYMENT.md) — VPS setup for production
- [API Reference](API.md) — Complete API documentation
- [Security Report](SECURITY.md) — OWASP compliance details
- [Contributing](../README.md#-contributing) — Add new frameworks

---

<p align="center">
  <strong>Ready to scale?</strong> Check out the <a href="DEPLOYMENT.md">Deployment Guide</a> for production setups.
</p>
