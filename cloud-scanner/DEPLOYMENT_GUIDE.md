# 🚀 CogniWatch Cloud Scanner - Deployment Guide

**Private scanning infrastructure for internet-wide agent discovery**

---

## 📋 **What This Does**

- Scans public IPv4 space for AI agent frameworks
- Focuses on OpenClaw Gateways (ports 18789, 18790, 18791)
- Stores results in PRIVATE database (not public)
- Web dashboard for analysis (login required)
- **Purpose:** Market research, threat intel, product validation

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────┐
│  VPS (DigitalOcean $6/mo)                  │
│  - Ubuntu 22.04                            │
│  - 2GB RAM, 1 vCPU, 50GB SSD               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Cloud Scanner (Python/asyncio)     │   │
│  │  - Rate-limited scanning            │   │
│  │  - WebSocket + HTTP fingerprinting  │   │
│  │  - Saves to PostgreSQL              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  PostgreSQL Database                │   │
│  │  - agents table (discoveries)       │   │
│  │  - scans table (scan history)       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Flask Dashboard (Login Only)       │   │
│  │  - Search agents                    │   │
│  │  - View statistics                  │   │
│  │  - Export data (CSV)                │   │
│  │  - NO PUBLIC ACCESS                 │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## ⚡ **Quick Deploy (30 Minutes)**

### **Step 1: Create VPS**

**Provider:** DigitalOcean (easiest, cheapest)

```bash
# Go to: https://digitalocean.com
# Click: "Create Droplet"

# Choose:
- OS: Ubuntu 22.04 LTS
- Plan: Basic ($6/month)
  - 1 vCPU
  - 2GB RAM
  - 50GB SSD
  - 2TB transfer
- Region: NYC3 (closest to you)
- Authentication: SSH key (recommended) or password

# Click: "Create Droplet"
# Wait 60 seconds
# Note the IP address (e.g., 159.65.XXX.XXX)
```

**Alternative providers:**
- Linode ($5/month)
- Vultr ($6/month)
- AWS EC2 t3.micro (free tier, but more complex)

---

### **Step 2: SSH Into VPS**

```bash
# From your laptop:
ssh root@YOUR_VPS_IP

# Or if using password:
ssh root@YOUR_VPS_IP
# Enter password when prompted
```

---

### **Step 3: Install Dependencies**

```bash
# Update system
apt update && apt upgrade -y

# Install PostgreSQL
apt install postgresql postgresql-contrib -y

# Install Python 3.10+
apt install python3 python3-pip python3-venv -y

# Install Git
apt install git -y

# Create app user
adduser cogniwatch
usermod -aG sudo cogniwatch
```

---

### **Step 4: Setup PostgreSQL**

```bash
# Switch to postgres user
su - postgres

# Create database
psql <<EOF
CREATE DATABASE cogniwatch;
CREATE USER cogniwatch_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE cogniwatch TO cogniwatch_user;
EOF

# Exit postgres
exit
```

**IMPORTANT:** Replace `STRONG_PASSWORD_HERE` with a real password!

---

### **Step 5: Clone CogniWatch**

```bash
# Switch to cogniwatch user
su - cogniwatch

# Clone repo
cd /home/cogniwatch
git clone https://github.com/YOUR_GITHUB/cogniwatch.git
cd cogniwatch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install cloud scanner dependencies
pip install aiohttp websocket-client asyncpg aiosmttplib
```

---

### **Step 6: Configure Scanner**

```bash
# Create config
cd /home/cogniwatch/cogniwatch/cloud-scanner
cp config.example.json config.json

# Edit config
nano config.json
```

**Update these values:**
```json
{
  "database": {
    "url": "postgresql://cogniwatch_user:STRONG_PASSWORD_HERE@localhost:5432/cogniwatch"
  },
  "scan_rate": 100,
  "ports": [18789, 18790, 18791],
  "scan_targets": [
    "159.65.0.0/16",
    "167.99.0.0/16",
    "104.248.0.0/16"
  ]
}
```

---

### **Step 7: Test Scanner**

