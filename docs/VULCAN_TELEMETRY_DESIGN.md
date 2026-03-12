# VULCAN Telemetry Design Document

## Mission Statement

Design the telemetry schema that makes CogniWatch valuable beyond "ports open". What unique data can we collect about AI agents that no one else has?

**Core Insight**: Traditional security scanners tell you what services are running. CogniWatch tells you what those services **think**, **know**, and **can do**.

---

## Why This Matters

### What Makes an Agent Directory VALUABLE?

1. **Capability Intelligence** - Not just "an agent exists" but "this agent can access email, execute code, and has a context window of 128K tokens"
2. **Security Posture** - Which agents are exposed without auth? Which have dangerous capabilities enabled?
3. **Performance Baselines** - What's normal response time? When does an agent start degrading?
4. **Behavioral Anomalies** - Agent suddenly active at 3 AM? Making 10x normal API calls? That's interesting.
5. **Ecosystem Mapping** - Which frameworks dominate? What models are people actually using?

### What Would Security Teams Pay To Know?

- **Exposed Agents**: AI agents without authentication on public IPs
- **Dangerous Capabilities**: Agents with code execution, file system access, or internal network access
- **Data Leakage Risk**: Agents connected to email, databases, or internal APIs
- **Compliance Gaps**: Agents processing PII without proper controls
- **Supply Chain Risk**: Agents using vulnerable framework versions (CVE matching)
- **Compromise Indicators**: Unusual activity patterns suggesting hijacking

### What Helps Developers Optimize?

- **Performance Benchmarks**: How does my agent's p99 compare to others using the same framework?
- **Capability Gaps**: What tools do similar agents have that mine doesn't?
- **Cost Optimization**: Token throughput and efficiency metrics
- **Uptime SLAs**: Am I meeting reliability expectations?

### Patterns Indicating Compromise

- Sudden capability changes (new tools enabled)
- Activity outside normal hours
- Unusual endpoint access patterns
- Version downgrades (potential rollback to vulnerable version)
- Spike in error rates (possible attack attempts)
- New network topology (agent now behind different proxy)

---

## Telemetry Categories

### 1. Identity & Capability Telemetry

**Purpose**: Know what each agent IS and what it CAN DO.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| framework | TEXT | Discovery scan | openclaw, langchain, autogen, crewai, etc. |
| framework_version | TEXT | /version endpoint, docs | For CVE matching |
| model_provider | TEXT | API response | openai, anthropic, ollama, etc. |
| model_name | TEXT | API response | gpt-4, claude-3, llama-2, etc. |
| context_window | INTEGER | Error messages, docs | Token limit |
| available_tools | JSON | Tool listing endpoint | ["web_search", "read", "exec", ...] |
| api_versions | JSON | /api/versions | Supported API endpoints |
| feature_flags | JSON | Config exposure | Debug mode, unsafe tools enabled |
| persona | TEXT | Self-description | Agent's stated purpose |
| capabilities_hash | TEXT | Computed | Quick change detection |

### 2. Performance Telemetry

**Purpose**: Measure how FAST and RELIABLE each agent is.

| Field | Type | Notes |
|-------|------|-------|
| response_time_p50 | REAL | Median response time (ms) |
| response_time_p95 | REAL | 95th percentile |
| response_time_p99 | REAL | 99th percentile - critical for SLA |
| throughput_rps | REAL | Requests/second before rate limit |
| concurrent_sessions | INTEGER | Max simultaneous connections |
| token_throughput | REAL | Tokens/second (if measurable) |
| error_rate | REAL | 5xx errors / total requests |
| availability_pct | REAL | Uptime percentage |
| last_performance_test | TIMESTAMP | When metrics were collected |

### 3. Security Posture Telemetry

**Purpose**: Assess how SECURE (or exposed) each agent is.

| Field | Type | Notes |
|-------|------|-------|
| auth_method | TEXT | none, api_key, jwt, oauth, basic |
| rate_limiting_enabled | BOOLEAN | X-RateLimit headers present |
| rate_limit_threshold | INTEGER | Requests per minute (if discoverable) |
| cors_policy | TEXT | permissive, restrictive, misconfigured |
| admin_endpoints_exposed | BOOLEAN | /admin, /debug, /config accessible |
| default_credentials | BOOLEAN | admin:admin, root:root work |
| https_enforced | BOOLEAN | Redirects HTTP to HTTPS |
| known_vulnerabilities | JSON | CVE list based on version |
| security_score | INTEGER | 0-100 composite score |
| last_security_scan | TIMESTAMP | Assessment timestamp |

### 4. Network Topology Telemetry

**Purpose**: Understand WHERE the agent lives in the network.

