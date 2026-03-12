#!/bin/bash
# 🟠 HIGH: Configure Fail2ban for Brute Force Protection
# Automatically bans IPs with too many failed auth attempts
# Run time: 3 minutes

set -e

echo "👮 Setting up Fail2ban for CogniWatch..."

if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as sudo: sudo $0"
    exit 1
fi

# Install Fail2ban
echo "📦 Installing Fail2ban..."
apt update -qq
apt install fail2ban -y -qq
echo "✅ Fail2ban installed"

# Create CogniWatch filter
echo "📝 Creating CogniWatch filter..."
cat > /etc/fail2ban/filter.d/cogniwatch.conf << 'EOF'
[Definition]
failregex = .*Unauthorized.*API token required.*"ip":"<HOST>".*
            .*Authentication required.*"ip":"<HOST>".*
            .*Invalid token.*"ip":"<HOST>".*
            .*401 Unauthorized.*<HOST>.*
ignoreregex = 
EOF
echo "✅ Filter created"

# Create jail configuration
echo "📝 Creating jail configuration..."
cat > /etc/fail2ban/jail.d/cogniwatch.local << 'EOF'
[cogniwatch]
enabled = true
port = 443,9000
filter = cogniwatch
logpath = /home/neo/cogniwatch/logs/cogniwatch.log
maxretry = 5
bantime = 3600
findtime = 600
action = iptables-allports[name=COGNIWATCH]
         sendmail-whois[name=CogniWatch, dest=root, sender=fail2ban@localhost]
EOF
echo "✅ Jail configured"

# Also protect SSH
echo "📝 Creating SSH jail configuration..."
cat > /etc/fail2ban/jail.d/ssh-local.local << 'EOF'
[sshd]
enabled = true
port = 22,2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
findtime = 600

[sshd-ddos]
enabled = true
port = 22,2222
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 6
bantime = 3600
findtime = 600
EOF
echo "✅ SSH jail configured"

# Enable and restart Fail2ban
echo "🔄 Starting Fail2ban service..."
systemctl daemon-reload
systemctl enable fail2ban
systemctl restart fail2ban

# Verify
sleep 2
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fail2ban Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status fail2ban --no-pager | head -10

echo ""
echo "Jails active:"
fail2ban-client status | grep "Jail list"

echo ""
echo "✅ Fail2ban configured and running!"
echo ""
echo "Useful commands:"
echo "  fail2ban-client status cogniwatch    # Check cogniwatch jail"
echo "  fail2ban-client status sshd          # Check SSH jail"
echo "  fail2ban-client set cogniwatch unbanip [IP]  # Unban IP if needed"
echo ""
echo "⚠️  To receive email alerts, configure postfix or sendmail"
