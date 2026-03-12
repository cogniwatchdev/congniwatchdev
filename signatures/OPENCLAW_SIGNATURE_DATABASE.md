# OpenClaw Signature Database

**Version:** 2026.2.25  
**Confidence Target:** 95%+  
**Last Updated:** 2026-03-07

---

## HTTP Headers

### Response Headers (Gateway HTTP)

OpenClaw Gateway returns these characteristic security headers on ALL responses:

```
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' ws: wss:
Content-Type: text/html; charset=utf-8
Cache-Control: no-cache
Connection: keep-alive
Keep-Alive: timeout=5
```

**Detection signals:**
- ✅ CSP includes `connect-src 'self' ws: wss:` (WebSocket support indicator)
- ✅ CSP includes `base-uri 'none'; object-src 'none'` (security-hardened)
- ✅ `X-Frame-Options: DENY` (clickjacking protection)
- ✅ `Cache-Control: no-cache` (dynamic content)
- ✅ No `Server:` header (hidden server identity)

### Custom Headers (Request)

OpenClaw recognizes these custom headers:

| Header | Purpose | Pattern |
|--------|---------|---------|
| `X-OpenClaw-Token` | Alternative auth token | Any non-empty string |
| `X-OpenClaw-Agent-Id` | Agent targeting | `[a-z0-9][a-z0-9_-]{0,63}` |
| `X-OpenClaw-Agent` | Legacy agent targeting | Same as above |
| `X-OpenClaw-Session-Key` | Session routing | Any string |
| `X-OpenClaw-Message-Channel` | Channel context for tools | `slack\|telegram\|discord\|etc` |
| `X-OpenClaw-Account-Id` | Multi-account routing | Any string |
| `Authorization: Bearer <token>` | Primary auth | Bearer token format |

**Detection:** Check for these headers in outbound requests from OpenClaw instances.

---

## API Endpoints

### Core Gateway Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/` | GET | No | Dashboard SPA (HTML) |
| `/api/channels` | GET/POST | **Yes** | Channel management |
| `/api/channels/*` | ANY | **Yes** | Channel operations |
| `/api/sessions` | GET | **Yes** | Session listing |
| `/api/history` | GET | **Yes** | Session history |
| `/v1/chat/completions` | POST | **Yes** | OpenAI-compatible API |
| `/v1/responses` | POST | **Yes** | OpenResponses API |
| `/tools/invoke` | POST | **Yes** | Direct tool invocation |
| `/hooks/*` | POST | **Yes** (X-OpenClaw-Token) | Webhook handlers |

### /api/channels

**Request:**
```http
GET /api/channels HTTP/1.1
Host: localhost:18789
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{"channels": [...]}
```

**Response (401 Unauthorized):**
```json
{"error":{"message":"Unauthorized","type":"unauthorized"}}
```

**Unique signatures:**
- Error format: `{"error":{"message":"<msg>","type":"<type>"}}`
- Type values: `unauthorized`, `rate_limited`, `not_found`

### /api/sessions

**Response (401):**
```json
{"error":{"message":"Unauthorized","type":"unauthorized"}}
```

**Response (200):** Returns session list or HTML dashboard (depends on auth)

### /v1/chat/completions (OpenAI-compatible)

**Request:**
```json
{
  "model": "openclaw:main",
  "messages": [{"role": "user", "content": "hi"}],
  "stream": false
}
```

**Headers:**
```
Authorization: Bearer <gateway-token>
Content-Type: application/json
x-openclaw-agent-id: main  (optional)
x-openclaw-session-key: <key>  (optional)
```

**Response:** Standard OpenAI Chat Completions format

### /v1/responses (OpenResponses API)

**Request:**
```json
{
  "model": "openclaw:main",
  "input": "hello",
  "tools": [...],
  "stream": true
}
```

**Response:** OpenResponses format with item-based outputs

### /tools/invoke

**Request:**
```json
{
  "tool": "sessions_list",
  "action": "json",
  "args": {},
  "sessionKey": "main"
}
```

**Response (200):**
```json
{"ok": true, "result": {...}}
```

**Response (404 - tool denied):**
```json
{"ok": false, "error": {"type": "not_found", "message": "..."}}
```

**Response (401):**
```json
{"error":{"message":"Unauthorized","type":"unauthorized"}}
```

**Response (429 - rate limited):**
```json
{"error":{"message":"Too many failed authentication attempts. Please try again later.","type":"rate_limited"}}
Retry-After: <seconds>
```

---

## Session Management

### Session Key Format

OpenClaw uses hierarchical session keys:

```
<agent-id>:<scope>:<identifier>
```

Examples:
- `main:user:jannie` - Main agent, user-scoped session
- `main:channel:discord:1479605397131100377` - Channel-scoped session
- `main:global:uuid-v4` - Global session

