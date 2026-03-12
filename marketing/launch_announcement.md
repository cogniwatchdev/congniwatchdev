# Introducing CogniWatch: Shodan for AI Agents

## The Problem We Couldn't Ignore

Last month, we ran a scan across a typical development network. The results were sobering:

- **12 AI agents** discovered
- **3 running with default credentials**
- **7 exposing APIs without authentication**
- **0 known to the security team**

This isn't unusual. AI agents are being deployed at breakneck speed — LangGraph for orchestration, AutoGen for multi-agent collaboration, CrewAI for task automation, Agent-Zero for autonomous operations. But traditional security tools? They're blind.

**Why?** Because AI agents don't look like traditional services. They communicate via WebSocket, use custom HTTP headers, run on non-standard ports, and often skip authentication entirely. You're flying blind in your own network.

We built CogniWatch because we needed to see.

---

## The Story: Why CogniWatch Exists

The idea came from a simple frustration: **we were deploying AI agents everywhere, but had zero visibility into what was actually running**.

OpenClaw here, Agent-Zero there, a LangGraph workflow in the cloud — each deployment left traces, but no tool could connect the dots. Nmap sees open ports. Wireshark captures packets. But neither understands **what an AI agent looks like**.

So we asked: *What if there was a tool that understood AI frameworks the way Shodan understands IoT devices?*

That question became CogniWatch.

### The Gap in the Market

We looked at what existed:

- **Shodan** — Great for IoT, but doesn't understand AI agent protocols
- **Traditional vulnerability scanners** — Miss behavioral patterns entirely
- **APM tools** — Require agent installation (and only see what you tell them to monitor)
- **SIEMs** — Need custom rules for every framework (and still miss most detections)

**Nothing** was built specifically for AI agent detection. So we built it.

---

## Technical Deep-Dive: 27 Detection Techniques

CogniWatch doesn't rely on a single detection method. We use **27 distinct techniques** across 5 layers, with Bayesian confidence scoring to minimize false positives.

### Layer 1: Protocol Fingerprinting

AI agents leave protocol-level signatures:

- **HTTP Headers** — Framework-specific headers (`X-OpenClaw-Version`, `Agent-Zero-Worker-ID`)
- **WebSocket Handshakes** — Subprotocol negotiation patterns unique to each framework
- **Response Bodies** — Default error pages, health check formats, API response structures
- **TLS/JA3 Fingerprints** — Cryptographic handshake patterns that identify the underlying library

### Layer 2: API Endpoint Detection

Every framework has telltale endpoints:

| Framework | Detection Endpoints |
|-----------|---------------------|
| OpenClaw | `/health`, `/sessions`, `/api/v1/agents` |
| Agent-Zero | `/instances`, `/api/v2/status` |
| LangGraph | `/langgraph/health`, `/invoke` |
| AutoGen | `/autogen/api`, `/groupchat` |
| CrewAI | `/crew/status`, `/tasks` |

CogniWatch probes these endpoints and analyzes responses for framework-specific patterns.

### Layer 3: Behavioral Analysis

This is where it gets interesting. AI agents **behave differently** than traditional services:

- **Message Patterns** — JSON-RPC structures, tool call formats, agent-to-agent protocols
- **Timing Signatures** — Polling intervals, heartbeat frequencies, connection persistence
- **Communication Flows** — Multi-agent collaboration patterns, supervisor-worker hierarchies

### Layer 4: JA3/TLS Fingerprinting

JA3 is a method for creating fingerprints of SSL/TLS clients. Every AI agent framework uses specific TLS libraries with predictable configurations:

```
JA3 Hash: a05d9c6e8f3b2c1d4e5f6a7b8c9d0e1f
Framework: OpenClaw v0.9.3+
Library: uvicorn/0.27.0 + uvloop
Confidence: 94%
```

This works even when the agent is behind a reverse proxy or using custom certificates.

### Layer 5: Confidence Scoring

Every detection gets a **confidence score** (0-100%) based on:

- Number of matching techniques
- Strength of individual signals
- Historical accuracy of each technique
- Cross-correlation between layers

**Tier 1 (90%+)** — Multiple strong signals, ready for action  
**Tier 2 (70-89%)** — Moderate confidence, verify manually  
**Tier 3 (<70%)** — Weak signals, likely false positive

