# 📝 Changelog

All notable changes to CogniWatch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-07

### 🎉 Initial Release

**CogniWatch v1.0.0** — Production-ready AI agent detection platform.

### ✨ Added

#### Detection Engine
- **7 Framework Signatures**
  - OpenClaw (HTTP headers, WebSocket, API paths)
  - CrewAI (default ports, agent endpoints)
  - AutoGen (manager patterns, group chat APIs)
  - LangChain (LangServer, chain endpoints)
  - Semantic Kernel (SK-specific headers, planners)
  - PydanticAI (Pydantic validation patterns)
  - AgentKit (Coinbase-specific APIs)

- **Multi-Layer Detection**
  - HTTP header analysis (framework-specific headers)
  - API endpoint detection (known paths and behaviors)
  - WebSocket handshake fingerprinting
  - TLS/JA3 fingerprinting for encrypted connections
  - Behavioral analysis (communication patterns, timing)

- **Confidence Scoring**
  - Bayesian inference across detection layers
  - Four-tier confidence levels (Low, Medium, High, Critical)
  - Transparent scoring breakdown per agent
  - Confidence contribution tracking per detection method

#### Telemetry
- Real-time agent behavior tracking
- Connection monitoring (WebSocket, HTTP)
- API call volume and rate tracking
- Resource usage metrics
- Error rate monitoring
- 24h/7d/30d telemetry ranges

#### Web UI
- **Modern Dashboard** (Superdesign styled)
  - Agent discovery list with confidence scores
  - Real-time telemetry heatmaps
  - Interactive filtering and search
  - Responsive design (mobile-friendly)
  - Dark mode support

- **Agent Details View**
  - Full detection breakdown
  - Endpoint inventory
  - Telemetry graphs
  - Historical timeline
  - Tag management

- **Alert Management**
  - Security alert dashboard
  - Severity filtering
  - Acknowledge/resolve workflows
  - Alert metadata and context

#### API
- **RESTful API**
  - JWT authentication
  - API key support for automation
  - Role-based access control (RBAC)
  - Rate limiting (60 req/min, 1000/day)
  - Comprehensive error handling

- **Endpoints**
  - `GET /api/agents` — List discovered agents
  - `GET /api/agents/:id` — Agent details
  - `POST /api/scan` — Trigger new scan
  - `GET /api/scan/status` — Scan progress
  - `GET /api/telemetry/:id` — Telemetry data
  - `GET /api/alerts` — Security alerts
  - `POST /api/alerts/:id/acknowledge` — Acknowledge alerts
  - `GET /api/health` — Health check

- **WebSocket API**
  - Real-time event streaming
  - Subscribe to agent detection events
  - Scan completion notifications
  - Alert notifications

#### Security
- **OWASP Top 10 Compliance** — 10/10 ✅
- **OWASP LLM Top 10 Compliance** — 10/10 ✅
- **Authentication**
  - JWT tokens with RS256 signing
  - API keys with scoping
  - Session cookies
  - MFA ready (TOTP support)

- **Encryption**
  - AES-256-GCM for data at rest
  - TLS 1.3 for data in transit
  - bcrypt password hashing (cost 12)
  - PBKDF2 key derivation (100k iterations)

- **Input Validation**
  - SQL injection prevention (parameterized queries)
  - XSS prevention (React escaping, CSP)
  - SSRF prevention (URL allowlist, metadata blocking)
  - Path traversal prevention (sanitization)
  - Command injection prevention (no shell execution)

- **Security Headers**
  - Content-Security-Policy
  - Strict-Transport-Security (HSTS)
  - X-Frame-Options, X-Content-Type-Options
  - X-XSS-Protection, Referrer-Policy
  - Permissions-Policy

- **Audit Logging**
  - All authentication events
  - API call logging
  - Configuration changes
  - Security event alerting

#### Deployment
- **Docker Deployment**
  - Multi-container setup (Web UI, Scanner, DB)
  - docker-compose.yml for one-command deploy
  - Persistent volume for database
  - Health checks and auto-restart

- **systemd Services**
  - cogniwatch.service (Web UI)
  - cogniwatch-scanner.service (Discovery engine)
  - Automatic startup on boot
  - Log rotation integration

- **Python Package**
  - pip installable (`cogniwatch`)
  - Virtual environment support
  - requirements.txt with pinned versions
  - Cross-platform (Linux, macOS, Windows)

#### Database
- SQLite with SQLAlchemy ORM
- Schema migrations support
- Automatic backup scripts
- Data integrity checks
- Indexed queries for performance

### 🔧 Technical Details

#### Architecture
```
Scanner (Nmap, HTTP, WS, TLS)
    ↓
Detector (Multi-layer AI, Bayesian Scoring)
    ↓
SQLite DB (Agents, Scans, Alerts, Telemetry)
    ↓
REST API (JWT Auth, Rate Limit)
    ↓
Web UI (React, Superdesign Styled)
```

#### Technologies
- **Backend:** Python 3.12+, FastAPI, SQLAlchemy
- **Frontend:** React 18, Superdesign, TailwindCSS
- **Database:** SQLite 3, SQLAlchemy 2.0
- **Scanner:** Custom Python (nmap, requests, websockets)
- **Security:** cryptography, PyJWT, bcrypt, passlib
- **Container:** Docker, Docker Compose
- **Process:** systemd, supervisord ready

#### Performance
- Scan speed: ~100 hosts/minute (full scan)
- API response time: <100ms (p95)
- Database queries: <50ms (indexed)
- Memory usage: <512MB (typical)
- CPU usage: <1 vCPU (idle), <2 vCPU (scanning)

