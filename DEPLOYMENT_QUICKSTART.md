# 🚀 CogniWatch VPS Deployment - Quick Start Guide

**Mission Critical:** Production deployment tonight  
**Estimated Time:** 1 hour  
**Cost:** ~$12/month (VPS) + ~$12/year (domain)

---

## 📋 What You Need Before Starting

1. **Credit/Debit Card** - For VPS provider signup
2. **Domain Name** - Or purchase one during deployment (~$12/year)
3. **~1 Hour** - Uninterrupted time for deployment
4. **This Workspace** - All scripts are ready to go!

---

## 🎯 Step-by-Step Instructions

### Step 1: Choose & Provision VPS (5-10 minutes)

**RECOMMENDED: Vultr High Performance**
- **URL:** https://www.vultr.com/pricing/
- **Plan:** Cloud Compute - High Performance
- **Spec:** 1 vCPU / 2GB RAM / 50GB NVMe
- **Cost:** $12/month
- **Location:** Choose closest to your users

**BUDGET ALTERNATIVE: Hetzner CPX11**
- **URL:** https://www.hetzner.com/cloud
- **Plan:** CPX11
- **Spec:** 2 vCPU / 2GB RAM / 80GB SSD
- **Cost:** ~$6.50/month (50% cheaper!)
- **Location:** EU (Germany/Finland)

**FREE OPTION: Oracle Cloud Always Free** (if available)
- **URL:** https://www.oracle.com/cloud/free/
- **Spec:** 4 OCPU ARM / 24GB RAM / 200GB
- **Cost:** $0/month (forever)
- **Note:** Often out of stock, ARM architecture

**What to do:**
1. Create account with chosen provider
2. Create new instance/server
3. Select **Ubuntu 24.04 LTS** (or 22.04)
4. Note the **public IP address**
5. Note the **root password** (if provided)

---

### Step 2: SSH Key Setup (2 minutes)

Your SSH key has already been generated!

**Location:** `/home/neo/.openclaw/credentials/cogniwatch-vps/ssh-keys/`

**Deploy SSH key to VPS:**
```bash
# Replace YOUR_VPS_IP with actual IP
cat /home/neo/.openclaw/credentials/cogniwatch-vps/ssh-keys/cogniwatch-vps.pub | \
  ssh root@YOUR_VPS_IP 'cat >> /root/.ssh/authorized_keys'

# Test SSH access
ssh -i /home/neo/.openclaw/credentials/cogniwatch-vps/ssh-keys/cogniwatch-vps root@YOUR_VPS_IP
```

**Alternatively, use password:**
```bash
ssh root@YOUR_VPS_IP
# Enter root password when prompted

# Then add SSH key for future passwordless access
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Paste your public key into ~/.ssh/authorized_keys
```

---

### Step 3: Upload Deployment Script (1 minute)

```bash
# From your local machine (this workspace)
scp DEPLOYMENT_AUTOMATION.sh root@YOUR_VPS_IP:/root/
```

---

### Step 4: Configure Domain DNS (5-60 minutes propagation)

**If you have a domain:**
1. Log into your domain registrar (Namecheap, Cloudflare, etc.)
2. Add DNS record:
   - **Type:** A
   - **Name:** cogniwatch (or @)
   - **Value:** YOUR_VPS_IP
   - **TTL:** 3600 (or Auto)

**If you need a domain:**
- **Cloudflare:** https://www.cloudflare.com/products/registrar/ (at-cost pricing)
- **Namecheap:** https://www.namecheap.com/
- **Porkbun:** https://porkbun.com/

**Wait for DNS propagation** (5-60 minutes typically)
- Check: `nslookup cogniwatch.yourdomain.com`
- Or use: https://dnschecker.org/

---

### Step 5: Run Automated Deployment (15 minutes)

**SSH into your VPS:**
```bash
ssh -i /home/neo/.openclaw/credentials/cogniwatch-vps/ssh-keys/cogniwatch-vps root@YOUR_VPS_IP
```

**Edit the deployment script** (optional - configure your settings):
```bash
nano /root/DEPLOYMENT_AUTOMATION.sh
```

**Update these variables in the script:**
```bash
DOMAIN_NAME="cogniwatch.yourdomain.com"  # Your domain
ADMIN_API_KEY="your-secure-random-key"   # Use generated key below
SCANNER_NETWORK="192.168.0.0/24"         # Your network to monitor
```

**Generate a secure admin key:**
```bash
openssl rand -hex 24
# Example output: 7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f
```

**Run the deployment:**
```bash
bash /root/DEPLOYMENT_AUTOMATION.sh
```

The script will automatically:
- ✅ Update system packages
- ✅ Install Docker & Docker Compose
- ✅ Configure firewall (UFW)
- ✅ Set up Fail2ban
- ✅ Enable automatic security updates
- ✅ Create swap space
- ✅ Deploy CogniWatch
- ✅ Configure HTTPS with Let's Encrypt
- ✅ Set up backup automation

---

### Step 6: Copy CogniWatch Files (5 minutes)

