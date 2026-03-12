# CogniWatch Security TODO List
**Created:** 2026-03-08  
**Priority:** Medium and Low priority items from security audit  
**Status:** Awaiting implementation

---

## 🔴 CRITICAL (APPLIED IMMEDIATELY)

### ✅ .env File Permissions
**Status:** FIXED (2026-03-08 14:30 UTC)  
**Action:** `chmod 600 /home/neo/cogniwatch/.env`

### ✅ Debug Mode Disabled
**Status:** FIXED  
**Action:** Changed `COGNIWATCH_DEBUG=false` in `.env`

### ✅ Weak Credentials Flagged
**Status:** FIXED  
**Action:** Changed admin password and secret key to placeholders requiring change before deployment

---

## 🟠 HIGH PRIORITY

### 1. Generate Production Secret Key
**Risk:** Development secret key could allow token forgery if leaked  
**Action Required:**
```bash
# Generate secure random secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env
COGNIWATCH_SECRET_KEY=<generated_key>
```

**Files to Update:**
- `/home/neo/cogniwatch/.env`

**Acceptance Criteria:**
- Secret key is 64-character hex string (32 bytes)
- Key is unique and not committed to version control

---

### 2. Enable HTTPS/TLS
**Risk:** All traffic (including auth tokens) transmitted in plaintext  
**Impact:** Critical for internet-facing deployment, optional for LAN

**Implementation Options:**

**Option A: Reverse Proxy (Recommended)**
```bash
# Install nginx
sudo apt install nginx

# Configure with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**Option B: Flask SSL Context (Quick)**
```python
# In server.py main entry point
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=9000,
        ssl_context='adhoc'  # Self-signed for testing
    )
```

**Files to Update:**
- `/home/neo/cogniwatch/webui/server.py` (if Option B)
- Nginx config (if Option A)

**Acceptance Criteria:**
- All HTTP requests redirect to HTTPS
- Valid SSL certificate (Let's Encrypt or trusted CA)
- HSTS header enabled

---

### 3. Database File Permissions
**Risk:** Database file readable by group/others exposes all data  
**Current:**
```bash
$ ls -la /home/neo/cogniwatch/data/cogniwatch.db
-rw-rw-r-- 1 neo neo 241664 Mar  8 11:34 cogniwatch.db
```

**Fix:**
```bash
chmod 600 /home/neo/cogniwatch/data/cogniwatch.db
chown neo:neo /home/neo/cogniwatch/data/cogniwatch.db
```

**Verification:**
```bash
ls -la /home/neo/cogniwatch/data/
# Should show: -rw------- 1 neo neo ...
```

---

## 🟡 MEDIUM PRIORITY

### 4. Implement CSRF Protection
**Risk:** Cross-site request forgery attacks on authenticated users  
**Current State:** Partial protection via `samesite='lax'` cookie attribute

**Implementation:**
```bash
# Install Flask-WTF
pip install flask-wtf
```

```python
# In server.py
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect(app)

# For API endpoints that need CSRF exemption (if using JWT)
@app.route('/api/auth/login', methods=['POST'])
@csrf.exempt
def api_login():
    ...
```

**Exemptions:**
- API endpoints using JWT tokens don't need CSRF protection (token-based auth)
- Forms using session cookies need CSRF tokens

**Files to Update:**
- `/home/neo/cogniwatch/webui/server.py`
- `/home/neo/cogniwatch/requirements.txt`

**Acceptance Criteria:**
- All form submissions include CSRF token
- CSRF validation on session-based endpoints
- JWT-based API endpoints exempt from CSRF

---

### 5. Database Encryption at Rest
**Risk:** Database theft exposes all data (though passwords are hashed)  
**Impact:** Primarily for sensitive deployments (production, multi-tenant)

**Options:**

**Option A: SQLCipher (Full Database Encryption)**
```bash
# Install SQLCipher
sudo apt install sqlcipher

# Use pysqlcipher3 Python wrapper
pip install pysqlcipher3
```

**Option B: Column-Level Encryption (Encrypt Sensitive Fields)**
```python
# In auth.py
from cryptography.fernet import Fernet

cipher = Fernet(os.environ.get('ENCRYPTION_KEY').encode())

def create_api_key(...):
    ...
    # Encrypt before storing
    encrypted_user_id = cipher.encrypt(user_id.encode())
    self.api_keys[key_hash] = {
        'user_id': encrypted_user_id,  # Encrypted
        ...
    }
```

**Recommendation:** Start with Option B for API keys and session data if SQLCipher is too complex.

**Files to Update:**
- `/home/neo/cogniwatch/requirements.txt`
- `/home/neo/cogniwatch/webui/auth.py`

---

### 6. Rate Limiting Hardening
**Current:** 60 requests/minute per IP  
**Recommended:** Per-endpoint limits for sensitive operations

**Implementation:**
```python
# In server.py middleware

# Login endpoint: 5 attempts/minute
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    ...

# API key creation: 10/hour
@app.route('/api/auth/api-key', methods=['POST'])
@limiter.limit("10 per hour")
def api_create_api_key():
    ...

# Scan endpoint: 3/hour (resource-intensive)
@app.route('/api/scan/start', methods=['POST'])
@limiter.limit("3 per hour")
def api_scan_start():
    ...
```

**Files to Update:**
- `/home/neo/cogniwatch/webui/server.py`

**Acceptance Criteria:**
- Login: 5 attempts/minute (prevent brute force)
- Scan: 3/hour (prevent resource exhaustion)
- API key creation: 10/hour (prevent key spam)

---

## 🟢 LOW PRIORITY

### 7. Enhanced Input Validation
**Risk:** SSRF (Server-Side Request Forgery) attacks via URL parameters

**Current:**
```python
# middleware.py Line 236
def validate_url_param(url: str) -> bool:
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    # Block localhost
    if hostname in ['localhost', '127.0.0.1', '::1']:
        return False