### 📦 Dependencies

**Core:**
- FastAPI 0.109.0
- SQLAlchemy 2.0.23
- PyJWT 2.8.0
- cryptography 41.0.7
- bcrypt 4.1.2
- requests 2.31.0
- python-dotenv 1.0.0

**Scanner:**
- python-nmap 0.7.1
- websockets 12.0
- tls-parser 1.3.0
- ja3 1.0.0

**Frontend:**
- React 18.2.0
- react-dom 18.2.0
- TailwindCSS 3.4.0
- recharts 2.10.0 (charts)
- axios 1.6.0

### 📖 Documentation

- **README.md** — Project overview and quick start
- **docs/QUICKSTART.md** — 5-minute setup guide
- **docs/DEPLOYMENT.md** — VPS deployment guide (DigitalOcean, AWS)
- **docs/API.md** — Complete API reference
- **docs/SECURITY.md** — Security compliance report
- **SECURITY_AUDIT.md** — Detailed security audit results
- **CHANGELOG.md** — Version history (this file)

### 🎯 Known Limitations

- WebSocket telemetry requires agent cooperation
- JA3 fingerprinting limited to TLS connections
- Cloud provider scanning (AWS, Azure, GCP) planned for Phase B
- Kubernetes-native scanning planned for Phase B
- Multi-region deployment requires manual setup

### 🐛 Known Issues

- None at release (all critical/high issues resolved)

### 🔮 Roadmap (Post-1.0.0)

#### Phase B — Cloud Scanner (Q2 2026)
- [ ] AWS cloud discovery (EC2, Lambda, ECS)
- [ ] Azure cloud discovery (VMs, Functions, AKS)
- [ ] GCP cloud discovery (GCE, Cloud Functions, GKE)
- [ ] Serverless agent detection
- [ ] Container orchestration scanning (K8s, ECS, EKS)
- [ ] Cloud metadata analysis
- [ ] Multi-region deployment support

#### Phase C — Enterprise (Q3 2026)
- [ ] Centralized management console
- [ ] Team collaboration & RBAC enhancements
- [ ] SIEM integration (Splunk, Elastic, Sentinel)
- [ ] Compliance reporting (SOC2, ISO 27001, HIPAA)
- [ ] API gateway for large deployments
- [ ] High-availability clustering
- [ ] PostgreSQL support for large datasets
- [ ] Redis caching for performance
- [ ] Advanced anomaly detection (ML-based)

---

## [Unreleased]

### Planned Features
- Cloud provider integrations (AWS, Azure, GCP)
- Kubernetes-native deployment (Helm charts)
- Advanced ML-based anomaly detection
- Enhanced SIEM integrations
- Mobile app (iOS/Android) for monitoring
- Slack/Discord alert integrations
- Custom framework signature builder (UI)

### Under Consideration
- Graph-based agent relationship mapping
- Autonomous remediation suggestions
- Integration with vulnerability scanners
- Agent behavior simulation for testing
- Collaborative threat intelligence sharing

---

## Version History (Pre-1.0.0)

### [0.9.0-beta] — 2026-03-01
- Feature freeze for 1.0.0 release
- Security audit completed (10/10 OWASP compliance)
- Documentation finalized
- Performance optimization pass

### [0.8.0-beta] — 2026-02-25
- Added JA3/TLS fingerprinting
- Implemented Bayesian confidence scoring
- WebSocket detection layer added
- UI redesign (Superdesign)

### [0.7.0-beta] — 2026-02-20
- Added 3 new framework signatures (LangChain, Semantic Kernel, PydanticAI)
- Implemented telemetry collection
- REST API with JWT authentication
- Docker deployment support

### [0.6.0-beta] — 2026-02-15
- Initial scanner implementation
- OpenClaw, CrewAI, AutoGen signatures
- Basic web dashboard
- SQLite database backend

### [0.1.0-alpha] — 2026-02-01
- Project inception
- Proof of concept scanner
- Single framework detection (OpenClaw)
- Command-line only interface

---

## Release Notes

### v1.0.0 Highlights

**What makes CogniWatch unique:**

1. **First AI agent detection platform** — Purpose-built for discovering AI agents across frameworks and protocols

2. **Multi-layer detection** — Not just port scanning. We analyze HTTP headers, API endpoints, WebSocket handshakes, TLS fingerprints, and behavioral patterns

3. **Confidence scoring** — Bayesian inference gives you actionable results, not just "maybe" detections

4. **Production ready** — OWASP compliant, enterprise security, Docker deployment, comprehensive documentation

5. **Open source** — MIT license, community-driven signature development, transparent security

**Who should use CogniWatch:**

- Security teams monitoring for unauthorized AI deployments
- Platform teams managing AI agent infrastructure
- Compliance officers tracking AI system inventory
- Developers debugging agent communication issues
- Researchers studying AI agent deployment patterns

**Getting started:**

```bash
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch
docker compose up -d
open http://localhost:3000
```

That's it — you're monitoring for AI agents in under 2 minutes.

---

## Contributing

We welcome contributions! See [README.md](README.md#-contributing) for guidelines on:

- Adding new framework signatures
- Reporting bugs
- Suggesting features
- Improving documentation
- Security research and audits

---

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/neo/cogniwatch/issues)
- **Security:** security@cogniwatch.io
- **Community:** [Discussions](https://github.com/neo/cogniwatch/discussions)

---

**Built with ⚡ by Neo**  
*Because visibility is the first step to security*
