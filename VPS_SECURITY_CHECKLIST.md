# VPS Security Checklist - CogniWatch Deployment
**Priority:** PRE-DEPLOYMENT REQUIREMENTS  
**Target Environment:** Public VPS (internet-facing)  
**Date Created:** 2026-03-08  
**Based on:** OWASP Security Audit findings

---

## 🔴 PHASE 1: CRITICAL (Before ANY internet exposure)

### 1. Fix Authentication Bypass
**File:** `/home/neo/cogniwatch/webui/auth.py`

```bash
# Edit auth.py, remove lines 197-204:
sudo nano /home/neo/cogniwatch/webui/auth.py

# DELETE these lines:
    if not user_info:
        user_info = {
            'user_id': 'test-admin',
            'role': 'admin',
            'auth_type': 'bypass'
        }

# UNCOMMENT this line:
        return jsonify({'error': 'Authentication required', 'message': 'Provide a valid Bearer token, API key, or session cookie'}), 401
```

**Verify:**
```bash
# Restart server, test without token:
curl http://[VPS_IP]:9000/api/agents
# Should return: 401 Unauthorized
```

☐ **COMPLETED** - Auth bypass removed

---

### 2. Install UFW Firewall
**All VPS instances**

```bash
# Install UFW
sudo apt update
sudo apt install ufw -y

# Deny ALL incoming by default
sudo ufw default deny incoming

# Allow outgoing traffic
sudo ufw default allow outgoing

# Allow SSH from YOUR IP only (CHANGE THIS TO YOUR IP)
sudo ufw allow from 101.177.163.167/32 to any port 22 proto tcp

# Allow HTTPS (we'll set up SSL next)
sudo ufw allow 443/tcp

# DO NOT allow HTTP (port 80) - redirect to HTTPS only
# DO NOT expose port 9000 directly - use Nginx proxy

# Enable firewall
sudo ufw enable

# Verify status
sudo ufw status verbose
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       101.177.163.167
443/tcp                    ALLOW       Anywhere
```

☐ **COMPLETED** - UFW configured and active

---

### 3. HTTPS with Let's Encrypt
**Required for production**

```bash
# Install Nginx and Certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config for CogniWatch proxy
sudo nano /etc/nginx/sites-available/cogniwatch

# Add this config (replace YOUR_DOMAIN):
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (auto-filled by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to CogniWatch
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

☐ **COMPLETED** - HTTPS active with valid certificate

---

## 🟠 PHASE 2: HIGH PRIORITY (Before public announcement)

### 4. Change Default Auth Tokens
**File:** `/home/neo/cogniwatch/config/cogniwatch.json`

```bash
# Generate secure random tokens
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit config
nano /home/neo/cogniwatch/config/cogniwatch.json

# Replace default tokens:
"auth": {
  "tokens": {
    "<NEW_RANDOM_TOKEN_1>": {
      "role": "admin",
      "permissions": ["read", "write", "admin"],
      "created": "2026-03-08T00:00:00Z"
    }
  }
}

# Set restrictive permissions on config file
chmod 600 /home/neo/cogniwatch/config/cogniwatch.json
chown neo:neo /home/neo/cogniwatch/config/cogniwatch.json
```

☐ **COMPLETED** - Default tokens removed, new tokens generated

---

### 5. Configure Fail2ban
**Prevent brute force attacks**

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Create cogniwatch filter
sudo nano /etc/fail2ban/filter.d/cogniwatch.conf

# Add filter rules:
[Definition]
failregex = ^.*Unauthorized.*API token required.*<HOST>.*$
            ^.*Authentication required.*<HOST>.*$
            ^.*Invalid token.*<HOST>.*$
ignoreregex = 

# Create jail
sudo nano /etc/fail2ban/jail.d/cogniwatch.local

# Add:
[cogniwatch]
enabled = true
port = 9000,443
filter = cogniwatch
logpath = /home/neo/cogniwatch/logs/cogniwatch.log
maxretry = 5
bantime = 3600
findtime = 600

# Enable and restart
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status cogniwatch
```

