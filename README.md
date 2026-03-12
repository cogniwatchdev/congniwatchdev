<p align="center">
  <h1 align="center">🔍 CogniWatch</h1>
  <p align="center"><strong>Shodan for AI Agents</strong></p>
  <p align="center">Detect, monitor, and secure AI agent deployments across your infrastructure</p>
</p>

<p align="center">
  <a href="#-features"><img src="https://img.shields.io/badge/status-Production%20Ready-success?style=flat-square" alt="Production Ready"></a>
  <a href="#-security"><img src="https://img.shields.io/badge/OWASP-Compliant-blue?style=flat-square" alt="OWASP Compliant"></a>
  <a href="https://github.com/neo/cogniwatch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/version-1.0.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/frameworks-23%2B-purple?style=flat-square" alt="Frameworks Detected">
</p>

<p align="center">
  <em>🚀 Just launched on <a href="https://news.ycombinator.com">Hacker News</a> • Coming soon to <a href="https://www.producthunt.com">Product Hunt</a></em>
</p>

---

## 🎯 The Problem

AI agents are being deployed at unprecedented speed — but **visibility is zero**. OpenClaw, CrewAI, AutoGen, and other frameworks leave traces across your network, but traditional tools can't detect them. You're flying blind.

**The reality:**
- 🚨 Agents communicate via WebSocket, HTTP, and custom protocols
- 🔓 Default credentials and exposed APIs are common
- 👁️ No centralized telemetry or monitoring
- ⚠️ Security teams can't see what they can't detect
- 📊 Compliance teams can't audit what they can't find

**Traditional scanners fail because:**
- Nmap detects ports, not frameworks
- Web vulnerability scanners miss agent-specific patterns
- SIEM tools require manual log correlation
- Cloud security tools ignore self-hosted agents

---

## 💡 The Solution

CogniWatch is a **multi-layer detection engine** that discovers AI agents through protocol fingerprinting, API endpoint detection, behavioral analysis, and confidence scoring.

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────┐     ┌─────────────┐
│   Scanner       │────▶│   Detector       │────▶│   DB     │────▶│  Dashboard  │
│  Network Probes │     │  Multi-Layer AI  │     │ SQLite   │     │  Real-time  │
└─────────────────┘     └──────────────────┘     └──────────┘     └─────────────┘
       │                        │
       ▼                        ▼
  HTTP/HTTPS              JA3/TLS
  WebSocket               Headers
  API Endpoints           Behavior
```

**What makes CogniWatch different:**
- ✅ **Framework-specific detection** — Not just "port 8080 open" but "OpenClaw Gateway v1.0"
- ✅ **Confidence scoring** — Bayesian inference tells you how certain we are
- ✅ **Real-time telemetry** — See agent behavior, not just existence
- ✅ **Security-first** — OWASP Top 10 + LLM Top 10 compliant
- ✅ **Self-hosted** — Your data stays on your network

---

## ✨ Features

### 🔎 Discovery Engine
- **23+ Framework Signatures** — OpenClaw (all variants), Agent-Zero, LangGraph, AutoGen, CrewAI, Microsoft/Google frameworks, and more
- **Multi-Layer Detection** — HTTP, API, WebSocket, TLS/JA3 fingerprinting
- **Confidence Scoring** — Bayesian inference with priority tiers (Tier 1/2/3)
- **Continuous Scanning** — Schedule automated scans or run on-demand

### 📊 Telemetry & Monitoring
- **Real-time Metrics** — Connections, API calls, WebSocket messages
- **Behavioral Analysis** — Detect anomalous agent activity
- **Historical Trends** — Track agent growth over time
- **Alerting System** — Get notified when new agents appear

### 🛡️ Enterprise Security
- **OWASP Compliant** — Top 10 + LLM Top 10 covered (10/10 ✅)
- **Production Security** — JWT auth, API keys, RBAC, AES-256-GCM encryption
- **Audit Logging** — Every action tracked with timestamps
- **Network Isolation** — LAN-only by default, optional HTTPS

### 🎨 Modern Interface
- **Clean Dashboard** — Filter, search, and export agent data
- **Telemetry Heatmaps** — Visualize agent activity
- **Export Formats** — JSON, CSV, PDF reports
- **Dark/Light Themes** — Beautiful in any environment

### 🚀 Developer Experience
- **Docker Ready** — `docker compose up` deployment
- **REST API** — Full programmatic control
- **WebSocket Updates** — Real-time event streaming
- **SDK Support** — Python, JavaScript examples

---

## 🚀 Quick Start

Get CogniWatch running in **3 commands**:

```bash
# 1. Clone the repository
git clone https://github.com/neo/cogniwatch.git && cd cogniwatch

