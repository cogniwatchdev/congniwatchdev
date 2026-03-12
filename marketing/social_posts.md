# CogniWatch Launch — Social Media Posts

## Twitter/X Thread (5 tweets)

### Tweet 1/5 — Hook
🚨 AI agents are deploying everywhere. Your security tools can't see them.

We built @CogniWatch to fix that.

"Shodan for AI Agents" is live. Detect OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI + more with 95%+ confidence.

Thread 🧵👇

#AIsecurity #CyberSecurity

---

### Tweet 2/5 — The Problem
The visibility gap is real:

• 12 AI agents discovered on a dev network
• 3 running with default credentials  
• 7 exposing APIs without auth
• 0 known to the security team

Traditional scanners miss AI agents because they don't look like regular services.

CogniWatch changes that.

---

### Tweet 3/5 — How It Works
27 detection techniques across 5 layers:

1️⃣ Protocol fingerprinting (HTTP, WebSocket, TLS/JA3)
2️⃣ API endpoint detection
3️⃣ Behavioral analysis
4️⃣ Confidence scoring (Bayesian inference)
5️⃣ Real-time telemetry

OWASP Top 10 + LLM Top 10 compliant. ✅✅

---

### Tweet 4/5 — The Tech
JA3/TLS fingerprinting alone can identify AI agents by their cryptographic handshake patterns — no decryption needed.

Combine that with API probes, behavioral analysis, and framework signatures, and you get 95%+ detection confidence.

Demo: [screenshot of dashboard]

Alt text: CogniWatch dashboard showing 3 detected AI agents with confidence scores (94%, 87%, 91%), IP addresses, framework names (OpenClaw, Agent-Zero, LangGraph), and status indicators. Dark theme with teal accents.

---

### Tweet 5/5 — CTA
Deploy in 5 minutes:

```
git clone https://github.com/neo/cogniwatch
docker compose up -d
```

That's it. You're now monitoring for AI agents.

Open-source. Self-hostable. Production-ready.

🔗 github.com/neo/cogniwatch

#Shodan #AIAgents #InfoSec #DevSecOps

---

## LinkedIn Post (Professional Tone)

**Introducing CogniWatch: The First Search Engine for AI Agents**

AI infrastructure is growing exponentially — but visibility hasn't kept pace. Security teams can see every server, container, and traditional service. But AI agents? They're invisible.

That blind spot ends today.

I'm excited to announce **CogniWatch v1.0.0** — a purpose-built detection engine that discovers AI agents across your network with 95%+ confidence.

**What makes CogniWatch different:**

• 27 detection techniques across 5 layers (protocol, API, behavioral, TLS/JA3, confidence scoring)
• Native support for 7+ major frameworks (OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI, and more)
• OWASP Top 10 + LLM Top 10 compliant — built for production security
• Deploy in 5 minutes with Docker, or scale to VPS for 24/7 monitoring
• Open-source (MIT license) — audit it, fork it, contribute

**Why this matters:**

Last month, we scanned a typical development network and found 12 AI agents. Three were running with default credentials. Seven exposed unauthenticated APIs. Zero were known to the security team.

This isn't unusual. AI agents communicate via WebSocket, use custom HTTP headers, and often skip authentication entirely. Traditional tools miss them completely.

CogniWatch makes the invisible visible.

**Get started:**
```bash
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch && docker compose up -d
```

Try it. Scan your network. See what's really there.

🔗 https://github.com/neo/cogniwatch

Shoutout to the open-source community — this is built for you. Contributions welcome.

#AIsecurity #CyberSecurity #ArtificialIntelligence #DevSecOps #OpenSource #MachineLearning #CloudSecurity #InfoSec

*Alt text for attached image: CogniWatch dashboard screenshot showing detected AI agents with framework names, IP addresses, confidence scores, and real-time telemetry graphs. Professional dark theme interface.*

---

## Reddit Posts

### r/netsec — Technical Angle

**Title:** "Shodan for AI Agents" — Open-source tool detects AI agent deployments with 27 techniques, 95%+ confidence

**Post:**

We just launched CogniWatch v1.0.0 — an open-source detection engine for AI agents.

**The problem:** AI agents (OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI, etc.) are being deployed everywhere, but traditional security tools can't detect them. They use WebSocket, custom HTTP headers, non-standard ports, and often skip auth entirely.

**The solution:** Multi-layer detection with 27 distinct techniques:

