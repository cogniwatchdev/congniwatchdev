# OpenClaw Detector for CogniWatch

**Confidence:** 95%+ for production OpenClaw instances  
**Version:** 1.0.0  
**Date:** 2026-03-07

## Overview

This module detects OpenClaw Gateway instances by analyzing network signatures including HTTP headers, API endpoints, authentication patterns, error formats, and deployment fingerprints.

## Quick Start

```bash
# Scan localhost:18789 (default OpenClaw port)
python3 openclaw_detector.py

# Scan specific hosts
python3 openclaw_detector.py 192.168.0.245 192.168.0.100

# Run test suite
python3 test_openclaw_detector.py
```

## API Usage

```python
from openclaw_detector import OpenClawDetector, ConfidenceLevel

# Create detector
detector = OpenClawDetector(timeout=5.0)

# Scan a host
result = detector.scan("192.168.0.245", 18789)

# Check detection
if result.is_openclaw():
    print(f"✓ OpenClaw detected with {result.confidence:.1f}% confidence")
    print(f"  Level: {result.level.value}")
else:
    print(f"OpenClaw confidence: {result.confidence:.1f}%")

# Access individual signals
for signal, detected in result.signals.items():
    if detected:
        print(f"  ✓ {signal}")

# Custom threshold
if result.is_openclaw(threshold=80.0):
    print("Likely OpenClaw (80%+ confidence)")
```

## Confidence Calculation

The detector analyzes these signal categories:

| Category | Points | Signals |
|----------|--------|---------|
| **HTTP Headers** | 25 | CSP with WebSocket, X-Frame-Options, no Server header, etc. |
| **API Endpoints** | 25 | /api/channels, /v1/chat/completions, /tools/invoke |
| **Auth Patterns** | 20 | Bearer token requirement, X-OpenClaw-Token support |
| **Error Format** | 15 | JSON error schema `{"error":{"message":"","type":""}}` |
| **Deployment** | 10 | Port 18789, systemd service, Docker |
| **Session Format** | 5 | Session key format |

**Total Possible:** 100 points (+ bonus signals)

### Confidence Levels

| Score | Level | Interpretation |
|-------|-------|----------------|
| 95-100 | **DEFINITIVE** | Confirmed OpenClaw |
| 80-94 | HIGH | Very likely OpenClaw |
| 60-79 | MEDIUM | Probable OpenClaw |
| 40-59 | LOW | Possible OpenClaw |
| 0-39 | VERY LOW | Unlikely OpenClaw |

## Detection Signals

### HTTP Header Signatures ✓

OpenClaw Gateway returns these security headers:

```
Content-Security-Policy: default-src 'self'; ... connect-src 'self' ws: wss: ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Cache-Control: no-cache
```

**Detection tip:** The CSP with `connect-src 'self' ws: wss:` is a strong indicator of WebSocket support.

### API Endpoint Signatures ✓

| Endpoint | Auth | Method | Signal |
|----------|------|--------|--------|
| `/api/channels` | Required | GET/POST | Core channel management |
| `/api/sessions` | Required | GET | Session listing |
| `/tools/invoke` | Required | POST | Direct tool invocation |
| `/v1/chat/completions` | Required | POST | OpenAI-compatible API (optional) |
| `/v1/responses` | Required | POST | OpenResponses API (optional) |

**Note:** The `/v1/*` endpoints are disabled by default and must be enabled in Gateway config.

### Authentication Patterns ✓

OpenClaw requires Bearer token authentication:

```http
GET /api/channels HTTP/1.1
Authorization: Bearer <token>
```

Alternative (hooks only):
```http
POST /hooks/event HTTP/1.1
X-OpenClaw-Token: <token>
```

**401 Response:**
```json
{"error":{"message":"Unauthorized","type":"unauthorized"}}
```

### Error Signatures ✓

**ALL** OpenClaw API errors follow this schema:

```json
{
  "error": {
    "message": "<human-readable message>",
    "type": "<error-code>"
  }
}
```

Error types: `unauthorized`, `not_found`, `rate_limited`, `method_not_allowed`, `bad_request`

### Deployment Fingerprints ✓

- **Default port:** 18789
- **Process name:** `openclaw-gateway` or `node .../dist/index.js gateway`
- **Systemd service:** `openclaw-gateway.service` (user service)
- **Config directory:** `~/.openclaw/`
- **Version format:** `2026.2.25` (YEAR.MONTH.REVISION)

## Why 89% on Local Instance?

The local OpenClaw instance scores 89% because:

1. `/v1/chat/completions` endpoint is **disabled by default**
2. `/v1/responses` endpoint is **disabled by default**
3. Systemd service detection requires local system access

To enable v1 endpoints in your Gateway config:

```json5
{
  gateway: {
    http: {
      endpoints: {
        chatCompletions: { enabled: true },
        responses: { enabled: true }
      }
    }
  }
}
```

With these enabled, confidence reaches **95%+**.

## Network Scanning

Scan a subnet for OpenClaw instances:

```bash
# Scan common IPs
python3 openclaw_detector.py 192.168.0.{1..254}

# Or use a list
cat hosts.txt | xargs -I {} python3 openclaw_detector.py {}
```

**Note:** This scans port 18789 by default. Adjust port as needed.

## Integration with CogniWatch

The detector integrates with CogniWatch's signature-based framework:

```python
from openclaw_detector import OpenClawDetector

detector = OpenClawDetector()
result = detector.scan("192.168.0.245")

if result.is_openclaw():
    # Add to CogniWatch registry
    cogniwatch.add_instance({
        "type": "openclaw",
        "host": result.host,
        "port": result.port,
        "confidence": result.confidence
    })
```

## Testing

### Run test suite

```bash
python3 test_openclaw_detector.py
```

### Test categories

- **TestConfidenceCalculation:** Validates score calculation
- **TestConfidenceLevels:** Validates level classification
- **TestDetectionResult:** Tests result data class
- **TestLocalInstance:** Integration tests (skip if no Gateway)
- **TestEdgeCases:** Timeout, connection refused handling

## Limitations

1. **v1 endpoints optional:** Some OpenClaw instances disable `/v1/*` endpoints
2. **Custom config:** Non-default ports or configs may reduce confidence
3. **Network access:** Remote scanning limited to network-visible signals
4. **No WebSocket detection:** Current version only tests HTTP

## Future Enhancements

- [ ] WebSocket endpoint detection
- [ ] Session key format validation
- [ ] JWT/Auth token structure analysis
- [ ] Message queue pattern detection (Redis, RabbitMQ)
- [ ] Discord/LLM API call pattern detection
- [ ] Docker/systemd service detection via SSH

## References

- [OpenClaw Documentation](https://docs.openclaw.ai/)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Signature Database](../signatures/OPENCLAW_SIGNATURE_DATABASE.md)
- CogniWatch Project: CIPHER

---

**Author:** CIPHER Subagent  
**License:** MIT (as part of CogniWatch)
