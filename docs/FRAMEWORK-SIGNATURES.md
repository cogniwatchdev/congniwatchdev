# Framework Signature CONTRIBUTING Guide

This guide explains how to create, test, and contribute new framework signatures to CogniWatch's detection engine.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [JSON Schema Reference](#json-schema-reference)
3. [Detection Patterns](#detection-patterns)
4. [Testing & Validation](#testing--validation)
5. [GitHub PR Template](#github-pr-template)
6. [Framework Fingerprinting Guide](#framework-fingerprinting-guide)

---

## Overview

CogniWatch detects AI agent frameworks using a **multi-layer detection approach**. Each framework has a signature file (JSON format) that defines:

- **Network indicators** (ports, WebSocket protocols, mDNS)
- **HTTP fingerprints** (headers, response patterns, API endpoints)
- **Process signatures** (binary names, container images)
- **Confidence scoring weights** (Bayesian probability model)

### Signature File Location

```
cogniwatch/
└── scanner/
    └── signatures/
        ├── openclaw.json
        ├── agent-zero.json
        ├── langgraph.json
        └── ...
```

### Naming Convention

- **Lowercase with hyphens**: `framework-name.json`
- **Use official framework name**: Match the project's branding
- **Avoid abbreviations**: Use `semantic-kernel` not `sk`

---

## JSON Schema Reference

### Complete Schema (TypeScript Definition)

```typescript
interface FrameworkSignature {
  // === Identity ===
  framework: string;           // Lowercase identifier (filename without .json)
  name: string;                // Display name (e.g., "Agent-Zero")
  version: string;             // Minimum version detected (e.g., "1.0+")
  category: string;            // Category (see below)
  
  // === Network Ports ===
  ports: {
    primary: number;           // Main/default port
    alternative: number[];     // Alternate ports (e.g., legacy, configurable)
    websocket: number | null;  // WebSocket port (can be same as primary)
    http: number;              // HTTP API port
  };
  
  // === HTTP Fingerprinting ===
  http_fingerprints: {
    title_patterns: string[];          // HTML <title> regex patterns
    header_patterns: Record<string, string>;  // HTTP header regex (key: header name, value: regex)
    body_patterns: string[];           // Response body regex patterns
    response_check_paths: string[];    // Paths to probe for detection
  };
  
  // === API Endpoints ===
  api_endpoints: {
    status: string;            // Health/status endpoint
    [key: string]: string;     // Other framework-specific endpoints
  };
  
  // === WebSocket Detection ===
  websocket: {
    enabled: boolean;
    path: string | null;       // WebSocket path (e.g., "/ws")
    protocol: string | null;   // Sec-WebSocket-Protocol value
    handshake_patterns: string[];  // Handshake header patterns
  };
  
  // === Configuration Files ===
  config_files: string[];      // Typical config file locations (support ~ expansion)
  
  // === Process Signatures ===
  process_names: string[];     // Process/command names (e.g., "openclaw", "node")
  
  // === Network Signatures ===
  network_signatures: {
    mdns: string | null;       // mDNS service name (e.g., "_openclaw._tcp.local")
    txt_records: string[];     // Expected TXT record prefixes
  };
  
  // === Confidence Scoring ===
  confidence: {
    port_match: number;        // Weight for port detection (0.0-1.0)
    http_pattern: number;      // Weight for single HTTP pattern match
    http_multiple: number;     // Bonus for multiple HTTP matches
    api_validated: number;     // Weight for confirmed API response
    websocket_match: number;   // Weight for WebSocket protocol match
    framework_specific: number; // Weight for unique indicators (mDNS, etc.)
    threshold_confirmed: number; // ≥ this = "Confirmed" badge
    threshold_likely: number;    // ≥ this = "Likely" badge
    threshold_possible: number;  // ≥ this = "Possible" badge
  };
  
  // === Priority & Metadata ===
  detection_priority: number;  // 1 (highest) to 3 (lowest)
  notes: string;               // Human-readable notes, caveats, tips
  variants: string[];          // Known variants/derivatives detected by this signature
}
```

### Category Values

Use one of these standard categories:

- `self-hosted-gateway` — Hub/orchestration (OpenClaw, LangGraph)
- `general-purpose-assistant` — Personal AI assistants (Agent-Zero)
- `library` — Python/.NET packages (Pydantic AI, CrewAI, Semantic Kernel)
- `conversational-ai` — Chatbot frameworks (Rasa)
- `low-code-builder` — Visual tools (Langflow)
- `cloud-based` — Primarily SaaS (OpenAI Agents SDK)

---

## Detection Patterns

### HTTP Response Fingerprints

**Server Headers:**
```json
"header_patterns": {
  "server": "OpenClaw-Gateway/.*",
  "x-powered-by": "Express",
  "x_openclaw_version": "[0-9]+\\.[0-9]+\\.[0-9]+"
}
```

**Response Body Patterns:**
```json
"body_patterns": [
  "OpenClaw",
  "WebSocket Gateway",
  "Control UI",
  "class=\"openclaw-app\""
]
```

**HTML Title Patterns:**
```json
"title_patterns": [
  "OpenClaw.*Gateway",
  "Agent.*Zero",
  "LangGraph.*Server"
]
```

### Port Detection Strategy

```json
"ports": {
  "primary": 18789,
  "alternative": [8787, 443],
  "websocket": 18789,
  "http": 18789
}
```

**Common Default Ports by Framework:**

| Port | Frameworks |
|------|-----------|
| 18789 | OpenClaw, NanoClaw, ZeroClaw, IronClaw |
| 8787 | OpenClaw (legacy) |
| 50001 | Agent-Zero (Docker default) |
| 50080 | Agent-Zero (user-reported alternate) |
| 8123 | LangGraph Server |
| 8080 | AutoGen Studio, Strands Agents |
| 8000-8004 | Google ADK, LangGraph, Microsoft Agent Framework |
| 5005 | Rasa |

### WebSocket Detection

```json
"websocket": {
  "enabled": true,
  "path": "/ws",
  "protocol": "openclaw-v1",
  "handshake_patterns": [
    "Upgrade: websocket",
    "Connection: Upgrade",
    "Sec-WebSocket-Protocol: openclaw"
  ]
}
```

### mDNS/Bonjour Detection

```json
"network_signatures": {
  "mdns": "_openclaw._tcp.local",
  "txt_records": [
    "version=",
    "node_id="
  ]
}
```

### Config File Detection

```json
"config_files": [
  "~/.openclaw/config.json",
  "~/.openclaw/sessions.json",
  "/etc/openclaw/gateway.conf"
]
```

These paths are checked during local scans (not remote network scans).

---

## Testing & Validation

### Step 1: Set Up Test Environment

```bash
# Clone CogniWatch
git clone https://github.com/neo/cogniwatch.git
cd cogniwatch

# Install dependencies
npm install

# Set up test framework (example: OpenClaw)
docker run -d -p 18789:18789 --name test-openclaw openclaw/gateway:latest
```

### Step 2: Create Signature File

```bash
# Copy template
cp scanner/signatures/template.json scanner/signatures/myframework.json
```

### Step 3: Manual Testing

**Test HTTP fingerprints:**
```bash
# Check response headers
curl -i http://localhost:18789/

# Check specific endpoints
curl http://localhost:18789/api/status
curl http://localhost:18789/v1/gateway

# Check WebSocket
wscat -c ws://localhost:18789/ws
```

**Test with signature patterns:**
```bash
# Test each pattern manually
curl -s http://localhost:18789/ | grep -E "OpenClaw|WebSocket Gateway"
curl -sI http://localhost:18789/ | grep "Server:"
```

### Step 4: Automated Validation

```bash
# Run signature validator
npm run validate-signatures

# Run scanner against test instance
npm run scan -- --target localhost:18789 --signature myframework

# Check confidence score output
# Expected: ≥85% for confirmed detection
```

### Step 5: Cleanup

```bash
docker stop test-openclaw
docker rm test-openclaw
```

### Validation Checklist

Before submitting, ensure:

- [ ] Signature file is valid JSON (passes `npm run validate-signatures`)
- [ ] At least 2-3 detection layers with positive weights
- [ ] Total confidence weights sum to ≤1.0 (100%)
- [ ] Thresholds are reasonable (confirmed ≥0.85, likely ≥0.60, possible ≥0.30)
- [ ] Tested against real deployment (local or cloud)
- [ ] No false positives against other frameworks
- [ ] Documentation updated (README.md framework list)

---

## GitHub PR Template

### Pull Request: Add `[Framework Name]` Signature

**Template:**

```markdown
## 🎯 New Framework Signature: [Framework Name]

**Framework:** [Official Name]  
**GitHub:** [Link to repo]  
**Website:** [Link to docs]  
**Category:** [See categories above]

### 📊 Detection Summary

| Detection Layer | Confidence Weight | Status |
|-----------------|-------------------|--------|
| Port Match | 30% | ✅ |
| HTTP Fingerprints | 25% | ✅ |
| API Validation | 25% | ✅ |
| WebSocket | 10% | ⚠️ (if applicable) |
| Framework-Specific | 10% | ✅ |
| **Total** | **100%** | |

**Expected Confidence:** ≥85% (Confirmed)

### 🧪 Testing Performed

- [ ] Tested against local deployment
- [ ] Tested against Docker container
- [ ] No false positives on other frameworks
- [ ] Validated all API endpoints respond correctly
- [ ] Checked mDNS/multicast (if applicable)

**Test Environment:**
```
OS: [e.g., Ubuntu 24.04, macOS 14, WSL2]
Framework Version: [e.g., OpenClaw 1.2.3]
Deployment: [e.g., Docker, native, npm]
```

### 📝 Framework Notes

[Brief description of the framework, why it's important to detect, any special considerations]

### 🔍 Detection Signatures

**Key Fingerprints:**
- Default port: [port]
- Server header: [header value]
- API endpoint: [path]
- WebSocket: [yes/no, path]
- mDNS: [service name or N/A]

### 📚 References

- Documentation: [link]
- Docker image: [link]
- Installation guide: [link]
- Any research/reports used

---

**Checklist:**
- [ ] Signature file added to `scanner/signatures/`
- [ ] README.md updated with framework in appropriate tier
- [ ] Confidence scoring documented
- [ ] No breaking changes to existing signatures
- [ ] Follows naming convention (lowercase, hyphens)
```

---

## Framework Fingerprinting Guide

### Phase 1: Reconnaissance

**Gather Information:**
1. Read framework documentation
2. Check GitHub README for deployment instructions
3. Look for Docker images and default port mappings
4. Identify HTTP API endpoints from docs
5. Search for "default port" or "configuration" in docs

**Tools:**
```bash
# Check Docker image ports
docker inspect <image> | grep -A5 '"Ports"'

# Search GitHub for port references
gh search code -R <org>/<repo> "port.*[0-9]{4,5}"
```

### Phase 2: Active Fingerprinting

**HTTP Response Analysis:**
```bash
# Full response with headers
curl -i http://localhost:<port>/

# Check common API paths
curl http://localhost:<port>/api/status
curl http://localhost:<port>/health
curl http://localhost:<port>/v1/info

# Check for WebSocket upgrade
curl -i -H "Upgrade: websocket" -H "Connection: Upgrade" http://localhost:<port>/ws
```

**WebSocket Testing:**
```bash
# Install wscat
npm install -g wscat

# Test WebSocket handshake
wscat -c ws://localhost:<port>/ws -s "Sec-WebSocket-Protocol: <proto>"
```

**mDNS Discovery:**
```bash
# Linux
avahi-browse -a

# macOS
dns-sd -B _http._tcp
dns-sd -L "OpenClaw" _http._tcp

# Check for framework-specific services
avahi-browse -t | grep -i "claw\|agent"
```

### Phase 3: Process & Container Signatures

**Process Detection:**
```bash
# Find running processes
ps aux | grep -i "openclaw\|agent.*zero"

# Check listening ports
netstat -tlnp | grep <port>
ss -tlnp | grep <port>

# Check container metadata
docker ps --format "table {{.Image}}\t{{.Ports}}\t{{.Names}}"
docker inspect <container> | jq '.[0].Config'
```

**Docker-Specific Indicators:**
```bash
# Image name
docker inspect <container> | jq '.[0].Config.Image'

# Environment variables (may reveal framework)
docker inspect <container> | jq '.[0].Config.Env'

# Labels
docker inspect <container> | jq '.[0].Config.Labels'
```

### Phase 4: Network Behavior Analysis

**Outbound Traffic Correlation:**
Many frameworks make outbound calls to LLM APIs. Correlate:
- Inbound service on port X
- Outbound to `api.openai.com`, `api.anthropic.com`, etc.
- Timing correlation (request → response)

**Tools:**
```bash
# Monitor outbound connections
sudo tcpdump -i eth0 -n port 443

# Check established connections
netstat -anp | grep ESTABLISHED
```

### Phase 5: Config File & Persistence Detection

**Common Locations:**
```bash
# Check user directories
ls -la ~/.openclaw/
ls -la ~/.agent-zero/
ls -la /etc/openclaw/

# Find config files by content
find ~ -name "*.json" -exec grep -l "openclaw\|agent" {} \;
```

---

## Example: Creating an OpenClaw Signature

**Step 1: Gather intel from docs**
```
Docs say: "OpenClaw runs on port 18789 by default"
GitHub shows: docker-compose.yml maps 18789:18789
API docs mention: /api/status, /v1/gateway endpoints
```

**Step 2: Test HTTP responses**
```bash
curl -i http://localhost:18789/
# Response:
# HTTP/1.1 200 OK
# Server: OpenClaw-Gateway/1.2.3
# X-OpenClaw-Version: 1.2.3
# Content-Type: application/json
```

**Step 3: Test WebSocket**
```bash
wscat -c ws://localhost:18789/ws
# Successful connection
# Protocol negotiation shows: openclaw-v1
```

**Step 4: Check mDNS**
```bash
avahi-browse -t | grep openclaw
# Found: _openclaw._tcp.local
```

**Step 5: Write signature**
```json
{
  "framework": "openclaw",
  "name": "OpenClaw",
  "ports": {
    "primary": 18789,
    "alternative": [8787],
    "websocket": 18789,
    "http": 18789
  },
  "http_fingerprints": {
    "header_patterns": {
      "server": "OpenClaw-Gateway/.*",
      "x_openclaw_version": ".*"
    }
  },
  "websocket": {
    "enabled": true,
    "path": "/ws",
    "protocol": "openclaw-v1"
  },
  "network_signatures": {
    "mdns": "_openclaw._tcp.local"
  },
  "confidence": {
    "port_match": 0.30,
    "http_pattern": 0.15,
    "api_validated": 0.25,
    "websocket_match": 0.15,
    "framework_specific": 0.05
  },
  "detection_priority": 1
}
```

**Step 6: Validate and test**
```bash
npm run validate-signatures
npm run scan -- --target localhost:18789
# Output: "✅ OpenClaw detected at 192.168.1.100:18789 (94% confidence)"
```

---

## Contributing

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/signature-<framework-name>`
3. **Add signature file** in `scanner/signatures/`
4. **Update README.md** with framework in appropriate tier
5. **Test** against real deployment
6. **Commit** with clear message: `Add [Framework] signature (Tier X)`
7. **Submit PR** using template above

**Questions?** Open an issue or ask in Discord community.

---

*Last Updated: March 7, 2026*