- Protocol fingerprinting (HTTP headers, WebSocket handshakes, TLS/JA3)
- API endpoint probing (framework-specific paths)
- Behavioral analysis (message patterns, timing, communication flows)
- Bayesian confidence scoring (95%+ accuracy)
- Real-time telemetry

**Results from a recent scan:**
- 12 AI agents discovered
- 3 with default credentials
- 7 exposing unauthenticated APIs
- 0 known to the security team

**Technical highlights:**
- OWASP Top 10 + LLM Top 10 compliant
- JWT auth, API keys, RBAC, AES-256-GCM
- Docker or VPS deployment
- MIT license

Deploy: `git clone https://github.com/neo/cogniwatch && docker compose up -d`

Repo: https://github.com/neo/cogniwatch

Happy to answer questions about the detection engine, framework signatures, or anything else. Built this for the community — contributions welcome.

---

### r/MachineLearning — Developer Angle

**Title:** [Tool] CogniWatch — Detect and monitor AI agent deployments in your infrastructure (open-source)

**Post:**

If you're deploying AI agents (LangGraph, AutoGen, CrewAI, OpenClaw, Agent-Zero, etc.), you should know what's actually running in your network.

We built **CogniWatch** — a detection engine that finds AI agents with 95%+ confidence using 27 different techniques.

**Why we made this:**

We were deploying agents everywhere but had zero visibility. Nmap sees ports, Wireshark captures packets, but neither understands what an AI agent looks like. So we built a tool that does.

**How it works:**

The scanner probes for framework-specific endpoints, analyzes HTTP/WebSocket headers, fingerprints TLS handshakes (JA3), and monitors behavioral patterns. Bayesian inference combines all signals into a confidence score.

**Features:**
- 7+ framework signatures (growing)
- Real-time dashboard
- API for automation
- OWASP compliant (security-first design)
- Docker deployment (5 minutes)

**Try it:**
```bash
git clone https://github.com/neo/cogniwatch
cd cogniwatch && docker compose up -d
# Open http://localhost:3000
```

GitHub: https://github.com/neo/cogniwatch

This is open-source (MIT). If you're using AI agents in production, give it a shot. If you want to contribute framework signatures or improve detections, PRs welcome.

---

## Discord/Slack Community Posts

### Variant 1 — Security-Focused (Discord r/netsec style)

**🚨 New Tool Alert: CogniWatch — "Shodan for AI Agents"**

AI agents are deploying everywhere, but traditional scanners can't detect them. CogniWatch fixes that with 27 detection techniques and 95%+ confidence scoring.

**Detects:** OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI + more  
**Methods:** Protocol fingerprinting, API probing, behavioral analysis, JA3/TLS  
**Security:** OWASP Top 10 + LLM Top 10 compliant  
**Deploy:** `docker compose up -d`  

GitHub: https://github.com/neo/cogniwatch

Scan your network tonight. See what you're missing. 👁️

---

### Variant 2 — DevOps/Infrastructure (Slack DevOps channel)

**🔍 CogniWatch v1.0.0 — AI Agent Discovery for Your Infrastructure**

If you're running AI agents (LangGraph, AutoGen, CrewAI, etc.), you need to know what's deployed and where.

CogniWatch is a new open-source tool that detects AI agents across your network with 95%+ confidence. Uses 27 detection techniques including JA3 fingerprinting, API endpoint probing, and behavioral analysis.

**Quick start:**
```bash
git clone https://github.com/neo/cogniwatch
cd cogniwatch && docker compose up -d
```

Dashboard: http://localhost:3000

Perfect for homelabs, dev environments, or production monitoring. OWASP compliant, production-ready.

Repo: https://github.com/neo/cogniwatch

---

### Variant 3 — Casual/Tech Enthusiast (Discord general tech)

**PSA: There's now a "Shodan for AI Agents" thing**

Called CogniWatch. It finds AI agents on your network (OpenClaw, Agent-Zero, LangGraph, etc.) using 27 different detection methods.

Why? Because AI agents leave traces everywhere, but normal tools can't see them. This one can. 95%+ detection confidence.

Takes 5 minutes to deploy:
```
git clone https://github.com/neo/cogniwatch
docker compose up -d
```

Open-source, free, looks slick. Worth checking out if you run any AI agents.

https://github.com/neo/cogniwatch

---

## Hacker News "Show HN" Post

**Title:** Show HN: CogniWatch – Shodan for AI Agents (open-source, 27 detection techniques)

**Post:**

Hi HN!

We're launching CogniWatch — an open-source detection engine for AI agents.

