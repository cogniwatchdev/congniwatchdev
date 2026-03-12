# Tabler UI Integration Summary - CogniWatch Backend

**Date:** 2026-03-08  
**Status:** ✅ Complete  
**File:** `/home/neo/cogniwatch/webui/server.py`

---

## 1. Routes Added

### Tabler UI Pages

| Route | Method | Template | Description |
|-------|--------|----------|-------------|
| `/dashboard` | GET | `dashboard-2026.html` | Main KPI view with widgets |
| `/scan` | GET | `scanner.html` | Scanner control UI |
| `/agents` | GET | `agents.html` | Agent list with search/filter |
| `/analytics` | GET | `analytics.html` | Charts and analytics |
| `/faq` | GET | `faq.html` | FAQ page |
| `/about` | GET | `about.html` | About page |
| `/help` | GET | `help.html` | Help center |

### Code Sample: Tabler Routes
```python
@app.route('/dashboard')
@require_auth('read')
def dashboard():
    """Main KPI dashboard - Tabler UI"""
    return render_template('dashboard-2026.html')


@app.route('/scan')
@require_auth('read')
def scan_page():
    """Scanner UI - Tabler"""
    return render_template('scanner.html')


@app.route('/agents')
@require_auth('read')
def agents_page():
    """Agent list with search/filter - Tabler"""
    return render_template('agents.html')
```

---

## 2. API Endpoints Updated/Created

### `/api/agents` (FIXED)
**Purpose:** Read agents from `detection_results` table  
**Method:** GET  
**Auth:** `read`

**Code Sample:**
```python
@app.route('/api/agents')
@require_auth('read')
def api_agents():
    """Get all agents from detection_results table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get latest detections per host:port
    cursor.execute('''
        SELECT DISTINCT host, port, top_framework, confidence, 
               confidence_level, layer_results, evidence, timestamp
        FROM detection_results
        WHERE (host, port, timestamp) IN (
            SELECT host, port, MAX(timestamp)
            FROM detection_results
            GROUP BY host, port
        )
        ORDER BY confidence DESC, timestamp DESC
    ''')
    
    agents = []
    for row in cursor.fetchall():
        layer_results = json.loads(row['layer_results']) if row['layer_results'] else {}
        evidence = json.loads(row['evidence']) if row['evidence'] else []
        
        agents.append({
            "id": f"{row['top_framework']}-{row['host'].replace('.', '-')}-{row['port']}",
            "name": f"{row['top_framework'].title()} @ {row['host']}:{row['port']}",
            "framework": row['top_framework'] or 'unknown',
            "host": row['host'],
            "port": row['port'],
            "model": layer_results.get('api', {}).get('model', 'unknown'),
            "status": "online" if row['confidence'] > 0.5 else "offline",
            "confidence": row['confidence'] or 0.0,
            "confidence_badge": row['confidence_level'] or 'unconfirmed',
            "evidence": evidence,
            "last_seen": row['timestamp']
        })
    
    return jsonify({"agents": agents, "total": len(agents)})
```

### `/api/scan/start` (NEW)
**Purpose:** Trigger new network scan  
**Method:** POST  
**Auth:** `scan`

**Code Sample:**
```python
@app.route('/api/scan/start', methods=['POST'])
@require_auth('scan')
def api_scan_start():
    """Start a new network scan"""
    global active_scan
    
    with cache_lock:
        if active_scan["running"]:
            return jsonify({"error": "Scan already in progress"}), 409
        
        scan_id = f"scan_{int(time.time())}"
        active_scan = {
            "running": True,
            "scan_id": scan_id,
            "start_time": datetime.now().isoformat(),
            "hosts_scanned": 0,
            "total_hosts": 254,
            "progress": 0,
            "status": "initializing"
        }
        
        # Start background scan thread
        from scanner.network_scanner import NetworkScanner
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "start_time": active_scan["start_time"]
        })
```

### `/api/scan/status` (NEW)
**Purpose:** Get scan progress  
**Method:** GET  
**Auth:** `read`

**Code Sample:**
```python
@app.route('/api/scan/status')
@require_auth('read')
def api_scan_status():
    """Get current scan progress"""
    with cache_lock:
        return jsonify({
            "running": active_scan["running"],
            "scan_id": active_scan.get("scan_id"),
            "progress": active_scan["progress"],
            "hosts_scanned": active_scan["hosts_scanned"],
            "total_hosts": active_scan["total_hosts"],
            "status": active_scan.get("status", "idle"),
            "scan_status": scan_cache["scan_status"],
            "agents_found": len(scan_cache.get("agents", []))
        })
```

---

## 3. Dashboard Widget Data Binding

### `/api/dashboard/stats` (NEW)
**Purpose:** Real-time data for dashboard widgets  
**Returns:** Total agents count, recent detections feed, scan status

**Code Sample:**
```python
@app.route('/api/dashboard/stats')
@require_auth('read')
def api_dashboard_stats():
    """Get real-time dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total agents count
    cursor.execute('''
        SELECT COUNT(DISTINCT host || ':' || port) as total
        FROM detection_results
        WHERE (host, port, timestamp) IN (
            SELECT host, port, MAX(timestamp)
            FROM detection_results
            GROUP BY host, port
        )
    ''')
    total_agents = cursor.fetchone()[0] or 0
    
    # Recent detections feed (last 10)
    cursor.execute('''
        SELECT host, port, top_framework, confidence, timestamp
        FROM detection_results
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    recent_detections = []
    for row in cursor.fetchall():
        recent_detections.append({
            "host": row[0],
            "port": row[1],
            "framework": row[2] or 'unknown',
            "confidence": row[3] or 0,
            "timestamp": row[4]
        })
    
    return jsonify({
        "total_agents": total_agents,
        "recent_detections": recent_detections,
        "scan_status": scan_cache["scan_status"],
        "last_scan": scan_cache["last_scan"]
    })
```

