#!/bin/bash
# =============================================================================
# CogniWatch VPS Deployment Automation Script
# =============================================================================
# Usage: bash DEPLOYMENT_AUTOMATION.sh
# 
# This script automates the entire VPS deployment process AFTER you've:
# 1. Provisioned a VPS (Vultr/DigitalOcean/Hetzner)
# 2. Pointed your domain DNS to the VPS IP
# 3. SSH'd into the VPS for the first time
#
# Run this script ONCE on your fresh VPS as root user
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}🦈 CogniWatch VPS Deployment Script${NC}"
echo -e "${BLUE}=================================================================${NC}"
echo ""

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES BEFORE RUNNING
# =============================================================================

# Domain name (e.g., cogniwatch.example.com)
DOMAIN_NAME=""

# Admin API key (generate a secure random string)
ADMIN_API_KEY=""

# Scanner network to monitor (e.g., 192.168.0.0/24 or 0.0.0.0/0 for internet-wide)
SCANNER_NETWORK="192.168.0.0/24"

# OpenClaw Gateway URL (optional, for agent integration)
OPENCLAW_GATEWAY_URL="ws://127.0.0.1:18789"

# OpenClaw Gateway Token (optional)
OPENCLAW_GATEWAY_TOKEN=""

# =============================================================================
# STEP 1: System Update & User Setup
# =============================================================================

echo -e "${YELLOW}[Step 1/10] System Update & User Setup${NC}"

# Update system packages
echo "Updating system packages..."
apt update && apt upgrade -y

# Install essential tools
echo "Installing essential tools..."
apt install -y curl wget git nano htop ufw fail2ban unattended-upgrades certbot python3-certbot-nginx

# Create non-root user
if ! id "cogniwatch" &>/dev/null; then
    echo "Creating cogniwatch user..."
    adduser --disabled-password --gecos "" cogniwatch
    usermod -aG sudo cogniwatch
fi

# =============================================================================
# STEP 2: SSH Key Setup
# =============================================================================

echo -e "${YELLOW}[Step 2/10] SSH Key Configuration${NC}"

# Create .ssh directory for cogniwatch user
mkdir -p /home/cogniwatch/.ssh
chmod 700 /home/cogniwatch/.ssh

# Instructions for adding SSH key
echo -e "${YELLOW}IMPORTANT: Add your SSH public key to /home/cogniwatch/.ssh/authorized_keys${NC}"
echo "Run this on your LOCAL machine:"
echo "  cat ~/.ssh/id_ed25519.pub | ssh root@YOUR_VPS_IP 'cat >> /home/cogniwatch/.ssh/authorized_keys'"
echo ""
echo "Waiting 30 seconds for you to add the SSH key..."
sleep 30

# Set permissions
chmod 600 /home/cogniwatch/.ssh/authorized_keys 2>/dev/null || true
chown -R cogniwatch:cogniwatch /home/cogniwatch/.ssh

# =============================================================================
# STEP 3: Docker Installation
# =============================================================================

echo -e "${YELLOW}[Step 3/10] Docker Installation${NC}"

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com | sh

# Add cogniwatch user to docker group
usermod -aG docker cogniwatch

# Enable Docker on boot
systemctl enable docker
systemctl start docker

echo -e "${GREEN}✓ Docker installed successfully${NC}"

# =============================================================================
# STEP 4: Firewall Configuration (UFW)
# =============================================================================

echo -e "${YELLOW}[Step 4/10] Firewall Configuration${NC}"

# Reset UFW
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP (Let'\''s Encrypt)'
ufw allow 443/tcp comment 'HTTPS (CogniWatch)'

# Enable UFW
echo "y" | ufw enable

echo -e "${GREEN}✓ Firewall configured${NC}"

# =============================================================================
# STEP 5: Swap Space (2GB recommended)
# =============================================================================

echo -e "${YELLOW}[Step 5/10] Swap Space Configuration${NC}"

# Check if swap exists
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swap file..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make permanent
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    echo -e "${GREEN}✓ Swap created${NC}"
else
    echo "Swap already exists, skipping..."
fi

# =============================================================================
# STEP 6: Fail2ban Configuration
# =============================================================================

echo -e "${YELLOW}[Step 6/10] Fail2ban Security${NC}"

# Create Fail2ban jail for SSH
cat > /etc/fail2ban/jail.d/local.conf << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 86400
findtime = 600
EOF

systemctl restart fail2ban
systemctl enable fail2ban

echo -e "${GREEN}✓ Fail2ban configured${NC}"

# =============================================================================
# STEP 7: Automatic Security Updates
# =============================================================================

echo -e "${YELLOW}[Step 7/10] Automatic Security Updates${NC}"

# Configure unattended upgrades
cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

echo -e "${GREEN}✓ Automatic updates enabled${NC}"

# =============================================================================
# STEP 8: CogniWatch Deployment
# =============================================================================

echo -e "${YELLOW}[Step 8/10] CogniWatch Deployment${NC}"

# Create application directory
mkdir -p /home/cogniwatch/cogniwatch
cd /home/cogniwatch/cogniwatch