| Field | Type | Detection Method |
|-------|------|------------------|
| behind_proxy | BOOLEAN | X-Forwarded-For, Via headers |
| proxy_type | TEXT | nginx, apache, traefik (from headers) |
| load_balanced | BOOLEAN | Cookie patterns, server header rotation |
| cdn_detected | BOOLEAN | Cloudflare, Akamai signatures |
| hosting_provider | TEXT | AWS, GCP, Azure, DO (IP ranges, headers) |
| container_detected | BOOLEAN | Kubernetes, Docker signatures |
| orchestrator | TEXT | k8s, swarm, nomad (if detectable) |
| asn | TEXT | Autonomous System Number |
| geo_location | TEXT | Country, region (from IP) |
| network_distance | INTEGER | Hops from scanner (TTL analysis) |

### 5. Behavioral Telemetry

**Purpose**: Learn HOW the agent BEHAVES over time.

| Field | Type | Notes |
|-------|------|-------|
| uptime_pattern | JSON | Hourly online/offline heatmap |
| peak_activity_hours | JSON | [9, 10, 11, 14, 15] - busiest hours |
| session_duration_p50 | REAL | Median session length (minutes) |
| session_duration_p95 | REAL | 95th percentile |
| endpoint_usage | JSON | {"web_search": 45, "read": 30, ...} |
| version_history | JSON | [{"version": "1.2", "date": "..."}] |
| update_frequency | REAL | Days between version changes |
| activity_trend | TEXT | increasing, stable, decreasing |
| anomaly_score | REAL | Deviation from normal behavior |

### 6. AI-Specific Telemetry

**Purpose**: Capture what makes AI agents UNIQUE.

| Field | Type | Detection Method |
|-------|------|------------------|
| streaming_support | BOOLEAN | SSE, WebSocket streaming tests |
| streaming_protocol | TEXT | sse, websocket, grpc |
| multimodal_input | JSON | ["image", "audio", "video"] |
| multimodal_output | JSON | ["image", "audio", "text"] |
| function_calling | BOOLEAN | Tool use capability |
| agent_orchestration | BOOLEAN | Can spawn/manage other agents |
| memory_persistence | BOOLEAN | Long-term memory across sessions |
| fine_tune_indicator | TEXT | Custom model name patterns |
| prompt_injection_resistance | REAL | Score from test payloads |
| jailbreak_resistance | REAL | Score from test payloads |
| context_retention | REAL | Tokens retained after N turns |

---

## Database Schema Design

### New Tables

#### `agent_capabilities`
Dynamic capability storage per agent.

```sql
CREATE TABLE agent_capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    framework TEXT,
    framework_version TEXT,
    model_provider TEXT,
    model_name TEXT,
    context_window INTEGER,
    available_tools JSON,
    api_versions JSON,
    feature_flags JSON,
    persona TEXT,
    capabilities_hash TEXT,
    streaming_support BOOLEAN,
    streaming_protocol TEXT,
    multimodal_input JSON,
    multimodal_output JSON,
    function_calling BOOLEAN,
    agent_orchestration BOOLEAN,
    memory_persistence BOOLEAN,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    UNIQUE(agent_id, updated_at)
);
```

#### `performance_metrics`
Time-series performance data.

```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    response_time_p50 REAL,
    response_time_p95 REAL,
    response_time_p99 REAL,
    throughput_rps REAL,
    concurrent_sessions INTEGER,
    token_throughput REAL,
    error_rate REAL,
    availability_pct REAL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_performance_metrics_agent ON performance_metrics(agent_id, measured_at DESC);
CREATE INDEX idx_performance_metrics_time ON performance_metrics(measured_at DESC);
```

#### `security_assessments`
Per-scan security posture.

```sql
CREATE TABLE security_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    auth_method TEXT,
    rate_limiting_enabled BOOLEAN,
    rate_limit_threshold INTEGER,
    cors_policy TEXT,
    admin_endpoints_exposed BOOLEAN,
    default_credentials BOOLEAN,
    https_enforced BOOLEAN,
    known_vulnerabilities JSON,
    security_score INTEGER,
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_security_assessments_agent ON security_assessments(agent_id, assessed_at DESC);
```

#### `topology_data`
Network position and infrastructure.

```sql
CREATE TABLE topology_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    behind_proxy BOOLEAN,
    proxy_type TEXT,
    load_balanced BOOLEAN,
    cdn_detected BOOLEAN,
    hosting_provider TEXT,
    container_detected BOOLEAN,
    orchestrator TEXT,
    asn TEXT,
    geo_location TEXT,
    network_distance INTEGER,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_topology_data_agent ON topology_data(agent_id);
CREATE INDEX idx_topology_data_hosting ON topology_data(hosting_provider);
```

#### `behavioral_patterns`
Learned patterns over time.

```sql
CREATE TABLE behavioral_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    uptime_pattern JSON,
    peak_activity_hours JSON,
    session_duration_p50 REAL,
    session_duration_p95 REAL,
    endpoint_usage JSON,
    version_history JSON,
    update_frequency REAL,
    activity_trend TEXT,
    anomaly_score REAL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_behavioral_patterns_agent ON behavioral_patterns(agent_id);
```