```bash
# Run scanner (foreground, for testing)
source venv/bin/activate
python scanner.py

# Watch logs - should see:
# "🚀 Starting scan of 159.65.0.0/16"
# "🎯 FOUND: openclaw @ IP:PORT (85%)"
# "📈 Scanned 1000 IPs, found 12 agents"
```

**Let it run for 5-10 minutes** to verify it's working.

**Expected:** Should find some OpenClaw instances if they exist in scanned ranges.

---

### **Step 8: Run as Systemd Service**

```bash
# Create systemd service
sudo nano /etc/systemd/system/cogniwatch-scanner.service
```

**Paste this:**
```ini
[Unit]
Description=CogniWatch Cloud Scanner
After=network.target postgresql.service

[Service]
Type=simple
User=cogniwatch
WorkingDirectory=/home/cogniwatch/cogniwatch/cloud-scanner
Environment="PATH=/home/cogniwatch/cogniwatch/cloud-scanner/venv/bin"
ExecStart=/home/cogniwatch/cogniwatch/cloud-scanner/venv/bin/python scanner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable cogniwatch-scanner
sudo systemctl start cogniwatch-scanner

# Check status
sudo systemctl status cogniwatch-scanner
```

**Logs:**
```bash
# View live logs
sudo journalctl -u cogniwatch-scanner -f

# View recent logs
sudo journalctl -u cogniwatch-scanner --since "1 hour ago"
```

---

### **Step 9: Setup Web Dashboard (Optional)**

```bash
# Still in /home/cogniwatch/cogniwatch
cd /home/cogniwatch/cogniwatch/webui

# Create dashboard config
cp config-dashboard.example.json config-dashboard.json
nano config-dashboard.json

# Edit with:
{
  "database": {
    "url": "postgresql://cogniwatch_user:PASSWORD@localhost:5432/cogniwatch"
  },
  "auth": {
    "username": "jannie",
    "password": "VERY_STRONG_PASSWORD"
  },
  "listen": "127.0.0.1:9000"
}

# Start dashboard (background)
nohup ./venv/bin/python server.py --config config-dashboard.json &
```

**Access:** `http://YOUR_VPS_IP:9000` (but only accessible from localhost for now)

---

### **Step 10: Setup HTTPS (Production)**

**Important:** Before exposing to internet, add HTTPS!