# 2. Start with Docker
docker compose up -d

# 3. Open your browser
open http://localhost:9000
```

That's it! You're now monitoring for AI agents. 🎉

### Configure Authentication (Recommended)

Edit `docker-compose.yml` before starting:

```yaml
environment:
  - COGNIWATCH_ADMIN_USER=admin
  - COGNIWATCH_ADMIN_PASSWORD=your-secure-password-here
```

**⚠️ Security Warning:** Change default credentials immediately in production!

### Your First Scan

```bash
# Trigger a network scan via API
curl -X POST http://localhost:9000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"network": "192.168.1.0/24"}'

# View discovered agents
curl http://localhost:9000/api/agents
```

---

## 📸 Screenshots

### Agent Discovery Dashboard
*Screenshot placeholder: CogniWatch dashboard showing a list of discovered AI agents with IP addresses, framework names, confidence scores (94%, 87%, 91%), and status indicators (active/offline). Dark theme with teal accent colors. Search bar at top, filter dropdowns for framework/status/confidence. Agent cards show framework icons, detected ports, and last-seen timestamps.*

**What you'll see:**
- List of all discovered agents with confidence badges
- Filter by framework, status, confidence level
- Click any agent for detailed telemetry
- Export button for reports

### Telemetry Heatmap
*Screenshot placeholder: Dashboard panel showing bar charts and heatmaps of agent activity over 24h. Metrics include API calls (2,847), WebSocket connections (1,923), authentication events (847), and security alerts (234). Color gradient from teal (low) to purple (high). Time-series line graph below showing activity trends.*

**What you'll see:**
- Real-time activity metrics
- Hourly breakdown of agent behavior
- Anomaly detection highlights
- Export to CSV/PDF

### Agent Detail View
*Screenshot placeholder: Detailed agent profile page showing framework (OpenClaw), version (1.0.0), detected endpoints (/api/v1/gateway/status, /ws/agent), confidence breakdown (Port: 30%, HTTP: 15%, API: 25%, WS: 15%, Behavior: 4%), network location info, and telemetry graphs.*

**What you'll see:**
- Complete detection methodology
- All discovered endpoints
- Historical telemetry
- Tag management

---

## 🏗️ Architecture

CogniWatch uses a **modular, microservices-inspired architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    CogniWatch Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                           │
│  │   Scanner    │  Network discovery & fingerprinting       │
│  │  (Nmap, HTTP │  - Port scanning (80, 443, 5000, 8080)    │
│  │   WS, TLS)   │  - HTTP header analysis                   │
│  └──────┬───────┘  - WebSocket handshake detection          │
│         │           - JA3/TLS fingerprinting                │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │   Detector   │  Multi-layer analysis engine              │
│  │  (Bayesian   │  - Framework signature matching           │
│  │   Scoring)   │  - Confidence calculation                 │
│  └──────┬───────┘  - Behavioral analysis                    │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  SQLite DB   │◀───▶│  Telemetry   │  Real-time storage   │
│  │  (Agents,    │     │  Collector   │  - Connections       │
│  │   Scans,     │     │              │  - API calls         │
│  │   Alerts)    │     │              │  - Resource usage    │
│  └──────┬───────┘     └──────────────┘                     │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │   REST API   │     │  Web UI      │  React dashboard     │
│  │  (JWT Auth)  │────▶│  (Superdesign│  - Agent list        │
│  │  Rate Limit  │     │   Styled)    │  - Telemetry views   │
│  └──────────────┘     └──────────────┘  - Alert management  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Scanner** | Network discovery | Python, Nmap, httpx, websockets |
| **Detector** | Framework identification | Bayesian scoring, regex patterns |
| **Database** | Persistent storage | SQLite with WAL mode |
| **Telemetry** | Real-time metrics | In-memory cache + SQLite |
| **API** | Programmatic access | FastAPI, JWT, rate limiting |
| **Web UI** | User interface | React, SuperDesign, WebSocket |

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for deep technical details.

---

## 🧩 Supported Frameworks

CogniWatch detects **23+ agent frameworks** across three priority tiers:

### Tier 1 — High Confidence (Production Priority)

| Framework | Ports | Detection Method | Confidence |
|-----------|-------|------------------|------------|
| **OpenClaw** (all variants) | 18789, 8787 | HTTP headers, WebSocket, API, mDNS | **HIGH** |
| **Agent-Zero** | 50001, 50080 | Web UI fingerprint, Docker metadata | **MEDIUM-HIGH** |
| **LangGraph** | 8123, 8000 | FastAPI endpoints, Redis/Postgres | **HIGH** |
| **AutoGen Studio** | 8080 | CLI signature, FastAPI Web UI | **HIGH** |

**OpenClaw Variants Detected:**
- OpenClaw (main) — Desktop/Server deployments
- NanoClaw — Raspberry Pi, low-power SBCs
- ZeroClaw — Minimal containers, WSL
- IronClaw — Enterprise/server with TLS
- PicoClaw — RP2040 microcontrollers (limited network surface)

### Tier 2 — Medium Confidence (Growing Adoption)

| Framework | Ports | Detection Method | Confidence |
|-----------|-------|------------------|------------|
| **CrewAI** | None (library) | Python import patterns, code inspection | **MEDIUM** |
| **Microsoft Agent Framework** | 8000-8004 | FastAPI/.NET endpoints, Azure correlation | **MEDIUM** |
| **Google ADK** | 8000-8003 | uvicorn services, Streamlit UI | **MEDIUM** |
| **Pydantic AI** | None (library) | Type-safe patterns, library imports | **MEDIUM** |

### Tier 3 — Emerging/Niche Frameworks

| Framework | Ports | Detection Method | Confidence |
|-----------|-------|------------------|------------|
| **Smolagents** (Hugging Face) | None (CLI) | CLI commands, sandbox detection | **LOW-MEDIUM** |
| **Agno** (ex-Phidata) | Unknown | FastAPI patterns, rebrand awareness | **MEDIUM** |
| **Strands Agents** (AWS) | 8080 | Bedrock API correlation, uvicorn | **MEDIUM** |
| **Semantic Kernel** (Microsoft) | None (library) | .NET/Python SDK patterns | **LOW** |

**Additional Frameworks Tracked:**
- Langflow (visual builder, configurable ports)
- Rasa (conversational AI, ports 5005/8000)
- AutoGPT (autonomous agent, configurable)
- LlamaIndex agents (RAG-focused, library-based)
- OpenAI Agents SDK (primarily cloud-based)
- MCP servers (protocol-based, emerging)

See [docs/FRAMEWORK-SIGNATURES.md](docs/FRAMEWORK-SIGNATURES.md) for complete signature documentation.

---

## 📊 Confidence Scoring System

Detection confidence is calculated using a **Bayesian multi-layer scoring model**:

| Detection Layer | Weight | Description |
|-----------------|--------|-------------|
| **Port Match** | 30% | Default port detected (e.g., 18789 for OpenClaw) |
| **HTTP Fingerprints** | 15-40% | Server headers, response body patterns, title matching |
| **API Validation** | 25% | Confirmed framework-specific API endpoint responses |
| **WebSocket Protocol** | 0-15% | Handshake analysis, protocol matching |
| **Framework-Specific** | 5-15% | mDNS, process names, config files, Docker metadata |

**Confidence Badges:**
- ✅ **Confirmed**: ≥85% confidence — Definitive detection
- ⚠️ **Likely**: 60-84% confidence — Strong indicators
- ❓ **Possible**: 30-59% confidence — Initial matches, needs validation

**Example OpenClaw Detection:**
```
Port 18789 open:            +30% (port match)
Server: OpenClaw-Gateway:   +15% (HTTP header)
/api/status responds:       +25% (API validated)
WebSocket handshake OK:     +15% (protocol match)
mDNS _openclaw._tcp found:  +5% (network signature)
────────────────────────────────────────
Total: 90% → ✅ CONFIRMED
```

---

## 🛡️ Security

CogniWatch is **production-ready** with enterprise-grade security:

<p align="center">
  <img src="https://img.shields.io/badge/OWASP%20Top%2010-10/10%20✅-success?style=flat-square" alt="OWASP Top 10">
  <img src="https://img.shields.io/badge/OWASP%20LLM%20Top%2010-10/10%20✅-success?style=flat-square" alt="OWASP LLM Top 10">
</p>

**Security Highlights:**
- 🔐 **Authentication** — JWT tokens, API keys, role-based access control (RBAC)
- 🔒 **Encryption** — AES-256-GCM for data at rest, TLS 1.3 for transit
- ✅ **Input Validation** — SQL injection, XSS, SSRF prevention
- 🛡️ **Security Headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- 📝 **Audit Logging** — All actions logged with timestamps and user context
- 🚨 **Rate Limiting** — 60 requests/minute default, configurable per endpoint

See [docs/SECURITY.md](docs/SECURITY.md) for complete security report and [SECURITY.md](SECURITY.md) for responsible disclosure policy.

---

## 📦 Installation

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+

```bash
# Clone repository
git clone https://github.com/neo/cogniwatch.git && cd cogniwatch

