# 🚀 CogniWatch Launch Checklist

**Target:** March 8-9, 2026 (THIS WEEKEND!)

---

## ✅ **REBRAND COMPLETE** (Mar 5)

- [x] Folder renamed: `agent-shodan` → `cogniwatch`
- [x] README.md updated with CogniWatch branding
- [x] config.example.json updated
- [x] Python files updated (server.py, schema.py, openclaw_integration.py)
- [x] Dashboard HTML updated
- [x] harden.sh script updated
- [x] Tagline: "Stay watchful. Trace every thought."
- [x] All references changed from AgentShodan → CogniWatch

---

## 🔧 **TESTING** (Mar 5-6)

### **Local Testing**
```bash
cd /home/neo/cogniwatch

# 1. Install dependencies
pip install -r requirements.txt

# 2. Create config
cp config/config.example.json config/cogniwatch.json
# Edit with your OpenClaw Gateway token

# 3. Run hardening (optional but recommended)
./deploy/harden.sh

# 4. Initialize database
python -c "from database.schema import init_db; init_db()"

# 5. Start server
python webui/server.py

# 6. Access dashboard
open http://localhost:9000
```

**Expected Results:**
- ✅ Server starts without errors
- ✅ Database initialized at `data/cogniwatch.db`
- ✅ Dashboard loads at http://localhost:9000
- ✅ Navy/pink/cyan theme displays correctly
- ✅ Config loads from `config/cogniwatch.json`

### **Gateway Integration Test**
```bash
# Make sure OpenClaw Gateway is running
openclaw gateway status

# If not running:
openclaw gateway start

# Then test CogniWatch connection
python -c "
from agents.openclaw_integration import OpenClawGateway
gw = OpenClawGateway('ws://127.0.0.1:18789', 'YOUR_TOKEN')
print('Gateway connection test:', gw.connect())
"
```

**Expected Results:**
- ✅ Gateway connect成功 s
- ✅ Agents discovered (Neo, Clawdia)
- ✅ Sessions polling works
- ✅ Activities feed populates

---

## 🎨 **BRANDING** (Jannie to Complete)

### **Domain & GitHub** (After Testing Success)
```bash
[ ] Buy CogniWatch.dev domain (~$15)
    - Registrar: Porkbun, Cloudflare, or Namecheap
    
[ ] Claim GitHub organization
    - github.com/cogniwatch
    
[ ] Reserve social handles
    - Twitter/X: @cogniwatch
    - Discord: CogniWatch bot
```

### **Logo & Visual Assets** (Marketing Agent Mission)
```bash
[ ] Primary logo (PNG 800x800)
[ ] Secondary logo (simplified)
[ ] Icon/favicon (512x512)
[ ] Color palette (navy, teal, white)
[ ] Typography guide (Inter font)
[ ] Social media kit (Twitter, Discord, GitHub)
```

**Tools:**
- Ideogram.ai (free AI image generation)
- Canva (free design templates)
- Remotion (optional for animated logo)

---

## 📦 **GITHUB PREP** (Mar 7)

### **Repository Setup**
```bash
[ ] Create GitHub repo: github.com/cogniwatch/cogniwatch
[ ] Push code
    git init
    git add .
    git commit -m "👁️ Initial CogniWatch MVP release"
    git branch -M main
    git remote add origin git@github.com:cogniwatch/cogniwatch.git
    git push -u origin main

[ ] Update README with actual GitHub URL
[ ] Add LICENSE file (MIT)
[ ] Add .gitignore
[ ] Enable GitHub Issues
[ ] Enable GitHub Discussions
[ ] Set up GitHub Pages (optional landing page)
```

### **Release Assets**
```bash
[ ] Create first release: v0.1.0 (MVP)
[ ] Add release notes
[ ] Tag: #mvp #launch #agent-observability
```

---

## 📢 **LAUNCH ANNOUNCEMENT** (Mar 8-9)

### **OpenClaw Discord**
```markdown
👁️ **Announcing CogniWatch!**

After days of intense development, I'm thrilled to launch **CogniWatch** - "Shodan for AI Agents"!

**What:** Real-time observability & security monitoring for self-hosted AI agents
**Why:** No existing tool for agent monitoring (we're first!)
**Security:** OWASP Top 10 + CIPHER compliant (FORTRESS-level secure)
**Cost:** $0 (local, open-source MVP)

**Features:**
✅ Real-time agent health monitoring
✅ Activity feed (every tool call tracked)
✅ Cost tracking (per-agent, per-session)
✅ Anomaly detection (API spikes, unusual behavior)
✅ Security compliance (OWASP, audit logging)

**Tech Stack:**
- Python + Flask (backend)
- SQLite (database)
- Navy/pink/cyan theme (because aesthetics matter)
- OpenClaw Gateway integration

**Try it:**
```bash
git clone https://github.com/cogniwatch/cogniwatch.git
cd cogniwatch
pip install -r requirements.txt
python webui/server.py
```

**Docs:** https://github.com/cogniwatch/cogniwatch
**Feedback:** GitHub Issues or DM me!

Built by Jannie + Neo 🦾
Monitored by Clawdia (Head of Ops) 👁️

#agentops #observability #security #openclaw #ai-agents
```

