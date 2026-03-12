# CogniWatch Security Hardening - 2026-03-08

**Status:** ✅ **AUTHENTICATION ENABLED**  
**Before public scan:** API endpoints protected  
**Date:** 2026-03-08 02:30 UTC

---

## 🔐 Authentication System

### Enabled: **TOKEN-BASED AUTH**

**Configuration:** `/home/neo/cogniwatch/config/cogniwatch.json`

### API Tokens:

| Token | Role | Permissions | Use Case |
|-------|------|-------------|----------|
| `cogniwatch-admin-2026` | admin | read, write, admin | Full access |
| `cogniwatch-readonly` | viewer | read | Dashboard viewing |

### API Usage:

```bash
# Without auth → 401 Unauthorized
curl http://192.168.0.245:9000/api/agents
# Response: {"error": "Unauthorized", "message": "Valid API token required"}

# With auth → Success
curl -H "Authorization: Bearer cogniwatch-admin-2026" http://192.168.0.245:9000/api/agents
# Response: {"agents": [...], "total": 5}
```

### Protected Endpoints:

- ✅ `/api/agents` - List discovered agents
- ✅ `/api/scan/status` - Scan progress
- ✅ `/api/agents/activity` - Activity feed
- ✅ `/` - Dashboard (HTML access not restricted for UI usability)

---

## 🛡️ Security Features

### 1. Token Validation
- Bearer token in Authorization header
- Tokens stored in config (not hardcoded)
- Role-based permissions

### 2. Rate Limiting (Configured)
```json
"rate_limiting": {
  "enabled": true,
  "requests_per_minute": 60
}
```

### 3. CORS Protection
```json
"cors": {
  "enabled": true,
  "allow_origins": ["http://127.0.0.1:9000", "http://192.168.0.245:9000"]
}
```

---

## 🔥 VPS Deployment Checklist

Before deploying to public internet:

- [x] ✅ Authentication enabled
- [ ] ⏳ HTTPS/SSL configured (Let's Encrypt)
- [ ] ⏳ Rate limiting enforced
- [ ] ⏳ UFW firewall configured
- [ ] ⏳ Fail2ban installed
- [ ] ⏳ Admin token changed from default
- [ ] ⏳ Database credentials secured

---

## 🚨 Post-Deployment Actions

1. **Change default tokens** immediately after deployment
2. **Enable HTTPS** (Certbot/Let's Encrypt)
3. **Configure firewall** (UFW - allow 443, 9000 from trusted IPs only)
4. **Monitor access logs** for suspicious activity
5. **Rotate tokens** monthly

---

## 📝 Production Token Management

For VPS deployment, create environment-specific tokens:

```bash
# Generate secure token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: e.g., "xK9mN2pQ7vR4sT8wY3zA6bC1dE5fG0hI"
```

Add to config:
```json
"tokens": {
  "your-secure-token-here": {
    "role": "admin",
    "permissions": ["read", "write", "admin"]
  }
}
```

---

**Current Status:** Ready for internet scan (auth enabled)  
**Next:** HTTPS + firewall + hardened tokens for VPS

🦈🔐
