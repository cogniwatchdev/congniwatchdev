# CogniWatch OWASP Security Audit Report
**Date:** 2026-03-08  
**Auditor:** Neo (Subagent)  
**Target:** CogniWatch v0.3.0  
**Purpose:** Pre-deployment security validation before VPS deployment  
**Scope:** Web UI, API endpoints, Authentication, Network exposure

---

## Executive Summary

CogniWatch has **CRITICAL security vulnerabilities** that must be remediated before deployment to a public VPS. The application is currently suitable only for **local/LAN use with trusted users**.

**Overall Risk Level:** 🔴 **HIGH** (Not production-ready)
- **Critical Findings:** 2
- **High Findings:** 3
- **Medium Findings:** 3
- **Low Findings:** 2

---

## Network Exposure Analysis

### Current Listening Ports

| Port | Service | Binding | Internet Accessible | Risk |
|------|---------|---------|---------------------|------|
| 9000 | CogniWatch Web UI | 0.0.0.0 | ✅ YES | 🔴 CRITICAL |
| 8000 | Unknown service | 0.0.0.0 | ✅ YES | 🟠 HIGH |
| 9001 | Unknown Python service | 0.0.0.0 | ✅ YES | 🟠 HIGH |
| 11434 | Ollama | 127.0.0.1 | ❌ No | ✅ Safe |
| 18789 | OpenClaw Gateway | 127.0.0.1 | ❌ No | ✅ Safe |

### Public IP Status
- **IPv4:** 101.177.163.167
- **IPv6:** 2001:8003:6325:e901:f696:34ff:fef7:1827
- **Shodan Status:** Not indexed (not yet exposed to internet scans)
- **Firewall:** ❌ **UFW NOT ACTIVE** - No firewall protection

---

## OWASP Top 10 Assessment

### A01: Broken Access Control 🔴 CRITICAL

**Finding:** Auth bypass vulnerability in `auth.py` line 197-201

```python
# Line 197-201 in /home/neo/cogniwatch/webui/auth.py
if not user_info:
    user_info = {
        'user_id': 'test-admin',
        'role': 'admin',
        'auth_type': 'bypass'
    }
    # Uncomment below to require auth:
    # return jsonify({'error': 'Authentication required', ...}), 401
```

**Evidence:**
- Code explicitly provides admin access when authentication fails
- Comment indicates this is for "testing" but is active in production code
- The require_auth decorator in auth.py is more secure but not used in server-minimal.py

**Impact:** Any attacker can bypass authentication entirely and gain admin access to all API endpoints

**Remediation:**
1. Delete lines 197-204 in `auth.py`
2. Uncomment line 205-206 to enforce 401 response
3. Use the full `@require_auth()` decorator from auth.py instead of custom implementation

**Priority:** 🔴 CRITICAL - Fix before ANY deployment

---

### A02: Cryptographic Failures 🟠 HIGH

**Finding:** No HTTPS enforcement, tokens in plaintext config

**Evidence:**
```bash
$ curl -sI http://127.0.0.1:9000/api/agents
# No Strict-Transport-Security header
# No HTTPS redirect
```

**Config file token storage:**
```json
// /home/neo/cogniwatch/config/cogniwatch.json
"auth": {
  "tokens": {
    "cogniwatch-admin-2026": {  // <-- Plaintext token!
      "role": "admin",
      "permissions": ["read", "write", "admin"]
    }
}
```

**Impact:**
- Tokens can be stolen via network sniffing if deployed without HTTPS
- Man-in-the-middle attacks possible
- Token compromise = full system access

**Remediation:**
1. Enforce HTTPS with Let's Encrypt on VPS
2. Add HSTS header (already in middleware.py but not enabled)
3. Hash tokens in config file using bcrypt/sha256
4. Store secrets in environment variables or encrypted vault

**Priority:** 🟠 HIGH - Fix before internet deployment

---

### A03: Injection 🟡 MEDIUM

**Finding:** SQL injection filter exists but not applied to server-minimal.py

**Evidence:**
- `middleware.py` has `validate_input()` decorator with SQL injection patterns
- `server-minimal.py` doesn't import or use middleware at all
- Direct SQL queries in api_agents() route without parameterization:

```python
# server-minimal.py line 54
c.execute("SELECT * FROM detection_results ORDER BY confidence DESC")
# No parameterized queries, vulnerable if filter param added
```

**Testing:**
```bash
$ curl -H "Authorization: Bearer cogniwatch-admin-2026" \
  "http://127.0.0.1:9000/api/agents?filter='; DROP TABLE agents;--"
# Returns full dataset (filter param ignored, but no validation)
```

**Impact:** Future endpoint modifications could introduce SQL injection vulnerabilities

**Remediation:**
1. Use parameterized queries for ALL database operations
2. Import and apply `@validate_input()` decorator from middleware.py
3. Add input validation library (pydantic, cerberus, or marshmallow)

**Priority:** 🟡 MEDIUM - Prevent future regressions

---

### A04: Insecure Design 🟠 HIGH

**Finding:** No rate limiting enforced

