#!/bin/bash
# =============================================================================
# CogniWatch File Transfer Script
# =============================================================================
# Usage: bash TRANSFER_TO_VPS.sh YOUR_VPS_IP
#
# This script transfers all necessary CogniWatch files to your VPS
# After running the deployment automation script.
# =============================================================================

set -e

VPS_IP="$1"

if [ -z "$VPS_IP" ]; then
    echo "Usage: bash TRANSFER_TO_VPS.sh YOUR_VPS_IP"
    echo ""
    echo "Example: bash TRANSFER_TO_VPS.sh 192.168.1.100"
    exit 1
fi

echo "CogniWatch File Transfer"
echo "========================"
echo ""
echo "Target VPS: $VPS_IP"
echo ""

# Check if SSH key exists
SSH_KEY="/home/neo/.openclaw/credentials/cogniwatch-vps/ssh-keys/cogniwatch-vps"
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found at $SSH_KEY"
    exit 1
fi

echo "Step 1: Creating directory structure on VPS..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@$VPS_IP "mkdir -p /home/cogniwatch/cogniwatch"

echo "Step 2: Transferring files (this may take a minute)..."

# Transfer essential files and directories
FILES_TO_TRANSFER=(
    "docker-compose.yml"
    "Dockerfile"
    ".env.example"
    "webui/"
    "scanner/"
    "config/"
    "database/"
    "data/"
    "requirements.txt"
)

for file in "${FILES_TO_TRANSFER[@]}"; do
    if [ -e "/home/neo/cogniwatch/$file" ]; then
        echo "  Transferring: $file"
        scp -i "$SSH_KEY" -r "/home/neo/cogniwatch/$file" "root@$VPS_IP:/home/cogniwatch/cogniwatch/"
    else
        echo "  WARNING: $file not found, skipping..."
    fi
done

echo ""
echo "Step 3: Setting permissions on VPS..."
ssh -i "$SSH_KEY" root@$VPS_IP "chown -R cogniwatch:cogniwatch /home/cogniwatch/cogniwatch"
ssh -i "$SSH_KEY" root@$VPS_IP "chmod 600 /home/cogniwatch/cogniwatch/.env 2>/dev/null || true"

echo ""
echo "✅ File transfer complete!"
echo ""
echo "Next steps:"
echo "  1. SSH to VPS: ssh -i $SSH_KEY cogniwatch@$VPS_IP"
echo "  2. Check deployment: docker compose ps"
echo "  3. View logs: docker compose logs -f"
echo "  4. Access dashboard: http://$VPS_IP:9000 (or your domain)"