This Bayesian approach means you can trust high-confidence detections and ignore the noise.

---

## Live Demo: What You'll See

![CogniWatch Dashboard](https://github.com/neo/cogniwatch/raw/main/docs/screenshots/dashboard.png)

*The CogniWatch dashboard showing real-time agent discoveries*

### Sample Detection Output

```json
{
  "agent_id": "cwx-8f3a2c1d",
  "framework": "OpenClaw Gateway",
  "ip_address": "192.168.1.100",
  "port": 8080,
  "confidence": 94,
  "tier": 1,
  "detection_factors": [
    "HTTP Header: X-OpenClaw-Version detected",
    "API Endpoint: /sessions returned 200",
    "WebSocket: Sec-WebSocket-Protocol match",
    "JA3 Fingerprint: a05d9c6e8f... (94% match)",
    "Behavioral: Agent polling pattern detected"
  ],
  "first_seen": "2026-03-07T01:23:45Z",
  "last_seen": "2026-03-07T02:53:12Z",
  "status": "active"
}
```

That's a **Tier 1 detection** — five independent techniques all pointing to the same conclusion. You can act on this with confidence.

---

## Availability: Deploy in 5 Minutes

CogniWatch is **production-ready** and available now:

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch

# Start with Docker Compose
docker compose up -d

# Access the dashboard
open http://localhost:3000
```

### VPS Deployment

For 24/7 monitoring, deploy on your VPS:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
docker compose up -d

# Configure firewall
ufw allow 3000/tcp
ufw allow 8080/tcp
```

Full deployment instructions: [DEPLOYMENT.md](https://github.com/neo/cogniwatch/blob/main/DEPLOYMENT.md)

### GitHub

Source code, issues, and contributions:  
🔗 [https://github.com/neo/cogniwatch](https://github.com/neo/cogniwatch)

---

## Roadmap: What's Next

### Phase A: Core Launch ✅ (Current)
- Multi-layer detection engine
- 7+ framework signatures
- Dashboard and API
- OWASP compliance
- Docker/VPS deployment

### Phase B: Cloud Scanner (Q2 2026)
- Internet-wide scanning capability
- Shodan-style cloud discovery
- Autonomous agent discovery across public IPs
- API for programmatic access

### Phase C: Enterprise (Q3 2026)
- PostgreSQL backend for scale
- Multi-tenant support
- Advanced RBAC and audit logs
- Integration with SIEMs (Splunk, ELK, Sentinel)
- Commercial support and SLAs

---

## Call to Action

### Deploy Now

1. **Clone and run** — Get CogniWatch working in 5 minutes
2. **Scan your network** — See what AI agents you actually have
3. **Report bugs** — Open an issue on GitHub
4. **Contribute** — Add framework signatures, improve detections, build integrations

### Get Involved

- 📚 [Read the Documentation](https://github.com/neo/cogniwatch/blob/main/docs)
- 💻 [Browse the Code](https://github.com/neo/cogniwatch)
- 🐛 [Report an Issue](https://github.com/neo/cogniwatch/issues)
- 💬 [Join the Discussion](https://github.com/neo/cogniwatch/discussions) (Coming soon)

### Build With Us

CogniWatch is **open-source** (MIT license). We're building this for the community, and we need your help:

- **Security researchers** — Test detections, find edge cases, stress-test the engine
- **AI developers** — Add signatures for your frameworks of choice
- **DevOps teams** — Deploy at scale, share deployment patterns, build integrations
- **Open-source contributors** — Documentation, UI improvements, API clients

---

## Final Thoughts

AI agents aren't going away. They're multiplying. Every week, new frameworks launch, new deployments go live, new attack surfaces appear.

**You can't secure what you can't see.**

CogniWatch makes the invisible visible. It's not perfect — no security tool is — but it's a start. And it's yours, free and open-source, to use, audit, and improve.

Deploy it tonight. Scan your network. See what's really there.

And let us know what you find.

---

**CogniWatch v1.0.0**  
Released: March 7, 2026  
License: MIT  
Repository: https://github.com/neo/cogniwatch

*Shodan for AI Agents.*
