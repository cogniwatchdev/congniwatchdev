# CogniWatch — Shodan for AI Agents

## Hero Section

**Shodan for AI Agents**

*Detect, monitor, and secure AI agent deployments across your infrastructure with 95%+ confidence*

---

## The Problem: The AI Visibility Gap

AI agents are being deployed at unprecedented speed — but **visibility is zero**.

Your security team can see every server, container, and service. But when AI agents start communicating via WebSocket, HTTP, and custom protocols, **traditional tools go blind**.

**The reality:**
- 🚨 Agents deploy without security team knowledge
- 🔓 Default credentials and exposed APIs are common
- 👁️ No centralized telemetry or monitoring
- ⚠️ You can't secure what you can't detect

**Result:** Critical blind spots in your AI infrastructure.

---

## The Solution: Multi-Layer Detection

CogniWatch is a **purpose-built detection engine** that discovers AI agents through 27 distinct techniques across multiple layers:

### Detection Layers

1. **Protocol Fingerprinting** — HTTP headers, WebSocket handshakes, TLS/JA3 signatures
2. **API Endpoint Detection** — Framework-specific paths and behavioral patterns
3. **Behavioral Analysis** — Communication patterns, message structures, timing
4. **Confidence Scoring** — Bayesian inference with 95%+ accuracy
5. **Real-Time Telemetry** — Live connections, API calls, resource usage

### How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────┐     ┌─────────────┐
│   Network       │────▶│   Multi-Layer    │────▶│   SQLite │────▶│  Dashboard  │
│   Scanner       │     │   Detector       │     │   DB     │     │  Real-time  │
│  27 Techniques  │     │  Confidence AI   │     │  Telemetry│    │  Agent List │
└─────────────────┘     └──────────────────┘     └──────────┘     └─────────────┘
```

**Output:** Actionable intelligence on every AI agent in your network.

---

## Key Features

### 🔎 7+ Framework Signatures
Native detection for:
- **OpenClaw** (all variants)
- **Agent-Zero** (multi-instance)
- **LangGraph** (LangChain)
- **AutoGen** (Microsoft)
- **CrewAI**
- **Google ADK**
- **Microsoft AutoDev**

### 🎯 JA3/TLS Fingerprinting
Identify AI agents by their TLS handshake patterns — no decryption needed.

### 📊 Confidence Scoring
Every detection includes:
- **Confidence score** (0-100%)
- **Priority tier** (Tier 1/2/3)
- **Detection factors** (what triggered the match)

### 📈 Real-Time Telemetry
Live monitoring of:
- Active connections
- API call frequency
- Message throughput
- Resource consumption

### 🛡️ OWASP Compliant
Built with security first:
- ✅ OWASP Top 10 covered (10/10)
- ✅ OWASP LLM Top 10 covered (10/10)
- JWT authentication
- API key management
- Role-based access control (RBAC)
- AES-256-GCM encryption

### 🐳 Deploy in 5 Minutes
```bash
docker compose up -d
```

That's it. You're now monitoring for AI agents.

---

## Social Proof

> *"Detected 12 AI agents across 3 networks in the first hour — including 2 we didn't know existed."*

**Live Statistics:**
- **27 detection techniques** deployed
- **95%+ confidence** scoring
- **OWASP 20/20** compliant
- **Open-source** and self-hostable

---

## Call to Action

### Deploy CogniWatch Today

**Get started in 3 steps:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/neo/cogniwatch.git
   ```

2. **Deploy on your VPS**
   ```bash
   cd cogniwatch && docker compose up -d
   ```

3. **Open your dashboard**
   ```
   http://your-vps-ip:3000
   ```

### Links
- 📚 [Documentation](/docs)
- 💻 [GitHub Repository](https://github.com/neo/cogniwatch)
- 🎮 [Live Demo](#) (Request access)
- 📖 [API Reference](/docs/api)

---

## FAQ

### How does CogniWatch detect AI agents?

CogniWatch uses 27 distinct detection techniques across 5 layers: protocol fingerprinting, API endpoint detection, behavioral analysis, TLS/JA3 signatures, and confidence scoring. This multi-layer approach ensures 95%+ detection accuracy while minimizing false positives.

### Do I need to install agents on my systems?

No. CogniWatch operates as a **passive scanner** — it monitors network traffic and probes endpoints without requiring any software installation on your AI agent systems.

### Can CogniWatch detect custom-built agents?

Yes. While CogniWatch includes signatures for 7+ major frameworks, the behavioral detection layer can identify unknown agents based on communication patterns, message structures, and API behaviors.

### Is CogniWatch suitable for production environments?

Absolutely. CogniWatch is **OWASP Top 10 + LLM Top 10 compliant**, with JWT authentication, API key management, RBAC, and AES-256-GCM encryption. It's built for production security teams.

### How scalable is CogniWatch?

CogniWatch uses SQLite for lightweight deployments and can scale to PostgreSQL for larger networks. The scanner is designed to handle thousands of endpoints with configurable scan intervals.

### Is it really free?

Yes. CogniWatch is **open-source** (MIT license) and free to use. Deploy it on your VPS, contribute to development, or fork it for custom needs.

---

## Footer

### CogniWatch
**Shodan for AI Agents**

### Product
- [Features](#features)
- [Documentation](/docs)
- [API Reference](/docs/api)
- [Changelog](https://github.com/neo/cogniwatch/blob/main/CHANGELOG.md)

### Community
- [GitHub](https://github.com/neo/cogniwatch)
- [Discord](#) (Coming soon)
- [Twitter](#) (Coming soon)

### Security
- [Security Policy](https://github.com/neo/cogniwatch/blob/main/SECURITY.md)
- [OWASP Compliance](/docs/security)

### Legal
- [License (MIT)](https://github.com/neo/cogniwatch/blob/main/LICENSE)

---

**Version 1.0.0** | Released March 7, 2026

*Built for security teams, by security teams.*
