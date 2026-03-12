#!/bin/bash
# CogniWatch Deployment Script
# Quick deploy to VPS or local server

set -e

echo "🦈 CogniWatch Deployment"
echo "======================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warn "Running as root. Consider creating a cogniwatch user for production."
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect deployment type
echo "Select deployment type:"
echo "  1) Docker (Recommended for testing)"
echo "  2) Systemd (Recommended for production)"
echo ""
read -p "Choice [1-2]: " DEPLOY_TYPE

if [ "$DEPLOY_TYPE" -eq "1" ]; then
    # Docker Deployment
    log_info "Docker Deployment Selected"
    echo ""
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi
    
    # Set COMPOSE_CMD
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Create .env
    if [ ! -f ".env" ]; then
        log_info "Creating .env from .env.example"
        cp .env.example .env
        log_warn "Edit .env with your configuration before starting!"
        read -p "Press Enter to open .env in nano..."
        nano .env
    else
        log_info ".env already exists"
    fi
    
    # Build and deploy
    log_info "Building Docker images..."
    $COMPOSE_CMD build
    
    log_info "Starting CogniWatch services..."
    $COMPOSE_CMD up -d
    
    log_info "Deployment complete!"
    echo ""
    HOST_IP=$(hostname -I | awk '{print $1}')
    echo "🌐 Web UI: http://${HOST_IP}:9000"
    echo "📊 Status:  $COMPOSE_CMD ps"
    echo "📋 Logs:    $COMPOSE_CMD logs -f"
    
elif [ "$DEPLOY_TYPE" -eq "2" ]; then
    # Systemd Deployment
    log_info "Systemd Deployment Selected"
    echo ""
    
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    # Create user
    if ! id "cogniwatch" &>/dev/null; then
        log_info "Creating cogniwatch user..."
        sudo useradd --system --no-create-home --shell /bin/false cogniwatch
    else
        log_info "User cogniwatch already exists"
    fi
    
    # Create directories
    log_info "Creating directory structure..."
    sudo mkdir -p /opt/cogniwatch
    sudo mkdir -p /var/log/cogniwatch
    sudo mkdir -p /etc/cogniwatch
    
    # Copy files
    log_info "Copying application files..."
    sudo cp -r . /opt/cogniwatch/
    sudo chown -R cogniwatch:cogniwatch /opt/cogniwatch
    sudo chown -R cogniwatch:cogniwatch /var/log/cogniwatch
    
    # Create virtual environment
    log_info "Setting up Python virtual environment..."
    sudo -u cogniwatch python3 -m venv /opt/cogniwatch/venv
    sudo -u cogniwatch /opt/cogniwatch/venv/bin/pip install --upgrade pip
    sudo -u cogniwatch /opt/cogniwatch/venv/bin/pip install -r requirements.txt
    
    # Configure
    log_info "Configuring application..."
    if [ ! -f "/opt/cogniwatch/config/cogniwatch.json" ]; then
        sudo cp /opt/cogniwatch/config/config.example.json /opt/cogniwatch/config/cogniwatch.json
        log_warn "Edit /opt/cogniwatch/config/cogniwatch.json with your settings!"
    fi
    
    if [ ! -f "/etc/cogniwatch/.env" ]; then
        sudo cp .env.example /etc/cogniwatch/.env
        log_warn "Edit /etc/cogniwatch/.env with your settings!"
    fi
    
    # Install systemd services
    log_info "Installing systemd services..."
    sudo cp cogniwatch.service /etc/systemd/system/
    sudo cp cogniwatch-scanner.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Enable and start
    log_info "Enabling and starting services..."
    sudo systemctl enable cogniwatch.service
    sudo systemctl enable cogniwatch-scanner.service
    sudo systemctl start cogniwatch.service
    sudo systemctl start cogniwatch-scanner.service
    
    # Setup firewall
    echo ""
    read -p "Configure UFW firewall? [y/N]: " CONFIGURE_UFW
    
    if [ "$CONFIGURE_UFW" = "y" ] || [ "$CONFIGURE_UFW" = "Y" ]; then
        log_info "Configuring UFW firewall..."
        
        if ! command -v ufw &> /dev/null; then
            log_warn "UFW not found. Installing..."
            sudo apt install -y ufw
        fi
        
        sudo ufw allow ssh
        sudo ufw allow from 192.168.0.0/24 to any port 9000 proto tcp comment "CogniWatch Local"
        
        if ! sudo ufw status | grep -q "Status: active"; then
            read -p "Enable UFW? [y/N]: " ENABLE_UFW
            if [ "$ENABLE_UFW" = "y" ] || [ "$ENABLE_UFW" = "Y" ]; then
                sudo ufw enable
            fi
        fi
    fi
    
    log_info "Deployment complete!"
    echo ""
    echo "🌐 Web UI: http://$(hostname -I | awk '{print $1}'):9000"
    echo "📊 Status:  sudo systemctl status cogniwatch"
    echo "📋 Logs:    sudo journalctl -u cogniwatch -f"
    echo ""
    echo "🔧 Management commands:"
    echo "   sudo systemctl start cogniwatch"
    echo "   sudo systemctl stop cogniwatch"
    echo "   sudo systemctl restart cogniwatch"
    
else
    log_error "Invalid selection"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Review configuration files"
echo "   2. Access web UI at http://YOUR_IP:9000"
echo "   3. Check logs for any issues"
echo "   4. Review DEPLOYMENT.md for advanced options"
