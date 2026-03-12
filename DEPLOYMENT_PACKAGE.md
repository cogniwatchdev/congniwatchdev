# 🦈 CogniWatch Deployment Package

## 📦 Deliverables

| File | Purpose |
|------|---------|
| **Dockerfile** | Container image definition (Python 3.12 + nmap + dependencies) |
| **docker-compose.yml** | Multi-service orchestration (webui + scanner + database) |
| **.env.example** | Configuration template with all environment variables |
| **cogniwatch.service** | Systemd service for web UI (production deployment) |
| **cogniwatch-scanner.service** | Systemd service for network scanner (production deployment) |
| **deploy.sh** | Automated deployment script (Docker or Systemd) |
| **DEPLOYMENT.md** | Complete step-by-step deployment and operations guide |
| **FIREWALL_RULES.md** | Security hardening and firewall configuration |

---

## ⚡ Quick Start

### Option 1: Docker (5 minutes)

```bash
# Navigate to cogniwatch directory
cd /home/neo/cogniwatch

# Copy and edit configuration
cp .env.example .env
nano .env

# Deploy
docker compose up -d --build

# Access
# Open: http://YOUR_IP:9000
```

### Option 2: Systemd (10 minutes)

```bash
# Run deployment script
./deploy.sh

# Follow prompts
# Select "2" for Systemd deployment
# Answer yes to firewall configuration

# Access
# Open: http://YOUR_IP:9000
```

---

## 🔧 Configuration Checklist

Before deploying, configure:

- [ ] `SCANNER_NETWORK` - Your network range (e.g., 192.168.0.0/24)
- [ ] `OPENCLAW_GATEWAY_URL` - Gateway WebSocket URL (if using)
- [ ] `OPENCLAW_GATEWAY_TOKEN` - Gateway authentication token
- [ ] `COGNIWATCH_PORT` - Web UI port (default: 9000)
- [ ] Firewall rules for port 9000

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│   CogniWatch Deployment                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────┐  ┌──────────────┐ │
│  │   Web UI        │  │   Scanner    │ │
│  │   Flask App     │  │   Nmap-based │ │
│  │   Port: 9000    │  │   Periodic   │ │
│  └────────┬────────┘  └──────┬───────┘ │
│           │                  │          │
│           └────────┬─────────┘          │
│                    │                    │
│           ┌────────▼────────┐           │
│           │   SQLite DB     │           │
│           │   cogniwatch.db │           │
│           └─────────────────┘           │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🎯 Services

### Docker Services

1. **cogniwatch-webui** - Flask dashboard (port 9000)
2. **cogniwatch-scanner** - Network discovery agent

### Systemd Services

1. **cogniwatch.service** - Web UI daemon
2. **cogniwatch-scanner.service** - Scanner daemon

---

## 🔐 Security Defaults

- ✅ Non-root user (`cogniwatch`)
- ✅ Systemd security hardening (ProtectSystem, NoNewPrivileges, etc.)
- ✅ SQLite database with restricted permissions
- ✅ Rate limiting ready (via firewall)
- ✅ Fail2ban integration supported
- ✅ Docker container security (user isolation)

---

## 📝 Common Commands

### Docker

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f cogniwatch-webui
docker compose logs -f cogniwatch-scanner

# Restart
docker compose restart

# Rebuild
docker compose build --no-cache
docker compose up -d --force-recreate
```

### Systemd

```bash
# Status
sudo systemctl status cogniwatch
sudo systemctl status cogniwatch-scanner

# Start/Stop/Restart
sudo systemctl start cogniwatch
sudo systemctl stop cogniwatch
sudo systemctl restart cogniwatch

# Logs
sudo journalctl -u cogniwatch -f
sudo journalctl -u cogniwatch-scanner -f
```

---

## 🩹 Troubleshooting

**Service won't start?**
```bash
# Check logs
docker compose logs cogniwatch-webui
# OR
sudo journalctl -u cogniwatch -n 50
```

**Port 9000 not accessible?**
```bash
# Check firewall
sudo ufw status | grep 9000

# Check if listening
sudo ss -tlnp | grep 9000
```

**Scanner not finding agents?**
```bash
# Verify network range in .env
# Test manually
python3 scanner/network_scanner.py
```

---

## 📋 System Requirements

- **OS:** Ubuntu 22.04+ or Debian 11+
- **CPU:** 2+ cores
- **RAM:** 2GB minimum
- **Storage:** 10GB+
- **Python:** 3.12 (for Systemd deployment)
- **Docker:** 20.10+ (for Docker deployment)

---

## 🚀 Post-Deployment

1. ✅ Access web UI: `http://YOUR_IP:9000`
2. ✅ Run initial network scan
3. ✅ Configure OpenClaw Gateway (optional)
4. ✅ Setup firewall rules
5. ✅ Enable automatic updates
6. ✅ Configure backups

---

## 📖 Documentation

- **Full Deployment Guide:** DEPLOYMENT.md
- **Firewall Rules:** FIREWALL_RULES.md
- **Application README:** README.md
- **Security Framework:** SECURITY.md

---

**Ready to deploy! Start with `./deploy.sh` or `docker compose up -d` 👁️**