# Start services
docker compose up -d

# Verify running
docker compose ps

# View logs
docker compose logs -f
```

**Access:** http://localhost:9000

### Option 2: From Source

**Prerequisites:**
- Python 3.12+
- pip 24.0+
- Git

```bash
# Clone repository
git clone https://github.com/neo/cogniwatch.git && cd cogniwatch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -m database.init_db

# Start Web UI
python3 -m webui.server &

# Start scanner (separate terminal)
source venv/bin/activate
python3 scanner/network_scanner.py
```

**Access:** http://localhost:9000

### Option 3: Systemd Service (Production)

For production deployments with automatic start on boot:

```bash
# Copy service files (as root)
cp cogniwatch.service /etc/systemd/system/
cp cogniwatch-scanner.service /etc/systemd/system/

# Enable and start
systemctl daemon-reload
systemctl enable cogniwatch cogniwatch-scanner
systemctl start cogniwatch cogniwatch-scanner

# Check status
systemctl status cogniwatch
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment guide including VPS setup, HTTPS configuration, and firewall rules.

---

## 💻 Usage Examples

### Command Line

```bash
# Trigger a scan
curl -X POST http://localhost:9000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"network": "192.168.1.0/24"}'

# List discovered agents
curl http://localhost:9000/api/agents

# Get agent details
curl http://localhost:9000/api/agents/ag_7k2m9n4p

# Get telemetry
curl "http://localhost:9000/api/telemetry/ag_7k2m9n4p?range=24h"

# List security alerts
curl http://localhost:9000/api/alerts?severity=high
```