---

## API Endpoints

### `/api/telemetry/heatmap`
**Purpose**: Global distribution of agent capabilities.

**Response**:
```json
{
  "frameworks": {
    "openclaw": 45,
    "langchain": 23,
    "autogen": 12,
    "crewai": 8
  },
  "models": {
    "gpt-4": 34,
    "claude-3": 28,
    "llama-2": 15,
    "ollama": 11
  },
  "capabilities": {
    "web_search": 67,
    "file_read": 54,
    "code_exec": 23,
    "email_access": 12
  },
  "security_posture": {
    "no_auth": 15,
    "api_key": 45,
    "jwt": 20,
    "oauth": 8
  }
}
```

### `/api/telemetry/trends`
**Purpose**: Temporal patterns (uptime, activity).

**Response**:
```json
{
  "uptime_24h": [
    {"hour": 0, "online_agents": 45},
    {"hour": 1, "online_agents": 43},
    ...
  ],
  "activity_peaks": {
    "day_of_week": {"monday": 0.85, "tuesday": 0.92, ...},
    "hour_of_day": {"9": 0.95, "10": 0.98, ...}
  },
  "new_agents_7d": 12,
  "version_updates_7d": 8
}
```

### `/api/telemetry/security-distribution`
**Purpose**: Security posture across agents.

**Response**:
```json
{
  "auth_distribution": {
    "none": {"count": 15, "percentage": 15.0},
    "api_key": {"count": 45, "percentage": 45.0},
    "jwt": {"count": 20, "percentage": 20.0},
    "oauth": {"count": 8, "percentage": 8.0},
    "basic": {"count": 12, "percentage": 12.0}
  },
  "vulnerability_summary": {
    "critical": 3,
    "high": 12,
    "medium": 28,
    "low": 45
  },
  "exposed_endpoints": {
    "admin Panels": 8,
    "debug_endpoints": 15,
    "config_files": 5
  },
  "avg_security_score": 72.5
}
```

### `/api/telemetry/framework-comparison`
**Purpose**: Performance by framework.

**Response**:
```json
{
  "frameworks": [
    {
      "name": "openclaw",
      "count": 45,
      "response_time_p50": 245,
      "response_time_p99": 890,
      "error_rate": 0.02,
      "availability": 99.5
    },
    {
      "name": "langchain",
      "count": 23,
      "response_time_p50": 312,
      "response_time_p99": 1020,
      "error_rate": 0.04,
      "availability": 98.2
    }
  ],
  "model_comparison": [
    {
      "model": "gpt-4",
      "avg_response_time": 280,
      "error_rate": 0.01
    },
    {
      "model": "claude-3",
      "avg_response_time": 320,
      "error_rate": 0.02
    }
  ]
}
```

### `/api/telemetry/anomalies`
**Purpose**: Unusual patterns detected.

**Response**:
```json
{
  "anomalies": [
    {
      "agent_id": "openclaw-192-168-1-100-8765",
      "type": "activity_spike",
      "severity": "high",
      "description": "Activity 340% above normal for this hour",
      "detected_at": "2026-03-06T23:45:00Z",
      "baseline": 12.5,
      "current": 55.0
    },
    {
      "agent_id": "langchain-192-168-1-105-9000",
      "type": "capability_change",
      "severity": "critical",
      "description": "New tool 'exec' enabled (was not present 24h ago)",
      "detected_at": "2026-03-06T22:30:00Z",
      "previous_tools": ["web_search", "read"],
      "current_tools": ["web_search", "read", "exec"]
    },
    {
      "agent_id": "autogen-192-168-1-110-8080",
      "type": "security_regression",
      "severity": "critical",
      "description": "Authentication disabled (was enabled)",
      "detected_at": "2026-03-06T21:15:00Z"
    }
  ],
  "total_anomalies": 3,
  "by_severity": {
    "critical": 2,
    "high": 1,
    "medium": 0,
    "low": 0
  }
}
```

---

## Security Implications

### High-Value Intelligence

1. **Exposed Agents Map**: Plot all agents without auth on a geographic map
2. **Capability Heatmap**: Which organizations have agents with code execution?
3. **Framework Vulnerabilities**: Alert when CVEs affect deployed frameworks
4. **Compromise Detection**: Behavioral anomalies = potential hijacking

### Ethical Considerations

- **Passive Collection Only**: We observe, don't exploit
- **Opt-Out Mechanism**: Agents can signal "don't scan me"
- **Data Minimization**: Collect only what's publicly observable
- **No Credential Storage**: Never store passwords or API keys

---

## Next Steps

1. **Implement schema migrations** for new tables
2. **Build telemetry collector** module
3. **Create API endpoints** in telemetry_api.py
4. **Add anomaly detection** algorithms
5. **Build dashboard visualizations** for heatmap, trends, anomalies

---

*"Knowledge is power. Information about AI agents is dangerous power."*
