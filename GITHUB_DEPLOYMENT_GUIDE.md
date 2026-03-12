# GitHub Deployment Guide for CogniWatch

This guide walks you through pushing the CogniWatch codebase to GitHub.

## Prerequisites

- GitHub account (will use `cogniwatch` organization or your personal account)
- Git installed on your system
- Access to `/home/neo/cogniwatch/` directory

## Quick Deploy (Automated)

Run this script to automate the entire process:

```bash
#!/bin/bash
# GitHub Deployment Script for CogniWatch

cd /home/neo/cogniwatch

# 1. Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
fi

# 2. Create/update .gitignore (already created)
echo "✅ .gitignore is ready"

# 3. Add all files
echo "📂 Adding files to Git..."
git add -A

# 4. Commit
echo "💾 Creating initial commit..."
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

# 5. Create repository on GitHub (requires gh CLI)
echo "🔗 Creating GitHub repository..."

# Option A: Using GitHub CLI (recommended)
if command -v gh &> /dev/null; then
    gh repo create cogniwatch --public --description "🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments" --source=. --remote=origin --push
    
    # Add topics
    gh repo edit cogniwatch --add-topic ai --add-topic security --add-topic scanning --add-topic agents --add-topic framework-detection --add-topic shodan
    
    echo "✅ Repository created and pushed!"
    echo "🌐 View at: https://github.com/cogniwatch/cogniwatch"
else
    echo "⚠️ GitHub CLI (gh) not found. Manual steps required:"
    echo ""
    echo "1. Install GitHub CLI:"
    echo "   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "   echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "   sudo apt update && sudo apt install gh -y"
    echo ""
    echo "2. Authenticate:"
    echo "   gh auth login"
    echo ""
    echo "3. Create repo and push:"
    echo "   gh repo create cogniwatch --public --description \"🦈 Shodan for AI Agents\" --source=. --remote=origin --push"
    echo "   gh repo edit cogniwatch --add-topic ai --add-topic security --add-topic scanning --add-topic agents"
fi
```

## Manual Deployment (Step-by-Step)

If you prefer to run commands manually or the script fails:

### Step 1: Install GitHub CLI (if not installed)

```bash
# Download and install GitHub CLI
cd /tmp
curl -fsSL https://github.com/cli/cli/releases/latest/download/gh_2.87.3_linux_amd64.tar.gz -o gh.tar.gz
tar -xzf gh.tar.gz
sudo cp gh_*/bin/gh /usr/local/bin/
gh --version
```

### Step 2: Authenticate with GitHub

```bash
# Login to GitHub
gh auth login

# Follow the prompts:
# - GitHub.com
# - Yes
# - HTTPS
# - Login with a web browser
# - Copy the one-time code and complete auth in your browser
```

### Step 3: Initialize Git Repository

```bash
cd /home/neo/cogniwatch

# Check if already a git repo
if [ ! -d ".git" ]; then
    git init
fi
```

### Step 4: Create .gitignore

The `.gitignore` file has already been created at `/home/neo/cogniwatch/.gitignore`. It excludes:

- Database files (`*.db`, `*.sqlite`, `data/`)
- Environment variables (`.env`)
- Python cache (`__pycache__/`, `*.pyc`)
- Node modules
- Test scripts and experimental files
- Logs and temporary files

### Step 5: Add and Commit Files

```bash
# Add all files
git add -A

# Review what will be committed (optional)
git status

# Create commit
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
```

### Step 6: Create GitHub Repository

```bash
# Create the repository
gh repo create cogniwatch --public --description "🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments" --source=. --remote=origin --push

# If you want to use a different name:
# gh repo create cogniwatch-platform --public --description "..." --source=. --remote=origin --push
```

### Step 7: Add Repository Topics

```bash
# Add topics for better discoverability
gh repo edit cogniwatch --add-topic ai --add-topic security --add-topic scanning --add-topic agents --add-topic framework-detection --add-topic shodan
```

### Step 8: Verify Deployment

```bash
# Check remote
git remote -v

# Should show:
# origin  https://github.com/cogniwatch/cogniwatch.git (fetch)
# origin  https://github.com/cogniwatch/cogniwatch.git (push)

# View repository in browser
echo "🌐 Repository URL: https://github.com/cogniwatch/cogniwatch"
```

