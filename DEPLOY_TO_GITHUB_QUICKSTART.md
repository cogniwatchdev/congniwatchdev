# 🦈 CogniWatch GitHub Deployment - Quick Start

**Mission**: Push CogniWatch to GitHub at `cogniwatch/cogniwatch`

---

## ⚡ One-Command Deploy (Recommended)

```bash
cd /home/neo/cogniwatch && bash deploy-to-github.sh
```

This script will:
1. Check for GitHub CLI (install if needed)
2. Authenticate with GitHub
3. Initialize git repository
4. Create .gitignore (already created ✅)
5. Commit all files
6. Create GitHub repository
7. Add topics and description
8. Push to GitHub

**Follow the prompts** when asked to authenticate!

---

## 📋 Manual Steps (If Script Fails)

### 1. Install GitHub CLI
```bash
cd /tmp
curl -fsSL https://github.com/cli/cli/releases/download/v2.87.3/gh_2.87.3_linux_amd64.tar.gz -o gh.tar.gz
tar -xzf gh.tar.gz
sudo cp gh_*/bin/gh /usr/local/bin/
gh --version
```

### 2. Authenticate
```bash
gh auth login
```

**Follow these prompts:**
- GitHub.com → Enter
- Yes → Enter
- HTTPS → Enter
- Login with web browser → Enter
- Copy the code shown
- Open browser and paste code
- Authorize OpenClaw

### 3. Initialize Git
```bash
cd /home/neo/cogniwatch
git init
git add -A
git commit -m "🚀 Initial commit: CogniWatch AI Agent Security Scanner"
```

### 4. Create Repository
```bash
gh repo create cogniwatch --public --description "🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments" --source=. --remote=origin --push
```

### 5. Add Topics
```bash
gh repo edit cogniwatch \
  --add-topic ai \
  --add-topic security \
  --add-topic scanning \
  --add-topic agents \
  --add-topic framework-detection \
  --add-topic shodan
```

### 6. Verify
```bash
echo "✅ Repository URL: https://github.com/cogniwatch/cogniwatch"
```

---

## 📁 What Gets Uploaded

### ✅ Included
- `webui/` - Flask backend + Tabler UI
- `scanner/` - Network scanner engine
- `config/` - Configuration files
- `signatures/` - Framework detection signatures
- `docs/` - All documentation (API, ARCHITECTURE, DEPLOYMENT, etc.)
- `README.md` - Main documentation
- `docker-compose.yml` - Docker setup
- `Dockerfile` - Container image
- `requirements.txt` - Python dependencies
- `.gitignore` - Exclusion rules

### ❌ Excluded (by .gitignore)
- `data/` - Scan results database (sensitive)
- `.env` - Environment secrets
- `*.db`, `*.sqlite` - SQLite databases
- `__pycache__/` - Python cache
- `*.log` - Log files
- `test_*.py`, `*_test.py` - Test scripts
- `exploit*.py`, `pentest*.py` - Security test scripts
- `venv/` - Virtual environment

---

## 🎯 Repository Configuration

After deployment, the repository will have:

- **Name**: `cogniwatch/cogniwatch`
- **Description**: "🦈 Shodan for AI Agents - Detect, monitor, and secure AI agent deployments"
- **Visibility**: Public
- **Topics**: ai, security, scanning, agents, framework-detection, shodan
- **Website**: (Optional) `https://cogniwatch.github.io/cogniwatch/`

---

## 🔧 Optional: Enable GitHub Pages

To host the landing page:

1. Go to `https://github.com/cogniwatch/cogniwatch/settings/pages`
2. Under "Source", select:
   - Branch: `main`
   - Folder: `/docs`
3. Click **Save**
4. Wait ~2 minutes
5. Your site will be live at: `https://cogniwatch.github.io/cogniwatch/`

Then add the website URL:
```bash
gh repo edit cogniwatch --homepage "https://cogniwatch.github.io/cogniwatch/"
```

---

## 🆘 Troubleshooting

### "Repository already exists"
```bash
# Use existing repo
cd /home/neo/cogniwatch
git remote add origin https://github.com/cogniwatch/cogniwatch.git
git push -u origin main
```

### "Authentication failed"
```bash
# Re-authenticate
gh auth logout
gh auth login
```

### "Large files rejected"
```bash
# Check for large files
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {if ($3 > 10485760) print $2, $3, $4}'

# Remove data directory if accidentally committed
git rm -r --cached data/
git commit -m "Remove data directory"
git push
```

### Script says "GitHub CLI not found"
```bash
# Use the temporary installation
export PATH="/tmp/gh_2.87.3_linux_amd64/bin:$PATH"
bash deploy-to-github.sh
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Repository accessible at https://github.com/cogniwatch/cogniwatch
- [ ] All documentation files visible (README, API.md, SECURITY.md, etc.)
- [ ] Code files present (webui/, scanner/, config/, signatures/)
- [ ] Description and topics set correctly
- [ ] No database files (.db, .sqlite) in repository
- [ ] No .env file with secrets in repository
- [ ] Repository is Public (not Private)

---

## 📊 File Statistics

- **Total size**: ~170KB documentation + code
- **Core directories**: 4 (webui/, scanner/, config/, signatures/)
- **Documentation files**: 7+ (README, API, SECURITY, DEPLOYMENT, USER_GUIDE, ARCHITECTURE, etc.)
- **Excluded files**: data/, .env, test scripts, logs

---

## 🚀 Post-Deployment Tasks

1. **Share the repository** with your team
2. **Create first release**:
   ```bash
   gh release create v1.0.0 --title "Initial Release" --notes "🦈 First public release of CogniWatch"
   ```
3. **Set up project board** for tracking issues
4. **Add issue templates** for bug reports and feature requests
5. **Configure branch protection** (Settings → Branches)
6. **Add CONTRIBUTING.md** for contributors

---

## 📞 Need Help?

- **GitHub CLI Manual**: https://cli.github.com/manual/
- **GitHub Docs**: https://docs.github.com/
- **Repository URL**: https://github.com/cogniwatch/cogniwatch

---

**Deployed with ❤️ by OpenClaw**
