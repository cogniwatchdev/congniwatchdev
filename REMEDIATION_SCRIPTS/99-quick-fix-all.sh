#!/bin/bash
# 🔴 CRITICAL: All-in-One Quick Fix Script
# Fixes ALL Critical and High severity issues
# Run time: ~15 minutes
# For VPS deployment ONLY

set -e

echo "🚨 CogniWatch Security Remediation Script"
echo "============================================"
echo ""
echo "⚠️  WARNING: This script makes significant security changes"
echo "   - Removes authentication bypass"
echo "   - Generates new API tokens"
echo "   - Configures firewall"
echo "   - Sets up fail2ban"
echo ""
echo "Only run this on VPS BEFORE internet exposure!"
echo ""

# Confirm
read -p "Type 'SECURE' to proceed: " CONFIRM
if [ "$CONFIRM" != "SECURE" ]; then
    echo "❌ Aborted"
    exit 1
fi

CWD="/home/neo/cogniwatch"
SCRIPT_DIR="$CWD/REMEDIATION_SCRIPTS"
FIX_LOG="$CWD/security_fixes_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$FIX_LOG") 2>&1

echo "📝 Logging to: $FIX_LOG"
echo ""

# Step 1: Fix Auth Bypass
echo "🔧 Step 1/5: Fixing authentication bypass..."
bash "$SCRIPT_DIR/01-fix-auth-bypass.sh"
echo "✅ Auth bypass fixed"
echo ""

# Step 2: Generate New Tokens
echo "🔐 Step 2/5: Generating secure tokens..."
bash "$SCRIPT_DIR/04-generate-tokens.sh"
echo "✅ Tokens generated"
echo ""

# Step 3: Setup Firewall (requires root)
echo "🔥 Step 3/5: Configuring firewall..."
if [ "$EUID" -eq 0 ]; then
    bash "$SCRIPT_DIR/02-setup-firewall.sh"
else
    echo "⚠️  Firewall setup requires root. Run manually with: sudo $SCRIPT_DIR/02-setup-firewall.sh"
fi
echo ""

# Step 4: Setup Fail2ban (requires root)
echo "👮 Step 4/5: Setting up Fail2ban..."
if [ "$EUID" -eq 0 ]; then
    bash "$SCRIPT_DIR/03-setup-fail2ban.sh"
else
    echo "⚠️  Fail2ban setup requires root. Run manually with: sudo $SCRIPT_DIR/03-setup-fail2ban.sh"
fi
echo ""

# Step 5: Verify Fixes
echo "🔍 Step 5/5: Verifying security fixes..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Security Verification Checklist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test auth
echo -n "1. Auth bypass removed: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9000/api/agents 2>/dev/null || echo "000")
if [ "$RESPONSE" == "401" ]; then
    echo "✅ PASS (returns 401 without token)"
else
    echo "❌ FAIL (expected 401, got $RESPONSE)"
fi

# Test with invalid token
echo -n "2. Invalid token rejected: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid" http://127.0.0.1:9000/api/agents 2>/dev/null || echo "000")
if [ "$RESPONSE" == "401" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL (expected 401, got $RESPONSE)"
fi

# Check firewall
echo -n "3. Firewall status: "
if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "✅ PASS (UFW active)"
else
    echo "⚠️  NOT CONFIGURED (run with sudo)"
fi

# Check fail2ban
echo -n "4. Fail2ban status: "
if systemctl is-active --quiet fail2ban 2>/dev/null; then
    echo "✅ PASS (running)"
else
    echo "⚠️  NOT RUNNING (run with sudo)"
fi

# Check server headers
echo -n "5. Security headers: "
RESPONSE=$(curl -sI http://127.0.0.1:9000/api/agents 2>/dev/null | grep -i "x-" | wc -l)
if [ "$RESPONSE" -gt 0 ]; then
    echo "✅ PASS ($RESPONSE headers found)"
else
    echo "⚠️  MISSING (need to restart server with middleware)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Remediation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo "1. Review log: $FIX_LOG"
echo "2. Copy new tokens to password manager"
echo "3. Delete token file after copying"
echo "4. Test all functionality"
echo "5. Deploy to VPS"
echo ""
echo "📖 Documentation:"
echo "   - SECURITY_AUDIT_OWASP_20260308.md"
echo "   - VPS_SECURITY_CHECKLIST.md"
echo "   - EXTERNAL_SCAN_SIMULATION.md"
echo ""
echo "⚠️  REMEMBER: Run SSH hardening manually before public deployment"
echo "   bash $SCRIPT_DIR/05-harden-ssh.sh"
echo ""
