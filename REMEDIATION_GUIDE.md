# CogniWatch Security Remediation Guide

## Priority 1: CRITICAL Fixes (Implement Immediately)

### 1. Fix Authentication Bypass

**Problem:** API endpoints accessible without authentication

**Solution:** Add authentication decorator to ALL API routes in `server-2026.py`

```python
# Add these imports at the top
from flask import redirect, url_for
from functools import wraps

# Add authentication check decorator
def require_api_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Validate API key against database
            from webui.auth import auth_manager
            user = auth_manager.validate_api_key(api_key)
            if user:
                g.user = user
                return f(*args, **kwargs)
        
        # Check for session cookie
        session_id = request.cookies.get('session_id')
        if session_id:
            from webui.auth import auth_manager
            session = auth_manager.get_session(session_id)
            if session:
                g.user = session
                return f(*args, **kwargs)
        
        # No valid auth - return 401 for API requests
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated

# Apply to ALL API routes
@app.route('/api/agents')
@require_api_auth  # ← Add this to every /api/* route
def api_agents():
    # ... existing code
```

**Files to modify:**
- `/home/neo/cogniwatch/webui/server-2026.py`

**Test after fix:**
```bash
curl http://localhost:9001/api/agents
# Should return: {"error": "Authentication required"}
```

---

### 2. Fix Session Fixation

**Problem:** Arbitrary session IDs accepted without validation

**Solution:** Implement proper session validation

Add to `server-2026.py`:

```python
def validate_session(session_id):
    """Validate session ID against server-side store"""
    if not session_id:
        return False
    
    # Check session exists and not expired
    from datetime import datetime, timezone
    from webui.auth import auth_manager
    
    session = auth_manager.get_session(session_id)
    if not session:
        return False
    
    # Check expiry
    expires_at = datetime.fromisoformat(session.get('expires_at', '2000-01-01'))
    if expires_at < datetime.now(timezone.utc):
        # Session expired - destroy it
        auth_manager.destroy_session(session_id)
        return False
    
    return True

# In your authentication check
session_id = request.cookies.get('session_id')
if session_id and validate_session(session_id):
    # Valid session - proceed
    g.user = session
else:
    # Invalid session - reject
    return jsonify({'error': 'Invalid session'}), 401
```

---

### 3. Add Rate Limiting

**Problem:** No rate limiting (330+ req/sec observed)

**Solution:** Install and configure Flask-Limiter

**Step 1: Install flask-limiter**
```bash
cd /home/neo/cogniwatch
source venv/bin/activate
pip install flask-limiter
```

**Step 2: Configure in server-2026.py**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize after app creation
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        "60 per minute",
        "1000 per day"
    ],
    storage_uri="memory://",  # Use Redis in production
    strategy="fixed-window"
)

# Apply strict limits to sensitive endpoints
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def api_login():
    # ...

@app.route('/api/agents')
@limiter.limit("30 per minute")  # Prevent scraping
@require_api_auth
def api_agents():
    # ...
```

---

### 4. Add Security Headers

**Problem:** Missing critical security headers

**Solution:** Add after_request handler

Add to `server-2026.py`:

```python
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # HSTS (force HTTPS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:"
    )
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Disable caching for sensitive data
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
    
    return response
```

**Test after fix:**
```bash
curl -I http://localhost:9001/api/agents
# Should show all security headers
```

---

### 5. Hide Server Information

**Problem:** Server header reveals Flask/Python versions

**Solution:** Override server header

Add to `server-2026.py`:

```python
# Option 1: Override in Flask config
app.config['SERVER'] = 'CogniWatch'

# Option 2: Remove in after_request
@app.after_request
def add_security_headers(response):
    # ... existing headers ...
    response.headers['Server'] = 'CogniWatch'
    return response
```

---

## Priority 2: HIGH (Implement Within 24 Hours)

### 6. Enable HTTPS

**Problem:** Application runs on HTTP, no TLS encryption

**Solution:** Use nginx reverse proxy with Let's Encrypt

**Step 1: Install nginx**
```bash
sudo apt update
sudo apt install nginx
```

**Step 2: Create nginx config**
```bash
sudo nano /etc/nginx/sites-available/cogniwatch
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (get from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Step 3: Enable and restart**
```bash
sudo ln -s /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 4: Get SSL certificate**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### 7. Implement IP Whitelisting (Optional for Local)

**Solution:** Restrict access to trusted IPs only

Add to `server-2026.py`:

```python
ALLOWED_IPS = ['127.0.0.1', '192.168.0.0/24']

@app.before_request
def check_ip():
    from ipaddress import ip_address, ip_network
    
    client_ip = request.remote_addr
    
    for allowed in ALLOWED_IPS:
        if '/' in allowed:
            if ip_address(client_ip) in ip_network(allowed, strict=False):
                return None
        else:
            if client_ip == allowed:
                return None
    
    # IP not allowed
    logger.warning(f"Blocked request from {client_ip}")
    return jsonify({'error': 'Access denied'}), 403
```

---

## Priority 3: MEDIUM (Implement Within 1 Week)

### 8. Input Validation

Add validation to all input parameters:

```python
import re

def validate_agent_id(agent_id):
    """Validate agent ID format"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        return False
    if len(agent_id) > 100:
        return False
    return True

@app.route('/api/agents/<agent_id>')
@require_api_auth
def get_agent(agent_id):
    if not validate_agent_id(agent_id):
        return jsonify({'error': 'Invalid agent ID'}), 400
    # ... rest of handler
```

---

### 9. Logging and Audit Trail

Add comprehensive logging:

```python
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cogniwatch/access.log'),
        logging.StreamHandler()
    ]
)

# Log API access
@app.before_request
def log_request():
    logger.info(f"{request.remote_addr} - {request.method} {request.path}")

# Log authentication events
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    # ... auth logic ...
    if success:
        logger.info(f"Login successful: {username} from {request.remote_addr}")
    else:
        logger.warning(f"Login failed: {username} from {request.remote_addr}")
```

---

## Implementation Checklist

### Critical (Do Today)
- [ ] Add authentication to all /api/* routes
- [ ] Fix session validation
- [ ] Add rate limiting
- [ ] Add security headers
- [ ] Hide server version

### High (Do This Week)
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Configure nginx reverse proxy
- [ ] Implement IP whitelisting
- [ ] Add comprehensive logging

### Medium (Do Next Week)
- [ ] Add input validation on all endpoints
- [ ] Implement audit logging
- [ ] Create security monitoring
- [ ] Document security procedures

---

## Testing After Remediation

### Test 1: Auth Bypass Fixed
```bash
curl http://localhost:9001/api/agents
# Expected: {"error": "Authentication required"}
```

### Test 2: Session Fixation Fixed
```bash
curl http://localhost:9001/api/agents \
  -H "Cookie: session_id=fake_session"
# Expected: 401 Unauthorized
```

### Test 3: Rate Limiting Active
```bash
for i in {1..20}; do
  curl -s http://localhost:9001/api/health
done
# Eventually should see 429 Too Many Requests
```

### Test 4: Security Headers Present
```bash
curl -I http://localhost:9001/api/agents
# Should show X-Frame-Options, CSP, HSTS, etc.
```

---

## Additional Recommendations

1. **Regular Security Audits:** Run this pentest script monthly
2. **Dependency Updates:** Keep Flask and dependencies updated
3. **Monitoring:** Set up alerts for failed login attempts
4. **Backups:** Regular database backups
5. **Incident Response:** Create security incident response plan

---

**Remember:** Security is ongoing, not a one-time fix!