### Python SDK

```python
import requests

API_KEY = "cw_live_xxxxx"
BASE_URL = "http://localhost:9000/api"

headers = {"X-API-Key": API_KEY}

# List agents
response = requests.get(f"{BASE_URL}/agents", headers=headers)
agents = response.json()["agents"]
print(f"Found {len(agents)} agents")

# Trigger scan
scan = requests.post(
    f"{BASE_URL}/scan",
    headers=headers,
    json={"network": "10.0.0.0/8"}
)
print(f"Scan started: {scan.json()['scan_id']}")

# Get telemetry for first agent
if agents:
    telemetry = requests.get(
        f"{BASE_URL}/telemetry/{agents[0]['id']}?range=7d",
        headers=headers
    )
    print(f"24h connections: {telemetry.json()['summary']['total_connections']}")
```

### JavaScript/Node.js

```javascript
const API_KEY = 'cw_live_xxxxx';
const BASE_URL = 'http://localhost:9000/api';

async function getAgents() {
  const response = await fetch(`${BASE_URL}/agents`, {
    headers: { 'X-API-Key': API_KEY }
  });
  const data = await response.json();
  return data.agents;
}

async function scanNetwork(network) {
  const response = await fetch(`${BASE_URL}/scan`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ network })
  });
  return response.json();
}

// Usage
(async () => {
  const agents = await getAgents();
  console.log(`Found ${agents.length} agents`);
  
  const scan = await scanNetwork('192.168.0.0/16');
  console.log(`Scan ${scan.scan_id} started`);
})();
```

See [docs/API.md](docs/API.md) for complete API reference with all endpoints, schemas, and error codes.

---

## 🗺️ Roadmap

### ✅ Phase A — Core Platform (COMPLETE)
- [x] **23+ framework signatures** (expanded from 7)
- [x] Multi-layer detection engine
- [x] Bayesian confidence scoring with tiers
- [x] Telemetry collection
- [x] Modern Web UI
- [x] OWASP compliance
- [x] Docker deployment
- [x] Priority tier system (Tier 1/2/3)
- [x] OpenClaw variant detection (NanoClaw, PicoClaw, ZeroClaw, IronClaw)

### 🚧 Phase B — Cloud Scanner (Q2 2026)
- [ ] AWS/Azure/GCP cloud discovery
- [ ] Serverless agent detection (Lambda, Cloud Functions)
- [ ] Container orchestration scanning (K8s, ECS)
- [ ] Multi-region deployment
- [ ] LangGraph cloud detection
- [ ] Microsoft Agent Framework Azure integration