**Option A: Nginx + Let's Encrypt (recommended)**

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Configure Nginx
sudo nano /etc/nginx/sites-available/cogniwatch
```

**Paste:**
```nginx
server {
    listen 80;
    server_name cogniwatch.dev;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Enable and get SSL:**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d cogniwatch.dev

# Follow prompts, choose "Redirect HTTP to HTTPS"
```

---

### **Step 11: Firewall Configuration**

```bash
# Install UFW
sudo apt install ufw -y

# Only allow SSH and HTTPS
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 80/tcp     # Block HTTP (redirects to HTTPS)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

**IMPORTANT:** Do NOT open port 9000 directly - always use HTTPS proxy!

---

## 📊 **Scanning Strategy**

### **Phase 1: Test Ranges (First 24 Hours)**
```
Scan small ranges to verify everything works:
- 159.65.0.0/24 (256 IPs) - DigitalOcean NYC
- 167.99.0.0/24 (256 IPs) - DigitalOcean NYC

Expected runtime: 10-20 minutes
Expected finds: 0-10 OpenClaw instances (if any)
```

### **Phase 2: VPS Provider Ranges (Week 1)**
```
Scan common VPS provider ranges:
- DigitalOcean: 159.65.0.0/16, 167.99.0.0/16, 104.248.0.0/16
- Linode: 45.33.0.0/16, 66.228.0.0/16
- AWS EC2: 54.0.0.0/8 (partial)

Expected runtime: 6-12 hours
Expected finds: 50-500 OpenClaw instances (estimate)
```

### **Phase 3: Full IPv4 Scan (Week 2-4)**
```
Scan entire IPv4 space for ports 18789-18791:
- ~4.3 billion IPs
- At 100 IPs/sec = ~500 days (too slow!)
- Solution: Focus on high-probability ranges only

Smart scanning:
1. Shodan API: Find IPs with port 18789 open (if available)
2. Censys API: Search for OpenClaw certificates
3. GitHub: Scan IPs mentioned in OpenClaw deployment guides
4. Common VPS ranges: DigitalOcean, Linode, AWS, GCP, Azure

Expected finds: 5,000-50,000 OpenClaw instances (wild guess)
```

---

## 🔒 **Security & Privacy**

### **Data Handling:**
✅ Results are PRIVATE (not publicly exposed)  
✅ No individual data sold or shared  
✅ Aggregate statistics only for marketing  
✅ Opt-out mechanism when we launch public registry  

### **Scanning Etiquette:**
✅ Rate limit: 100 IPs/sec (don't overwhelm networks)  
✅ Respect `robots.txt` where applicable  
✅ Add `User-Agent: CogniWatch-Scanner/1.0 (Research)`  
✅ Monitor for abuse complaints, respond promptly  

### **Legal Compliance:**
✅ Scanning public IPs is generally legal (US)  
✅ Only collecting public metadata (banners, versions)  
✅ No exploitation, no payload delivery  
✅ Clear research purpose documented  

---

## 📈 **Monitoring & Maintenance**

### **Daily Checks:**
```bash
# Scanner running?
sudo systemctl status cogniwatch-scanner

# Database size?
su - postgres
psql -c "SELECT COUNT(*) FROM cogniwatch.agents;"

# Disk usage?
df -h

# Logs (any errors?)
sudo journalctl -u cogniwatch-scanner --since "24 hours ago" | grep -i error
```

### **Weekly Tasks:**
- Review scan progress
- Check for new framework signatures
- Update scanner if needed
- Backup database

```bash
# Backup database
pg_dump -U cogniwatch_user cogniwatch > backup_$(date +%Y%m%d).sql

# Store backup somewhere safe
scp backup_*.sql your-laptop:/backups/
```

---

## 🎯 **Success Metrics**

### **Week 1 Goals:**
- ✅ Infrastructure deployed and running
- ✅ 100,000 IPs scanned
- ✅ 10+ OpenClaw instances found
- ✅ Dashboard accessible, data viewable

### **Month 1 Goals:**
- ✅ 10M IPs scanned
- ✅ 1,000+ OpenClaw instances catalogued
- ✅ Version distribution analyzed
- ✅ Geographic distribution mapped

### **Launch Content (from this data):**
- "We scanned 10M IPs and found 1,000+ exposed AI agents"
- "X% running outdated versions"
- "Top countries: US (30%), Germany (15%), UK (10%)"
- "Most popular model: qwen3.5:cloud (40%)"

**This data becomes our LAUNCH AMMUNITION!** 🚀

---

## 🚨 **Troubleshooting**

### **Scanner not finding anything?**
```bash
# Check if ports are actually in use
nmap -p 18789,18790,18791 scanme.nmap.org

# Test scanner on known target
python scanner.py --test-target YOUR_OWN_GATEWAY_IP

# Check logs for errors
sudo journalctl -u cogniwatch-scanner -f
```

### **Database connection failed?**
```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Test connection
psql -U cogniwatch_user -d cogniwatch -h localhost

# Reset password if needed
sudo -u postgres psql
\password cogniwatch_user
```

### **Scanner using too much CPU?**
```bash
# Reduce scan rate in config.json
"scan_rate": 50  # Down from 100

# Restart scanner
sudo systemctl restart cogniwatch-scanner
```

---

## 📞 **Next Steps**

1. **Deploy VPS** (30 min)
2. **Install scanner** (15 min)
3. **Test on small range** (10 min)
4. **Let it run overnight**
5. **Check results in morning**
6. **Scale up scanning**
7. **Analyze findings**
8. **Prepare launch content**

**Total time to first data: ~2 hours**

**Let's do this, Jannie!** 🎯👁️

---

**Questions?** Ping me and I'll troubleshoot with you!
