# CogniWatch VPS Deployment Recommendations

**Generated:** March 7, 2026  
**Purpose:** Optimal VPS deployment strategy for CogniWatch production deployment

---

## 1. Provider Comparison Table

| Provider | Plan | vCPU | RAM | Disk | Bandwidth | Monthly Cost | Locations | Docker Setup | SLA | Notes |
|----------|------|------|-----|------|-----------|--------------|-----------|--------------|-----|-------|
| **DigitalOcean** | Basic Droplet | 1 | 1GB | 25GB | 1TB | $6 | US, EU, Asia, SA | 1-click marketplace | 99.99% | Best developer experience, excellent docs |
| **DigitalOcean** | Basic Droplet | 1 | 2GB | 50GB | 2TB | $12 | US, EU, Asia, SA | 1-click marketplace | 99.99% | Recommended for headroom |
| **Vultr** | Cloud Compute (Regular) | 1 | 1GB | 25GB SSD | 1TB | $5 | 32 locations global | 1-click marketplace | 99.99% | Cheapest option, NVMe standard |
| **Vultr** | High Performance | 1 | 2GB | 50GB NVMe | 2TB | $12 | 32 locations global | 1-click marketplace | 99.99% | Great performance/price |
| **Linode (Akamai)** | Shared CPU | 1 | 1GB | 25GB | 1TB | ~$5 | US, EU, Asia | 1-click marketplace | 99.9% | Solid performer |
| **Linode (Akamai)** | Shared CPU | 1 | 2GB | 50GB | 2TB | ~$10 | US, EU, Asia | 1-click marketplace | 99.9% | Good middle ground |
| **AWS** | EC2 t3.micro | 2 | 1GB | EBS extra | N/A | ~$7.59 | Global | Manual setup | 99.99% | More complex, overkill for this use |
| **AWS** | EC2 t3.small | 2 | 2GB | EBS extra | N/A | ~$15.18 | Global | Manual setup | 99.99% | Expensive for needs |
| **Google Cloud** | e2-micro | 2 (shared) | 1GB | Persistent extra | N/A | ~$6.11 | Global | Manual setup | 99.95% | Free tier eligible regions |
| **Google Cloud** | e2-small | 2 (shared) | 2GB | Persistent extra | N/A | ~$12.23 | Global | Manual setup | 99.95% | $300 free credits (90 days) |
| **Oracle Cloud** | Always Free (A1) | 4 (ARM) | 24GB | 200GB | 10TB | **FREE** | US, EU, Asia | Manual setup | 99.95% | Best value IF available (often out of stock) |
| **Hetzner** | CX23 | 2 | 4GB | 40GB | 20TB | ~$4.09 | EU (DE/FI), US, SG | Manual setup | 99.9% | Cheapest EU option, excellent value |
| **Hetzner** | CPX11 | 2 | 2GB | 80GB | 20TB | ~$6.49 | EU (DE/FI), US, SG | Manual setup | 99.9% | Great EU production option |

### Support Quality Summary:
- **DigitalOcean:** ⭐⭐⭐⭐⭐ Excellent docs, community, 24/7 ticket support
- **Vultr:** ⭐⭐⭐⭐ Good docs, responsive support, active community
- **Linode:** ⭐⭐⭐⭐ Strong docs, good support (now Akamai)
- **AWS:** ⭐⭐⭐ Complex, enterprise-focused (free tier = minimal support)
- **Google Cloud:** ⭐⭐⭐ Enterprise-focused, steep learning curve
- **Oracle Cloud:** ⭐⭐ Poor support for free tier, complex UI
- **Hetzner:** ⭐⭐⭐ Good value, EU-focused support, slower response times

---

## 2. CogniWatch Resource Requirements

### Current Usage Profile:
- **RAM Baseline:** ~220MB (Scanner 100MB + Detector 50MB + DB 20MB + Web UI 50MB)
- **CPU Usage:** 10-20% single core during scans, <5% idle
- **Disk:** ~10MB per 10K agents (SQLite), logs ~100MB/month
- **Bandwidth:** ~500MB/month for daily scans + variable API usage

### Minimum Viable Spec:
```
vCPU: 1 core (shared is fine)
RAM: 512MB absolute minimum, 1GB recommended
Disk: 20GB minimum (allows growth to ~50K agents)
Bandwidth: 500GB/month minimum
```

### Recommended Spec:
```
vCPU: 1-2 cores
RAM: 2GB (gives 9x headroom over baseline)
Disk: 40-50GB NVMe/SSD
Bandwidth: 1-2TB/month
```

