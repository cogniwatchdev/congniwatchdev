# 🏗️ CogniWatch Architecture

**Version:** 1.0.0  
**Last Updated:** March 8, 2026

Technical architecture documentation covering system design, component breakdown, data flow, security architecture, and scalability considerations.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow](#data-flow)
4. [Security Architecture](#security-architecture)
5. [Scalability Considerations](#scalability-considerations)
6. [Technology Stack](#technology-stack)
7. [Deployment Patterns](#deployment-patterns)
8. [Performance Characteristics](#performance-characteristics)

---

## 🖼️ System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CogniWatch System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Scanner    │───▶│   Detector   │───▶│   Database   │       │
│  │   Layer      │    │   Layer      │    │   Layer      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Network    │    │   Analysis   │    │   Telemetry  │       │
│  │   Probing    │    │   Engine     │    │   Collector  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                 │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                             ▼                                    │
│                    ┌──────────────┐                              │
│                    │   REST API   │                              │
│                    │   Gateway    │                              │
│                    └──────────────┘                              │
│                             │                                    │
│              ┌──────────────┴──────────────┐                     │
│              │                             │                     │
│              ▼                             ▼                     │
│     ┌──────────────┐              ┌──────────────┐               │
│     │   Web UI     │              │  WebSocket   │               │
│     │  (React)     │              │   Updates    │               │
│     └──────────────┘              └──────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

**Design Goals:**
- ✅ **Modularity** — Loose coupling between components
- ✅ **Scalability** — Horizontal scaling where possible
- ✅ **Security** — Defense in depth, zero-trust
- ✅ **Observability** — Comprehensive logging and metrics
- ✅ **Maintainability** — Clean interfaces, documented APIs

**Key Decisions:**
- **Microservices-inspired** — Separate scanner, detector, API, UI
- **Event-driven** — Asynchronous processing via message queue
- **Local-first** — SQLite for simplicity, PostgreSQL planned
- **API-first** — All functionality available via REST API

---

## 🧩 Component Breakdown

### 1. Scanner Layer

**Purpose:** Network discovery and data collection

**Sub-components:**

```
┌─────────────────────────────────────────────┐
│              Scanner Layer                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Port       │  │   HTTP       │         │
│  │   Scanner    │  │   Scanner    │         │
│  │              │  │              │         │
│  │ - Nmap       │  │ - httpx      │         │
│  │ - Masscan    │  │ - Requests   │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   WebSocket  │  │   TLS/JA3    │         │
│  │   Scanner    │  │   Scanner    │         │
│  │              │  │              │         │
│  │ - websockets │  │ - pyOpenSSL  │         │
│  │ - aiohttp    │  │ - TLS lib    │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   mDNS       │  │   Banner     │         │
│  │   Scanner    │  │   Grabber    │         │
│  │              │  │              │         │
│  │ - zeroconf   │  │ - Socket     │         │
│  │ - Bonjour    │  │ - Raw TCP    │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
└─────────────────────────────────────────────┘
```

**Responsibilities:**
- Network reconnaissance (port scanning)
- Service fingerprinting (banner grabbing)
- Protocol detection (HTTP, WebSocket, TLS)
- Data collection for detector layer

**Interfaces:**
- Input: Scan configuration (network range, ports, options)
- Output: Raw scan results (open ports, headers, responses)

**Configuration:**
```json
{
  "scanner": {
    "rate_limit": 100,
    "timeout": 300,
    "parallel_scans": 3,
    "ports": [80, 443, 5000, 8080, 18789],
    "detection_layers": {
      "http": true,
      "websocket": true,
      "tls": true,
      "mdns": true
    }
  }
}
```

---

### 2. Detector Layer

**Purpose:** Multi-layer analysis and framework identification

**Sub-components:**

```
┌─────────────────────────────────────────────┐
│              Detector Layer                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Signature  │  │   Bayesian   │         │
│  │   Matcher    │  │   Scorer     │         │
│  │              │  │              │         │
│  │ - Regex      │  │ - Priors     │         │
│  │ - Patterns   │  │ - Likelihood │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Framework  │  │   Behavioral │         │
│  │   Registry   │  │   Analyzer   │         │
│  │              │  │              │         │
│  │ - Signatures │  │ - Patterns   │         │
│  │ - Versions   │  │ - Anomalies  │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
└─────────────────────────────────────────────┘
```

**Detection Pipeline:**

```
Raw Scan Data
     │
     ▼
┌─────────────┐
│ Layer 1:    │ → Port Match (30% weight)
│ Port Scan   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Layer 2:    │ → HTTP Headers (15-40% weight)
│ HTTP/FQDN   │ → Response Body Patterns
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Layer 3:    │ → API Endpoint Validation
│ API         │ → Response Schema Match
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Layer 4:    │ → WebSocket Handshake
│ WebSocket   │ → Message Structure
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Layer 5:    │ → Request Patterns
│ Behavioral  │ → Timing Analysis
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Bayesian    │ → Final Confidence Score
│ Aggregation │ → Framework Classification
└─────┬───────┘
      │
      ▼
Agent Record
```

**Responsibilities:**
- Pattern matching against framework signatures
- Confidence score calculation
- Behavioral analysis
- Classification and tagging

**Interfaces:**
- Input: Raw scan data from scanner layer
- Output: Agent records with confidence scores

---

### 3. Database Layer

**Purpose:** Persistent storage for agents, scans, telemetry

**Schema Overview:**

```sql
-- Agents table
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    framework TEXT,
    framework_version TEXT,
    confidence REAL,
    confidence_level TEXT,
    status TEXT,
    detected_at TIMESTAMP,
    last_seen TIMESTAMP,
    location_json TEXT,
    endpoints_json TEXT,
    telemetry_json TEXT,
    tags_json TEXT,
    metadata_json TEXT
);

-- Scans table
CREATE TABLE scans (
    id TEXT PRIMARY KEY,
    network TEXT NOT NULL,
    scan_type TEXT,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    agents_found INTEGER,
    configuration_json TEXT,
    results_json TEXT
);

-- Telemetry table
CREATE TABLE telemetry (
    id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(id),
    timestamp TIMESTAMP,
    metric_type TEXT,
    metric_value REAL,
    metadata_json TEXT
);

-- Alerts table
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,
    type TEXT,
    severity TEXT,
    status TEXT,
    agent_id TEXT REFERENCES agents(id),
    title TEXT,
    description TEXT,
    created_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    metadata_json TEXT
);
```

**Storage Strategy:**
- **SQLite** (Phase A): Simple, embedded, no external dependencies
- **PostgreSQL** (Phase C planned): For enterprise deployments, better concurrency

**Data Retention:**
- **Agents**: Indefinite (until manually deleted)
- **Scans**: 90 days (configurable)
- **Telemetry**: 90 days (configurable, with aggregation for older data)
- **Alerts**: 1 year (configurable)

---

### 4. Telemetry Collector

**Purpose:** Real-time metrics collection and storage

**Collection Methods:**
- **Passive**: Listen to agent communications
- **Active**: Poll agent endpoints for metrics
- **Hybrid**: Combination of both

**Metrics Collected:**

| Metric Type | Collection Method | Frequency |
|-------------|------------------|-----------|
| Connections | Passive | Real-time |
| API Calls | Passive | Real-time |
| WebSocket Messages | Passive | Real-time |
| Response Times | Active | Every 60s |
| Error Rates | Passive | Real-time |
| Resource Usage | Active | Every 300s |

**Aggregation Strategy:**
- **Raw data**: Stored for 24 hours
- **Hourly aggregates**: Stored for 7 days
- **Daily aggregates**: Stored for 90 days

---

### 5. REST API Gateway

**Purpose:** Programmatic access to all functionality

**Architecture:**
```
┌─────────────────────────────────────────────┐
│           REST API Gateway                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Auth       │  │   Rate       │         │
│  │   Middleware │  │   Limiter    │         │
│  │              │  │              │         │
│  │ - JWT        │  │ - Token      │         │
│  │ - API Keys   │  │   Bucket     │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Router     │  │   Validators │         │
│  │              │  │              │         │
│  │ - Endpoints  │  │ - Schema     │         │
│  │ - Methods    │  │ - Input      │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Response   │  │   Error      │         │
│  │   Formatter  │  │   Handler    │         │
│  │              │  │              │         │
│  │ - JSON       │  │ - Standard   │         │
│  │ - Pagination │  │   Format     │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
└─────────────────────────────────────────────┘
```

**API Endpoints:**
- See [API.md](API.md) for complete endpoint reference

**Security:**
- JWT authentication
- API key support
- Rate limiting per endpoint
- Input validation
- CORS configuration

---

### 6. Web UI

**Purpose:** User interface for monitoring and management

**Technology Stack:**
- **Frontend Framework**: React 18+
- **Styling**: Custom CSS with SuperDesign influence
- **State Management**: React Context + Hooks
- **Real-time Updates**: WebSocket
- **Charts**: Custom SVG/Canvas or lightweight library

**Architecture:**
```
┌─────────────────────────────────────────────┐
│               Web UI                        │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Dashboard  │  │   Agents     │         │
│  │   View       │  │   View       │         │
│  │              │  │              │         │
│  │ - Summary    │  │ - List       │         │
│  │ - Cards      │  │ - Details    │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │  Telemetry   │  │   Alerts     │         │
│  │   View       │  │   View       │         │
│  │              │  │              │         │
│  │ - Graphs     │  │ - Queue      │         │
│  │ - Heatmaps   │  │ - History    │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Scans      │  │   Settings   │         │
│  │   View       │  │   View       │         │
│  │              │  │              │         │
│  │ - Schedule   │  │ - Config     │         │
│  │ - History    │  │ - Profile    │         │
│  └──────────────┘  └──────────────┘         │
│                                             │
└─────────────────────────────────────────────┘
```

**Key Features:**
- Responsive design (desktop, tablet, mobile)
- Dark/light theme
- Real-time updates via WebSocket
- Export capabilities (JSON, CSV, PDF)
- Accessibility (WCAG 2.1 AA target)

---

## 🔄 Data Flow

### Scan Execution Flow

```
1. User Request
   │
   ▼
2. API Gateway (POST /api/scan)
   │
   ▼
3. Scan Scheduler
   │
   ├─▶ Queue scan job
   │
   ▼
4. Scanner Layer
   │
   ├─▶ Port scanning (Nmap)
   ├─▶ HTTP probing (httpx)
   ├─▶ WebSocket testing
   └─▶ TLS fingerprinting
   │
   ▼
5. Raw Results
   │
   ▼
6. Detector Layer
   │
   ├─▶ Pattern matching
   ├─▶ Confidence scoring
   └─▶ Framework classification
   │
   ▼
7. Database Layer
   │
   ├─▶ Insert/update agent records
   ├─▶ Store scan results
   └─▶ Update telemetry
   │
   ▼
8. Notification
   │
   ├─▶ WebSocket broadcast to UI
   ├─▶ Trigger alerts (if configured)
   └─▶ Update dashboard
```

### Real-Time Update Flow

```
1. Event Occurs
   (new agent, alert, scan complete)
   │
   ▼
2. Event Bus
   │
   ├─▶ Store in database
   ├─▶ Queue for processing
   │
   ▼
3. WebSocket Server
   │
   ├─▶ Format message
   ├─▶ Filter by subscription
   │
   ▼
4. Connected Clients
   │
   ├─▶ Web UI (auto-update)
   └─▶ External WebSocket clients
```

### API Request Flow

```
1. HTTP Request
   │
   ▼
2. Rate Limiter
   │  └─▶ Check quota
   │  └─▶ Reject if exceeded (429)
   │
   ▼
3. Authentication
   │  └─▶ Validate JWT/API key
   │  └─▶ Reject if invalid (401)
   │
   ▼
4. Authorization
   │  └─▶ Check scopes
   │  └─▶ Reject if insufficient (403)
   │
   ▼
5. Input Validation
   │  └─▶ Validate schema
   │  └─▶ Reject if invalid (400)
   │
   ▼
6. Business Logic
   │  └─▶ Execute operation
   │
   ▼
7. Database Operation
   │
   ▼
8. Response Formatting
   │
   ▼
9. HTTP Response
```

---

## 🛡️ Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────┐
│            Perimeter Security               │
├─────────────────────────────────────────────┤
│  • Firewall rules                           │
│  • Rate limiting                            │
│  • DDoS protection                          │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│            Network Security                 │
├─────────────────────────────────────────────┤
│  • HTTPS/TLS 1.3                            │
│  • CORS configuration                       │
│  • Network segmentation                     │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│           Application Security              │
├─────────────────────────────────────────────┤
│  • JWT authentication                       │
│  • Role-based access control                │
│  • Input validation                         │
│  • SQL injection prevention                 │
│  • XSS protection                           │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│             Data Security                   │
├─────────────────────────────────────────────┤
│  • Encryption at rest (AES-256-GCM)         │
│  • Encryption in transit (TLS)              │
│  • Secure secret storage                    │
│  • Audit logging                            │
└─────────────────────────────────────────────┘
```

### Authentication Flow

```
User Login
   │
   ▼
Credentials → API
   │
   ▼
Validate against DB
   │
   ├─▶ Invalid → 401 Unauthorized
   │
   ▼
Generate JWT Token
   │
   ├─▶ Payload: user ID, scopes, expiry
   ├─▶ Sign with secret key
   │
   ▼
Return Token to Client
   │
   ▼
Subsequent Requests
   │
   ├─▶ Include in Authorization header
   ├─▶ Server validates signature
   ├─▶ Check expiry
   ├─▶ Verify scopes
   │
   ▼
Grant/Deny Access
```

### OWASP Compliance

**OWASP Top 10:2025:**

| Vulnerability | Mitigation | Status |
|--------------|------------|--------|
| **A01: Broken Access Control** | JWT auth, RBAC, read-only mode | ✅ |
| **A02: Security Misconfiguration** | Secure defaults, security headers | ✅ |
| **A03: Supply Chain Failures** | Pinned deps, SHA256 checksums | ✅ |
| **A04: Cryptographic Failures** | AES-256-GCM, TLS 1.3 | ✅ |
| **A05: Injection** | Parameterized queries, input validation | ✅ |
| **A06: Insecure Design** | Zero-trust architecture, threat modeling | ✅ |
| **A07: Authentication Failures** | Secure tokens, session expiry | ✅ |
| **A08: Integrity Failures** | Backup integrity checks, audit logs | ✅ |
| **A09: Logging Failures** | Comprehensive logging, alerting | ✅ |
| **A10: SSRF** | No external URL fetching | ✅ |

**OWASP LLM Top 10:2025:**
- See [SECURITY.md](SECURITY.md) for complete compliance matrix

---

## 📈 Scalability Considerations

### Current Limitations (v1.0.0)

| Component | Limitation | Workaround |
|-----------|------------|------------|
| **Database** | SQLite concurrency | Read-only replicas, WAL mode |
| **Scanner** | Single-threaded | Multiple instances, network sharding |
| **Web UI** | Single instance | Load balancer, multiple instances |
| **Telemetry** | In-memory aggregation | Reduce retention, external cache |

### Scaling Strategies

#### Horizontal Scaling (Phase C planned)

```
┌─────────────────────────────────────────────┐
│              Load Balancer                  │
│              (nginx/HAProxy)                │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│  API   │  │  API   │  │  API   │
│ Node 1 │  │ Node 2 │  │ Node 3 │
└────────┘  └────────┘  └────────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │  PostgreSQL DB  │
        │  (primary +     │
        │   read replicas)│
        └─────────────────┘
```

#### Network Sharding

For large networks (>10,000 hosts):

```
Scanner Instance 1: 192.168.0.0/16
Scanner Instance 2: 10.0.0.0/8
Scanner Instance 3: 172.16.0.0/12
                         │
                         ▼
               Central Aggregator
               (merges results)
```

#### Database Scaling

**Phase A (Current):**
- SQLite with WAL mode
- Single writer, multiple readers
- Suitable for <1,000 agents

**Phase C (Planned):**
- PostgreSQL with connection pooling
- Read replicas for telemetry queries
- Partitioning by date for telemetry tables

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Scan Speed** | 1,000 hosts/min | 500 hosts/min |
| **API Latency** | <100ms (p95) | <150ms (p95) |
| **Concurrent Users** | 100 | 50 |
| **Agents Supported** | 10,000 | 1,000 |
| **Telemetry Points/sec** | 10,000 | 1,000 |

---

## 🛠️ Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Language** | Python | 3.12+ | Core logic |
| **Web Framework** | FastAPI | 0.109+ | REST API |
| **Database** | SQLite | 3.40+ | Data storage |
| **ORM** | SQLAlchemy | 2.0+ | Database access |
| **Scanner** | Nmap, httpx | Latest | Network scanning |
| **WebSocket** | websockets | Latest | Real-time updates |
| **Authentication** | PyJWT | Latest | JWT tokens |
| **Validation** | Pydantic | 2.0+ | Input validation |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | React | 18+ | UI components |
| **Styling** | Custom CSS | — | Visual design |
| **State** | Context API | — | State management |
| **HTTP** | Fetch API | — | API communication |
| **WebSocket** | Native WS | — | Real-time updates |
| **Charts** | Custom/SVG | — | Data visualization |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Containerization** | Docker | 20.10+ | Deployment |
| **Orchestration** | Docker Compose | 2.0+ | Multi-service |
| **Reverse Proxy** | Nginx | 1.24+ | HTTPS, load balancing |
| **SSL/TLS** | Let's Encrypt | — | Certificates |
| **Monitoring** | Prometheus | Planned | Metrics |
| **Logging** | Structured JSON | — | Log aggregation |

---

## 🏗️ Deployment Patterns

### Single Instance (Development)

```
┌─────────────────────┐
│  CogniWatch         │
│  - Scanner          │
│  - Detector         │
│  - API              │
│  - Web UI           │
│  - SQLite DB        │
└─────────────────────┘
```

**Use Case:** Development, testing, small deployments  
**Capacity:** <100 hosts, <50 agents

### Docker Compose (Production)

```
┌─────────────────────┐
│  Web UI             │
│  (port 9000)        │
└──────────┬──────────┘
           │
┌──────────┴──────────┐
│  REST API           │
│  (internal)         │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───┴───┐   ┌────┴────┐
│Scanner│   │SQLite DB│
│Service│   │(volume) │
└───────┘   └─────────┘
```

**Use Case:** Most production deployments  
**Capacity:** <1,000 hosts, <500 agents

### Clustered (Enterprise - Planned)

```
         ┌─────────────┐
         │Load Balancer│
         │   (nginx)   │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───┴───┐ ┌────┴────┐ ┌───┴───┐
│  API  │ │  API    │ │  API  │
│ Node1 │ │ Node2   │ │ Node3 │
└───┬───┘ └────┬────┘ └───┬───┘
    │          │          │
    └──────────┼──────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴───┐         ┌──────┴──────┐
│Primary│         │Read Replicas│
│   DB  │         │  (2x)       │
└───────┘         └─────────────┘
```

**Use Case:** Large enterprise deployments  
**Capacity:** >10,000 hosts, >5,000 agents

---

## ⚡ Performance Characteristics

### Benchmark Results (v1.0.0)

**Scan Performance:**
- Small network (/24, 256 hosts): 2-5 minutes
- Medium network (/20, 4,096 hosts): 15-30 minutes
- Large network (/16, 65,536 hosts): 2-4 hours

**API Performance:**
- GET /api/agents (100 agents): <50ms
- GET /api/agents/:id: <20ms
- POST /api/scan: <100ms (queues immediately)
- GET /api/telemetry/:id (24h range): <200ms

**Database Performance:**
- Agent insert: <10ms
- Agent query (with filters): <50ms
- Telemetry insert (batch): <100ms (1000 points)
- Telemetry query (24h range): <150ms

### Resource Usage

**Idle (No Scans):**
- CPU: <5%
- RAM: ~300MB
- Disk: ~50MB (database grows with usage)

**During Scan (/24 network):**
- CPU: 30-50%
- RAM: ~500MB
- Network: Variable (based on rate limit)

**Under Load (100 API req/min):**
- CPU: 10-20%
- RAM: ~400MB
- Response time: <200ms (p95)

---

## 📚 Additional Resources

- **API Reference:** [API.md](API.md)
- **Security Report:** [SECURITY.md](SECURITY.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Framework Signatures:** [FRAMEWORK-SIGNATURES.md](FRAMEWORK-SIGNATURES.md)

---

<p align="center">
  <strong>Want to contribute?</strong> Check out our <a href="../README.md#contributing">Contributing Guidelines</a>!
</p>