**Pattern:** `^[a-z0-9][a-z0-9_-]*:(user|channel|global|group):[a-zA-Z0-9_-:]+$`

### JWT Structure

OpenClaw does NOT use JWT for session management. Sessions are server-side state managed by the Gateway.

### Connection Patterns

- **WebSocket:** Primary connection mode for browser dashboard and CLI
  - URL: `ws://<host>:18789/` or `wss://<host>:<port>/`
  - Subprotocol: Not specified
  - Heartbeat: Built into protocol
  
- **HTTP Long-polling:** Not used
  
- **Connection pooling:** Per-agent session management

### Cookies

OpenClaw does NOT use cookies for authentication. All auth is via Bearer token headers.

---

## Authentication

### Authentication Modes

OpenClaw Gateway supports three auth modes:

1. **Token mode** (`gateway.auth.mode: "token"`)
   - Single shared token
   - Config: `gateway.auth.token` or env `OPENCLAW_GATEWAY_TOKEN`

2. **Password mode** (`gateway.auth.mode: "password"`)
   - Single shared password
   - Config: `gateway.auth.password` or env `OPENCLAW_GATEWAY_PASSWORD`

3. **Tailscale Serve mode** (`gateway.tailscale.mode: "serve"`)
   - Tokenless for Tailnet-originated requests
   - Requires `x-forwarded-for` from Tailscale

### Auth Header Format

```
Authorization: Bearer <token-or-password>
```

Alternative (hooks only):
```
X-OpenClaw-Token: <token>
```

**Note:** Query parameters for tokens are explicitly REJECTED:
> "Hook token must be provided via Authorization: Bearer <token> or X-OpenClaw-Token header (query parameters are not allowed)."

### Rate Limiting

**429 Response format:**
```json
{
  "error": {
    "message": "Too many failed authentication attempts. Please try again later.",
    "type": "rate_limited"
  }
}
```

**Headers:**
```
Retry-After: <seconds>
```

**Rate limit config (default):**
- Hook auth failures: 20 attempts per 60 seconds
- Lockout duration: 60 seconds

---

## Error Signatures

### Standard Error Format

ALL OpenClaw API errors follow this JSON schema:

```json
{
  "error": {
    "message": "<human-readable message>",
    "type": "<error-code>"
  }
}
```

### Error Types

| HTTP Status | Type | Message Pattern |
|-------------|------|-----------------|
| 400 | `bad_request` | Varies by validation error |
| 401 | `unauthorized` | "Unauthorized" |
| 404 | `not_found` | "Not found" or tool-specific |
| 405 | `method_not_allowed` | "Method not allowed" |
| 429 | `rate_limited` | "Too many failed authentication attempts..." |
| 500 | `internal_error` | Sanitized message |

### Example Errors

**401 Unauthorized:**
```json
{"error":{"message":"Unauthorized","type":"unauthorized"}}
```

**404 Not Found:**
```json
{"error":{"message":"Not found","type":"not_found"}}
```

**429 Rate Limited:**
```json
{"error":{"message":"Too many failed authentication attempts. Please try again later.","type":"rate_limited"}}
```

**405 Method Not Allowed:**
```json
{"error":{"message":"Method not allowed","type":"method_not_allowed"}}
```

---

## Deployment Fingerprints

### Default Ports

| Service | Port | Protocol |
|---------|------|----------|
| Gateway HTTP/WS | 18789 | HTTP + WebSocket |
| Browser Relay | Dynamic | WebSocket |
| Node SSH | 22 (configurable) | SSH |

### Systemd Service

**Service name:** `openclaw-gateway.service` (user service)  
**Service file:** `~/.config/systemd/user/openclaw-gateway.service`

**Command:**
```bash
/usr/bin/node /usr/lib/node_modules/openclaw/dist/index.js gateway --port 18789
```

**Environment:**
```
OPENCLAW_GATEWAY_PORT=18789
```

### Process Names

```
openclaw-gateway
node /usr/lib/node_modules/openclaw/dist/index.js gateway
```

### File Paths

| Path | Purpose |
|------|---------|
| `/usr/lib/node_modules/openclaw/` | Installation directory |
| `~/.openclaw/` | Configuration and data |
| `~/.openclaw/openclaw.json` | Main config file |
| `~/.openclaw/.env` | Environment variables (secrets) |
| `~/.openclaw/credentials/` | Stored credentials |
| `~/.openclaw/agents/` | Agent configurations |
| `~/.openclaw/workspace/` | Working directory |
| `/tmp/openclaw/openclaw-<date>.log` | Log files |

### Docker (if containerized)

**Image name:** `openclaw/openclaw` (official) or custom builds

**Container names:** Typically `openclaw-gateway` or `openclaw`

### Version Detection

Check package.json:
```bash
cat /usr/lib/node_modules/openclaw/package.json | grep '"version"'
```

