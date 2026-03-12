# 🚀 CogniWatch Deployment Guide

**Version:** 1.0.0  
**Last Updated:** March 8, 2026

Complete guide for deploying CogniWatch on Ubuntu/Debian VPS, local servers, or Docker environments.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Deployment Options](#deployment-options)
3. [Docker Deployment (Recommended)](#docker-deployment-recommended)
4. [VPS Deployment (Ubuntu/Debian)](#vps-deployment-ubuntudebian)
5. [From-Source Deployment](#from-source-deployment)
6. [Configuration Options](#configuration-options)
7. [HTTPS Setup](#https-setup)
8. [Firewall Configuration](#firewall-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Migration & Upgrades](#migration--upgrades)

---

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **CPU** | 2 cores | 4+ cores recommended for large networks |
| **RAM** | 2 GB | 4+ GB recommended |
| **Storage** | 10 GB | SSD recommended for database performance |
| **OS** | Ubuntu 22.04+, Debian 11+, or Docker host | Other Linux distros possible |
| **Network** | Static IP or reserved IP | Recommended for production |

### Network Requirements

| Direction | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| **Inbound** | TCP | 9000 | Web UI (configurable) |
| **Inbound** | TCP | 22 | SSH (management) |
| **Outbound** | TCP/UDP | All | Network scanning |
| **Inbound** | TCP | 80/443 | HTTP/HTTPS (if using reverse proxy) |

### Scalability Guidelines

| Deployment Size | Hosts | Recommendations |
|-----------------|-------|-----------------|
| **Small** | <100 | Minimum specs, SQLite, single instance |
| **Medium** | 100-1,000 | 4 CPU, 4GB RAM, increase scan timeout |
| **Large** | 1,000-10,000 | 8 CPU, 8GB RAM, multiple scanner instances |
| **Enterprise** | >10,000 | Cluster deployment, PostgreSQL (Phase C) |

---

## 🎯 Deployment Options

### Option 1: Docker (Recommended ⭐)

**Best for:** Most deployments, quick setup, isolated environment

**Pros:**
- ✅ Fast deployment (3 commands)
- ✅ Isolated dependencies
- ✅ Easy updates
- ✅ Pre-configured security

**Cons:**
- ❌ Slight overhead (~50MB RAM)
- ❌ Docker knowledge required

### Option 2: VPS (Production)

**Best for:** Production deployments, bare metal, maximum performance

**Pros:**
- ✅ Direct system access
- ✅ No containerization overhead
- ✅ Full control over configuration
- ✅ Systemd service management

**Cons:**
- ❌ More setup steps
- ❌ Manual dependency management

### Option 3: From Source (Development)

**Best for:** Developers, contributors, custom modifications

**Pros:**
- ✅ Full source access
- ✅ Easy debugging
- ✅ Custom builds

**Cons:**
- ❌ Complex setup
- ❌ Manual updates
- ❌ Environment management

---

## 🐳 Docker Deployment (Recommended)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Step 1: Install Docker

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Repository

```bash
# Clone CogniWatch
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Edit these values:**

```bash
# Admin credentials (CHANGE THESE!)
COGNIWATCH_ADMIN_USER=admin
COGNIWATCH_ADMIN_PASSWORD=your-secure-password-here

# Network to scan (adjust for your network)
SCANNER_NETWORK=192.168.1.0/24

# Optional: OpenClaw Gateway integration
OPENCLAW_GATEWAY_URL=ws://your-gateway:18789
OPENCLAW_GATEWAY_TOKEN=your-token-here

# Web UI port (default: 9000)
COGNIWATCH_PORT=9000

# Scan schedule (cron format)
SCAN_SCHEDULE=0 */6 * * *
```

### Step 4: Deploy

```bash
# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Step 5: Access Web UI

Open your browser: `http://<your-server-ip>:9000`

**Default credentials:**
- Username: `admin`
- Password: (whatever you set in .env)

### Docker Services

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| **Web UI** | cogniwatch-webui | 9000 | React dashboard |
| **Scanner** | cogniwatch-scanner | — | Network discovery |
| **Database** | cogniwatch-db | — | SQLite (persistent volume) |

### Docker Commands Cheat Sheet

```bash
# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f cogniwatch-webui
docker compose logs -f cogniwatch-scanner

# Restart services
docker compose restart

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build

# Scale scanner instances (for large networks)
docker compose up -d --scale cogniwatch-scanner=3

# Run manual scan
docker compose exec cogniwatch-scanner python3 scanner/network_scanner.py

# Backup database
docker compose exec cogniwatch-db cp /data/cogniwatch.db /backup/
```

### Docker Troubleshooting

```bash
# Container won't start
docker compose logs cogniwatch-webui

# Port already in use
# Edit docker-compose.yml, change ports section:
ports:
  - "3001:9000"  # Use different host port

# Permission denied errors
sudo chown -R $USER:$USER data/

# Database corruption
docker compose down
# Backup corrupted DB
cp data/cogniwatch.db data/cogniwatch.db.corrupted
# Reinitialize
docker compose up -d
```

---

## ☁️ VPS Deployment (Ubuntu/Debian)

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Dependencies

```bash
# Python and build tools
sudo apt install -y python3.12 python3.12-venv python3-pip git curl

# Network scanning tools
sudo apt install -y nmap

# Nginx (for reverse proxy)
sudo apt install -y nginx

# Node.js (for Web UI build, if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 3: Create Application Directory

```bash
# Create directory structure
sudo mkdir -p /opt/cogniwatch
sudo mkdir -p /var/log/cogniwatch
sudo mkdir -p /etc/cogniwatch

# Create cogniwatch user (no login shell)
sudo useradd --system --no-create-home --shell /bin/false cogniwatch

# Set ownership
sudo chown -R cogniwatch:cogniwatch /opt/cogniwatch
sudo chown -R cogniwatch:cogniwatch /var/log/cogniwatch
```

### Step 4: Install Application

```bash
# Clone or copy CogniWatch
cd /opt/cogniwatch
# (Use git clone or copy files via scp/rsync)

# Create virtual environment
sudo -u cogniwatch python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### Step 5: Configure Application

```bash
# Copy configuration templates
sudo -u cogniwatch cp config/config.example.json config/cogniwatch.json
sudo -u cogniwatch cp .env.example /etc/cogniwatch/.env

# Edit configuration
sudo nano config/cogniwatch.json
```

**Update configuration:**

```json
{
  "openclaw_gateway": {
    "url": "ws://your-gateway-host:18789",
    "token": "your-actual-token",
    "poll_interval_seconds": 30
  },
  "webui": {
    "host": "0.0.0.0",
    "port": 9000,
    "debug": false,
    "admin_user": "admin",
    "admin_password": "your-secure-password"
  },
  "scanner": {
    "enabled": true,
    "network": "192.168.1.0/24",
    "scan_interval_hours": 24,
    "rate_limit": 100,
    "timeout_seconds": 300
  },
  "security": {
    "token_expiry_hours": 24,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    }
  },
  "telemetry": {
    "enabled": true,
    "retention_days": 90,
    "collection_interval_seconds": 60
  }
}
```

```bash
# Edit environment file
sudo nano /etc/cogniwatch/.env
```

### Step 6: Install Systemd Services

```bash
# Copy service files (from repository)
sudo cp cogniwatch.service /etc/systemd/system/
sudo cp cogniwatch-scanner.service /etc/systemd/system/

# Set permissions
sudo chmod 644 /etc/systemd/system/cogniwatch*.service

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable cogniwatch.service
sudo systemctl enable cogniwatch-scanner.service

# Start services
sudo systemctl start cogniwatch.service
sudo systemctl start cogniwatch-scanner.service

# Check status
sudo systemctl status cogniwatch.service
sudo systemctl status cogniwatch-scanner.service
```

### Step 7: Setup Nginx Reverse Proxy (Optional)

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/cogniwatch
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name cogniwatch.yourdomain.com;

    # Redirect HTTP to HTTPS (after SSL setup)
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeout for long-running scans
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 8: Setup HTTPS with Let's Encrypt (Optional)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d cogniwatch.yourdomain.com

# Verify auto-renewal
sudo systemctl status certbot.timer
```

**Test certificate renewal:**

```bash
sudo certbot renew --dry-run
```

---

## 💻 From-Source Deployment

### Prerequisites

- Python 3.12+
- pip 24.0+
- Git
- Node.js 18+ (for Web UI)

### Step 1: Clone Repository

```bash
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch
```

### Step 2: Create Virtual Environment

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
python3 -m database.init_db
```

### Step 5: Start Services

**Terminal 1 - Web UI:**

```bash
source venv/bin/activate
python3 -m webui.server
```

**Terminal 2 - Scanner:**

```bash
source venv/bin/activate
python3 scanner/network_scanner.py
```

---

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COGNIWATCH_ADMIN_USER` | `admin` | Admin username |
| `COGNIWATCH_ADMIN_PASSWORD` | (required) | Admin password |
| `COGNIWATCH_PORT` | 9000 | Web UI port |
| `COGNIWATCH_HOST` | `0.0.0.0` | Web UI bind address |
| `SCANNER_NETWORK` | `192.168.1.0/24` | Default scan range |
| `SCAN_SCHEDULE` | `0 */6 * * *` | Cron schedule for scans |
| `OPENCLAW_GATEWAY_URL` | — | Gateway WebSocket URL |
| `OPENCLAW_GATEWAY_TOKEN` | — | Gateway auth token |

### Configuration File (config/cogniwatch.json)

**Scanner Settings:**

```json
{
  "scanner": {
    "enabled": true,
    "network": "192.168.1.0/24",
    "scan_interval_hours": 24,
    "rate_limit": 100,
    "timeout_seconds": 300,
    "ports": [80, 443, 5000, 8080, 8081, 18789],
    "detect_tls": true,
    "detect_websocket": true,
    "grab_banners": true
  }
}
```

**Web UI Settings:**

```json
{
  "webui": {
    "host": "0.0.0.0",
    "port": 9000,
    "debug": false,
    "theme": "dark",
    "session_timeout_hours": 24
  }
}
```

**Security Settings:**

```json
{
  "security": {
    "auth_required": true,
    "token_expiry_hours": 24,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 100
    },
    "cors_origins": ["http://localhost:9000", "http://192.168.1.0/24"]
  }
}
```

**Telemetry Settings:**

```json
{
  "telemetry": {
    "enabled": true,
    "retention_days": 90,
    "collection_interval_seconds": 60,
    "metrics": ["connections", "api_calls", "websocket_messages", "errors"]
  }
}
```

---

## 🔒 HTTPS Setup

### Option 1: Let's Encrypt (Recommended)

See VPS Deployment Step 8 above.

### Option 2: Self-Signed Certificate (Testing)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/cogniwatch.key \
  -out /etc/ssl/certs/cogniwatch.crt

# Set permissions
sudo chmod 600 /etc/ssl/private/cogniwatch.key
sudo chmod 644 /etc/ssl/certs/cogniwatch.crt

# Update nginx config to use SSL
# (Add to server block in /etc/nginx/sites-available/cogniwatch)
ssl_certificate /etc/ssl/certs/cogniwatch.crt;
ssl_certificate_key /etc/ssl/private/cogniwatch.key;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
```

---

## 🔥 Firewall Configuration

### UFW (Uncomplicated Firewall)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (CRITICAL - do this FIRST!)
sudo ufw allow ssh

# Allow CogniWatch web UI
sudo ufw allow 9000/tcp comment "CogniWatch Web UI"

# Rate limit SSH (prevent brute force)
sudo ufw limit ssh

# Allow HTTP/HTTPS (if using nginx)
sudo ufw allow 'Nginx Full'

# Check status
sudo ufw status verbose
```

### iptables (Advanced)

```bash
# Allow web UI from specific IPs only
sudo iptables -A INPUT -p tcp --dport 9000 -s 192.168.1.0/24 -j ACCEPT

# Rate limit new connections
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 -j DROP

# Save rules (Debian/Ubuntu)
sudo netfilter-persistent save

# Save rules (RHEL/CentOS)
sudo service iptables save
```

### Cloud Firewall (AWS, DigitalOcean, etc.)

**Security Group Rules:**

| Direction | Protocol | Port | Source | Purpose |
|-----------|----------|------|--------|---------|
| Inbound | TCP | 22 | Your IP | SSH |
| Inbound | TCP | 9000 | Your network/VPN | Web UI |
| Inbound | TCP | 80 | 0.0.0.0/0 | HTTP (if using nginx) |
| Inbound | TCP | 443 | 0.0.0.0/0 | HTTPS (if using nginx) |
| Outbound | ALL | ALL | 0.0.0.0/0 | Outbound traffic |

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check systemd status
sudo systemctl status cogniwatch

# View detailed logs
sudo journalctl -u cogniwatch -n 100 --no-pager

# Check if port is in use
sudo ss -tlnp | grep 9000

# Check permissions
ls -la /opt/cogniwatch/data/
```

### Database Errors

```bash
# Check database file permissions
ls -l /opt/cogniwatch/data/cogniwatch.db

# Test database connection
sqlite3 /opt/cogniwatch/data/cogniwatch.db ".tables"

# Restore from backup
cp /backup/cogniwatch_YYYYMMDD.db /opt/cogniwatch/data/cogniwatch.db
```

### Scanner Not Finding Agents

1. **Verify network range:**

```bash
# Check your actual network
ip addr show
# or
ifconfig
```

2. **Test connectivity:**

```bash
ping 192.168.1.1
nmap -sn 192.168.1.0/24
```

3. **Check firewall:**

```bash
sudo ufw status
```

4. **Run scanner manually:**

```bash
source venv/bin/activate
python3 scanner/network_scanner.py --verbose
```

### Web UI Access Issues

1. **Check service is running:**

```bash
sudo systemctl status cogniwatch
```

2. **Test locally:**

```bash
curl http://localhost:9000/health
```

3. **Check firewall:**

```bash
sudo ufw status | grep 9000
```

4. **Check nginx (if using):**

```bash
sudo nginx -t
sudo systemctl status nginx
```

### High Resource Usage

```bash
# Monitor resource usage
htop
# or
top -p $(pgrep -f cogniwatch)

# Check database size
ls -lh /opt/cogniwatch/data/cogniwatch.db

# Reduce scanner parallelism
# Edit config/cogniwatch.json, lower rate_limit
```

### Docker-Specific Issues

```bash
# View container logs
docker compose logs -f cogniwatch-webui
docker compose logs -f cogniwatch-scanner

# Check container status
docker compose ps

# Check disk space
docker system df

# Clean up unused resources
docker system prune -a

# Rebuild containers
docker compose build --no-cache
docker compose up -d --force-recreate
```

---

## ⬆️ Migration & Upgrades

### Upgrading from Previous Version

```bash
# Docker deployment
cd /opt/cogniwatch
git pull origin main
docker compose pull
docker compose up -d

# VPS deployment
cd /opt/cogniwatch
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cogniwatch cogniwatch-scanner
```

### Database Migration

```bash
# Backup current database
cp /opt/cogniwatch/data/cogniwatch.db /backup/cogniwatch-$(date +%Y%m%d).db

# Run migrations (if any)
cd /opt/cogniwatch
python3 -m database.migrate
```

### Rollback Procedure

```bash
# Stop services
sudo systemctl stop cogniwatch cogniwatch-scanner

# Restore previous code version
cd /opt/cogniwatch
git checkout <previous-tag>

# Restore database
cp /backup/cogniwatch_YYYYMMDD.db /opt/cogniwatch/data/cogniwatch.db

# Restart services
sudo systemctl start cogniwatch cogniwatch-scanner
```

---

## 📊 Performance Tuning

### Large Network Optimization

For networks with >1,000 hosts:

```json
{
  "scanner": {
    "rate_limit": 200,
    "timeout_seconds": 600,
    "parallel_scans": 3,
    "batch_size": 256
  },
  "telemetry": {
    "collection_interval_seconds": 300,
    "retention_days": 30
  }
}
```

### Database Optimization

```bash
# Enable WAL mode for better concurrency
sqlite3 /opt/cogniwatch/data/cogniwatch.db "PRAGMA journal_mode=WAL;"

# Vacuum database (reclaim space)
sqlite3 /opt/cogniwatch/data/cogniwatch.db "VACUUM;"

# Analyze for query optimization
sqlite3 /opt/cogniwatch/data/cogniwatch.db "ANALYZE;"
```

---

## 📞 Support

**Documentation:** Review all markdown files in `/opt/cogniwatch/`  
**Logs:** Check `/var/log/cogniwatch/` and `journalctl`  
**GitHub Issues:** Report bugs and feature requests  
**Email:** support@cogniwatch.dev

---

<p align="center">
  <strong>Deployed successfully?</strong> Now you're watching the AI agent ecosystem! 👁️
</p>
