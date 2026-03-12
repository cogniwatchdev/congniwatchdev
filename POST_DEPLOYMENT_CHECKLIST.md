# 🦈 CogniWatch - POST-DEPLOYMENT CHECKLIST

**Document Type:** Operational checklist for first 30 days after VPS deployment  
**Version:** 1.0.0  
**Last Updated:** 2026-03-07 07:25 UTC  
**Applicable To:** v1.0.0 production deployments  

---

## Quick Reference

| Phase | Timeframe | Key Actions | Success Criteria |
|-------|-----------|-------------|------------------|
| **T-0** | Pre-deployment | VPS provision, run deploy script | All services green |
| **First 24h** | Hour 0-24 | Verify, monitor, first scan | 100% uptime, clean logs |
| **First Week** | Day 1-7 | Daily checks, trend analysis | No critical alerts |
| **First Month** | Week 2-4 | Security review, optimization | Ready for public launch |

---

## 🚀 Pre-Deployment (T-Minus)

### Infrastructure Readiness

- [ ] VPS provisioned (Vultr High Performance $12/mo or equivalent)
  - [ ] 1 vCPU / 2GB RAM / 50GB NVMe
  - [ ] Ubuntu 22.04 LTS or 24.04 LTS
  - [ ] Static/reserved IP assigned
- [ ] Domain DNS configured
  - [ ] A record: `cogniwatch.yourdomain.com` → VPS IP
  - [ ] Wait for DNS propagation (check: `dig cogniwatch.yourdomain.com`)
- [ ] SSH keys generated and secured
  - [ ] Private key: `chmod 600`
  - [ ] Public key deployed to VPS
  - [ ] Password authentication disabled on VPS

### Deployment Script Prep

- [ ] Download deployment artifacts to local machine:
  - [ ] `docker-compose.production.yml`
  - [ ] `deploy-vultr.sh`
  - [ ] `backup-automation.sh`
  - [ ] `.env.production.example`
  - [ ] `nginx/nginx.conf` template
- [ ] Review and customize `.env.production`:
  - [ ] `DOMAIN_NAME=cogniwatch.yourdomain.com`
  - [ ] `DB_PASSWORD=<random 32-char string>`
  - [ ] `JWT_SECRET=<random 32-char hex>`
  - [ ] `API_KEY=<random 40-char hex>`
  - [ ] `ENCRYPTION_KEY=<random 32-char hex>`
  - [ ] `SCANNER_NETWORK=<your target network>` (default: 192.168.0.0/24)
- [ ] Test deployment script syntax:
  ```bash
  bash -n deploy-vultr.sh  # Should produce no output
  ```

### Rollback Prep

- [ ] Document current state (snapshots, backups)
- [ ] Keep Vultr dashboard accessible
- [ ] Have rollback script ready: `./deployment/ROLLBACK.md`
- [ ] Emergency contacts list available

---

## ✅ Deployment Day (T-0)

### Step 1: Run Deployment Script

```bash
# SSH into VPS
ssh -i /path/to/private/key root@YOUR_VPS_IP

# Upload deployment script
scp -i /path/to/private/key deploy-vultr.sh root@YOUR_VPS_IP:/root/

# Run deployment (takes ~15 minutes)
bash /root/deploy-vultr.sh cogniwatch.yourdomain.com
```

- [ ] Script completes without errors
- [ ] Docker Compose services started
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Firewall configured (UFW: 22, 80, 443)

### Step 2: Verify Deployment

```bash
# Check all services running
docker compose ps

# Expected output:
# NAME                   STATUS         PORTS
# cogniwatch-app         Up (healthy)   3000/tcp
# cogniwatch-db          Up (healthy)   5432/tcp
# cogniwatch-nginx       Up             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# cogniwatch-certbot     Up
# cogniwatch-monitor     Up             0.0.0.0:9000->3001/tcp
# cogniwatch-redis       Up (healthy)   6379/tcp
```

- [ ] All services show "Up" or "Up (healthy)"
- [ ] No "Restarting" or "Exited" containers

### Step 3: HTTPS Verification