### 🏢 Phase C — Enterprise (Q3 2026)
- [ ] Centralized management console
- [ ] Team collaboration & RBAC
- [ ] SIEM integration (Splunk, Elastic)
- [ ] Compliance reporting (SOC2, ISO 27001)
- [ ] API gateway for large deployments
- [ ] Agent-Zero enterprise deployment patterns
- [ ] Pydantic AI production monitoring

See [CHANGELOG.md](CHANGELOG.md) for version history and upcoming features.

---

## 🤝 Contributing

We welcome contributions from the community!

### Adding New Framework Signatures

1. Create signature file in `scanner/signatures/`
2. Define detection patterns (HTTP headers, API paths, WebSocket behaviors)
3. Test against known deployments
4. Submit PR with documentation

```python
# Example: scanner/signatures/newframework.py
class NewFrameworkSignature:
    name = "NewFramework"
    detection_layer = "http_headers"
    
    def detect(self, response):
        patterns = [
            r"X-Agent-Framework: NewFramework",
            r"/api/v1/agent/\d+/chat"
        ]
        return self.match_patterns(response, patterns)
```

See [docs/FRAMEWORK-SIGNATURES.md](docs/FRAMEWORK-SIGNATURES.md) for complete signature guide.

### Other Ways to Contribute

- 🐛 **Report bugs** via GitHub Issues
- 💡 **Suggest features** or improvements
- 📖 **Improve documentation**
- 🔒 **Security audits** and penetration testing
- 🧪 **Write tests** for new features

### Contributor Guidelines

1. **Fork the repository** and create a feature branch
2. **Follow existing code style** (PEP 8 for Python, ESLint/Prettier for JavaScript)
3. **Write tests** for new features (see `tests/` directory)
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description of changes

**PR Review Process:**
- All PRs reviewed within 48 hours
- At least one maintainer approval required
- CI/CD tests must pass
- Security-sensitive changes require additional review

---

## 🔒 Security Policy

We take security seriously. If you discover a vulnerability:

- **Email:** security@cogniwatch.dev
- **GitHub:** Use [private vulnerability reporting](https://github.com/neo/cogniwatch/security/advisories)
- **Response Time:** Within 48 hours

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Do not** disclose vulnerabilities publicly until we've had time to investigate and patch.

See [SECURITY.md](SECURITY.md) for our full security policy and process.

---

## ⚖️ Legal & Compliance

**Important:** Users must have authorization for all scans. Unauthorized scanning may violate computer crime laws.

CogniWatch includes comprehensive legal documentation:
- [Terms of Service](legal/TERMS_OF_SERVICE.md) — License terms, acceptable use
- [Privacy Policy](legal/PRIVACY_POLICY.md) — Data handling, GDPR/CCPA
- [Disclaimer](legal/DISCLAIMER.md) — No warranty, liability limits
- [Acceptable Use Policy](legal/ACCEPTABLE_USE.md) — Permitted/prohibited uses

Contact: legal@cogniwatch.dev

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

**TL;DR:** Use it for anything you want. Just don't hold us liable if something breaks.

---

## 🔗 Links & Community

### Documentation
- 📚 [Quick Start Guide](docs/QUICKSTART.md)
- 🚀 [Deployment Guide](docs/DEPLOYMENT.md)
- 🛠️ [API Reference](docs/API.md)
- 🛡️ [Security Report](docs/SECURITY.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- 📝 [Changelog](CHANGELOG.md)
- 🐛 [Issue Tracker](https://github.com/neo/cogniwatch/issues)

### Community
- 💬 [Discord Server](#) (Coming soon) — Chat with developers and users
- 🐦 [Twitter/X](https://twitter.com/CogniWatch) — Updates and announcements
- 📰 [Blog](#) (Coming soon) — Deep dives, tutorials, and release notes
- 🎮 [Live Demo](#) (Request access) — See CogniWatch in action

### Support
- 📧 Legal: legal@cogniwatch.dev
- 🔒 Security: security@cogniwatch.dev
- 💬 Discord: Coming soon

---

<p align="center">
  <strong>Built with ⚡ by Neo</strong><br>
  <em>Because visibility is the first step to security</em>
</p>

<p align="center">
  <a href="https://github.com/neo/cogniwatch/stargazers">
    <img src="https://img.shields.io/github/stars/neo/cogniwatch?style=social" alt="GitHub Stars">
  </a>
  <a href="https://github.com/neo/cogniwatch/network/members">
    <img src="https://img.shields.io/github/forks/neo/cogniwatch?style=social" alt="GitHub Forks">
  </a>
</p>