### Why 2GB RAM?
- Allows for OS overhead (~200-300MB on minimal Linux)
- Provides buffer for memory spikes during scans
- Room for future features (caching, more agents)
- Prevents OOM kills during unexpected load
- Cost difference is minimal ($6 vs $12/month)

---

## 3. Total Cost of Ownership (TCO)

### Scenario A: Vultr Cloud Compute (1 vCPU / 2GB / 50GB NVMe)
**Base Cost:** $12/month

| Timeframe | VPS Cost | Domain | SSL | Backups (5GB B2) | Monitoring | Total |
|-----------|----------|--------|-----|------------------|------------|-------|
| **6 months** | $72 | $12 | $0 | $3 | $0 (Uptime Robot free) | **$87** |
| **12 months** | $144 | $12 | $0 | $6 | $0 (Uptime Robot free) | **$162** |

### Scenario B: DigitalOcean Basic (1 vCPU / 2GB / 50GB)
**Base Cost:** $12/month

| Timeframe | VPS Cost | Domain | SSL | Backups (5GB B2) | Monitoring | Total |
|-----------|----------|--------|-----|------------------|------------|-------|
| **6 months** | $72 | $12 | $0 | $3 | $0 | **$87** |
| **12 months** | $144 | $12 | $0 | $6 | $0 | **$162** |

### Scenario C: Hetzner CPX11 (2 vCPU / 2GB / 80GB) - EU
**Base Cost:** ~$6.49/month

| Timeframe | VPS Cost | Domain | SSL | Backups (5GB B2) | Monitoring | Total |
|-----------|----------|--------|-----|------------------|------------|-------|
| **6 months** | $39 | $12 | $0 | $3 | $0 | **$54** |
| **12 months** | $78 | $12 | $0 | $6 | $0 | **$96** |

### Scenario D: Oracle Cloud Always Free (4 ARM / 24GB) - IF AVAILABLE
**Base Cost:** $0/month

| Timeframe | VPS Cost | Domain | SSL | Backups (5GB B2) | Monitoring | Total |
|-----------|----------|--------|-----|------------------|------------|-------|
| **6 months** | $0 | $12 | $0 | $3 | $0 | **$15** |
| **12 months** | $0 | $12 | $0 | $6 | $0 | **$18** |

**Notes:**
- Domain: ~$12/year (Cloudflare at-cost, Namecheap, Porkbun)
- SSL: Let's Encrypt = FREE (auto-renew via certbot)
- Backups: Backblaze B2 ~$0.60/GB/month = ~$3/month for 5GB
- Monitoring: Uptime Robot free tier = 50 monitors, 5-min intervals

---

## 4. Deployment Checklist

### Pre-Deployment
- [ ] **VPS provisioned** - Select provider, create instance
- [ ] **SSH keys configured** - `ssh-copy-id` or provider console
- [ ] **Firewall rules (UFW) applied** - Only ports 22, 80, 443 open
- [ ] **Domain pointed to VPS** - Update DNS A record, wait for propagation

### Deployment
- [ ] **Docker installed** - `curl -fsSL https://get.docker.com | sh`
- [ ] **SSL certificate obtained** - Use certbot or Caddy auto-SSL
- [ ] **CogniWatch deployed (docker compose)** - `docker compose up -d`
- [ ] **Health check passing** - Verify all containers running, API responding
- [ ] **Login test** - Verify authentication works

### Post-Deployment
- [ ] **Backup automation configured** - SQLite dump cron job to S3/Backblaze
- [ ] **Monitoring enabled** - Uptime Robot ping monitor, optional: Prometheus
- [ ] **Alert thresholds set** - CPU >80%, RAM >85%, disk >80%
- [ ] **Log rotation configured** - Prevent disk fill from logs
- [ ] **Security audit** - Fail2ban installed, root login disabled, updates scheduled