☐ **COMPLETED** - Fail2ban active and monitoring

---

### 6. Enable Rate Limiting
**File:** `/home/neo/cogniwatch/webui/server.py` (full server)

```python
# Initialize SecurityMiddleware in server.py:
from middleware import SecurityMiddleware

app = Flask(__name__)
# ... other config ...

# Add before routes:
security = SecurityMiddleware()
security.init_app(app)

# Add strict rate limits for auth endpoints:
@app.route('/api/login', methods=['POST'])
def login():
    # Rate limited in decorator
    pass
```

**Alternative (quick fix for server-minimal.py):**
```python
# Add to server-minimal.py imports:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter:
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute", "1000 per day"],
    storage_uri="memory://"  # Change to Redis in production
)

# Add to API routes:
@app.route('/api/agents')
@require_auth
@limiter.limit("30 per minute")
def api_agents():
    # ... existing code ...
```

**Test rate limiting:**
```bash
# Should start returning 429 after 30 requests
for i in {1..35}; do 
  curl -s -o /dev/null -w "%{http_code} " \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://127.0.0.1:9000/api/agents" & 
done; wait
```

Expected: Some 429 responses after 30 requests

☐ **COMPLETED** - Rate limiting active and tested

---

### 7. Secure Database & Logs
**SQLite hardening**

```bash
# Set restrictive permissions
chmod 640 /home/neo/cogniwatch/data/cogniwatch.db
chown neo:neo /home/neo/cogniwatch/data/cogniwatch.db

# Make data directory restrictive
chmod 750 /home/neo/cogniwatch/data

# Configure log rotation
sudo nano /etc/logrotate.d/cogniwatch

# Add:
/home/neo/cogniwatch/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 neo neo
}

# Test log rotation
sudo logrotate -f /etc/logrotate.d/cogniwatch
```

☐ **COMPLETED** - Database and logs secured

---

### 8. SSH Hardening (VPS-specific)
**Prevent SSH brute force**

```bash
# Backup SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Configure:
Port 2222                    # Change from default 22
PermitRootLogin no           # No root login
PasswordAuthentication no    # Key-based auth only
PubkeyAuthentication yes
AllowUsers neo               # Your username only
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Restart SSH
sudo systemctl restart sshd

# Test new SSH port BEFORE closing current session:
ssh -p 2222 neo@your-vps-ip

# Update firewall for new SSH port
sudo ufw delete allow 22/tcp
sudo ufw allow 2222/tcp
```

☐ **COMPLETED** - SSH hardened

---

## 🟡 PHASE 3: MEDIUM PRIORITY (First week of operation)

### 9. Create Python Virtual Environment
**Stop using --break-system-packages**

```bash
# Navigate to CogniWatch directory
cd /home/neo/cogniwatch

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies properly
pip install --upgrade pip
pip install -r requirements.txt

# Verify versions
pip list | grep -iE "flask|jwt|bcrypt"

# Test server runs in venv
./venv/bin/python3 webui/server.py
```

☐ **COMPLETED** - Virtual environment active

---

### 10. Structured Logging Setup
**Security audit trail**

```python
# Add to server.py:
import logging
from pythonjsonlogger import jsonlogger

# Install dependency
pip install python-json-logger

# Configure logging:
logger = logging.getLogger(__name__)
logHandler = logging.FileHandler('logs/cogniwatch.json')
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log security events:
logger.info("API request", extra={
    "event_type": "api_access",
    "endpoint": "/api/agents",
    "user_id": user_id,
    "ip": request.remote_addr,
    "timestamp": datetime.utcnow().isoformat()
})
```

☐ **COMPLETED** - Structured logging enabled

---

### 11. Health Check & Monitoring
**Uptime monitoring**