## Alternative: Using Git Without GitHub CLI

If you can't install `gh`, you can use standard git:

```bash
cd /home/neo/cogniwatch

# Initialize and commit (same as above)
git init
git add -A
git commit -m "Initial commit: CogniWatch"

# Create repository manually on GitHub.com:
# 1. Go to https://github.com/new
# 2. Repository name: cogniwatch
# 3. Description: 🦈 Shodan for AI Agents
# 4. Public
# 5. DO NOT initialize with README
# 6. Create repository

# Then add remote and push
git remote add origin https://github.com/cogniwatch/cogniwatch.git
git branch -M main
git push -u origin main
```

## Repository Structure

The following files and directories will be included:

```
cogniwatch/
├── webui/                  # Flask backend + Tabler UI
├── scanner/                # Network scanner engine
├── config/                 # Configuration files
├── signatures/             # Framework detection signatures
├── docs/                   # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── USER_GUIDE.md
│   ├── SECURITY.md
│   └── index.html          # Landing page
├── data/                   # ⚠️ EXCLUDED (scan results)
├── .env                    # ⚠️ EXCLUDED (secrets)
├── .gitignore              # ✅ Git ignore rules
├── README.md               # ✅ Main documentation
├── SECURITY.md             # ✅ Security policy
├── docker-compose.yml      # ✅ Docker Compose
├── Dockerfile              # ✅ Docker image
├── requirements.txt        # ✅ Python dependencies
└── cogniwatch.service      # ⚠️ EXCLUDED (systemd)
```

## File Statistics

- **Total documentation**: ~170KB
- **Core files**: webui/, scanner/, config/, signatures/
- **Excluded**: data/, .env, test scripts, logs, temporary files

## Post-Deployment Tasks

After pushing to GitHub:

1. **Enable GitHub Pages** (optional):
   - Go to Settings → Pages
   - Source: Deploy from branch `main` / `docs` folder
   - Save
   - Your site will be at: `https://cogniwatch.github.io/cogniwatch/`

2. **Add Website URL**:
   ```bash
   gh repo edit cogniwatch --homepage "https://cogniwatch.github.io/cogniwatch/"
   ```

3. **Enable Issues and Projects**:
   - Already enabled by default
   - Consider adding issue templates

4. **Set Up GitHub Actions** (optional):
   - Add CI/CD workflows
   - Automated testing
   - Docker image builds

5. **Add Collaborators** (if needed):
   ```bash
   gh repo collaborator add <username> --permission push
   ```

## Troubleshooting

### "Repository already exists"
```bash
# If cogniwatch repo exists, use a different name:
gh repo create cogniwatch-platform --public --source=. --remote=origin --push
```

### "Authentication failed"
```bash
# Re-authenticate:
gh auth logout
gh auth login
```

### "Large files rejected"
```bash
# Check for large files:
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {if ($3 > 10485760) print $2, $3, $4}'

# Remove large files from git history if needed:
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch path/to/large/file' --prune-empty HEAD
```

### "Data directory accidentally committed"
```bash
# Remove data directory from git (but keep locally):
git rm -r --cached data/
git commit -m "Remove data directory from version control"
git push
```

## Success Checklist

- [ ] GitHub repository created: `cogniwatch/cogniwatch`
- [ ] All code pushed successfully
- [ ] Documentation uploaded (README, API, SECURITY, etc.)
- [ ] Repository description set
- [ ] Topics added: ai, security, scanning, agents, framework-detection, shodan
- [ ] .gitignore excludes sensitive files
- [ ] No database files or secrets in repository
- [ ] Repository is public
- [ ] Website URL configured (optional)

## Next Steps After Deployment

1. Share repository URL with team
2. Set up project board for tracking issues
3. Create release tags for versions
4. Set up automated backups
5. Configure branch protection rules
6. Add CONTRIBUTING.md and CODE_OF_CONDUCT.md

---

**Need Help?**

If you encounter any issues during deployment:

1. Check GitHub status: https://www.githubstatus.com/
2. GitHub CLI docs: https://cli.github.com/manual/
3. Git documentation: https://git-scm.com/doc

**Repository URL**: `https://github.com/cogniwatch/cogniwatch`