### **Twitter/X Thread** (7-10 tweets)
```
1/ "Introducing CogniWatch - Shodan for AI Agents 👁️

Just launched MVP for monitoring self-hosted AI agents (OpenClaw, Agent-Zero, etc.)

Real-time observability + security compliance + cost tracking

All $0, open-source, local-first

GitHub: [link]

#AI #agents #observability"

2/ "Why CogniWatch?

AI agent market: $5.2B (2025) → $47.3B (2027)

But zero tools for monitoring self-hosted agents

You're flying blind:
- No idea what agents are doing
- No cost visibility
- No security audit trail

Time to change that 👁️"

[Tweets 3-7: Features, security, demo screenshots]

8/ "Built in 5 days with:
- Python + Flask
- SQLite
- OpenClaw Gateway
- OWASP Top 10 + CIPHER security

Big thanks to @OpenClaw for the amazing platform!

GitHub: [link]

Feedback welcome! #buildinpublic #AI #devtools"
```

### **Hacker News** (Submit on Launch Day)
```
Title: CogniWatch – Open-source AI agent observability (Shodan for Agents)
URL: https://github.com/cogniwatch/cogniwatch

Comments: "Built this because I run multiple AI agents (Neo, Clawdia) and had zero visibility.

Features: Real-time monitoring, cost tracking, anomaly detection, OWASP compliance

Self-hosted, $0, local-first

Would love feedback from HN community!"
```

### **Reddit** (r/selfhosted, r/devops, r/LocalLLaMA)
```
Title: "Built CogniWatch - Shodan for AI Agents (Open-Source, Local-First)"

Post: "Hey r/selfhosted!

I built CogniWatch after realizing I had no visibility into my self-hosted AI agents (Neo, Clawdia).

It's like Shodan/Datadog but specifically for AI agents:
- Real-time health monitoring
- Activity feed (every tool call)
- Cost tracking (tokens, $)
- Anomaly detection
- OWASP security compliance

Tech: Python, Flask, SQLite, OpenClaw Gateway integration
Cost: $0 (self-hosted)
Code: https://github.com/cogniwatch/cogniwatch

Built in 5 days, launching MVP this weekend!

Would love your feedback! Is this useful? What features would you add?"
```

---

## 📊 **SUCCESS METRICS** (Week 1)

```
🎯 GitHub stars: 20+
🎯 Clones: 50+
🎯 Discord feedback: 5+ users testing
🎯 Issues opened: 3+ (engagement!)
🎯 External mentions: 1+ (blog, tweet, Discord)
```

---

## 📊 **SUCCESS METRICS** (Month 1)

```
🎯 GitHub stars: 100+
🎯 Active users: 10+ (daily dashboard users)
🎯 Agent frameworks supported: 2+ (OpenClaw + Agent-Zero)
🎯 Community contributors: 2+
🎯 First feature request implemented from community
```

---

## 🎯 **POST-LAUNCH** (Week 2+)

### **Immediate Iterations**
```bash
[ ] Fix bugs from user reports
[ ] Add most-requested feature
[ ] Improve documentation
[ ] Add demo video/screenshot gallery
```

### **Phase B Planning** (Mar 15-29)
```bash
[ ] LAN agent discovery
[ ] Multi-framework support (Agent-Zero, Pico-Claw)
[ ] Advanced anomaly detection (ML-based)
[ ] Alert integrations (Discord webhooks, email)
```

---

## 🧪 **LAUNCH DAY CHECKLIST** (Mar 8)

**Morning (9 AM - 12 PM)**
```bash
[ ] Final testing (fresh install on clean machine)
[ ] Push to GitHub
[ ] Create release v0.1.0
[ ] Test installation from GitHub (not local folder)
```

**Afternoon (1 PM - 5 PM)**
```bash
[ ] OpenClaw Discord announcement
[ ] Twitter/X thread
[ ] Reddit posts (r/selfhosted, r/devops, r/LocalLLaMA)
[ ] Hacker News submission
[ ] Monitor feedback, respond to issues
```

**Evening (6 PM - 9 PM)**
```bash
[ ] Review day's feedback
[ ] Triage GitHub Issues
[ ] Plan next iteration
[ ] CELEBRATE! 🎉
```

---

## 🎉 **LAUNCH COMPLETE!**

**After launch:**
- [ ] Update memory/2026-03-08.md with launch results
- [ ] Send thank you to early testers
- [ ] Plan Phase B based on feedback
- [ ] Consider domain purchase (if traction confirmed)
- [ ] Rest & recover! 😅

---

**Status:** 🟡 **REBRAND COMPLETE, READY FOR TESTING**
**Next:** Run local tests (today/tomorrow)
**Launch:** Weekend (Mar 8-9)

**Let's ship this, Jannie!** 🚀👁️