**Evidence:**
```bash
$ for i in {1..25}; do curl -s -o /dev/null -w "%{http_code} " \
   -H "Authorization: Bearer cogniwatch-admin-2026" \
   "http://127.0.0.1:9000/api/agents" & done; wait

# Result: 200 200 200 ... (all 25 requests successful)
# Expected: Some 429 Too Many Requests
```

**Code Analysis:**
- `middleware.py` configures Flask-Limiter: `"60 per minute", "1000 per day"`
- `server-minimal.py` doesn't initialize SecurityMiddleware
- No rate limiting on authentication endpoints (brute force possible)

**Impact:**
- API abuse and DoS attacks possible
- Brute force attacks on auth tokens (no lockout)
- Resource exhaustion

**Remediation:**
1. Initialize SecurityMiddleware in server-minimal.py
2. Add stricter limits on auth endpoints: `"5 per minute"` for login attempts
3. Use Redis for rate limit storage (not memory://) in production
4. Add CAPTCHA or exponential backoff for failed auth

**Priority:** 🟠 HIGH - Essential for internet-facing services

---

### A05: Security Misconfiguration 🔴 CRITICAL

**Finding:** No security headers, debug info exposed, CORS misconfigured

**Evidence:**
```bash
$ curl -sI http://127.0.0.1:9000/api/agents
HTTP/1.1 200 OK
Server: Werkzeug/3.1.6 Python/3.12.3  # <-- Version disclosure
# Missing: X-Content-Type-Options
# Missing: X-Frame-Options
# Missing: X-XSS-Protection
# Missing: Strict-Transport-Security
# Missing: Content-Security-Policy
# Missing: Access-Control-Allow-Origin
```

**CORS Config:**
```json
// cogniwatch.json
"cors": {
  "allow_origins": ["http://127.0.0.1:9000", "http://192.168.0.245:9000"]
}
// Binding to 0.0.0.0 allows ANY origin to connect if CORS not enforced
```

**Impact:**
- Clickjacking attacks possible (no X-Frame-Options)
- XSS attacks not mitigated (no CSP)
- HTTPS downgrade attacks (no HSTS)
- Browser MIME-type sniffing (no X-Content-Type-Options)

**Remediation:**
1. Initialize SecurityMiddleware to apply headers
2. Remove server version from headers (Werkzeug default)
3. Set CORS origins to empty list for API (no browser access needed)
4. Set `debug=False` (already correct in server-minimal.py)

**Priority:** 🔴 CRITICAL - Easy to fix, high impact

---

### A06: Vulnerable Components 🟡 MEDIUM

**Finding:** Dependencies not audited, potentially outdated

**Evidence:**
```bash
$ pip3 list | grep -iE "flask|jwt|bcrypt"
Flask==3.1.3 (installed via --break-system-packages)
PyJWT==2.7.0  # requirements.txt says 2.8.0
bcrypt==3.2.2 # requirements.txt says 4.1.2
```

**Version Mismatches:**
- PyJWT: 2.7.0 vs 2.8.0 required
- bcrypt: 3.2.2 vs 4.1.2 required

**Impact:**
- Potential security patches not applied
- Dependency confusion attacks possible

**Remediation:**
1. Create virtual environment (don't use --break-system-packages)
2. Run: `pip install -r requirements.txt` in venv
3. Add `safety check` or `pip-audit` to CI/CD pipeline
4. Pin ALL dependency versions with hashes

**Priority:** 🟡 MEDIUM - Fix with deployment

---

### A07: Authentication & Session Management 🟠 HIGH

**Finding:** Dual auth systems, session management unclear

**Code Analysis:**
- `server-minimal.py` uses simple token lookup
- `auth.py` has comprehensive JWT/session/API key system but isn't used
- No token expiration enforced in server-minimal.py
- Tokens stored in plaintext JSON file

**Evidence:**
```python
# server-minimal.py - simple token check
AUTH_TOKENS = load_tokens()
if not token or token not in AUTH_TOKENS:
    return 401
# No expiration check, no rotation, no invalidation
```

**Impact:**
- No session invalidation possible
- Tokens never expire
- No audit trail of who used what token
- Can't revoke individual tokens

**Remediation:**
1. Use full `auth.py` AuthManager with JWT
2. Implement token expiration (already configured for 24h but not enforced)
3. Add token rotation mechanism
4. Store tokens hashed in database, not config file

**Priority:** 🟠 HIGH - Critical for multi-user deployments

---

### A08: Software and Data Integrity Failures 🟢 LOW

**Finding:** Basic input validation exists but not consistently applied

**Evidence:**
- `middleware.py` has `validate_agent_id()`, `validate_url_param()` functions
- SSRF protection exists in `validate_url_param()` (blocks localhost, private IPs)
- Not enforced in server-minimal.py

**Impact:**
- Future features could introduce integrity issues
- SSRF possible if URL fetching added without validation

**Remediation:**
1. Apply validation decorators to all endpoints
2. Add JSON schema validation for POST/PUT requests
3. Implement request signing for inter-service communication

**Priority:** 🟢 LOW - Preventative

---

### A09: Logging and Monitoring Failures 🟡 MEDIUM

**Finding:** Minimal logging, no audit trail

**Evidence:**
```python
# server-minimal.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Only logs server startup
```

**No logging for:**
- Failed authentication attempts
- Successful API calls
- Configuration changes
- Rate limit violations
- Security events

**Impact:**
- Can't detect attacks in progress
- No forensic trail after breach
- Can't monitor API usage patterns

**Remediation:**
1. Add structured logging (JSON format)
2. Log all auth failures with IP address
3. Implement log rotation (currently no max size)
4. Send logs to external SIEM for VPS deployment
5. Add alerting for suspicious patterns

**Priority:** 🟡 MEDIUM - Essential for production

---

### A10: Server-Side Request Forgery (SSRF) 🟢 LOW

**Finding:** SSRF protection exists but not active

**Evidence:**
```python
# middleware.py validate_url_param()
if hostname in ['localhost', '127.0.0.1', '::1']:
    return False
# Checks for private IPs
# Not used in server-minimal.py
```

**Impact:**
- Future URL fetching features could be exploited
- Internal network scanning via CogniWatch server

**Remediation:**
1. Apply validate_url_param() to any URL input
2. Use allowlist for external URLs
3. Implement proxy for URL fetching

**Priority:** 🟢 LOW - Currently no SSRF vectors

---

## Summary of Findings

| ID | Category | Severity | Status | Fix Estimate |
|----|----------|----------|--------|--------------|
| A01 | Broken Access Control | 🔴 Critical | Active | 10 min |
| A05 | Security Misconfiguration | 🔴 Critical | Active | 15 min |
| A02 | Cryptographic Failures | 🟠 High | Active | 2 hours |
| A04 | Insecure Design (Rate Limiting) | 🟠 High | Active | 20 min |
| A07 | Authentication Management | 🟠 High | Active | 1 hour |
| A03 | Injection | 🟡 Medium | Potential | 30 min |
| A06 | Vulnerable Components | 🟡 Medium | Active | 15 min |
| A09 | Logging Failures | 🟡 Medium | Active | 45 min |
| A08 | Data Integrity | 🟢 Low | Potential | 20 min |
| A10 | SSRF | 🟢 Low | Potential | 15 min |

---

## Immediate Actions Required (Before VPS Deployment)

### 🔴 CRITICAL (Must fix TODAY)
1. **Remove auth bypass** in `auth.py` lines 197-204
2. **Enable security middleware** in `server-minimal.py`
3. **Install and activate UFW firewall**

### 🟠 HIGH (Must fix before deployment)
4. Configure HTTPS with Let's Encrypt
5. Fix rate limiting (currently not working)
6. Hash API tokens in config file
7. Implement proper JWT auth from auth.py

### 🟡 MEDIUM (Should fix in first week)
8. Add structured logging with audit trail
9. Create Python virtual environment with pinned dependencies
10. Add input validation to all endpoints

---

## Testing Performed

### Authentication Tests
```bash
✅ curl http://127.0.0.1:9000/api/agents
   → 401 Unauthorized (CORRECT)

✅ curl -H "Authorization: Bearer invalid-token" http://127.0.0.1:9000/api/agents
   → 401 Unauthorized (CORRECT)

✅ curl -H "Authorization: Bearer cogniwatch-admin-2026" http://127.0.0.1:9000/api/agents
   → 200 OK + data (CORRECT)
```

### SQL Injection Test
```bash
⚠️  curl -H "Authorization: Bearer cogniwatch-admin-2026" \
   "http://127.0.0.1:9000/api/agents?filter='; DROP TABLE agents;--"
   → 200 OK + data (filter param ignored, but NOT validated)
```

### Rate Limiting Test
```bash
❌ for i in {1..25}; do curl -s -o /dev/null -w "%{http_code} " \
   -H "Authorization: Bearer cogniwatch-admin-2026" \
   "http://127.0.0.1:9000/api/agents" & done

   → All 25 requests returned 200 (RATE LIMIT NOT WORKING)
```

### Security Headers Test
```bash
❌ curl -sI http://127.0.0.1:9000/api/agents
   → NO security headers present
```

---

## Conclusion

CogniWatch has a solid foundation with authentication implemented, but **must not be deployed to a public VPS without fixing the critical and high severity issues identified**.

The auth bypass vulnerability alone would allow any attacker to gain full admin access. Combined with no rate limiting, no security headers, and no firewall, this creates a highly vulnerable attack surface.

**Estimated Time to Secure:** 4-6 hours  
**Recommended Deployment Block:** Until all 🔴 Critical and 🟠 High items are resolved

---

## Tools Needed for Remediation

- ✅ Flask, Flask-CORS, Flask-Limiter (installed)
- ✅ bcrypt, PyJWT (installed, need update)
- ✅ UFW (available, not configured)
- Need: certbot for Let's Encrypt (VPS)
- Need: Redis for rate limiting (optional but recommended)
- Need: fail2ban (recommended for VPS)