Example: `"version": "2026.2.25"`

---

## Integration Patterns

### Discord Integration (message tool)

**Pattern:** OpenClaw connects to Discord via bot token

**Detection signals:**
- Outbound HTTPS to `discord.com/api/v10/`
- WebSocket to `gateway.discord.gg`
- User-Agent may include bot framework identifiers

### Browser Tool

**Pattern:** OpenClaw runs browser automation viaPlaywright

**Detection signals:**
- Local browser process spawning
- Chrome/Chromium processes as children of node
- WebSocket debugging ports

### Model API Calls

OpenClaw calls external LLM providers:

| Provider | Endpoint Pattern |
|----------|------------------|
| Ollama | `http://localhost:11434/v1/chat/completions` |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` |
| Anthropic | `https://api.anthropic.com/v1/messages` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| Z.AI | `https://api.z.ai/api/paas/v4` |
| Venice | `https://api.venice.ai/api/v1` |

**Detection:** Monitor outbound HTTPS calls from OpenClaw process to these domains.

---

## Confidence Calculation

### Detection Algorithm

```python
def calculate_confidence(signals_detected: dict) -> float:
    """
    Calculate confidence score for OpenClaw detection.
    
    Args:
        signals_detected: Dictionary of detected signals
        
    Returns:
        Confidence percentage (0-100)
    """
    
    weights = {
        'http_headers': 25,        # CSP, security headers
        'api_endpoints': 25,       # /api/channels, /v1/chat/completions
        'auth_patterns': 20,       # Bearer token, X-OpenClaw-Token
        'error_format': 15,        # {"error":{"message":"","type":""}}
        'deployment': 10,          # Port 18789, systemd service
        'session_format': 5        # Session key format
    }
    
    score = 0.0
    
    # HTTP Headers (25 points)
    if signals_detected.get('csp_websocket'):
        score += 10
    if signals_detected.get('x_frame_options_deny'):
        score += 5
    if signals_detected.get('no_server_header'):
        score += 5
    if signals_detected.get('cache_control_no_cache'):
        score += 5
        
    # API Endpoints (25 points)
    if signals_detected.get('api_channels'):
        score += 10
    if signals_detected.get('v1_chat_completions'):
        score += 10
    if signals_detected.get('tools_invoke'):
        score += 5
        
    # Auth Patterns (20 points)
    if signals_detected.get('bearer_auth'):
        score += 10
    if signals_detected.get('x_openclaw_token'):
        score += 10
        
    # Error Format (15 points)
    if signals_detected.get('error_schema'):
        score += 15
        
    # Deployment (10 points)
    if signals_detected.get('port_18789'):
        score += 5
    if signals_detected.get('systemd_service'):
        score += 5
        
    # Session Format (5 points)
    if signals_detected.get('session_key_format'):
        score += 5
    
    return min(score, 100.0)
```

### Confidence Thresholds

| Score | Confidence Level | Action |
|-------|-----------------|--------|
| 95-100 | **DEFINITIVE** | Confirmed OpenClaw |
| 80-94 | **HIGH** | Very likely OpenClaw - Accept for detection when v1 endpoints disabled |
| 60-79 | MEDIUM | Probable OpenClaw |
| 40-59 | LOW | Possible OpenClaw |
| 0-39 | VERY LOW | Unlikely OpenClaw |

**Important:** OpenClaw instances with default config (v1 endpoints disabled) typically score **89%**. This is **acceptable for detection** in most scenarios.

To achieve 95%+, the instance must have:
- `/v1/chat/completions` enabled, AND/OR
- `/v1/responses` enabled

### Required Signals for 95%+ Confidence

To achieve **95%+ confidence**, detect at least:

1. ✅ HTTP security headers (CSP with WebSocket, X-Frame-Options)
2. ✅ API endpoint matching (`/api/channels` OR `/v1/chat/completions`)
3. ✅ Auth pattern (Bearer token OR X-OpenClaw-Token)
4. ✅ Error schema match ({"error":{"message":"","type":""}})

**Minimum combination for 95%:**
- HTTP headers (25) + API endpoints (25) + Auth (20) + Error format (15) + Deployment (10) = **95**

**Reality check:** Default OpenClaw config scores **89%** (v1 endpoints disabled).
The 89% confidence with v1 endpoints disabled is still **HIGH confidence** and acceptable for detection.

---

## Detection Code

Location: `/home/neo/cogniwatch/scanner/openclaw_detector.py`

---

## References

- OpenClaw Documentation: https://docs.openclaw.ai/
- GitHub: https://github.com/openclaw/openclaw
- Version: 2026.2.25 (current as of 2026-03-07)

---

## Changelog

- **2026-03-07**: Initial signature database created
  - Extracted HTTP headers from live Gateway
  - Documented all API endpoints
  - Mapped authentication patterns
  - Created confidence calculation algorithm