```bash
# Test HTTPS (should redirect HTTP → HTTPS)
curl -I http://cogniwatch.yourdomain.com

# Expected: 301 redirect to https://

# Test HTTPS directly
curl -I https://cogniwatch.yourdomain.com

# Expected: 200 OK with valid SSL certificate
```

- [ ] HTTP redirects to HTTPS
- [ ] HTTPS returns 200 OK
- [ ] SSL certificate valid (check: `curl -v https://...`)
- [ ] Certificate issued by Let's Encrypt

### Step 4: Dashboard Access

```bash
# Access dashboard in browser
open https://cogniwatch.yourdomain.com
```

- [ ] Dashboard loads successfully
- [ ] Login page appears (JWT authentication required)
- [ ] No console errors in browser DevTools
- [ ] UI responsive and styled correctly

### Step 5: API Authentication

```bash
# Get JWT token
curl -X POST https://cogniwatch.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"api_key": "<YOUR_API_KEY>"}'

# Expected: JWT token returned
```

- [ ] API returns JWT token
- [ ] Token is valid (decode at https://jwt.io)
- [ ] Expiry set correctly (24 hours from issue)

### Step 6: First Network Scan

```bash
# Trigger scan via API
curl -X POST https://cogniwatch.yourdomain.com/api/scan \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Or use dashboard UI: Click "Start Scan"
```

- [ ] Scan initiated successfully
- [ ] Scan progress visible in dashboard
- [ ] Scan completes (check `/api/scan/status`)
- [ ] Results stored in database

### Step 7: Monitoring Setup

```bash
# Access Uptime Kuma monitoring
open http://YOUR_VPS_IP:9000
```

- [ ] Uptime Kuma dashboard accessible
- [ ] Add monitor for `https://cogniwatch.yourdomain.com/health`
- [ ] Configure notification (email, Slack, Discord, etc.)
- [ ] Test notification (send test alert)

### Step 8: Backup Verification

```bash
# Check backup automation configured
cat /etc/cron.d/cogniwatch-backup

# Expected: Cron job scheduled for 02:00 UTC daily
```

- [ ] Cron job exists
- [ ] Backup directory writable
- [ ] Test backup manually:
  ```bash
  cd /home/cogniwatch/deployment
  ../backups/backup-automation.sh
  ```
- [ ] Backup file created in `/home/cogniwatch/backups/database/`

### Step 9: Security Hardening Check

```bash
# Check Fail2ban active
sudo fail2ban-client status

# Check UFW firewall
sudo ufw status verbose

# Check automatic updates enabled
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

- [ ] Fail2ban running with sshd jail active
- [ ] UFW allows only ports 22, 80, 443
- [ ] Automatic security updates enabled

### Step 10: Log Review

```bash
# Application logs
docker compose logs --tail=100 cogniwatch

# Nginx logs
docker compose logs --tail=50 nginx

# Database logs
docker compose logs --tail=50 postgres
```

- [ ] No ERROR or CRITICAL level logs
- [ ] No stack traces or exceptions
- [ ] Startup messages normal
- [ ] No authentication failures

---

## 📊 First 24 Hours (Hour 0-24)

### Hour 1: Initial Watch

- [ ] Monitor dashboard for errors or crashes
- [ ] Check `docker stats` for resource usage
- [ ] Verify no restart loops
- [ ] Confirm SSL certificate valid (Grade A+ at https://www.ssllabs.com/ssltest/)

```bash
# Resource check
docker stats --no-stream

# Expected:
# - CPU: <50% sustained
# - RAM: <1.5GB / 2GB
```

### Hour 2-6: Stabilization

- [ ] Review first scan results
- [ ] Validate detection quality (check confidence scores)
- [ ] Monitor API response times via Uptime Kuma
- [ ] Check disk usage growth rate

```bash
# Disk usage
df -h

# Expected growth: <1GB in first 6 hours
```

### Hour 6-12: Pattern Analysis

- [ ] Check log patterns for anomalies
- [ ] Review any failed authentication attempts
- [ ] Verify backup automation still scheduled
- [ ] Monitor network I/O for unusual spikes

```bash
# Check Fail2ban for blocked IPs
sudo fail2ban-client get sshd banned
```

### Hour 12-24: First Full Day

- [ ] Survived first full day without downtime
- [ ] First automated backup completed at 02:00 UTC
- [ ] Uptime: 100% (or document any outages)
- [ ] Resource usage stable (no memory leaks)

```bash
# Verify backup completed
ls -lt /home/cogniwatch/backups/database/
# Should see new backup from 02:00 UTC

# Check uptime
uptime
# Should show >24 hours
```

**End of Day 1 Checklist:**
- [ ] ✅ Uptime ≥99%
- [ ] ✅ No data loss
- [ ] ✅ Backups working
- [ ] ✅ Monitoring active
- [ ] ✅ Logs clean

---

## 📅 First Week (Day 1-7)

### Daily Tasks (Repeat Days 1-7)

**Each Morning:**
- [ ] Check Uptime Kuma dashboard (no overnight incidents)
- [ ] Review overnight logs (scroll last 200 lines)
- [ ] Verify disk usage (<70% threshold)
- [ ] Check for security updates available

```bash
# Quick health check (copy-paste)
docker compose ps && docker stats --no-stream && df -h /
```

**Each Evening:**
- [ ] Review daily scan results
- [ ] Check detection confidence trends
- [ ] Monitor API error rate (should be <1%)

### Day 3: Mid-Week Review

- [ ] Analyze 3-day scan data trends
- [ ] Check for any repeated detection false positives
- [ ] Review Fail2ban logs for patterns
- [ ] Validate SSL certificate still valid (89 days remaining)

```bash
# Check certificate expiry
echo | openssl s_client -connect cogniwatch.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Day 5: Performance Baseline

- [ ] Document baseline metrics:
  - Average API response time: _____ ms
  - Average scan duration: _____ seconds
  - Average RAM usage: _____ MB
  - Average CPU usage: _____ %
  - Daily disk growth: _____ MB
- [ ] Compare against targets in `DEPLOYMENT_READINESS_REPORT.md`
- [ ] Identify any performance degradation

### Day 7: End-of-Week Summary

- [ ] Full week completed without critical incidents
- [ ] Calculate weekly uptime: _____ % (target: ≥99.5%)
- [ ] Total agents detected: _____
- [ ] Total scans completed: _____
- [ ] Average detection confidence: _____ %
- [ ] Total API calls: _____
- [ ] Backup success rate: _____ % (should be 100%)

**End of Week 1 Decision Point:**
- [ ] ✅ System stable → Proceed to Month 1
- [ ] ⚠️ Issues present → Troubleshoot before scaling

---

## 📆 First Month (Week 2-4)

### Week 2: Security Focus

- [ ] Review security logs for intrusion attempts
- [ ] Check Fail2ban effectiveness (blocked IPs: _____)
- [ ] Verify no unauthorized API access
- [ ] Review OWASP Top 10 compliance (quarterly audit prep)
- [ ] Test rate limiting (60 req/min limit working?)

```bash
# Review auth logs
grep "Failed password" /var/log/auth.log | tail -20

# Check Nginx access logs for suspicious patterns
docker compose logs nginx | grep -E "(403|401|429)" | tail -50
```

### Week 3: Optimization

- [ ] Analyze slowest API endpoints (optimize if p95 >200ms)
- [ ] Review database query performance
- [ ] Check for unused or stale data
- [ ] Optimize scanner configuration (interval, parallelism)
- [ ] Consider adding Redis caching if API slow

```bash
# Check slow queries (if enabled in Postgres)
docker compose exec postgres psql -U cogniwatch_admin -d cogniwatch -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Week 4: Month-End Audit

- [ ] Calculate monthly uptime: _____ % (target: ≥99.5%)
- [ ] Total agents discovered: _____
- [ ] Total scans completed: _____
- [ ] Average detection accuracy (field validation): _____ %
- [ ] Total API calls: _____
- [ ] Peak concurrent users: _____
- [ ] Storage used: _____ GB / 50 GB (target: <40%)

**Security Audit (Monthly):**
- [ ] Review all user access (revoke unused API keys)
- [ ] Check SSL certificate expiry (≥60 days remaining)
- [ ] Verify automatic updates applied
- [ ] Test backup restoration procedure
  ```bash
  # Test restore on staging or isolated environment
  cd /home/cogniwatch/deployment
  ../backups/backup-automation.sh --list
  ../backups/backup-automation.sh --restore <backup_file>
  ```

### Month-End Decision: Public Launch?

**Criteria:**
- [ ] Uptime ≥99.5% for 30 days
- [ ] Zero data loss incidents
- [ ] Detection accuracy ≥85% (field validated)
- [ ] No critical security vulnerabilities
- [ ] Backup restoration tested successfully
- [ ] Monitoring and alerting functioning

If all ✅: **GREEN LIGHT FOR PUBLIC LAUNCH**

---

## 🔍 Troubleshooting Quick Reference

### Service Won't Start

```bash
# Check container logs
docker compose logs cogniwatch

# Restart service
docker compose restart cogniwatch

# Check database connection
docker compose exec postgres pg_isready
```

### Database Issues

```bash
# Check database logs
docker compose logs postgres

# Verify database accessible
docker compose exec postgres psql -U cogniwatch_admin -d cogniwatch -c "SELECT 1;"

# Restart database (preserves data volumes)
docker compose restart postgres
```

### SSL Certificate Issues

```bash
# Force certificate renewal
docker compose run --rm certbot renew --force-renewal

# Restart Nginx to pick up new cert
docker compose restart nginx
```

### High Resource Usage

```bash
# Identify resource hogs
docker stats

# Check disk usage
docker system df

# Clean Docker resources (careful!)
docker system prune -af
```

### Rollback Emergency

```bash
# Stop all services
cd /home/cogniwatch/deployment
docker compose down

# Follow rollback procedure
cat ROLLBACK.md
```

---

## 📞 Support & Escalation

**During First 30 Days:**

| Issue Type | Response Time | Contact |
|------------|---------------|---------|
| Service Down | Immediate | On-call admin |
| Security Incident | Immediate | Security team |
| Performance Degradation | <4 hours | Dev team |
| Feature Request | Next sprint | GitHub Issues |

**Resources:**
- **Deployment Guide:** `/home/neo/cogniwatch/DEPLOYMENT.md`
- **Rollback Procedures:** `/home/neo/cogniwatch/deployment/ROLLBACK.md`
- **Known Issues:** `/home/neo/cogniwatch/KNOWN_ISSUES_REGISTER.md`
- **Security Audit:** `/home/neo/cogniwatch/SECURITY_AUDIT.md`
- **GitHub Issues:** https://github.com/neo/cogniwatch/issues
- **Security Reports:** security@cogniwatch.io

---

## ✅ 30-Day Success Criteria

**Technical:**
- [ ] Uptime ≥99.5% (allowed downtime: <3.6 hours/month)
- [ ] Zero data loss (all backups successful)
- [ ] API response time p95 <200ms
- [ ] Detection accuracy ≥85%
- [ ] Storage usage <40% (20GB / 50GB)

**Operational:**
- [ ] Monitoring configured and tested
- [ ] Backup restoration verified
- [ ] Security audit completed
- [ ] Documentation updated with learnings
- [ ] Team trained on troubleshooting

**Business:**
- [ ] Ready for public announcement
- [ ] Community prepared for launch (social media, docs)
- [ ] Support capacity adequate for expected load
- [ ] Roadmap v0.3.1 prioritized based on field data

---

**Checklist Status Tracker:**

| Milestone | Date | Status | Notes |
|-----------|------|--------|-------|
| Deployment Complete | _______ | ⬜ | |
| 24-Hour Watch Passed | _______ | ⬜ | |
| Week 1 Review | _______ | ⬜ | |
| Month 1 Audit | _______ | ⬜ | |
| Public Launch | _______ | ⬜ | |

---

*"Stay watchful. Trace every thought."* 🦈

**Last Updated:** 2026-03-07 07:25 UTC  
**Version:** 1.0.0  
**Next Review:** After v0.3.1 release