```

**Enhancement:**
```python
# Add CIDR validation for network scanner
def validate_network_range(network: str) -> bool:
    try:
        net = ipaddress.ip_network(network, strict=False)
        # Block private ranges on public deployments
        if net.is_private:
            if os.environ.get('COGNIWATCH_DEPLOYMENT') == 'public':
                return False  # Reject private ranges on VPS
        return True
    except ValueError:
        return False
```

**Files to Update:**
- `/home/neo/cogniwatch/webui/middleware.py`
- `/home/neo/cogniwatch/scanner/network_scanner.py`

---

### 8. Security Headers Enhancement
**Current Headers:**
```python
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; ...",
    ...
}
```

**Missing Headers:**
```python
# Add to SECURITY_HEADERS
'Referrer-Policy': 'strict-origin-when-cross-origin',
'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
'X-Permitted-Cross-Domain-Policies': 'none',
'Cross-Origin-Embedder-Policy': 'require-corp',
'Cross-Origin-Opener-Policy': 'same-origin',
'Cross-Origin-Resource-Policy': 'same-origin',
```

**Files to Update:**
- `/home/neo/cogniwatch/webui/middleware.py` Line 24-33

---

### 9. Audit Logging Enhancement
**Current:** Basic logging to stdout  
**Enhancement:** Structured logging with security events

**Implementation:**
```python
# Add to server.py
import json

class SecurityLogger:
    def __init__(self, log_file='security.log'):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_security_event(self, event_type, user_id, details):
        self.logger.info(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details
        }))

# Usage
security_logger = SecurityLogger()

# Log failed login attempts
security_logger.log_security_event('login_failed', username, {'ip': request.remote_addr})
security_logger.log_security_event('login_success', user['username'], {'ip': request.remote_addr})
```

**Files to Update:**
- `/home/neo/cogniwatch/webui/server.py`
- `/home/neo/cogniwatch/webui/auth.py`

**Log Events to Track:**
- ✅ Login success/failure
- 🔐 Permission denied (403)
- 🚫 Rate limit exceeded
- 👤 User creation
- 🔑 API key creation
- 🚨 SQL injection attempt
- 🛡️ CSRF violation

---

## Implementation Checklist

**Before Next Deployment:**

- [ ] Generate production secret key (HIGH)
- [ ] Enable HTTPS/TLS (HIGH)
- [ ] Fix database permissions (HIGH)
- [ ] Add CSRF protection (MEDIUM)
- [ ] Consider database encryption (MEDIUM)
- [ ] Implement per-endpoint rate limits (MEDIUM)

**Before Production:**

- [ ] All HIGH items complete
- [ ] All MEDIUM items complete
- [ ] Enhanced input validation (LOW)
- [ ] Security headers enhanced (LOW)
- [ ] Audit logging implemented (LOW)
- [ ] Penetration testing completed

---

## Security Testing Commands

### Verify Rate Limiting
```bash
# Install testing tool
pip install httpie

# Test rate limit on login endpoint
for i in {1..10}; do
  curl -X POST http://localhost:9000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
done

# Should return 429 Too Many Requests after 5-10 attempts
```

### Verify Headers
```bash
curl -I http://localhost:9000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Check response includes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: ...`

### Verify SSL (after HTTPS setup)
```bash
curl -I https://yourdomain.com:9000/api/agents
# Should return 200 OK with valid certificate
```

### Verify File Permissions
```bash
ls -la /home/neo/cogniwatch/.env
# Should show: -rw------- 1 neo neo ...

ls -la /home/neo/cogniwatch/data/cogniwatch.db
# Should show: -rw------- 1 neo neo ...

ls -la /home/neo/cogniwatch/config/auth.json
# Should show: -rw------- 1 neo neo ...
```

---

## Security Configuration Examples

### Production .env Template
```bash
# Admin Credentials (USE STRONG PASSWORDS!)
COGNIWATCH_ADMIN_USER=neo
COGNIWATCH_ADMIN_PASSWORD=<strong_password_here>

# Web UI Configuration
COGNIWATCH_HOST=0.0.0.0
COGNIWATCH_PORT=9000
COGNIWATCH_DEBUG=false

# Security
COGNIWATCH_SECRET_KEY=<64_char_hex_string>
COGNIWATCH_SECURE_COOKIES=true  # Enable for HTTPS
COGNIWATCH_TOKEN_EXPIRY=24

# CORS (restrict to your domain)
COGNIWATCH_ALLOWED_ORIGINS=https://yourdomain.com

# IP Whitelist (optional, comma-separated)
# COGNIWATCH_ALLOWED_IPS=192.168.0.0/24,10.0.0.1

# Scanner Configuration
SCANNER_NETWORK=192.168.0.0/24
SCANNER_INTERVAL_HOURS=24

# OpenClaw Gateway
OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=<your_gateway_token>
```

### Nginx Configuration (Recommended for HTTPS)
```nginx
server {
    listen 80;
    server_name cogniwatch.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cogniwatch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/cogniwatch.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cogniwatch.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security Best Practices: https://flask.palletsprojects.com/security/
- Flask-Limiter Documentation: https://flask-limiter.readthedocs.io/
- Flask-WTF CSRF: https://flask-wtf.readthedocs.io/en/stable/csrf/

---

**Next Review Date:** 2026-03-15 (after addressing HIGH priority items)