**The problem:** AI agents (OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI) are being deployed everywhere, but traditional security tools can't detect them. They use WebSocket, custom HTTP headers, and non-standard ports. You're flying blind.

**The solution:** CogniWatch uses 27 distinct detection techniques across 5 layers:

1. Protocol fingerprinting (HTTP headers, WebSocket handshakes, TLS/JA3)
2. API endpoint detection (framework-specific paths)
3. Behavioral analysis (message patterns, timing, communication flows)
4. Confidence scoring (Bayesian inference, 95%+ accuracy)
5. Real-time telemetry (live connections, API calls, resource usage)

**Why we built this:** We scanned a dev network and found 12 AI agents. Three had default credentials. Seven exposed unauthenticated APIs. Zero were known to the security team. This isn't unusual — AI visibility is a blind spot across the industry.

**Tech highlights:**
- OWASP Top 10 + LLM Top 10 compliant
- JWT auth, API keys, RBAC, AES-256-GCM encryption
- SQLite (scalable to PostgreSQL)
- Docker or VPS deployment
- MIT license

**Try it:**
```bash
git clone https://github.com/neo/cogniwatch
cd cogniwatch && docker compose up -d
# Open http://localhost:3000
```

GitHub: https://github.com/neo/cogniwatch

We're security folks who got tired of not knowing what AI agents were running in our networks. Built this over the past few months. Would love feedback from the HN community — especially on detection accuracy, framework coverage, and anything we're missing.

AMA!

---

## Hashtag Bank

**Primary:**
- #AIsecurity
- #CyberSecurity
- #AIAgents
- #InfoSec
- #DevSecOps

**Secondary:**
- #Shodan
- #MachineLearning
- #ArtificialIntelligence
- #CloudSecurity
- #OpenSource
- #SecurityTools
- #ThreatDetection
- #NetworkSecurity

**Platform-Specific:**

*Twitter/X:* 2-3 hashtags per tweet max  
*LinkedIn:* 5-8 hashtags in post body or comments  
*Reddit:* No hashtags (community guidelines)  
*Discord/Slack:* 0-1 for emphasis only

---

## Screenshot Descriptions (Alt Text)

### Dashboard Overview
"Dark-themed CogniWatch dashboard showing 3 detected AI agents in a list. Each row displays framework name (OpenClaw Gateway, Agent-Zero Instance, LangGraph Orchestrator), IP address and port, confidence score badge (94%, 87%, 91%), status indicator (green dot for active), and last seen timestamp. Right sidebar shows real-time telemetry graphs with connection counts and API call frequency. Top navigation includes 'Scan Network', 'Settings', and 'Documentation' buttons."

### Agent Detail View
"Expanded agent detail modal showing detection factors: HTTP Header match, API endpoint response, WebSocket handshake pattern, JA3 fingerprint hash, behavioral analysis result. Confidence breakdown displays a progress bar at 94% with individual technique scores. Bottom section shows agent metadata: first seen date, last contact, total requests, and associated IP geolocation."

### Confidence Scoring Visualization
"Bayesian confidence score visualization with 5 horizontal bars representing each detection layer (Protocol, API, Behavioral, TLS, Telemetry). Each bar filled to different levels showing individual technique contributions. Overall confidence score of 94% displayed prominently with 'Tier 1 — High Confidence' badge in green. Tooltip text explains scoring methodology."

---

## Posting Schedule Recommendations

**Day 1 (Launch Day):**
- Twitter thread (morning, 9-10 AM EST)
- LinkedIn post (morning, 8-9 AM EST)
- Reddit r/netsec (afternoon, 2-3 PM EST)
- Hacker News "Show HN" (morning, 10-11 AM EST for front page chance)

**Day 2-3:**
- Reddit r/MachineLearning (different angle, day 2)
- Discord/Slack communities (spread across day 2-3)
- Twitter follow-up (day 3, share early feedback/stats)

**Day 7:**
- Twitter thread recap (week later, "Week 1 with CogniWatch" — stats, learnings, contributors)

---

## Engagement Tips

**Respond to:**
- Technical questions about detection methods
- Framework signature requests
- Bug reports (redirect to GitHub issues)
- Contribution offers (point to CONTRIBUTING.md)

**Avoid:**
- Arguing about false positives (acknowledge, investigate, improve)
- Overpromising on cloud scanner timeline
- Engaging with bad-faith criticism

**Amplify:**
- User success stories ("Found X agents I didn't know about!")
- Contributions and PRs
- Blog posts or tutorials from the community
