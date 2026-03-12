#!/bin/bash
# 🟠 HIGH: Generate Secure API Tokens and Update Config
# Replaces default tokens with cryptographically secure ones
# Run time: 2 minutes

set -e

CONFIG_FILE="/home/neo/cogniwatch/config/cogniwatch.json"
BACKUP_FILE="/home/neo/cogniwatch/config/cogniwatch.json.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔐 Generating secure API tokens..."

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Create backup
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Generate new tokens
echo "🎲 Generating new random tokens..."

ADMIN_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
VIEWER_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SCANNER_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 NEW TOKENS (SAVE THESE SECURELY!)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Admin Token:   $ADMIN_TOKEN"
echo "Viewer Token:  $VIEWER_TOKEN"
echo "Scanner Token: $SCANNER_TOKEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save to file
TOKENS_FILE="/home/neo/cogniwatch/config/tokens-$(date +%Y%m%d).txt"
cat > "$TOKENS_FILE" << EOF
CogniWatch API Tokens
Generated: $(date)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Admin (full access):
$ADMIN_TOKEN

Viewer (read-only):
$VIEWER_TOKEN

Scanner (scan permissions only):
$SCANNER_TOKEN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  SECURITY WARNING:
- Store this file securely (chmod 600)
- Do NOT commit to version control
- Rotate tokens every 90 days
- Delete after copying to password manager
EOF

chmod 600 "$TOKENS_FILE"
echo "✅ Tokens saved to: $TOKENS_FILE"

# Update config file
echo "📝 Updating config file..."

# Use Python to properly update JSON
python3 << PYEOF
import json

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

# Replace tokens
config['auth']['tokens'] = {
    '$ADMIN_TOKEN': {
        'role': 'admin',
        'permissions': ['read', 'write', 'admin'],
        'created': '$(date -Iseconds)'
    },
    '$VIEWER_TOKEN': {
        'role': 'viewer',
        'permissions': ['read'],
        'created': '$(date -Iseconds)'
    },
    '$SCANNER_TOKEN': {
        'role': 'scanner',
        'permissions': ['read', 'scan'],
        'created': '$(date -Iseconds)'
    }
}

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')  # Add trailing newline
PYEOF

# Set restrictive permissions
chmod 600 "$CONFIG_FILE"
chown $(whoami):$(whoami) "$CONFIG_FILE"

echo "✅ Config updated!"
echo ""
echo "🔐 Next steps:"
echo "1. Copy tokens to password manager"
echo "2. Delete $TOKENS_FILE after copying"
echo "3. Restart CogniWatch server"
echo "4. Test new tokens: curl -H 'Authorization: Bearer $ADMIN_TOKEN' http://127.0.0.1:9000/api/agents"
echo ""
echo "⚠️  Delete old tokens: cogniwatch-admin-2026 and cogniwatch-readonly"
