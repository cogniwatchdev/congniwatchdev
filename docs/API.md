# 🛠️ CogniWatch API Reference

**Version:** 1.0.0  
**Base URL:** `http://localhost:9000/api`  
**Last Updated:** March 8, 2026

Complete API documentation for integrating with CogniWatch. All endpoints require authentication unless noted.

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Health & Status](#health--status)
   - [Authentication](#authentication-endpoints)
   - [Agents](#agents)
   - [Scans](#scans)
   - [Telemetry](#telemetry)
   - [Alerts](#alerts)
   - [API Keys](#api-keys)
   - [Configuration](#configuration)
5. [WebSocket API](#websocket-api)
6. [Code Examples](#code-examples)
7. [SDKs & Libraries](#sdks--libraries)

---

## 🔐 Authentication

CogniWatch supports two authentication methods:

### Method 1: JWT Tokens (Recommended)

**Step 1: Obtain JWT Token**

```bash
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcxMDAwMDAwMH0.abc123",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": "2026-03-08T15:24:00Z",
  "scope": "admin:all"
}
```

**Step 2: Use Token in Requests**

```bash
curl http://localhost:9000/api/agents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Token Expiry:**
- Default: 1 hour (3600 seconds)
- Configurable: 15 minutes to 24 hours
- Refresh: Re-authenticate to get new token

### Method 2: API Keys (For Automation)

**Create API Key:**

```bash
curl -X POST http://localhost:9000/api/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Scanner",
    "scopes": ["read:agents", "write:scans"],
    "expires_in_days": 90
  }'
```

**Response:**
```json
{
  "api_key": "cw_live_xK9mP2nQ4rS6tU8vW0xY",
  "key_id": "key_7a8b9c0d",
  "name": "Production Scanner",
  "scopes": ["read:agents", "write:scans"],
  "created_at": "2026-03-08T14:24:00Z",
  "expires_at": "2026-06-06T14:24:00Z"
}
```

**⚠️ Important:** API key is shown only once! Store it securely.

**Use API Key:**

```bash
curl http://localhost:9000/api/agents \
  -H "X-API-Key: cw_live_xK9mP2nQ4rS6tU8vW0xY"
```

**API Key Scopes:**

| Scope | Permission | Endpoints |
|-------|------------|-----------|
| `read:agents` | List and view agents | GET /agents, GET /agents/:id |
| `write:scans` | Trigger and manage scans | POST /scan, GET /scan/status |
| `read:telemetry` | Access telemetry data | GET /telemetry/:id |
| `read:alerts` | View security alerts | GET /alerts |
| `write:alerts` | Acknowledge/resolved alerts | POST /alerts/:id/acknowledge |
| `read:config` | View configuration | GET /config |
| `write:config` | Modify configuration | PUT /config |
| `admin:api-keys` | Manage API keys | All /api-keys endpoints |
| `admin:all` | Full administrative access | All endpoints |

---

## 📏 Rate Limiting

**Default Limits:**

| Tier | Requests/Minute | Requests/Day | Concurrent |
|------|-----------------|--------------|------------|
| **Standard** | 60 | 1,000 | 10 |
| **Premium** | 300 | 10,000 | 50 |
| **Enterprise** | 1,000 | 100,000 | 200 |

**Rate Limit Headers:**

All API responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1709740800
X-RateLimit-Policy: 60;w=60;1000;w=86400
```

**429 Too Many Requests Response:**

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 30 seconds.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 30,
  "limit": 60,
  "remaining": 0,
  "reset_at": "2026-03-08T14:25:00Z"
}
```

**Best Practices:**
- ✅ Implement exponential backoff on 429 responses
- ✅ Cache responses when possible
- ✅ Use WebSocket for real-time updates instead of polling
- ❌ Don't retry immediately without waiting

---

## ❌ Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "invalid_request",
  "message": "Network parameter is required",
  "code": "MISSING_PARAMETER",
  "details": {
    "parameter": "network",
    "expected": "CIDR notation",
    "example": "192.168.1.0/24"
  },
  "request_id": "req_abc123def456",
  "documentation": "https://docs.cogniwatch.dev/api/errors#MISSING_PARAMETER"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created (POST) |
| `204` | No Content | Request succeeded, no body (DELETE) |
| `400` | Bad Request | Invalid JSON, missing parameters, validation failed |
| `401` | Unauthorized | Missing or expired authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Resource already exists, scan already running |
| `422` | Unprocessable Entity | Valid syntax, semantic errors |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Maintenance, overloaded |

### Error Codes

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `AUTH_REQUIRED` | 401 | Authentication required | Include Authorization header or X-API-Key |
| `AUTH_INVALID` | 401 | Invalid credentials | Check username/password or API key |
| `AUTH_EXPIRED` | 401 | Token has expired | Re-authenticate to get new token |
| `FORBIDDEN` | 403 | Insufficient permissions | Request required scope from admin |
| `NOT_FOUND` | 404 | Resource not found | Check ID, resource may have been deleted |
| `ALREADY_EXISTS` | 409 | Resource already exists | Use different name/ID or update existing |
| `SCAN_IN_PROGRESS` | 409 | Scan already running | Wait for current scan to complete |
| `INVALID_NETWORK` | 400 | Invalid CIDR notation | Use format like "192.168.1.0/24" |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait and retry after timeout |
| `INTERNAL_ERROR` | 500 | Server error | Check server logs, report if persistent |

---

## 📡 Endpoints

### Health & Status

#### GET /api/health

Health check endpoint (no authentication required).

**Request:**
```bash
curl http://localhost:9000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "build": "20260308-142400",
  "uptime": 12345,
  "uptime_human": "3h 25m 45s",
  "services": {
    "database": {
      "status": "ok",
      "latency_ms": 2
    },
    "scanner": {
      "status": "ok",
      "last_scan": "2026-03-08T14:00:00Z",
      "next_scan": "2026-03-08T15:00:00Z"
    },
    "webui": {
      "status": "ok"
    }
  },
  "metrics": {
    "agents_discovered": 7,
    "scans_completed": 42,
    "alerts_active": 3
  },
  "timestamp": "2026-03-08T14:24:00Z"
}
```

**Use Cases:**
- Load balancer health checks
- Monitoring system integration
- Pre-flight checks before API calls

---

#### GET /api/version

Get version and build information.

**Request:**
```bash
curl http://localhost:9000/api/version
```

**Response:**
```json
{
  "version": "1.0.0",
  "build": "20260308-142400",
  "commit": "abc123def456",
  "branch": "main",
  "build_date": "2026-03-08T14:24:00Z",
  "python_version": "3.12.0",
  "api_version": "v1"
}
```

---

### Authentication Endpoints

#### POST /api/auth/login

Authenticate and receive JWT token.

**Request:**
```bash
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": "2026-03-08T15:24:00Z",
  "scope": "admin:all",
  "user": {
    "username": "admin",
    "role": "admin",
    "last_login": "2026-03-08T13:00:00Z"
  }
}
```

**Error Responses:**

```json
// 401 Unauthorized
{
  "error": "authentication_failed",
  "message": "Invalid username or password",
  "code": "AUTH_INVALID"
}
```

---

#### POST /api/auth/logout

Invalidate current token (logout).

**Request:**
```bash
curl -X POST http://localhost:9000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "token_invalidated": true
}
```

---

#### GET /api/auth/me

Get current user information.

**Request:**
```bash
curl http://localhost:9000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "user": {
    "username": "admin",
    "role": "admin",
    "scopes": ["admin:all"],
    "created_at": "2026-03-01T00:00:00Z",
    "last_login": "2026-03-08T13:00:00Z"
  }
}
```

---

### Agents

#### GET /api/agents

List all discovered agents.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by status: `active`, `offline`, `unknown` |
| `framework` | string | — | Filter by framework: `OpenClaw`, `CrewAI`, etc. |
| `confidence` | string | — | Min confidence: `low`, `medium`, `high`, `critical` |
| `limit` | integer | 50 | Number of results (max: 100) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | `last_seen` | Sort field: `detected_at`, `last_seen`, `confidence`, `ip` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Request:**
```bash
curl "http://localhost:9000/api/agents?status=active&confidence=high&limit=20&sort=confidence&order=desc" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "agents": [
    {
      "id": "ag_7k2m9n4p",
      "ip": "192.168.1.100",
      "port": 8080,
      "framework": "OpenClaw",
      "framework_version": "1.0.0",
      "confidence": 0.94,
      "confidence_level": "HIGH",
      "detected_at": "2026-03-07T00:25:00Z",
      "last_seen": "2026-03-08T14:20:00Z",
      "status": "active",
      "location": {
        "network": "192.168.1.0/24",
        "hostname": "gateway.local",
        "mac_address": "00:1A:2B:3C:4D:5E"
      },
      "endpoints": [
        {
          "path": "/api/v1/gateway/status",
          "method": "GET",
          "protocol": "http",
          "status": "active"
        },
        {
          "path": "/ws/agent",
          "method": "WS",
          "protocol": "websocket",
          "status": "active"
        }
      ],
      "telemetry": {
        "connections_24h": 1247,
        "api_calls_24h": 8934,
        "avg_response_time_ms": 145
      },
      "tags": ["production", "gateway"]
    },
    {
      "id": "ag_5x6y7z8w",
      "ip": "10.0.0.45",
      "port": 5000,
      "framework": "CrewAI",
      "framework_version": "0.85.0",
      "confidence": 0.67,
      "confidence_level": "MEDIUM",
      "detected_at": "2026-03-06T12:00:00Z",
      "last_seen": "2026-03-08T14:15:00Z",
      "status": "active",
      "location": {
        "network": "10.0.0.0/8",
        "hostname": null,
        "mac_address": null
      },
      "endpoints": [
        {
          "path": "/v1/chat/completions",
          "method": "POST",
          "protocol": "http",
          "status": "active"
        }
      ],
      "telemetry": {
        "connections_24h": 523,
        "api_calls_24h": 2341,
        "avg_response_time_ms": 230
      },
      "tags": ["development"]
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

---

#### GET /api/agents/:id

Get details for a specific agent.

**Request:**
```bash
curl http://localhost:9000/api/agents/ag_7k2m9n4p \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "agent": {
    "id": "ag_7k2m9n4p",
    "ip": "192.168.1.100",
    "port": 8080,
    "framework": "OpenClaw",
    "framework_version": "1.0.0",
    "confidence": 0.94,
    "confidence_level": "HIGH",
    "detection_details": {
      "layers": {
        "port_match": {
          "detected": true,
          "port": 8080,
          "confidence_contribution": 0.30
        },
        "http_headers": {
          "detected": true,
          "patterns_matched": [
            "X-OpenClaw-Version: 1.0",
            "X-Agent-Framework: OpenClaw"
          ],
          "confidence_contribution": 0.15
        },
        "api_endpoints": {
          "detected": true,
          "paths_found": [
            "/api/v1/gateway/status",
            "/api/v1/agents"
          ],
          "confidence_contribution": 0.25
        },
        "websocket": {
          "detected": true,
          "endpoint": "/ws/agent",
          "handshake_valid": true,
          "confidence_contribution": 0.15
        },
        "behavioral": {
          "detected": true,
          "patterns": [
            "periodic_heartbeat",
            "batch_api_calls"
          ],
          "confidence_contribution": 0.09
        }
      },
      "total_score": 0.94,
      "threshold_met": "HIGH"
    },
    "detected_at": "2026-03-07T00:25:00Z",
    "last_seen": "2026-03-08T14:20:00Z",
    "status": "active",
    "location": {
      "network": "192.168.1.0/24",
      "hostname": "gateway.local",
      "mac_address": "00:1A:2B:3C:4D:5E",
      "geo": {
        "country": "US",
        "city": "San Francisco",
        "timezone": "America/Los_Angeles"
      }
    },
    "endpoints": [
      {
        "path": "/api/v1/gateway/status",
        "method": "GET",
        "protocol": "http",
        "last_checked": "2026-03-08T14:20:00Z",
        "status_code": 200,
        "response_time_ms": 45
      },
      {
        "path": "/ws/agent",
        "method": "WS",
        "protocol": "websocket",
        "last_checked": "2026-03-08T14:20:00Z",
        "status": "connected"
      }
    ],
    "telemetry": {
      "connections_24h": 1247,
      "api_calls_24h": 8934,
      "websocket_messages_24h": 3421,
      "avg_response_time_ms": 145,
      "error_rate": 0.02,
      "uptime_percentage": 99.8
    },
    "tags": ["production", "gateway"],
    "metadata": {
      "os": "Linux 5.15.0",
      "container": true,
      "container_id": "abc123def456",
      "docker_image": "openclaw/gateway:1.0"
    },
    "notes": "Primary production gateway"
  }
}
```

---

#### PUT /api/agents/:id/tags

Update tags for an agent.

**Request:**
```bash
curl -X PUT http://localhost:9000/api/agents/ag_7k2m9n4p/tags \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["production", "gateway", "critical"]
  }'
```

**Response:**
```json
{
  "agent_id": "ag_7k2m9n4p",
  "tags": ["production", "gateway", "critical"],
  "updated_at": "2026-03-08T14:24:00Z"
}
```

---

#### PUT /api/agents/:id/notes

Add or update notes for an agent.

**Request:**
```bash
curl -X PUT http://localhost:9000/api/agents/ag_7k2m9n4p/notes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Primary production gateway. Contact: ops@example.com"
  }'
```

**Response:**
```json
{
  "agent_id": "ag_7k2m9n4p",
  "notes": "Primary production gateway. Contact: ops@example.com",
  "updated_at": "2026-03-08T14:24:00Z"
}
```

---

#### DELETE /api/agents/:id

Remove an agent from the database.

**Request:**
```bash
curl -X DELETE http://localhost:9000/api/agents/ag_7k2m9n4p \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "Agent deleted successfully",
  "agent_id": "ag_7k2m9n4p",
  "deleted_at": "2026-03-08T14:24:00Z"
}
```

---

### Scans

#### POST /api/scan

Trigger a new network scan.

**Request Body:**

```json
{
  "network": "192.168.1.0/24",
  "ports": [80, 443, 5000, 8080, 8081, 18789],
  "scan_type": "full",
  "timeout_seconds": 300,
  "frameworks": ["OpenClaw", "CrewAI", "AutoGen"],
  "options": {
    "detect_tls": true,
    "detect_websocket": true,
    "grab_banners": true,
    "rate_limit": 100
  }
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `network` | string | Yes | — | CIDR notation or IP range |
| `ports` | array | No | [80, 443, 5000, 8080, 18789] | Custom port list |
| `scan_type` | string | No | `full` | `quick` (common ports) or `full` |
| `timeout_seconds` | integer | No | 300 | Maximum scan duration |
| `frameworks` | array | No | all | Specific frameworks to detect |
| `options.detect_tls` | boolean | No | true | Enable TLS/JA3 fingerprinting |
| `options.detect_websocket` | boolean | No | true | Enable WebSocket detection |
| `options.grab_banners` | boolean | No | true | Grab service banners |
| `options.rate_limit` | integer | No | 100 | Packets per second |

**Request:**
```bash
curl -X POST http://localhost:9000/api/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "network": "10.0.0.0/8",
    "scan_type": "full",
    "timeout_seconds": 600
  }'
```

**Response:**
```json
{
  "scan_id": "scan_9x8y7z6w",
  "status": "queued",
  "created_at": "2026-03-08T14:24:00Z",
  "estimated_duration_seconds": 300,
  "estimated_completion": "2026-03-08T14:29:00Z",
  "network": "10.0.0.0/8",
  "scan_type": "full",
  "ports_to_scan": 5,
  "hosts_to_scan": 16777216,
  "priority": "normal"
}
```

---

#### GET /api/scan/status

Get status of current or recent scans.

**Request:**
```bash
curl http://localhost:9000/api/scan/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "current_scan": {
    "scan_id": "scan_9x8y7z6w",
    "status": "running",
    "progress": 45,
    "started_at": "2026-03-08T14:24:00Z",
    "estimated_completion": "2026-03-08T14:29:00Z",
    "network": "10.0.0.0/8",
    "scan_type": "full",
    "stats": {
      "hosts_scanned": 7549747,
      "hosts_total": 16777216,
      "agents_found": 3,
      "ports_scanned": 11250,
      "ports_total": 25000
    }
  },
  "recent_scans": [
    {
      "scan_id": "scan_5a4b3c2d",
      "status": "completed",
      "started_at": "2026-03-08T13:20:00Z",
      "completed_at": "2026-03-08T13:25:00Z",
      "duration_seconds": 287,
      "agents_found": 7,
      "network": "192.168.1.0/24",
      "scan_type": "quick"
    },
    {
      "scan_id": "scan_1a2b3c4d",
      "status": "completed",
      "started_at": "2026-03-08T12:00:00Z",
      "completed_at": "2026-03-08T12:08:00Z",
      "duration_seconds": 456,
      "agents_found": 5,
      "network": "172.16.0.0/12",
      "scan_type": "full"
    }
  ],
  "next_scheduled_scan": "2026-03-08T15:00:00Z"
}
```

---

#### DELETE /api/scan/:id

Cancel a running or queued scan.

**Request:**
```bash
curl -X DELETE http://localhost:9000/api/scan/scan_9x8y7z6w \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "Scan cancelled successfully",
  "scan_id": "scan_9x8y7z6w",
  "status": "cancelled",
  "cancelled_at": "2026-03-08T14:24:00Z",
  "progress_at_cancel": 45
}
```

---

### Telemetry

#### GET /api/telemetry/:agent_id

Get telemetry data for a specific agent.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | string | `24h` | Time range: `1h`, `24h`, `7d`, `30d` |
| `metrics` | string | all | Comma-separated: `connections`, `api_calls`, `websocket`, `errors` |
| `resolution` | string | auto | Data resolution: `1m`, `5m`, `1h`, `1d`, `auto` |

**Request:**
```bash
curl "http://localhost:9000/api/telemetry/ag_7k2m9n4p?range=24h&metrics=connections,api_calls&resolution=1h" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "agent_id": "ag_7k2m9n4p",
  "range": "24h",
  "resolution": "1h",
  "metrics": {
    "connections": {
      "data": [
        {"timestamp": "2026-03-08T00:00:00Z", "value": 45},
        {"timestamp": "2026-03-08T01:00:00Z", "value": 52},
        {"timestamp": "2026-03-08T02:00:00Z", "value": 38},
        {"timestamp": "2026-03-08T03:00:00Z", "value": 41}
      ],
      "total": 1247,
      "avg_per_hour": 52,
      "peak": 89,
      "peak_time": "2026-03-08T14:00:00Z",
      "min": 12,
      "min_time": "2026-03-08T04:00:00Z"
    },
    "api_calls": {
      "data": [
        {"timestamp": "2026-03-08T00:00:00Z", "value": 342},
        {"timestamp": "2026-03-08T01:00:00Z", "value": 398},
        {"timestamp": "2026-03-08T02:00:00Z", "value": 287},
        {"timestamp": "2026-03-08T03:00:00Z", "value": 315}
      ],
      "total": 8934,
      "avg_per_hour": 372,
      "peak": 521,
      "peak_time": "2026-03-08T15:00:00Z",
      "min": 98,
      "min_time": "2026-03-08T05:00:00Z"
    }
  },
  "summary": {
    "total_connections": 1247,
    "total_api_calls": 8934,
    "total_websocket_messages": 3421,
    "avg_response_time_ms": 145,
    "error_rate": 0.02,
    "uptime_percentage": 99.8,
    "period_start": "2026-03-07T14:24:00Z",
    "period_end": "2026-03-08T14:24:00Z"
  }
}
```

---

#### GET /api/telemetry/aggregate

Get aggregated telemetry across all agents.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | string | `24h` | Time range |
| `group_by` | string | `agent` | Group by: `agent`, `framework`, `network` |

**Request:**
```bash
curl "http://localhost:9000/api/telemetry/aggregate?range=7d&group_by=framework" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "range": "7d",
  "group_by": "framework",
  "data": {
    "OpenClaw": {
      "agent_count": 3,
      "total_connections": 8934,
      "total_api_calls": 45678,
      "avg_response_time_ms": 145,
      "error_rate": 0.02
    },
    "CrewAI": {
      "agent_count": 2,
      "total_connections": 3421,
      "total_api_calls": 12345,
      "avg_response_time_ms": 230,
      "error_rate": 0.05
    },
    "AutoGen": {
      "agent_count": 1,
      "total_connections": 1234,
      "total_api_calls": 5678,
      "avg_response_time_ms": 180,
      "error_rate": 0.03
    }
  }
}
```

---

### Alerts

#### GET /api/alerts

List security alerts.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | — | Filter: `low`, `medium`, `high`, `critical` |
| `status` | string | — | Filter: `new`, `acknowledged`, `resolved` |
| `agent_id` | string | — | Filter by specific agent |
| `type` | string | — | Filter by alert type |
| `limit` | integer | 50 | Number of results |
| `offset` | integer | 0 | Pagination offset |

**Request:**
```bash
curl "http://localhost:9000/api/alerts?severity=high&status=new&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert_abc123",
      "type": "new_agent_detected",
      "severity": "high",
      "status": "new",
      "agent_id": "ag_7k2m9n4p",
      "agent_ip": "192.168.1.100",
      "title": "New High-Confidence Agent Detected",
      "description": "OpenClaw gateway detected with 94% confidence on 192.168.1.100:8080",
      "created_at": "2026-03-08T14:20:00Z",
      "metadata": {
        "framework": "OpenClaw",
        "confidence": 0.94,
        "detection_method": "multi_layer"
      }
    },
    {
      "id": "alert_def456",
      "type": "unusual_activity",
      "severity": "medium",
      "status": "acknowledged",
      "agent_id": "ag_5x6y7z8w",
      "agent_ip": "10.0.0.45",
      "title": "Unusual API Call Pattern",
      "description": "Agent making 10x more API calls than baseline",
      "created_at": "2026-03-08T13:15:00Z",
      "acknowledged_at": "2026-03-08T14:10:00Z",
      "acknowledged_by": "admin",
      "metadata": {
        "baseline_avg": 100,
        "current_rate": 1050,
        "deviation_percentage": 950
      }
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

---

#### POST /api/alerts/:id/acknowledge

Acknowledge an alert.

**Request:**
```bash
curl -X POST http://localhost:9000/api/alerts/alert_abc123/acknowledge \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "note": "Investigated, confirmed legitimate agent"
  }'
```

**Response:**
```json
{
  "alert": {
    "id": "alert_abc123",
    "status": "acknowledged",
    "acknowledged_at": "2026-03-08T14:24:00Z",
    "acknowledged_by": "admin",
    "note": "Investigated, confirmed legitimate agent"
  }
}
```

---

#### POST /api/alerts/:id/resolve

Mark an alert as resolved.

**Request:**
```bash
curl -X POST http://localhost:9000/api/alerts/alert_abc123/resolve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "Agent verified as authorized deployment",
    "action_taken": "Added to production inventory"
  }'
```

**Response:**
```json
{
  "alert": {
    "id": "alert_abc123",
    "status": "resolved",
    "resolved_at": "2026-03-08T14:24:00Z",
    "resolved_by": "admin",
    "resolution": "Agent verified as authorized deployment",
    "action_taken": "Added to production inventory"
  }
}
```

---

#### GET /api/alerts/stats

Get alert statistics.

**Request:**
```bash
curl http://localhost:9000/api/alerts/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_alerts": 47,
  "by_status": {
    "new": 3,
    "acknowledged": 12,
    "resolved": 32
  },
  "by_severity": {
    "critical": 2,
    "high": 8,
    "medium": 15,
    "low": 22
  },
  "by_type": {
    "new_agent_detected": 23,
    "unusual_activity": 12,
    "agent_offline": 7,
    "security_anomaly": 5
  },
  "last_24h": {
    "created": 8,
    "acknowledged": 5,
    "resolved": 6
  },
  "avg_resolution_time_hours": 4.2,
  "oldest_unacknowledged": "2026-03-08T12:00:00Z"
}
```

---

### API Keys

#### GET /api/api-keys

List all API keys.

**Required Scope:** `admin:api-keys`

**Request:**
```bash
curl http://localhost:9000/api/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "api_keys": [
    {
      "key_id": "key_7a8b9c0d",
      "name": "Production Scanner",
      "scopes": ["read:agents", "write:scans"],
      "created_at": "2026-03-01T00:00:00Z",
      "expires_at": "2026-06-06T14:24:00Z",
      "last_used": "2026-03-08T14:20:00Z",
      "usage_count": 1247,
      "status": "active"
    },
    {
      "key_id": "key_1x2y3z4w",
      "name": "Monitoring Integration",
      "scopes": ["read:agents", "read:telemetry", "read:alerts"],
      "created_at": "2026-02-15T10:00:00Z",
      "expires_at": "2026-05-15T10:00:00Z",
      "last_used": "2026-03-08T14:22:00Z",
      "usage_count": 8934,
      "status": "active"
    }
  ],
  "total": 2
}
```

---

#### POST /api/api-keys

Create a new API key.

**Required Scope:** `admin:api-keys`

**Request:**
```bash
curl -X POST http://localhost:9000/api/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "scopes": ["read:agents", "write:scans"],
    "expires_in_days": 365,
    "description": "Used by GitHub Actions for automated scanning"
  }'
```

**Response:**
```json
{
  "api_key": "cw_live_xK9mP2nQ4rS6tU8vW0xY",
  "key_id": "key_9z8y7x6w",
  "name": "CI/CD Pipeline",
  "scopes": ["read:agents", "write:scans"],
  "created_at": "2026-03-08T14:24:00Z",
  "expires_at": "2027-03-08T14:24:00Z",
  "description": "Used by GitHub Actions for automated scanning"
}
```

**⚠️ Important:** API key is shown only once!

---

#### DELETE /api/api-keys/:id

Revoke an API key.

**Required Scope:** `admin:api-keys`

**Request:**
```bash
curl -X DELETE http://localhost:9000/api/api-keys/key_7a8b9c0d \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "API key revoked successfully",
  "key_id": "key_7a8b9c0d",
  "revoked_at": "2026-03-08T14:24:00Z"
}
```

---

### Configuration

#### GET /api/config

Get current configuration.

**Required Scope:** `read:config`

**Request:**
```bash
curl http://localhost:9000/api/config \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "config": {
    "scanner": {
      "enabled": true,
      "network": "192.168.1.0/24",
      "scan_interval_hours": 24,
      "rate_limit": 100,
      "timeout_seconds": 300
    },
    "webui": {
      "host": "0.0.0.0",
      "port": 9000,
      "debug": false,
      "theme": "dark"
    },
    "security": {
      "auth_required": true,
      "token_expiry_hours": 24,
      "rate_limiting": {
        "enabled": true,
        "requests_per_minute": 60
      }
    },
    "telemetry": {
      "enabled": true,
      "retention_days": 90,
      "collection_interval_seconds": 60
    },
    "alerts": {
      "enabled": true,
      "email_notifications": false,
      "slack_webhook": null
    }
  },
  "last_updated": "2026-03-08T14:24:00Z"
}
```

---

#### PUT /api/config

Update configuration.

**Required Scope:** `write:config`

**Request:**
```bash
curl -X PUT http://localhost:9000/api/config \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scanner": {
      "network": "10.0.0.0/8",
      "scan_interval_hours": 12
    }
  }'
```

**Response:**
```json
{
  "message": "Configuration updated successfully",
  "updated_at": "2026-03-08T14:24:00Z",
  "changes": {
    "scanner.network": {
      "old": "192.168.1.0/24",
      "new": "10.0.0.0/8"
    },
    "scanner.scan_interval_hours": {
      "old": 24,
      "new": 12
    }
  }
}
```

---

## 🔮 WebSocket API

Real-time updates via WebSocket connection.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:9000/ws/updates');

ws.onopen = () => {
  console.log('Connected to CogniWatch');
  
  // Authenticate (if required)
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_JWT_TOKEN'
  }));
  
  // Subscribe to event types
  ws.send(JSON.stringify({
    type: 'subscribe',
    events: [
      'agent_detected',
      'scan_completed',
      'alert_created',
      'telemetry_update'
    ]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event received:', data.type, data.payload);
  
  // Handle different event types
  switch (data.type) {
    case 'agent_detected':
      console.log('New agent found:', data.payload.agent);
      break;
    case 'scan_completed':
      console.log('Scan finished:', data.payload.stats);
      break;
    case 'alert_created':
      console.log('New alert:', data.payload.alert);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed, reconnecting...');
  setTimeout(() => connect(), 5000);
};
```

### Event Types

| Event | Payload | Description |
|-------|---------|-------------|
| `agent_detected` | `{agent: Agent}` | New agent discovered |
| `agent_offline` | `{agent_id: string, last_seen: timestamp}` | Agent went offline |
| `scan_started` | `{scan_id: string, network: string}` | Scan initiated |
| `scan_progress` | `{scan_id: string, progress: number, stats: object}` | Scan progress update |
| `scan_completed` | `{scan_id: string, agents_found: number, duration: number}` | Scan finished |
| `alert_created` | `{alert: Alert}` | New security alert |
| `telemetry_update` | `{agent_id: string, metrics: object}` | Telemetry data update |

---

## 💻 Code Examples

### Python

```python
import requests
import time

API_KEY = "cw_live_xxxxx"
BASE_URL = "http://localhost:9000/api"

headers = {"X-API-Key": API_KEY}

def list_agents(status=None, framework=None):
    """List all discovered agents with optional filters."""
    params = {}
    if status:
        params['status'] = status
    if framework:
        params['framework'] = framework
    
    response = requests.get(f"{BASE_URL}/agents", headers=headers, params=params)
    response.raise_for_status()
    return response.json()["agents"]

def trigger_scan(network, scan_type="full"):
    """Trigger a new network scan."""
    response = requests.post(
        f"{BASE_URL}/scan",
        headers=headers,
        json={"network": network, "scan_type": scan_type}
    )
    response.raise_for_status()
    return response.json()

def wait_for_scan_completion(scan_id, poll_interval=5):
    """Wait for a scan to complete by polling status."""
    while True:
        response = requests.get(f"{BASE_URL}/scan/status", headers=headers)
        response.raise_for_status()
        status = response.json()
        
        current_scan = status.get("current_scan")
        if not current_scan or current_scan["scan_id"] != scan_id:
            print("Scan not found or already completed")
            break
        
        if current_scan["status"] == "completed":
            print(f"Scan completed! Found {current_scan['stats']['agents_found']} agents")
            break
        elif current_scan["status"] == "failed":
            print("Scan failed")
            break
        
        progress = current_scan.get("progress", 0)
        print(f"Scan progress: {progress}%")
        time.sleep(poll_interval)

def get_telemetry(agent_id, range="24h"):
    """Get telemetry data for an agent."""
    response = requests.get(
        f"{BASE_URL}/telemetry/{agent_id}",
        headers=headers,
        params={"range": range}
    )
    response.raise_for_status()
    return response.json()

# Usage example
if __name__ == "__main__":
    # List all active agents
    agents = list_agents(status="active")
    print(f"Found {len(agents)} active agents")
    
    # Trigger a scan
    scan_response = trigger_scan("192.168.1.0/24")
    scan_id = scan_response["scan_id"]
    print(f"Scan started: {scan_id}")
    
    # Wait for completion
    wait_for_scan_completion(scan_id)
    
    # Get updated agent list
    agents = list_agents()
    for agent in agents:
        print(f"  - {agent['framework']} at {agent['ip']}:{agent['port']} ({agent['confidence_level']})")
    
    # Get telemetry for first agent
    if agents:
        telemetry = get_telemetry(agents[0]["id"])
        print(f"\nAgent {agents[0]['id']} telemetry (24h):")
        print(f"  Connections: {telemetry['summary']['total_connections']}")
        print(f"  API calls: {telemetry['summary']['total_api_calls']}")
```

### JavaScript/Node.js

```javascript
const API_KEY = 'cw_live_xxxxx';
const BASE_URL = 'http://localhost:9000/api';

async function listAgents(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/agents?${params}`, {
    headers: {
      'X-API-Key': API_KEY
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const data = await response.json();
  return data.agents;
}

async function triggerScan(network, options = {}) {
  const response = await fetch(`${BASE_URL}/scan`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      network,
      ...options
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

async function getTelemetry(agentId, range = '24h') {
  const response = await fetch(
    `${BASE_URL}/telemetry/${agentId}?range=${range}`,
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

async function acknowledgeAlert(alertId, note = '') {
  const response = await fetch(`${BASE_URL}/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ note })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

// Usage example
(async () => {
  try {
    // List all agents
    const agents = await listAgents({ status: 'active' });
    console.log(`Found ${agents.length} active agents`);
    
    // Trigger a scan
    const scan = await triggerScan('10.0.0.0/8', { scan_type: 'quick' });
    console.log(`Scan started: ${scan.scan_id}`);
    
    // Get telemetry for first agent
    if (agents.length > 0) {
      const telemetry = await getTelemetry(agents[0].id, '7d');
      console.log(`7-day connections: ${telemetry.summary.total_connections}`);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

### cURL

```bash
# Set variables
API_KEY="cw_live_xxxxx"
BASE_URL="http://localhost:9000/api"

# List all agents
curl "$BASE_URL/agents" \
  -H "X-API-Key: $API_KEY"

# List agents filtered by framework
curl "$BASE_URL/agents?framework=OpenClaw&status=active" \
  -H "X-API-Key: $API_KEY"

# Trigger a scan
curl -X POST "$BASE_URL/scan" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"network": "192.168.1.0/24", "scan_type": "full"}'

# Get scan status
curl "$BASE_URL/scan/status" \
  -H "X-API-Key: $API_KEY"

# Get telemetry for specific agent
curl "$BASE_URL/telemetry/ag_7k2m9n4p?range=7d" \
  -H "X-API-Key: $API_KEY"

# List alerts
curl "$BASE_URL/alerts?severity=high&status=new" \
  -H "X-API-Key: $API_KEY"

# Acknowledge an alert
curl -X POST "$BASE_URL/alerts/alert_abc123/acknowledge" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"note": "Investigated and verified"}'

# Get current configuration
curl "$BASE_URL/config" \
  -H "X-API-Key: $API_KEY"

# Update configuration
curl -X PUT "$BASE_URL/config" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scanner": {"scan_interval_hours": 12}}'
```

---

## 📚 SDKs & Libraries

### Official SDKs

**Python SDK** (Coming soon)
```bash
pip install cogniwatch-sdk
```

**JavaScript SDK** (Coming soon)
```bash
npm install @cogniwatch/sdk
```

### Community Libraries

*(This section will be populated as community contributions are made)*

---

## 📚 Additional Resources

- [Quick Start Guide](QUICKSTART.md) — Get started in 5 minutes
- [Deployment Guide](DEPLOYMENT.md) — Production setup
- [Security Report](SECURITY.md) — OWASP compliance details
- [User Guide](USER_GUIDE.md) — End-user documentation

---

## 🆘 Support

**API Issues:**
- GitHub Issues: https://github.com/neo/cogniwatch/issues
- Email: support@cogniwatch.dev

**Documentation:**
- Report errors: https://github.com/neo/cogniwatch/issues
- Suggest improvements: https://github.com/neo/cogniwatch/discussions

---

<p align="center">
  <strong>Need help?</strong> Check the <a href="USER_GUIDE.md">User Guide</a> or open an issue on GitHub.
</p>
