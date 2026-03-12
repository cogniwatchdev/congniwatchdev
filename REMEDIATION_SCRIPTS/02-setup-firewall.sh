#!/bin/bash
# 🔴 CRITICAL: Install and Configure UFW Firewall
# Prevents unauthorized network access
# Run time: 5 minutes

set -e

echo "🔥 Installing and configuring UFW firewall..."

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as sudo: sudo $0"
    exit 1
fi

# Install UFW
echo "📦 Installing UFW..."
apt update -qq
apt install ufw -y -qq
echo "✅ UFW installed"

# Reset firewall to clean state (optional, removes old rules)
if command -v ufw &> /dev/null; then
    echo "⚠️  Resetting UFW to defaults (will remove existing rules)"
    ufw --force reset
fi

# Default policies
echo "🚫 Setting default policies..."
ufw default deny incoming
ufw default allow outgoing

# Allow SSH from YOUR IP only
echo "🔑 Configuring SSH access..."
read -p "Enter YOUR public IP address (or press Enter to allow from anywhere): " MY_IP

if [ -z "$MY_IP" ]; then
    echo "⚠️  Allowing SSH from anywhere (not recommended for production)"
    ufw allow 22/tcp comment "SSH access - OPEN TO ALL"
else
    echo "✅ Allowing SSH from $MY_IP only"
    ufw allow from "$MY_IP/32" to any port 22 proto tcp comment "SSH from trusted IP"
fi

# Allow HTTPS
echo "🔒 Allowing HTTPS..."
ufw allow 443/tcp comment "HTTPS traffic"

# Allow HTTP temporarily for Let's Encrypt
echo "☀️  Allowing HTTP for Let's Encrypt (will be closed after SSL setup)"
ufw allow 80/tcp comment "HTTP for Let's Encrypt - CLOSE AFTER SSL SETUP"

# DENY all CogniWatch direct access (use Nginx proxy instead)
echo "🛡️  Blocking direct access to CogniWatch ports..."
ufw deny 9000/tcp comment "CogniWatch - proxy via Nginx only"
ufw deny 9001/tcp comment "Internal service"
ufw deny 8000/tcp comment "Internal service"

# Enable firewall
echo "🔴 ENABLING UFW (this will start filtering traffic)..."
ufw --force enable

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "UFW Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ufw status verbose

echo ""
echo "✅ UFW firewall configured!"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Test SSH connection in NEW terminal before closing current one"
echo "2. If SSH fails, console access needed to fix"
echo "3. After Let's Encrypt setup, run: sudo ufw delete allow 80/tcp"
echo ""
echo "To check status anytime: ufw status"