### Widget Data Binding Examples

**Total Agents Widget:**
```javascript
// Fetch and display total agents count
fetch('/api/dashboard/stats')
  .then(res => res.json())
  .then(data => {
    document.getElementById('total-agents').textContent = data.total_agents;
  });
```

**Recent Detections Feed:**
```javascript
// Populate recent detections table
fetch('/api/dashboard/stats')
  .then(res => res.json())
  .then(data => {
    const tbody = document.querySelector('#recent-detections tbody');
    tbody.innerHTML = data.recent_detections.map(d => `
      <tr>
        <td>${d.host}:${d.port}</td>
        <td>${d.framework}</td>
        <td>${(d.confidence * 100).toFixed(1)}%</td>
        <td>${new Date(d.timestamp).toLocaleString()}</td>
      </tr>
    `).join('');
  });
```

**Scan Status Widget:**
```javascript
// Real-time scan status polling
setInterval(() => {
  fetch('/api/scan/status')
    .then(res => res.json())
    .then(data => {
      document.getElementById('scan-progress').value = data.progress;
      document.getElementById('scan-status').textContent = data.status;
    });
}, 2000);
```

---

## 4. Test curl Commands

### Test Authentication
```bash
# Login
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' \
  -c cookies.txt
```

### Test Agents API
```bash
# Get all agents from detection_results
curl http://localhost:9000/api/agents \
  -b cookies.txt | jq .
```

**Expected Output:**
```json
{
  "agents": [
    {
      "id": "openclaw-127-0-0-1-18789",
      "name": "Openclaw @ 127.0.0.1:18789",
      "framework": "openclaw",
      "host": "127.0.0.1",
      "port": 18789,
      "model": "ollama/qwen3.5:cloud",
      "status": "online",
      "confidence": 1.0,
      "confidence_badge": "confirmed"
    }
  ],
  "total": 1
}
```

### Test Scan Start
```bash
# Start new scan
curl -X POST http://localhost:9000/api/scan/start \
  -b cookies.txt | jq .
```

**Expected Output:**
```json
{
  "success": true,
  "scan_id": "scan_1741443200",
  "start_time": "2026-03-08T14:00:00.000000"
}
```

### Test Scan Status
```bash
# Check scan progress
curl http://localhost:9000/api/scan/status \
  -b cookies.txt | jq .
```

**Expected Output:**
```json
{
  "running": true,
  "scan_id": "scan_1741443200",
  "progress": 45,
  "hosts_scanned": 114,
  "total_hosts": 254,
  "status": "scanning",
  "agents_found": 3
}
```

### Test Dashboard Stats
```bash
# Get dashboard widget data
curl http://localhost:9000/api/dashboard/stats \
  -b cookies.txt | jq .
```

**Expected Output:**
```json
{
  "total_agents": 5,
  "recent_detections": [
    {
      "host": "127.0.0.1",
      "port": 18789,
      "framework": "openclaw",
      "confidence": 1.0,
      "timestamp": "2026-03-08T13:55:00"
    }
  ],
  "scan_status": "complete",
  "last_scan": "2026-03-08T13:50:00"
}
```

### Test Agent Search
```bash
# Search agents by framework
curl "http://localhost:9000/api/agents/search?q=openclaw" \
  -b cookies.txt | jq .
```

### Test Analytics
```bash
# Get framework distribution
curl http://localhost:9000/api/analytics/frameworks \
  -b cookies.txt | jq .

# Get detection timeline
curl http://localhost:9000/api/analytics/timeline \
  -b cookies.txt | jq .
```

---

## 5. Database Schema Integration

All API endpoints now read from the `detection_results` table:

```sql
-- Table structure used by /api/agents
CREATE TABLE detection_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_time_ms REAL,
    top_framework TEXT,
    confidence REAL,
    confidence_level TEXT,
    detection_quality TEXT,
    layer_results JSON,
    framework_scores JSON,
    all_signals JSON,
    evidence JSON,
    recommendation TEXT,
    UNIQUE(host, port, timestamp)
);
```

**Key Fields Used:**
- `host`, `port` - Agent location
- `top_framework` - Detected framework (OpenClaw, Flask, etc.)
- `confidence` - Detection confidence (0.0-1.0)
- `confidence_level` - Badge level (confirmed, probable, unconfirmed)
- `layer_results` - JSON with API info (model, version, etc.)
- `evidence` - JSON array of detection evidence

---

## 6. Summary

### What Was Done:
1. ✅ Added 7 Tabler UI page routes (`/dashboard`, `/scan`, `/agents`, `/analytics`, `/faq`, `/about`, `/help`)
2. ✅ Fixed `/api/agents` to read from `detection_results` table
3. ✅ Created `/api/scan/start` endpoint to trigger scans
4. ✅ Created `/api/scan/status` endpoint for real-time progress
5. ✅ Connected dashboard widgets to real data via `/api/dashboard/stats`
6. ✅ Added search/filter API at `/api/agents/search`
7. ✅ Added analytics endpoints (`/api/analytics/frameworks`, `/api/analytics/timeline`)
8. ✅ Maintained authentication/authorization on all routes
9. ✅ Preserved existing security middleware

### Files Modified:
- `/home/neo/cogniwatch/webui/server.py` (main backend)
- Backup created: `/home/neo/cogniwatch/webui/server.py.bak`

### Next Steps:
1. Create/update Tabler HTML templates (if not already done)
2. Frontend JavaScript to consume APIs
3. Test with live data
4. Deploy and verify

---

**Integration Status:** ✅ Backend Ready for Tabler UI