**From your local machine:**
```bash
# Copy all CogniWatch files to VPS
scp -r /home/neo/cogniwatch/* cogniwatch@YOUR_VPS_IP:/home/cogniwatch/cogniwatch/

# Or use rsync for faster transfer
rsync -avz /home/neo/cogniwatch/ cogniwatch@YOUR_VPS_IP:/home/cogniwatch/cogniwatch/
```

---

### Step 7: Verify Deployment (5 minutes)

**SSH to VPS and check:**
```bash
ssh cogniwatch@YOUR_VPS_IP

# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test local access
curl http://localhost:9000/health
```

**Expected output:**
```
NAME                  STATUS
cogniwatch-webui      Up (healthy)
cogniwatch-scanner    Up
```

---

### Step 8: Access Dashboard

**Via HTTPS (if domain configured):**
```
https://cogniwatch.yourdomain.com
```

**Via IP (temporary - configure domain for HTTPS):**
```
http://YOUR_VPS_IP:9000
```

**Login:**
- Use the ADMIN_API_KEY you configured
- Store it securely - you'll need it for API access

---

### Step 9: Set Up Monitoring (5 minutes)

**Uptime Robot (free tier):**
1. Go to: https://uptimerobot.com/
2. Create free account
3. Add new monitor:
   - **Type:** HTTPS
   - **URL:** https://cogniwatch.yourdomain.com/api/health
   - **Interval:** 5 minutes
   - **Alert contacts:** Your email

**You'll get notified if:**
- Dashboard goes down
- SSL certificate expires
- Server becomes unreachable

---

### Step 10: Store Credentials Securely

**Update credentials file:**
```bash
# Create credentials file
cat > /home/neo/.openclaw/credentials/cogniwatch-vps/vps-credentials.txt << EOF
VPS Provider: Vultr
VPS IP: YOUR_VPS_IP
Root Password: [stored in password manager]
Domain: cogniwatch.yourdomain.com
Admin API Key: [your generated key]
Deployment Date: 2026-03-07
EOF

chmod 600 /home/neo/.openclaw/credentials/cogniwatch-vps/vps-credentials.txt
```

**NEVER:**
- ❌ Commit `.env` files to git
- ❌ Share API keys in chat
- ❌ Log passwords anywhere

---

## 🎉 Deployment Complete!

### What's Running:
- ✅ CogniWatch Web UI (port 9000)
- ✅ CogniWatch Scanner (scans your network)
- ✅ Nginx reverse proxy
- ✅ Let's Encrypt SSL (auto-renewing)
- ✅ Fail2ban (SSH protection)
- ✅ Automatic security updates
- ✅ Daily backups (2 AM UTC)

### URLs:
| Service | URL |
|---------|-----|
| Dashboard | https://cogniwatch.yourdomain.com |
| API | https://cogniwatch.yourdomain.com/api |
| Health Check | https://cogniwatch.yourdomain.com/api/health |

### Monthly Costs:
- VPS: $12 (Vultr) or $6.50 (Hetzner) or $0 (Oracle)
- Domain: ~$1/year (amortized)
- SSL: $0 (Let's Encrypt)
- Monitoring: $0 (Uptime Robot free tier)
- **Total: ~$12-13/month**

---

## 🆘 Troubleshooting

### Can't SSH to VPS
```bash
# Check if you're using the right IP
ping YOUR_VPS_IP

# Try with verbose output
ssh -v root@YOUR_VPS_IP

# Check firewall (run from VPS console if available)
ufw status
```

### Docker not working
```bash
# Restart Docker
systemctl restart docker

# Check Docker status
systemctl status docker

# Reinstall if needed
curl -fsSL https://get.docker.com | sh
```

### SSL certificate failed
```bash
# Check domain DNS
nslookup cogniwatch.yourdomain.com

# Re-run certbot
certbot --nginx -d cogniwatch.yourdomain.com

# Check Nginx config
nginx -t
```

### Containers not starting
```bash
# Check logs
docker compose logs

# Restart containers
docker compose down
docker compose up -d

# Check resources
free -h  # RAM
df -h   # Disk
```

### Can't access dashboard
```bash
# Check if CogniWatch is running
docker compose ps

# Check port binding
netstat -tlnp | grep 9000

# Check firewall
ufw status

# Check Nginx
systemctl status nginx
```

---

## 📚 Reference Documents

- **Full Deployment Guide:** `/home/neo/cogniwatch/DEPLOYMENT.md`
- **VPS Recommendations:** `/home/neo/cogniwatch/VPS_DEPLOYMENT_RECOMMENDATIONS.md`
- **Security Framework:** `/home/neo/cogniwatch/SECURITY_FRAMEWORK.md`
- **Deployment Log:** `/home/neo/cogniwatch/DEPLOYMENT_LOG.md`
- **Automation Script:** `/home/neo/cogniwatch/DEPLOYMENT_AUTOMATION.sh`

---

## 🚀 Ready to Deploy?

1. **Pick your VPS provider** (Vultr recommended)
2. **Create account and provision VPS**
3. **Run the deployment script**
4. **Ship it! 🦈**

**Estimated Total Time:** 1 hour  
**Difficulty:** Beginner-friendly (automated)

Good luck! The production launch is tonight! 🎯
