#!/bin/bash
# CogniWatch VPS Deployment Script
# Deploys local changes to production VPS (CogniWatch.dev)

set -e

# Config
VPS_HOST="45.63.21.236"
VPS_USER="root"
SSH_KEY="/home/neo/.ssh/do-cogniwatch"
LOCAL_PATH="/home/neo/cogniwatch"
REMOTE_PATH="/home/cogniwatch"

echo "🚀 CogniWatch VPS Deployment"
echo "=============================="
echo ""
echo "From: $LOCAL_PATH"
echo "To: $VPS_USER@$VPS_HOST:$REMOTE_PATH"
echo ""

# Confirm deployment
read -p "Deploy to production? [y/N] " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "📦 Syncing files to VPS..."
rsync -avz \
    --exclude 'data/' \
    --exclude 'logs/' \
    --exclude 'backups/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    $LOCAL_PATH/ \
    $VPS_USER@$VPS_HOST:$REMOTE_PATH/

echo ""
echo "🔄 Restarting containers on VPS..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST << 'EOF'
    cd /home/cogniwatch
    docker compose restart
    docker compose logs -f --tail=20
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Check: https://cogniwatch.dev"
echo "🔍 Verify: curl -Ik https://cogniwatch.dev"
echo ""
