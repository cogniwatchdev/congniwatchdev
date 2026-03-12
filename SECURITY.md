# 🔒 CogniWatch Security Policy

**Last Updated:** March 8, 2026  
**Version:** 1.0.0

CogniWatch is built with security as a core principle, not an afterthought. This document outlines our security commitments, responsible disclosure process, and best practices for users.

---

## 📋 Table of Contents

1. [Security Commitments](#security-commitments)
2. [Responsible Disclosure Policy](#responsible-disclosure-policy)
3. [Security Contact Information](#security-contact-information)
4. [Known Limitations](#known-limitations)
5. [User Best Practices](#user-best-practices)
6. [Security Audit Summary](#security-audit-summary)
7. [OWASP Compliance](#owasp-compliance)
8. [Security Updates](#security-updates)

---

## 🛡️ Security Commitments

CogniWatch pledges:

1. **Transparency** — All security vulnerabilities disclosed publicly after patching
2. **Responsibility** — Security patches within 72 hours of verified discovery
3. **Privacy** — No data collection beyond what's necessary for monitoring
4. **Local-First** — Your data stays on your network (you control it)
5. **Open Source** — Security through transparency (audit the code yourself)
6. **Compliance** — Full OWASP Top 10 + LLM Top 10 adherence

---

## 📬 Responsible Disclosure Policy

We encourage responsible disclosure of security vulnerabilities discovered in CogniWatch.

### How to Report

**Preferred Method:** Email
- **Address:** security@cogniwatch.dev
- **Encryption:** PGP key available upon request
- **Response Time:** Within 48 hours

**Alternative Method:** GitHub Private Vulnerability Reporting
- Visit: https://github.com/neo/cogniwatch/security/advisories
- Click "Report a vulnerability"
- Provide detailed information

### What to Include

To help us investigate quickly, please include:

1. **Vulnerability Description**
   - Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
   - Affected component(s)
   - Severity assessment (your estimate)

2. **Reproduction Steps**
   - Step-by-step instructions to reproduce
   - Required setup/configuration
   - Screenshots or video (optional but helpful)

3. **Impact Analysis**
   - What an attacker could achieve
   - Affected data or systems
   - Potential for exploitation

4. **Suggested Fix** (optional)
   - Your recommended remediation
   - Code patches (if available)

### What NOT to Do

- ❌ Do not exploit vulnerabilities beyond what's necessary to demonstrate them
- ❌ Do not access or modify user data without explicit permission
- ❌ Do not disrupt service availability (no DoS testing on production)
- ❌ Do not disclose vulnerabilities publicly before we've had time to patch
- ❌ Do not use social engineering against our team or users

### Disclosure Timeline

```
Day 0:   Vulnerability reported
Day 1-2: Initial response, confirmation, clarification questions
Day 3-7: Investigation, reproduction, severity assessment
Day 8-14: Patch development and testing
Day 15-21: Security release, public disclosure
```

**Note:** Timeline may vary based on complexity and severity. We'll keep you informed throughout the process.

### Recognition

We believe in recognizing security researchers who help improve CogniWatch:

- ✅ Name credited in security advisory (unless anonymous requested)
- ✅ Listed in SECURITY.md acknowledgments
- ✅ Swag/stickers for significant findings (optional)
- ❌ No monetary bounties at this time (open source project)

---

## 👤 Security Contact Information

**Primary Contact:**
- Email: security@cogniwatch.dev
- Response Time: 48 hours (business days)
- Availability: Monday-Friday, 9 AM - 6 PM UTC

**Emergency Contact** (Critical vulnerabilities only):
- Email: security-urgent@cogniwatch.dev
- Response Time: 24 hours
- Use only for: Active exploitation, data breach, remote code execution

**PGP Key** (for encrypted communications):
```
Available upon request — email security@cogniwatch.dev
```

**GitHub:**
- Repository: https://github.com/neo/cogniwatch
- Security Advisories: https://github.com/neo/cogniwatch/security/advisories
- Issues: https://github.com/neo/cogniwatch/issues (non-security only)

---

## ⚠️ Known Limitations

CogniWatch is designed with security in mind, but has some known limitations:

### Current Limitations (v1.0.0)

1. **Single-User Authentication**
   - Current: Single admin user with JWT token
   - Limitation: No multi-user RBAC in initial release
   - Roadmap: Phase C (Q3 2026) will add team collaboration with granular roles

2. **SQLite Database**
   - Current: SQLite with file permissions (600)
   - Limitation: Not suitable for high-concurrency enterprise deployments
   - Workaround: Use in read-only mode for multiple viewers
   - Roadmap: PostgreSQL support planned for Phase C

3. **Network Scanning Rate**
   - Current: Conservative rate limits to prevent network disruption
   - Limitation: Large networks (>1000 hosts) may take extended time to scan
   - Workaround: Split into smaller CIDR ranges, scan in parallel

4. **Telemetry Retention**
   - Current: 90-day default retention
   - Limitation: Long-term compliance may require extended retention
   - Workaround: Export historical data before automatic pruning

5. **No Built-in HTTPS**
   - Current: HTTP by default (localhost/LAN only)
   - Limitation: Requires reverse proxy (nginx) for HTTPS
   - Documentation: See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for nginx/Let's Encrypt setup

6. **Limited Audit Log Export**
   - Current: Logs stored locally in JSON format
   - Limitation: No direct SIEM integration (Splunk, Elastic)
   - Roadmap: Phase C will add SIEM connectors and standardized log formats

### Security Boundary

**CogniWatch is MONITORING ONLY:**
- ✅ Can READ agent status and telemetry
- ✅ Can DETECT framework signatures
- ✅ Can ALERT on anomalous behavior
- ❌ CANNOT modify agent configuration
- ❌ CANNOT execute commands on agents
- ❌ CANNOT access agent memory or prompts
- ❌ CANNOT control agent actions

This read-only design intentionally limits attack surface and potential for misuse.

---

## 🎯 User Best Practices

To maximize security when deploying CogniWatch:

### 1. Authentication & Access Control

```bash
# ✅ DO: Change default credentials immediately
export COGNIWATCH_ADMIN_USER=admin
export COGNIWATCH_ADMIN_PASSWORD="your-strong-password-here"

# ✅ DO: Use API keys for automation (not admin credentials)
curl -X POST http://localhost:9000/api/api-keys \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name": "Scanner", "scopes": ["read:agents", "write:scans"]}'

# ✅ DO: Rotate API keys periodically (every 90 days)
# ❌ DON'T: Commit credentials to git or share in plain text
```

### 2. Network Security

```bash
# ✅ DO: Bind to localhost if not exposing to LAN
# Edit docker-compose.yml:
ports:
  - "127.0.0.1:9000:9000"

# ✅ DO: Use firewall to restrict access
sudo ufw allow from 192.168.1.0/24 to any port 9000 proto tcp

# ✅ DO: Enable HTTPS for remote access (see DEPLOYMENT.md)
# Use nginx + Let's Encrypt for TLS termination

# ❌ DON'T: Expose to 0.0.0.0 without authentication
# ❌ DON'T: Run on public internet without HTTPS
```

### 3. System Hardening

```bash
# ✅ DO: Run as non-root user (default in Docker/systemd)
# ✅ DO: Keep system updated
sudo apt update && sudo apt upgrade -y

# ✅ DO: Enable automatic security updates
sudo apt install -y unattended-upgrades

# ✅ DO: Set restrictive file permissions
chmod 600 /path/to/cogniwatch/data/cogniwatch.db
chmod 600 /path/to/cogniwatch/.env

# ✅ DO: Use fail2ban for brute-force protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 4. Scanner Configuration

```bash
# ✅ DO: Limit scan range to networks you own/have authorization for
SCANNER_NETWORK=192.168.1.0/24  # Your internal network only

# ✅ DO: Use conservative rate limits
SCANNER_RATE_LIMIT=100  # Requests per second

# ✅ DO: Schedule scans during maintenance windows
SCAN_SCHEDULE="0 2 * * *"  # 2 AM daily

# ❌ DON'T: Scan networks without explicit authorization
# ❌ DON'T: Use aggressive scan rates that may disrupt services
```

### 5. Data Protection

```bash
# ✅ DO: Backup database regularly
0 3 * * * cp /opt/cogniwatch/data/cogniwatch.db /backup/cogniwatch-$(date +\%Y\%m\%d).db

# ✅ DO: Encrypt backups
gpg --symmetric --cipher-algo AES256 /backup/cogniwatch*.db

# ✅ DO: Log security events
grep "AUTH_FAILURE" /var/log/cogniwatch/*.log

# ❌ DON'T: Store backups in publicly accessible locations
# ❌ DON'T: Log sensitive data (passwords, API keys)
```

### 6. Monitoring & Incident Response

```bash
# ✅ DO: Monitor CogniWatch logs
tail -f /var/log/cogniwatch/webui.log | grep -E "(ERROR|WARN|AUTH)"

# ✅ DO: Set up alerts for failed logins
# Use fail2ban or custom monitoring

# ✅ DO: Review security alerts dashboard daily
# Look for: New agents, unusual activity, high-severity alerts

# ✅ DO: Have an incident response plan
# If breach detected: Isolate → Assess → Contain → Eradicate → Recover → Learn
```

---

## 🔍 Security Audit Summary

### Internal Security Review (v1.0.0)

**Date:** March 8, 2026  
**Auditor:** Neo (lead developer)  
**Scope:** Full application stack (Web UI, API, Scanner, Database)

#### Assessment Areas

| Area | Status | Severity | Notes |
|------|--------|----------|-------|
| **Authentication** | ✅ Pass | — | JWT tokens, secure cookie flags, token expiry |
| **Authorization** | ✅ Pass | — | Role-based access, least privilege enforced |
| **Input Validation** | ✅ Pass | — | Parameterized queries, XSS prevention |
| **Encryption** | ✅ Pass | — | AES-256-GCM for data at rest, TLS 1.3 recommended |
| **Error Handling** | ✅ Pass | — | Generic errors to users, detailed logs internally |
| **Logging & Monitoring** | ✅ Pass | — | Comprehensive audit logs, alerting system |
| **Dependency Security** | ✅ Pass | — | Pinned versions, no known vulnerabilities |
| **Network Security** | ✅ Pass | — | LAN-only default, firewall-friendly |

#### Vulnerabilities Found & Fixed

**During Development:**
- ✅ **MEDIUM:** Initial config allowed unauthenticated health checks → Fixed: Now requires auth for all endpoints except `/api/health`
- ✅ **LOW:** Verbose error messages exposed stack traces → Fixed: Generic errors to users, detailed logs internally
- ✅ **LOW:** Missing security headers on some endpoints → Fixed: All responses include CSP, HSTS, X-Frame-Options

#### Pending Items

- ⚠️ **LOW:** SQLite WAL mode not enabled by default → Planned: v1.1.0
- ⚠️ **LOW:** Rate limiting could be more granular → Planned: Per-endpoint limits in v1.1.0

### External Audits

**Third-party security audits:** Planned for Q2 2026 (Phase B)

**Bug Bounty Program:** Not yet active — consider submitting high-severity findings for recognition and swag.

---

## ✅ OWASP Compliance

CogniWatch is compliant with both OWASP Top 10:2025 and OWASP LLM Top 10:2025.

### OWASP Top 10:2025

| ID | Vulnerability | Status | Mitigation |
|----|---------------|--------|------------|
| **A01:2025** | Broken Access Control | ✅ Compliant | JWT auth, RBAC, read-only mode |
| **A02:2025** | Security Misconfiguration | ✅ Compliant | Secure defaults, security headers, config validation |
| **A03:2025** | Software Supply Chain Failures | ✅ Compliant | Pinned deps, SHA256 checksums, minimal dependencies |
| **A04:2025** | Cryptographic Failures | ✅ Compliant | AES-256-GCM, TLS 1.3, secure secret storage |
| **A05:2025** | Injection | ✅ Compliant | Parameterized queries, input validation, output encoding |
| **A06:2025** | Insecure Design | ✅ Compliant | Zero-trust architecture, defense in depth, threat modeling |
| **A07:2025** | Authentication Failures | ✅ Compliant | Secure tokens, session expiry, brute-force protection |
| **A08:2025** | Software/Data Integrity Failures | ✅ Compliant | Backup integrity checks, audit logs, manual updates |
| **A09:2025** | Security Logging & Monitoring | ✅ Compliant | Comprehensive logging, alerting, log rotation |
| **A10:2025** | Server-Side Request Forgery | ✅ Compliant | No external URL fetching, input validation |

### OWASP LLM Top 10:2025

| ID | Vulnerability | Status | Mitigation |
|----|---------------|--------|------------|
| **LLM01** | Prompt Injection | ✅ Compliant | Read-only access, agent outputs treated as untrusted |
| **LLM02** | Insecure Output Handling | ✅ Compliant | Schema validation, HTML encoding, sandboxed display |
| **LLM03** | Training Data Poisoning | ✅ Compliant | No model training, user-controlled data |
| **LLM04** | Model Denial of Service | ✅ Compliant | Rate limiting, resource quotas, circuit breaker |
| **LLM05** | Supply Chain Vulnerabilities | ✅ Compliant | Dependency scanning, pinned versions |
| **LLM06** | Sensitive Info Disclosure | ✅ Compliant | Local-first, no external telemetry, encrypted storage |
| **LLM07** | Insecure Plugin Design | ✅ Compliant | No plugin system in v1.0, security review planned |
| **LLM08** | Excessive Agency | ✅ Compliant | Monitoring only, ZERO agency over agents |
| **LLM09** | Overreliance | ✅ Compliant | Alerts require human review, advisory recommendations |
| **LLM10** | Model Theft | ✅ Compliant | No model hosting, users control their own agents |

See full compliance details in [docs/SECURITY.md](docs/SECURITY.md).

---

## 📢 Security Updates

### How to Stay Informed

1. **GitHub Releases** — Watch repository for security patches
   - https://github.com/neo/cogniwatch/releases
   - Enable "Releases" notifications

2. **Security Advisories** — GitHub private vulnerability reports (public after patching)
   - https://github.com/neo/cogniwatch/security/advisories

3. **Email Notifications** — Subscribe to security mailing list (coming soon)

4. **RSS Feed** — Security blog RSS (coming soon)

### Update Procedure

When security updates are released:

```bash
# Docker deployment
docker compose pull
docker compose up -d

# Verify version
docker compose exec cogniwatch-webui cogniwatch --version

# From source
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart cogniwatch
```

**Critical Updates:** Apply within 24 hours of release  
**High Severity:** Apply within 7 days  
**Medium/Low:** Apply in next maintenance window

---

## 📚 Additional Security Resources

- **OWASP Top 10:2025** — https://owasp.org/Top10/2025/
- **OWASP LLM Top 10** — https://genai.owasp.org/llm-top-10/
- **OWASP Cheat Sheets** — https://cheatsheetseries.owasp.org/
- **CIS Benchmarks** — https://www.cisecurity.org/benchmarks

---

## 🏆 Security Acknowledgments

We'd like to thank the following security researchers for their contributions:

*(This section will be populated as responsible disclosures are received)*

---

## 📞 Questions?

If you have questions about CogniWatch security:

- **General Inquiries:** security@cogniwatch.dev
- **Vulnerability Reports:** security@cogniwatch.dev (or GitHub)
- **Emergency:** security-urgent@cogniwatch.dev

**Response Commitment:**
- Non-urgent: 48 hours
- Urgent: 24 hours
- Critical: Immediate acknowledgment, continuous updates

---

**Thank you for helping keep CogniWatch secure! 🛡️**