### Security Hardening
- [ ] SSH key-only authentication (no passwords)
- [ ] Fail2ban installed and configured
- [ ] Automatic security updates enabled (`unattended-upgrades`)
- [ ] Docker daemon hardened (non-root user, no privileged containers)
- [ ] Firewall audit (only necessary ports open)

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **VPS provider downtime** | Low | High | - Use provider with 99.9%+ SLA<br>- Daily SQLite dumps to external storage<br>- Have migration plan documented |
| **Data loss (SQLite corruption)** | Low | Critical | - **Daily automated backups** to S3/Backblaze<br>- Test restore procedure quarterly<br>- Consider WAL mode for SQLite |
| **Security breach** | Medium | Critical | - Auth required on all endpoints<br>- Secrets encrypted (Docker secrets or .env with restricted perms)<br>- Regular security updates (auto-enabled)<br>- Fail2ban for SSH brute-force protection |
| **Cost overrun** | Low | Medium | - Fixed-price VPS (not usage-based like AWS)<br>- Alerting on unusual traffic<br>- Avoid auto-scaling without caps |
| **Provider locks account** | Very Low | High | - Use established provider (DO, Vultr, Linode)<br>- Keep local backups<br>- Have migration script ready |
| **ARM incompatibility (Oracle)** | Medium | Medium | - Test Docker images on ARM before deploying<br>- Most Node.js/Python images support ARM64 now<br>- Has minor performance quirks on some x86-optimized code |
| **Hetzner availability (EU-only best pricing)** | Low | Low | - EU datacenters usually have capacity<br>- Have Vultr/DO as backup options |

---

## 6. Scaling Path

### When to Upgrade VPS:
**Trigger Conditions:**
- Agents discovered > 10K
- API calls > 10K/day sustained
- RAM usage consistently > 70%
- CPU usage > 50% during scans
- Response time degradation noticed

**Upgrade Path (Vultr Example):**
```
Current: 1 vCPU / 2GB / $12/mo
↓
Step 1: 2 vCPU / 4GB / $20/mo (2x CPU, 2x RAM)
↓
Step 2: 4 vCPU / 8GB / $40/mo (production scale)
↓
Step 3: 8 vCPU / 16GB / $80/mo (heavy usage)
```

### Horizontal Scaling Strategy:

#### Phase 1: Single VPS (Current - 10K agents)
- All services on one machine
- Simple, cost-effective, easy to manage

#### Phase 2: Separated Services (10K-50K agents)
- **Scanner VPS** ($12/mo): Runs scanner + detector only
- **API VPS** ($12/mo): Runs web UI + API + SQLite
- **Shared DB**: SQLite still fine, mounted via NFS or synced

#### Phase 3: Database Migration (50K+ agents or 50K+ API calls/day)
**Migrate SQLite → PostgreSQL:**
```bash
# When to migrate:
- DB size > 500MB
- Write contention causing lock issues
- Need for advanced queries
- Multiple scanner instances

# Migration steps:
1. Spin up managed PostgreSQL (DigitalOcean $15/mo or self-hosted)
2. Update CogniWatch config to use Postgres connection string
3. Run migration script (provided in CogniWatch repo)
4. Verify data integrity
5. Switch traffic, monitor for 48h
```

#### Phase 4: Caching Layer (100K+ API calls/day)
**Add Redis:**
- Cache frequent API responses
- Session storage
- Rate limiting
- ~1GB Redis instance: $10-15/mo

#### Phase 5: Multiple Scanners (100K+ agents)
- Deploy scanner instances in different regions
- All report to central API/DB
- Reduce scan latency for geographically distributed agents
- Consider Kubernetes for orchestration at this scale

---

## 7. Promo Codes & Startup Credits

### DigitalOcean
- **GitHub Student Developer Pack:** $200 credit (1 year validity)
  - Requires .edu email + GitHub student verification
  - Link: https://www.digitalocean.com/github-students
- **Standard promo:** $100 credit for 60 days (new accounts)
  - Search: "DigitalOcean $100 credit" - various affiliate links
- **Startups program:** Up to $5,000 in credits for funded startups
  - Apply: https://www.digitalocean.com/startups

### AWS
- **AWS Activate Founders:** $1,000 credit (pre-revenue startups)
- **AWS Activate Portfolio:** Up to $100,000 (VC-backed startups)
- **Free tier:** 12 months free on t2.micro/t3.micro (750 hrs/month)
  - Expires after 12 months, converts to pay-as-you-go
- Apply: https://aws.amazon.com/startups/credits

### Google Cloud
- **Free trial:** $300 credit for 90 days (all new accounts)
- **Free tier:** e2-micro free in us regions (limited)
- **Startups:** Up to $200,000 via Google for Startups Cloud Program
- Apply: https://cloud.google.com/developers/startups

### Vultr
- **GitHub Student Pack:** $50-100 credit (varies)
- **Standard promo:** $100 credit for 30 days (new accounts via affiliates)
- Search: "Vultr $100 credit" for current offers

