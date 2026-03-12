# 🦈 CogniWatch VPS Deployment Guide

Complete guide for deploying CogniWatch on Ubuntu/Debian VPS or local servers.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deploy (Docker)](#quick-deploy-docker)
3. [Production Deploy (Systemd)](#production-deploy-systemd)
4. [Firewall Configuration](#firewall-configuration)
5. [Security Hardening](#security-hardening)
6. [Maintenance & Monitoring](#maintenance--monitoring)
7. [Troubleshooting](#troubleshooting)

---

## 🛠️ Prerequisites

### System Requirements

- **OS:** Ubuntu 22.04+ or Debian 11+
- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 2GB minimum (4GB+ recommended)
- **Storage:** 10GB+ free space
- **Network:** Static IP or reserved IP recommended

### What You'll Need

1. SSH access to your VPS
2. Root or sudo privileges
3. OpenClaw Gateway URL and token (optional, for agent integration)
4. Domain name (optional, for HTTPS)

---

## 🐳 Quick Deploy (Docker)

**Recommended for:** Development, testing, and containerized deployments.

### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone & Configure

```bash
# Clone or copy CogniWatch to your server
cd /opt

# Create application directory
sudo mkdir -p /opt/cogniwatch
cd /opt/cogniwatch

# Copy deployment files
# (Copy Dockerfile, docker-compose.yml, .env.example from your local machine)
```

### Step 3: Configure Environment

```bash
# Create .env from example
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum required changes:**

```bash
# Update network range to match your network
SCANNER_NETWORK=192.168.0.0/24

# If using OpenClaw Gateway
OPENCLAW_GATEWAY_URL=ws://your-gateway-host:18789
OPENCLAW_GATEWAY_TOKEN=your-actual-token
```

### Step 4: Deploy

```bash
# Build and start services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f cogniwatch-webui
docker compose logs -f cogniwatch-scanner
```

### Step 5: Access Web UI

Open your browser: `http://<your-server-ip>:9000`

### Docker Commands Cheat Sheet

```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build

# Run one-time scan manually
docker compose exec cogniwatch-scanner python3 scanner/network_scanner.py
```

---

## 🔧 Production Deploy (Systemd)

**Recommended for:** Production deployments, bare metal, maximum control.

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Dependencies

```bash
# Python and build tools
sudo apt install -y python3.12 python3.12-venv python3-pip git curl nginx

# Network scanning tools
sudo apt install -y nmap
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
# Copy CogniWatch files to /opt/cogniwatch
# (Use scp, rsync, or git clone)
cd /opt/cogniwatch

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
# Copy config
sudo cp config/config.example.json config/cogniwatch.json

# Edit configuration
sudo nano config/cogniwatch.json
```

**Update these values:**

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
    "debug": false
  },
  "scanner": {
    "enabled": true,
    "network": "192.168.0.0/24",
    "scan_interval_hours": 24
  }
}
```

```bash
# Copy env file
sudo cp /path/to/.env.example /etc/cogniwatch/.env
sudo nano /etc/cogniwatch/.env
```

### Step 6: Install Systemd Services

```bash
# Copy service files
sudo cp cogniwatch.service /etc/systemd/system/
sudo cp cogniwatch-scanner.service /etc/systemd/system/

# Set permissions
sudo chmod 644 /etc/systemd/system/cogniwatch*.service

# Reload systemd
sudo systemctl daemon-reload

# Enable services
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
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Setup HTTPS with Let's Encrypt (Optional)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d cogniwatch.yourdomain.com

# Auto-renewal is configured automatically
```

---

## 🔥 Firewall Configuration

### UFW (Uncomplicated Firewall)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (CRITICAL - do before enabling firewall!)
sudo ufw allow ssh

# Allow CogniWatch web UI (if exposing directly)
sudo ufw allow 9000/tcp comment "CogniWatch Web UI"

# If using Nginx (ports 80/443)
sudo ufw allow 'Nginx Full'

# Rate limiting for SSH (prevent brute force)
sudo ufw limit ssh

# Check status
sudo ufw status verbose
```

### iptables (Advanced)

```bash
# Allow web UI from specific IPs only
sudo iptables -A INPUT -p tcp --dport 9000 -s 192.168.0.0/24 -j ACCEPT

# Rate limit new connections
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 -j DROP

# Save rules
sudo netfilter-persistent save
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

## 🔒 Security Hardening

### 1. System Security

```bash
# Keep system updated
sudo apt update && sudo apt upgrade -y

# Install security updates automatically
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Fail2ban for intrusion prevention
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**Fail2ban Jail for CogniWatch:**

```ini
# /etc/fail2ban/jail.local
[cogniwatch]
enabled = true
port = 9000
filter = cogniwatch
logpath = /var/log/cogniwatch/*.log
maxretry = 5
bantime = 3600
findtime = 600
```

### 2. Network Security

```bash
# Disable root SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use SSH keys only
# Set: PasswordAuthentication no

# Change SSH port (optional)
# Set: Port 2222

# Restart SSH
sudo systemctl restart sshd
```

### 3. Application Security

- **Run as non-root user** (already configured in service files)
- **Use .env files** for sensitive configuration (never commit to git)
- **Enable HTTPS** in production (use Let's Encrypt)
- **Limit scanner rate** to prevent network abuse
- **Review and restrict** scanner network ranges

### 4. Database Security

```bash
# Set restrictive permissions
sudo chmod 600 /opt/cogniwatch/data/cogniwatch.db
sudo chown cogniwatch:cogniwatch /opt/cogniwatch/data/cogniwatch.db
```

### 5. Log Security

```bash
# Rotate logs to prevent disk fill
sudo nano /etc/logrotate.d/cogniwatch
```

**Logrotate Config:**

```
/var/log/cogniwatch/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 cogniwatch cogniwatch
    postrotate
        systemctl reload cogniwatch > /dev/null 2>&1 || true
    endscript
}
```

---

## 📊 Maintenance & Monitoring

### Service Management

```bash
# Check status
sudo systemctl status cogniwatch
sudo systemctl status cogniwatch-scanner

# View logs
sudo journalctl -u cogniwatch -f
sudo journalctl -u cogniwatch-scanner -f

# Restart services
sudo systemctl restart cogniwatch
sudo systemctl restart cogniwatch-scanner

# Stop services
sudo systemctl stop cogniwatch
sudo systemctl stop cogniwatch-scanner
```

### Log Files

- Web UI: `/var/log/cogniwatch/webui.log`
- Scanner: `/var/log/cogniwatch/scanner.log`
- System logs: `sudo journalctl -u cogniwatch`

### Database Backups

```bash
# Manual backup
cp /opt/cogniwatch/data/cogniwatch.db /backup/cogniwatch-$(date +%Y%m%d).db

# Automated backup script
sudo nano /opt/cogniwatch/backup.sh
```

**Backup Script:**

```bash
#!/bin/bash
BACKUP_DIR="/backup/cogniwatch"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
sqlite3 /opt/cogniwatch/data/cogniwatch.db ".dump" | gzip > $BACKUP_DIR/cogniwatch_$DATE.sql.gz
# Keep only 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

```bash
# Add to crontab
crontab -e
# Run daily at 3 AM
0 3 * * * /opt/cogniwatch/backup.sh
```

### Health Checks

```bash
# Check web UI health endpoint
curl http://localhost:9000/health

# Check if services are running
systemctl is-active cogniwatch
systemctl is-active cogniwatch-scanner

# Check port is listening
ss -tlnp | grep 9000
```

### Updates

```bash
# Pull latest code (if using git)
cd /opt/cogniwatch
git pull origin main

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt
deactivate

# Restart services
sudo systemctl restart cogniwatch
sudo systemctl restart cogniwatch-scanner
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check status for errors
sudo systemctl status cogniwatch

# View detailed logs
sudo journalctl -u cogniwatch -n 100 --no-pager

# Check if port is in use
sudo ss -tlnp | grep 9000

# Check permissions
ls -la /opt/cogniwatch/data/
```

### Scanner Not Finding Agents

1. **Verify network range:** Check `SCANNER_NETWORK` in `.env`
2. **Check firewall:** Ensure scanning isn't blocked
3. **Test manually:**
   ```bash
   source venv/bin/activate
   python3 scanner/network_scanner.py
   ```
4. **Increase timeout:** Set longer timeout for slow networks

### Web UI Access Issues

1. **Check firewall:**
   ```bash
   sudo ufw status | grep 9000
   ```
2. **Verify service is running:**
   ```bash
   sudo systemctl status cogniwatch
   ```
3. **Test locally:**
   ```bash
   curl http://localhost:9000/health
   ```
4. **Check nginx config (if using):**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
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

### High Resource Usage

```bash
# Monitor resource usage
htop
# or
top -p $(pgrep -f cogniwatch)

# Reduce scanner parallelism (in config)
# Lower SCANNER_NETWORK range or parallel threads
```

### Docker-Specific Issues

```bash
# View container logs
docker compose logs -f cogniwatch-webui
docker compose logs -f cogniwatch-scanner

# Check container status
docker compose ps

# Restart containers
docker compose restart

# Rebuild images
docker compose build --no-cache
docker compose up -d --force-recreate

# Check disk space
docker system df
```

---

## 📞 Support

- **Documentation:** Review all markdown files in `/opt/cogniwatch/`
- **Logs:** Check `/var/log/cogniwatch/` and `journalctl`
- **GitHub Issues:** Report bugs and feature requests
- **Community:** Join Discord/Slack for support

---

## 🎯 Quick Reference

### Key Files

- Configuration: `/opt/cogniwatch/config/cogniwatch.json`
- Environment: `/etc/cogniwatch/.env`
- Database: `/opt/cogniwatch/data/cogniwatch.db`
- Logs: `/var/log/cogniwatch/`
- Services: `/etc/systemd/system/cogniwatch*.service`

### Common Commands

```bash
# Start all services
sudo systemctl start cogniwatch cogniwatch-scanner

# Stop all services
sudo systemctl stop cogniwatch cogniwatch-scanner

# Restart all services
sudo systemctl restart cogniwatch cogniwatch-scanner

# View combined logs
sudo journalctl -u cogniwatch -u cogniwatch-scanner -f

# Check if running
curl http://localhost:9000/health
```

---

**Deployed successfully? You're now watching the AI agent ecosystem! 👁️**
