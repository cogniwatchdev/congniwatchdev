#!/bin/bash
# 🔴 CRITICAL: Fix Authentication Bypass Vulnerability
# File: auth.py lines 197-204
# Run time: <2 minutes

set -e

AUTH_FILE="/home/neo/cogniwatch/webui/auth.py"
BACKUP_FILE="/home/neo/cogniwatch/webui/auth.py.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Fixing authentication bypass vulnerability..."

# Check file exists
if [ ! -f "$AUTH_FILE" ]; then
    echo "❌ ERROR: $AUTH_FILE not found!"
    exit 1
fi

# Create backup
cp "$AUTH_FILE" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Remove the vulnerable lines (197-204)
# Using sed to delete lines containing the bypass code
sed -i '197,204d' "$AUTH_FILE"

# Now we need to uncomment the return statement that should be at line 197
# First, find the line with the commented return
if grep -q "# return jsonify({'error': 'Authentication required'" "$AUTH_FILE"; then
    echo "✅ Found commented auth requirement"
    # Uncomment it
    sed -i "s/# return jsonify({'error': 'Authentication required'/return jsonify({'error': 'Authentication required'/" "$AUTH_FILE"
    sed -i "s/# }), 401/}), 401/" "$AUTH_FILE"
    echo "✅ Auth requirement uncommented"
else
    echo "⚠️  Could not find commented auth return statement"
    echo "📝 Manual fix required in $AUTH_FILE around line 197"
fi

echo "✅ Vulnerability fixed!"
echo ""
echo "Next steps:"
echo "1. Test authentication: curl http://127.0.0.1:9000/api/agents (should return 401)"
echo "2. Test with valid token: curl -H 'Authorization: Bearer YOUR_TOKEN' http://127.0.0.1:9000/api/agents"
echo "3. Restart CogniWatch server"