```bash
# Create health check script
cat > /home/neo/cogniwatch/healthcheck.sh << 'EOF'
#!/bin/bash
# Check if CogniWatch is responding
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9000/api/scan/status)
if [ "$RESPONSE" != "200" ]; then
    echo "$(date) - CogniWatch health check failed (HTTP $RESPONSE)" >> /var/log/cogniwatch-health.log
    # Optionally restart:
    # systemctl restart cogniwatch
fi
EOF

chmod +x /home/neo/cogniwatch/healthcheck.sh

# Add to crontab (every 5 minutes)
crontab -e
# Add line:
*/5 * * * * /home/neo/cogniwatch/healthcheck.sh
```

☐ **COMPLETED** - Health monitoring active

---

## ✅ VERIFICATION CHECKLIST

### Run these tests BEFORE deployment:

```bash
# 1. Test auth is required
curl http://[VPS_IP]:9000/api/agents
# Expected: 401 Unauthorized

# 2. Test invalid token rejected
curl -H "Authorization: Bearer invalid" http://[VPS_IP]:9000/api/agents
# Expected: 401 Unauthorized

# 3. Test valid token works
curl -H "Authorization: Bearer YOUR_TOKEN" http://[VPS_IP]:9000/api/agents
# Expected: 200 OK + JSON

# 4. Test HTTPS redirect
curl -I http://[VPS_IP]/
# Expected: 301 redirect to HTTPS

# 5. Test HTTPS works
curl -I -k https://[VPS_IP]/
# Expected: 200 OK + security headers

# 6. Test security headers
curl -I -k https://[VPS_IP]/ | grep -E "X-|Content-Security|Strict-Transport"
# Expected: All security headers present

# 7. Test rate limiting
for i in {1..35}; do curl -s -o /dev/null -w "%{http_code} " -H "Authorization: Bearer YOUR_TOKEN" https://[VPS_IP]/api/agents & done; wait
# Expected: Some 429 responses

# 8. Test firewall
nmap -p 22,443,80,9000 [VPS_IP]
# Expected: Only 22 (SSH) and 443 (HTTPS) open
# Ports 80, 9000 should be filtered/closed

# 9. Check Shodan (wait 24h after deployment)
# Visit: https://www.shodan.io/host/[VPS_IP]
# Expected: Minimal or no information
```

---

## 🚨 EMERGENCY PROCEDURES

### If you detect an attack:

```bash
# 1. Block attacking IP immediately
sudo ufw deny from [ATTACKER_IP]

# 2. Check logs
tail -f /home/neo/cogniwatch/logs/cogniwatch.log

# 3. Temporarily take service offline
sudo systemctl stop cogniwatch  # or kill the process

# 4. Change all auth tokens
nano /home/neo/cogniwatch/config/cogniwatch.json

# 5. Review access logs for compromise
grep "200" /home/neo/cogniwatch/logs/cogniwatch.log | grep -v "health"

# 6. Check for unauthorized access
# Look for successful requests from unknown IPs
```

### If system is compromised:

1. **Disconnect from network** (VPS provider console)
2. **Preserve evidence** (copy logs before deletion)
3. **Rebuild from scratch** (don't try to clean)
4. **Rotate ALL credentials** (tokens, SSH keys, API keys)
5. **Review backup integrity** before restoring

---

## DEPLOYMENT READINESS SCORE

| Category | Status | Score |
|----------|--------|-------|
| Authentication | ☐ Not Started | 0/10 |
| Firewall | ☐ Not Started | 0/10 |
| HTTPS/SSL | ☐ Not Started | 0/10 |
| Rate Limiting | ☐ Not Started | 0/10 |
| Logging | ☐ Not Started | 0/10 |
| SSH Hardening | ☐ Not Started | 0/10 |
| Fail2Ban | ☐ Not Started | 0/10 |
| Token Security | ☐ Not Started | 0/10 |
| Database Security | ☐ Not Started | 0/10 |
| Monitoring | ☐ Not Started | 0/10 |

**Minimum Viable Deployment:** 60/100 (Critical items only)  
**Production Ready:** 90/100 (All items complete)

---

**Last Updated:** 2026-03-08  
**Next Review:** Before each major deployment  
**Contact:** Security findings → Jannie
