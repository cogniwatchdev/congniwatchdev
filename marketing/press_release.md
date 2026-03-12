# FOR IMMEDIATE RELEASE

## CogniWatch Launches: First Search Engine for AI Agents

### Open-source tool detects and monitors AI agent deployments with 95%+ confidence

**March 7, 2026** — CogniWatch today announced the launch of version 1.0.0, the first open-source detection engine purpose-built for discovering and monitoring AI agent deployments across networks.

Dubbed the "Shodan for AI Agents," CogniWatch uses 27 distinct detection techniques to identify AI agents from major frameworks including OpenClaw, Agent-Zero, LangGraph, AutoGen, CrewAI, and Microsoft/Google frameworks. The tool achieves 95%+ detection confidence through multi-layer fingerprinting and Bayesian inference scoring.

**The Visibility Problem**

AI agents are being deployed at unprecedented speed — but traditional security tools cannot detect them. Unlike conventional services, AI agents communicate via WebSocket, use custom HTTP headers, run on non-standard ports, and often operate without authentication.

A recent scan of a typical development network revealed the scale of the blind spot: 12 AI agents discovered, 3 running with default credentials, 7 exposing unauthenticated APIs, and 0 known to the security team.

"Security teams can see every server, container, and traditional service in their network," said [SPOKEN PERSON NAME], [TITLE]. "But AI agents? They're invisible. You can't secure what you can't detect. That's the problem CogniWatch solves."

**Multi-Layer Detection Engine**

CogniWatch discovers AI agents through five detection layers:

1. **Protocol Fingerprinting** — HTTP headers, WebSocket handshakes, TLS/JA3 signatures
2. **API Endpoint Detection** — Framework-specific paths and behavioral patterns
3. **Behavioral Analysis** — Communication patterns, message structures, timing
4. **Confidence Scoring** — Bayesian inference with 95%+ accuracy
5. **Real-Time Telemetry** — Live connections, API calls, resource usage

The tool assigns each detection a confidence score and priority tier, enabling security teams to focus on high-confidence findings while minimizing false positives.

**Security-First Design**

CogniWatch is OWASP Top 10 and OWASP LLM Top 10 compliant (20/20), with:

- JWT authentication and API key management
- Role-based access control (RBAC)
- AES-256-GCM encryption for data at rest
- TLS 1.3 for data in transit
- Comprehensive audit logging

"This isn't a research prototype," said [SPOKEN PERSON NAME], [TITLE]. "CogniWatch is production-ready, with enterprise-grade security built in from day one."

**Availability**

CogniWatch v1.0.0 is available now as open-source software under the MIT license. The tool can be deployed in five minutes using Docker:

```bash
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch && docker compose up -d
```

The dashboard is accessible at `http://localhost:3000` after deployment. Full documentation, API reference, and deployment guides are available in the GitHub repository.

**Roadmap**

Future development phases include:

- **Phase B (Q2 2026):** Cloud scanner for internet-wide AI agent discovery
- **Phase C (Q3 2026):** Enterprise features including PostgreSQL backend, multi-tenant support, and SIEM integrations

**Contributing**

The CogniWatch project welcomes contributions from the security and AI communities. Framework signatures, detection improvements, documentation, and integrations are all encouraged via GitHub pull requests.

**About CogniWatch**

CogniWatch is an open-source AI agent detection and monitoring platform. Built by security researchers and AI engineers, it provides visibility into AI agent deployments across infrastructure. The project is community-driven and available under the MIT license.

**Media Contact**

[Media Contact Name]  
[Title]  
Email: [media@cogniwatch.dev] (placeholder)  
GitHub: https://github.com/neo/cogniwatch  
Twitter: @CogniWatch (placeholder)

---

## Editor's Notes

### Key Statistics
- **27 detection techniques** across 5 layers
- **95%+ confidence** scoring with Bayesian inference
- **7+ major frameworks** supported (23+ total)
- **OWASP 20/20 compliant** (Top 10 + LLM Top 10)
- **5-minute deployment** with Docker
- **Open-source** (MIT license)

### Supported Frameworks (v1.0.0)

**Tier 1 — High Confidence:**
- OpenClaw (all variants: NanoClaw, ZeroClaw, IronClaw, PicoClaw)
- Agent-Zero
- LangGraph (LangChain)
- AutoGen Studio (Microsoft)

**Tier 2 — Medium Confidence:**
- CrewAI
- Microsoft Agent Framework
- Google ADK
- Pydantic AI

**Tier 3 — Emerging:**
- Smolagents (Hugging Face)
- Agno (ex-Phidata)
- Strands Agents (AWS)
- Semantic Kernel (Microsoft)

### Technical Requirements
- Docker and Docker Compose
- 2GB RAM minimum (4GB recommended)
- Linux, macOS, or Windows (WSL2)
- Network access to target systems

### Download & Resources
- **GitHub Repository:** https://github.com/neo/cogniwatch
- **Documentation:** https://github.com/neo/cogniwatch/tree/main/docs
- **Deployment Guide:** https://github.com/neo/cogniwatch/blob/main/DEPLOYMENT.md
- **Security Report:** https://github.com/neo/cogniwatch/blob/main/SECURITY.md

### Quote Placeholders

Replace the following placeholders before distribution:

- `[SPOKEN PERSON NAME]` — Primary spokesperson (Jannie or Neo)
- `[TITLE]` — Title/role (e.g., "Creator, CogniWatch" or "Lead Developer")
- `[Media Contact Name]` — Media relations contact
- `[media@cogniwatch.dev]` — Media contact email
- `@CogniWatch` — Official Twitter handle (if applicable)

**Recommended quote attribution:**

Option 1 (Technical):
> "[QUOTE]" said Neo, Creator of CogniWatch.

Option 2 (Project-focused):
> "[QUOTE]" said Jannie, Lead Developer of CogniWatch.

Option 3 (Anonymous/Project voice):
> "[QUOTE]," the CogniWatch development team said.

### Suggested Pull Quotes for Articles

> "You can't secure what you can't detect."

> "Shodan for AI Agents — that's what we set out to build."

> "AI agents are being deployed everywhere. Traditional tools miss them. CogniWatch doesn't."

> "This isn't hype. This is a real tool solving a real problem."

### Distribution Channels

- **Wire Services:** Business Wire, PR Newswire (if budget allows)
- **Tech Media:** TechCrunch, The Verge, Ars Technica, Wired
- **Security Media:** The Hacker News, KBHacker, DarkReading, BleepingComputer
- **AI Media:** The Batch (DeepLearning.AI), Import AI, AI Weekly
- **Developer Communities:** Hacker News, Reddit (r/netsec, r/security, r/MachineLearning), Lobsters
- **Social Media:** Twitter/X, LinkedIn, Mastodon (infosec.cloud)

### Embargo Information (Optional)

If distributing under embargo:

**EMBARGO UNTIL:** March 7, 2026, 9:00 AM EST  
**CONTACT FOR QUESTIONS:** [media contact email]

---

**END OF RELEASE**