# Note: User needs to copy files from local machine
echo -e "${YELLOW}Copy CogniWatch files to /home/cogniwatch/cogniwatch/${NC}"
echo "Required files:"
echo "  - docker-compose.yml"
echo "  - Dockerfile"
echo "  - .env.example"
echo "  - webui/"
echo "  - scanner/"
echo "  - config/"
echo ""
echo "From your local machine, run:"
echo "  scp -r /path/to/cogniwatch/* cogniwatch@YOUR_VPS_IP:/home/cogniwatch/cogniwatch/"
echo ""
echo "Waiting 60 seconds for file transfer..."
sleep 60

# Create .env file
echo -e "${YELLOW}Creating .env configuration...${NC}"

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

cat > /home/cogniwatch/cogniwatch/.env << EOF
# CogniWatch Production Configuration
# Auto-generated: $(date -Iseconds)

# Web UI
COGNIWATCH_PORT=9000
COGNIWATCH_DEBUG=false

# Network Scanner
SCANNER_NETWORK=${SCANNER_NETWORK}
SCANNER_INTERVAL_HOURS=24

# OpenClaw Gateway (optional)
OPENCLAW_GATEWAY_URL=${OPENCLAW_GATEWAY_URL}
OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}

# Security
COGNIWATCH_SECRET_KEY=${JWT_SECRET}
COGNIWATCH_ADMIN_TOKEN=${ADMIN_API_KEY}
EOF

chmod 600 /home/cogniwatch/cogniwatch/.env
chown cogniwatch:cogniwatch /home/cogniwatch/cogniwatch/.env

echo -e "${GREEN}✓ .env configuration created${NC}"

# Deploy with Docker Compose
cd /home/cogniwatch/cogniwatch
echo "Deploying CogniWatch..."
docker compose up -d --build

echo -e "${GREEN}✓ CogniWatch deployed${NC}"

# =============================================================================
# STEP 9: HTTPS with Nginx + Certbot
# =============================================================================

echo -e "${YELLOW}[Step 9/10] HTTPS Configuration${NC}"

# Wait for domain to be ready
echo "Waiting for DNS propagation and container to be ready..."
sleep 10

# Install Nginx if not already installed
apt install -y nginx

# Create Nginx configuration
cat > /etc/nginx/sites-available/cogniwatch << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/cogniwatch /etc/nginx/sites-enabled/cogniwatch
nginx -t && systemctl restart nginx

if [ ! -z "${DOMAIN_NAME}" ]; then
    echo "Obtaining SSL certificate with Let's Encrypt..."
    certbot --nginx -d ${DOMAIN_NAME} -d www.${DOMAIN_NAME} --non-interactive --agree-tos --email admin@${DOMAIN_NAME}
    echo -e "${GREEN}✓ HTTPS configured with Let's Encrypt${NC}"
else
    echo -e "${YELLOW}No domain configured, skipping SSL setup${NC}"
    echo "Access via: http://YOUR_VPS_IP:9000"
fi

# =============================================================================
# STEP 10: Backup Automation
# =============================================================================

echo -e "${YELLOW}[Step 10/10] Backup Automation${NC}"

# Create backup script
cat > /home/cogniwatch/backup.sh << 'BACKUP_EOF'
#!/bin/bash
# CogniWatch Daily Backup Script

BACKUP_DIR="/home/cogniwatch/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/home/cogniwatch/cogniwatch/data/cogniwatch.db"
RETENTION_DAYS=30

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup SQLite database
if [ -f "${DB_PATH}" ]; then
    cp "${DB_PATH}" "${BACKUP_DIR}/cogniwatch_${DATE}.db"
    echo "Backup created: cogniwatch_${DATE}.db"
else
    echo "Database not found at ${DB_PATH}"
    exit 1
fi

# Compress backup
gzip "${BACKUP_DIR}/cogniwatch_${DATE}.db"

# Delete old backups
find ${BACKUP_DIR} -name "cogniwatch_*.db.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup complete. Retention: ${RETENTION_DAYS} days"
BACKUP_EOF

chmod +x /home/cogniwatch/backup.sh
chown cogniwatch:cogniwatch /home/cogniwatch/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/cogniwatch/backup.sh >> /home/cogniwatch/backup.log 2>&1") | crontab -

echo -e "${GREEN}✓ Backup automation configured (daily at 2 AM UTC)${NC}"

# =============================================================================
# DEPLOYMENT COMPLETE
# =============================================================================

echo ""
echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}🎉 CogniWatch Deployment Complete!${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo ""
echo "Dashboard URL:"
if [ ! -z "${DOMAIN_NAME}" ]; then
    echo -e "  ${GREEN}https://${DOMAIN_NAME}${NC}"
else
    echo -e "  ${YELLOW}http://YOUR_VPS_IP:9000${NC}"
    echo "  (Configure domain for HTTPS)"
fi
echo ""
echo "Admin API Key (save securely):"
echo -e "  ${YELLOW}${ADMIN_API_KEY}${NC}"
echo ""
echo "Next Steps:"
echo "  1. Verify containers: docker compose ps"
echo "  2. Check logs: docker compose logs -f"
echo "  3. Access dashboard and test functionality"
echo "  4. Set up Uptime Robot monitoring: https://uptimerobot.com"
echo "  5. Configure domain DNS (if not done)"
echo ""
echo "Security Checklist:"
echo "  ✓ SSH key authentication"
echo "  ✓ Firewall (UFW) enabled"
echo "  ✓ Fail2ban active"
echo "  ✓ Automatic security updates"
echo "  ✓ Daily backups configured"
echo ""
echo -e "${YELLOW}IMPORTANT: Never commit .env files or share API keys!${NC}"
echo ""
