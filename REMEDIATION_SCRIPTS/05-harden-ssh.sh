#!/bin/bash
# 🟠 HIGH: SSH Hardening Script
# Move SSH to non-standard port, disable password auth
# ⚠️  WARNING: Test in new terminal before closing current session!
# Run time: 5 minutes

set -e

echo "🔒 SSH Hardening Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  WARNING: This will change SSH configuration!"
echo "DO NOT close your current SSH session until you've tested"
echo "a NEW connection with the new settings."
echo ""

# Confirm continuation
read -p "Type 'YES' to continue: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
    echo "❌ Aborted"
    exit 1
fi

SSH_CONFIG="/etc/ssh/sshd_config"
SSH_CONFIG_BACKUP="/etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)"

# Backup config
cp "$SSH_CONFIG" "$SSH_CONFIG_BACKUP"
echo "✅ Backup created: $SSH_CONFIG_BACKUP"

# Generate new port number (between 2000-9999)
NEW_PORT=$((RANDOM % 7999 + 2000))
echo ""
echo "🎲 Generated new SSH port: $NEW_PORT"
echo ""

# Get user's current IP for firewall rule
CURRENT_IP=$(curl -s https://api.ipify.org 2>/dev/null || echo "101.177.163.167")
read -p "Allow SSH from IP [$CURRENT_IP]: " CONFIRM_IP
if [ -n "$CONFIRM_IP" ]; then
    CURRENT_IP="$CONFIRM_IP"
fi

# Create new SSH config
cat > /tmp/sshd_hardened_config << EOF
# Hardened SSH Configuration
# Generated: $(date)

# Basic settings
Port $NEW_PORT
Protocol 2
AddressFamily inet

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
MaxSessions 10

# Security
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60

# Logging
SyslogFacility AUTH
LogLevel VERBOSE

# Restrict to specific users (optional)
# AllowUsers neo
EOF

echo "📝 Backing up original config and applying hardened settings..."

# Add match block for the user to /etc/ssh/sshd_config
cat >> "$SSH_CONFIG" << EOF

# ============ HARDENED CONFIGURATION (added $(date)) ============
Port $NEW_PORT
PermitRootLogin no
PasswordAuthentication no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
EOF

# Test config syntax
echo "🔍 Testing SSH configuration syntax..."
if sshd -t; then
    echo "✅ SSH config syntax OK"
else
    echo "❌ ERROR: SSH config has syntax errors!"
    echo "Restoring backup..."
    cp "$SSH_CONFIG_BACKUP" "$SSH_CONFIG"
    exit 1
fi

# Restart SSH
echo "🔄 Restarting SSH service..."
systemctl restart sshd

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SSH Hardening Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 NEW SSH DETAILS:"
echo "   Port: $NEW_PORT"
echo "   Password Auth: DISABLED"
echo "   Root Login: DISABLED"
echo ""
echo "⚠️  CRITICAL: Test new SSH connection BEFORE closing current session!"
echo ""
echo "In a NEW terminal, run:"
echo "  ssh -p $NEW_PORT $(whoami)@$(hostname -I | awk '{print $1}')"
echo ""
echo "If that works, in a NEW terminal test:"
echo "  sudo ufw delete allow 22/tcp"
echo "  sudo ufw allow $NEW_PORT/tcp"
echo ""
echo "To revert if something breaks:"
echo "  sudo cp $SSH_CONFIG_BACKUP $SSH_CONFIG"
echo "  sudo systemctl restart sshd"
echo ""