### Linode (Akamai)
- **GitHub Student Pack:** $50 credit
- **Standard promo:** $20-100 credit (varies by campaign)
- No formal startup program, but contact sales for larger credits

### Oracle Cloud
- **Always Free:** Permanent free tier (4 OCPU ARM, 24GB RAM, 200GB storage)
  - No credit card required for free tier
  - Limited availability (ARM instances often out of stock)
- **Free trial:** $300 credit for 30 days (paid tier)

### Hetzner
- **No free credits** (already cheapest provider)
- No startup program
- Occasional referral bonuses from existing customers

---

## 8. FINAL RECOMMENDATION

### 🏆 **Best Overall: Vultr Cloud Compute**
**Plan:** High Performance (1 vCPU / 2GB RAM / 50GB NVMe)  
**Cost:** $12/month  
**Why:**
- Best price/performance ratio
- NVMe storage standard (faster than SATA SSD)
- 32 global locations (more than DO)
- 1-click Docker deployment
- Hourly billing (can destroy/recreate cheaply)
- $100 credit available via affiliates

### 🥈 **Runner-Up: DigitalOcean Basic Droplet**
**Plan:** 1 vCPU / 2GB RAM / 50GB SSD  
**Cost:** $12/month  
**Why:**
- Best developer experience and documentation
- Larger community, more tutorials
- Excellent uptime track record
- Slightly better support than Vultr
- Choose if you value docs/community over raw performance

### 🥉 **Budget Pick: Hetzner CPX11**
**Plan:** 2 vCPU / 2GB RAM / 80GB SSD  
**Cost:** ~$6.49/month (50% cheaper!)  
**Why:**
- Insane value for money
- 2 vCPU + 80GB at this price is unmatched
- Choose if you're EU-based or cost is primary concern
- Trade-off: Slower support, fewer locations

### 🎁 **If Available: Oracle Cloud Always Free**
**Plan:** 4 OCPU ARM / 24GB RAM / 200GB  
**Cost:** $0/month (seriously)  
**Why:**
- Completely free, forever
- Massive resources (overkill for CogniWatch)
- ARM architecture (test compatibility first)
- **Problem:** Often out of stock, hard to provision
- Worth attempting first; have Vultr/DO as backup

### 🚀 **Decision Matrix:**

| Priority | Recommendation |
|----------|----------------|
| **Cheapest (long-term)** | Oracle Always Free → Hetzner CPX11 |
| **Best value** | Vultr High Performance |
| **Easiest setup** | DigitalOcean (best docs) |
| **Most reliable** | DigitalOcean or Vultr |
| **EU deployment** | Hetzner or Vultr (Frankfurt/Amsterdam) |
| **Startup credits available** | DigitalOcean ($200 via GitHub) |
| **Maximum headroom** | Oracle Always Free (24GB RAM!) |

---

## 9. Quick Start Commands

Once you've picked a provider:

```bash
# 1. SSH into your new VPS
ssh root@your-vps-ip

# 2. Create non-root user
adduser cogniwatch
usermod -aG sudo cogniwatch
su - cogniwatch

# 3. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 4. Install UFW firewall
sudo apt update && sudo apt install -y ufw
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 5. Clone and deploy CogniWatch
git clone https://github.com/your-org/cogniwatch.git
cd cogniwatch
docker compose up -d

# 6. Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 7. Set up backup cron job
crontab -e
# Add: 0 2 * * * /path/to/backup-script.sh

# 8. Install Fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 9. Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 10. Tonight's Deployment Plan

**For deployment tonight, here's the play-by-play:**

1. **Sign up for Vultr** (or DO if you prefer) - 5 min
2. **Create droplet/instance:** 2 vCPU / 2GB / Ubuntu 24.04 - 2 min
3. **Point domain DNS** to VPS IP - 1 min (wait ~5-60 min for propagation)
4. **SSH in, run setup commands** (above) - 15 min
5. **Deploy CogniWatch** via docker compose - 5 min
6. **Configure SSL** with certbot - 5 min
7. **Test everything** - 10 min
8. **Set up backup cron** - 5 min
9. **Add Uptime Robot monitor** - 5 min

**Total time:** ~1 hour (mostly waiting on DNS)

**Budget:** $36 for first quarter (VPS $12 × 3 + domain $12 ÷ 4)

---

**You're ready to deploy. Good luck! 🚀**

*Questions or issues? The provider docs + CogniWatch README should cover 95% of scenarios. Worst case, destroy and recreate - that's the beauty of cloud.*
