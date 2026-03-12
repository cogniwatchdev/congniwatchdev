#!/bin/bash
# CogniWatch GitHub Deployment Script
# This script automates the entire GitHub deployment process
# Run with: bash deploy-to-github.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🦈 CogniWatch GitHub Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Navigate to CogniWatch directory
cd /home/neo/cogniwatch

echo -e "${YELLOW}📁 Working directory: $(pwd)${NC}"
echo ""

# Step 1: Check for GitHub CLI
echo -e "${YELLOW}Step 1: Checking for GitHub CLI...${NC}"
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI found: $(gh --version | head -1)${NC}"
else
    echo -e "${RED}❌ GitHub CLI not found${NC}"
    echo ""
    echo "Installing GitHub CLI..."
    
    # Try to install gh
    if [ -d "/tmp/gh_2.87.3_linux_amd64/bin" ]; then
        echo "Found pre-downloaded GitHub CLI in /tmp"
        export PATH="/tmp/gh_2.87.3_linux_amd64/bin:$PATH"
        echo -e "${GREEN}✅ GitHub CLI ready (temporary installation)${NC}"
    else
        echo -e "${RED}Please install GitHub CLI manually:${NC}"
        echo "  cd /tmp"
        echo "  curl -fsSL https://github.com/cli/cli/releases/latest/download/gh_2.87.3_linux_amd64.tar.gz -o gh.tar.gz"
        echo "  tar -xzf gh.tar.gz"
        echo "  sudo cp gh_*/bin/gh /usr/local/bin/"
        exit 1
    fi
fi
echo ""

# Step 2: Check authentication
echo -e "${YELLOW}Step 2: Checking GitHub authentication...${NC}"
if gh auth status &> /dev/null; then
    echo -e "${GREEN}✅ Already authenticated${NC}"
    GH_USER=$(gh api user | jq -r '.login')
    echo -e "${BLUE}👤 Logged in as: ${GH_USER}${NC}"
else
    echo -e "${YELLOW}⚠️  Not authenticated with GitHub${NC}"
    echo ""
    echo -e "${BLUE}Please authenticate by running:${NC}"
    echo "  gh auth login"
    echo ""
    echo "Follow these steps:"
    echo "  1. Choose GitHub.com"
    echo "  2. Select HTTPS protocol"
    echo "  3. Login with a web browser"
    echo "  4. Copy the one-time code"
    echo "  5. Complete authentication in your browser"
    echo ""
    read -p "Press Enter after completing authentication..."
    
    # Verify authentication
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}❌ Authentication failed. Please try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Authentication successful!${NC}"
    GH_USER=$(gh api user | jq -r '.login')
    echo -e "${BLUE}👤 Logged in as: ${GH_USER}${NC}"
fi
echo ""

# Step 3: Initialize Git repository
echo -e "${YELLOW}Step 3: Initializing Git repository...${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git repository already initialized${NC}"
else
    echo "Creating new Git repository..."
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi
echo ""

# Step 4: Check .gitignore
echo -e "${YELLOW}Step 4: Verifying .gitignore...${NC}"
if [ -f ".gitignore" ]; then
    echo -e "${GREEN}✅ .gitignore exists${NC}"
else
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
*.py[cod]
*$py.class
*.so
.Python
__pycache__/
*.pyc
venv/

# Virtual environments
venv/
ENV/
env/
.venv

# Database
*.db
*.sqlite
*.sqlite3
data/

# Environment variables
.env
.env.local

# Node
node_modules/

# Logs
*.log

# Secrets
*.key
*.pem
EOF
    echo -e "${GREEN}✅ .gitignore created${NC}"
fi
echo ""

# Step 5: Add all files
echo -e "${YELLOW}Step 5: Adding files to Git...${NC}"
git add -A
echo -e "${GREEN}✅ Files staged${NC}"

# Show what will be committed
FILES_COUNT=$(git status --short | wc -l)
echo -e "${YELLOW}📊 Files to commit: ${FILES_COUNT}${NC}"
echo ""

# Step 6: Create commit
echo -e "${YELLOW}Step 6: Creating initial commit...${NC}"
git commit -m "🚀 Initial commit: CogniWatch AI Agent Security Scanner

🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments

Features:
- Network scanning for AI agent frameworks
- Web UI with Tabler dashboard
- SQLite database for scan results
- REST API for automation
- Docker support

Includes:
- Core scanner engine
- Flask web interface
- API documentation
- Deployment guides
- Security documentation"

echo -e "${GREEN}✅ Initial commit created${NC}"
echo ""

# Step 7: Check if repository exists on GitHub
echo -e "${YELLOW}Step 7: Creating GitHub repository...${NC}"
REPO_NAME="cogniwatch"

if gh repo view "$REPO_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Repository '$REPO_NAME' already exists on GitHub${NC}"
    echo "Do you want to:"
    echo "  1) Use existing repository and push to it"
    echo "  2) Create a new repository with a different name"
    echo "  3) Cancel deployment"
    read -p "Choose option (1/2/3): " choice
    
    case $choice in
        1)
            echo "Using existing repository..."
            if git remote get-url origin &> /dev/null; then
                echo "Remote 'origin' already configured"
            else
                git remote add origin https://github.com/cogniwatch/cogniwatch.git
            fi
            ;;
        2)
            read -p "Enter new repository name: " new_name
            REPO_NAME="$new_name"
            ;;
        3)
            echo "Deployment cancelled"
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
fi

# Create repository
echo "Creating repository: $REPO_NAME"
if gh repo create "$REPO_NAME" --public --description "🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments" --source=. --remote=origin --push; then
    echo -e "${GREEN}✅ Repository created and pushed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Repository creation may have failed or already exists${NC}"
    # Try to push anyway
    git branch -M main
    git remote set-url origin https://github.com/cogniwatch/$REPO_NAME.git 2>/dev/null || git remote add origin https://github.com/cogniwatch/$REPO_NAME.git
    git push -u origin main
fi
echo ""

# Step 8: Add repository topics
echo -e "${YELLOW}Step 8: Adding repository topics...${NC}"
gh repo edit "$REPO_NAME" --add-topic ai \
    --add-topic security \
    --add-topic scanning \
    --add-topic agents \
    --add-topic framework-detection \
    --add-topic shodan
echo -e "${GREEN}✅ Topics added${NC}"
echo ""

# Step 9: Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}✅ Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}🎉 CogniWatch is now on GitHub!${NC}"
echo ""
echo -e "📦 Repository: ${GREEN}cogniwatch/$REPO_NAME${NC}"
echo -e "🌐 URL: ${BLUE}https://github.com/cogniwatch/$REPO_NAME${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Visit the repository URL in your browser"
echo "  2. Configure GitHub Pages (optional)"
echo "  3. Add collaborators (if needed)"
echo "  4. Set up GitHub Actions for CI/CD"
echo ""
echo -e "${BLUE}========================================${NC}"

# End of script
