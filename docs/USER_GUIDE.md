# 📖 CogniWatch User Guide

**Version:** 1.0.0  
**Last Updated:** March 8, 2026

Complete end-user documentation for getting started with CogniWatch, running scans, understanding results, and configuring settings.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Tour](#dashboard-tour)
3. [Running Scans](#running-scans)
4. [Understanding Results](#understanding-results)
5. [Working with Agents](#working-with-agents)
6. [Telemetry & Monitoring](#telemetry--monitoring)
7. [Security Alerts](#security-alerts)
8. [Settings Configuration](#settings-configuration)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- ✅ CogniWatch installed (see [DEPLOYMENT.md](DEPLOYMENT.md))
- ✅ Web browser (Chrome, Firefox, Safari, Edge)
- ✅ Network authorization to scan

### First Login

1. **Open CogniWatch** in your browser:
   ```
   http://localhost:9000
   # Or your server IP: http://<server-ip>:9000
   ```

2. **Enter credentials**:
   - Username: `admin` (or as configured)
   - Password: (your secure password)

3. **Change default password** immediately after first login!

### Initial Setup Wizard

On first login, you'll see the setup wizard:

**Step 1: Configure Network**
```
Network Range: 192.168.1.0/24
Scan Frequency: Every 6 hours
```

**Step 2: Notification Settings**
```
Email Alerts: [ ] Enable
Slack Webhook: [Optional]
```

**Step 3: Security Settings**
```
Token Expiry: 24 hours
Rate Limiting: Enabled (60 req/min)
```

**Step 4: Complete Setup**
Click "Finish" to start your first scan!

---

## 🎨 Dashboard Tour

### Overview

*Screenshot placeholder: Main CogniWatch dashboard showing summary cards at top (Total Agents: 7, Active Scans: 1, Alerts: 3), agent list in center with framework icons and confidence badges, sidebar navigation on left, search bar at top.*

The dashboard is your central hub for monitoring AI agents.

### Dashboard Sections

#### 1. **Header Bar** (Top)

- **Logo** — Click to return to dashboard
- **Search** — Quick agent search by IP, framework, or tag
- **Notifications** — Bell icon shows unread alerts
- **User Menu** — Profile, settings, logout

#### 2. **Summary Cards** (Top Row)

| Card | Shows | Click Action |
|------|-------|--------------|
| **Total Agents** | Number of discovered agents | View all agents |
| **Active Now** | Currently online agents | Filter by active |
| **Scans Completed** | Total scans run | View scan history |
| **Active Alerts** | Unresolved alerts | View alert queue |

#### 3. **Agent List** (Center)

Shows all discovered agents with:

- **Framework Icon** — Visual identification
- **Agent Name** — Framework + version
- **IP:Port** — Network location
- **Confidence Badge** — Detection certainty (Critical/High/Medium/Low)
- **Status Indicator** — Green (active), Gray (offline)
- **Last Seen** — Timestamp
- **Quick Actions** — View details, export, delete

**Sorting:** Click column headers to sort  
**Filtering:** Use dropdowns above table  
**Selection:** Checkboxes for bulk actions

#### 4. **Navigation Sidebar** (Left)

- 🏠 **Dashboard** — Main overview
- 🔍 **Agents** — Full agent list
- 📊 **Telemetry** — Metrics and graphs
- 🚨 **Alerts** — Security notifications
- 📅 **Scans** — Scan history & scheduling
- ⚙️ **Settings** — Configuration
- 📚 **Documentation** — Help & guides

#### 5. **Recent Activity** (Right Panel)

Real-time feed showing:
- New agents detected
- Scans completed
- Alerts triggered
- Configuration changes

---

## 🔍 Running Scans

### Quick Scan (Common Ports)

**When to use:** Fast discovery of common AI frameworks

**Steps:**
1. Navigate to **Scans** → **New Scan**
2. Select **Quick Scan**
3. Enter network range: `192.168.1.0/24`
4. Click **Start Scan**

**Duration:** ~2-5 minutes for /24 network  
**Ports scanned:** 80, 443, 5000, 8080, 18789

### Full Scan (All Ports)

**When to use:** Comprehensive discovery, initial baseline

**Steps:**
1. Navigate to **Scans** → **New Scan**
2. Select **Full Scan**
3. Enter network range: `192.168.1.0/24`
4. Configure options:
   - **Custom Ports:** `[80, 443, 5000, 8080, 8081, 18789]`
   - **TLS Detection:** ✅ Enabled
   - **WebSocket Detection:** ✅ Enabled
   - **Banner Grabbing:** ✅ Enabled
   - **Rate Limit:** `100` packets/sec
5. Click **Start Scan**

**Duration:** ~10-15 minutes for /24 network  
**Ports scanned:** All specified ports

### Scheduled Scans

**Set up automatic scanning:**

1. Navigate to **Scans** → **Schedule**
2. Click **New Schedule**
3. Configure:
   - **Network:** `192.168.1.0/24`
   - **Frequency:** Daily / Weekly / Custom cron
   - **Scan Type:** Quick or Full
   - **Notifications:** Email on completion
4. Click **Save Schedule**

**Example schedules:**
- **Daily at 2 AM:** `0 2 * * *`
- **Every 6 hours:** `0 */6 * * *`
- **Weekdays only:** `0 9 * * 1-5`

### Manual CLI Scan

```bash
# Using API
curl -X POST http://localhost:9000/api/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "network": "192.168.1.0/24",
    "scan_type": "full"
  }'

# Using Python script (from source)
source venv/bin/activate
python3 scanner/network_scanner.py --network 192.168.1.0/24
```

### Scan Status & Progress

**Monitor scan progress:**

1. Navigate to **Scans** → **Active Scans**
2. View real-time progress:
   - **Progress Bar** — Percentage complete
   - **Hosts Scanned** — X of Y
   - **Agents Found** — Running count
   - **Estimated Time** — Time remaining

**Scan states:**
- ⏳ **Queued** — Waiting to start
- 🔄 **Running** — In progress
- ✅ **Completed** — Finished successfully
- ❌ **Failed** — Error occurred
- ⏹️ **Cancelled** — Manually stopped

### Scan History

**View past scans:**

1. Navigate to **Scans** → **History**
2. Filter by date, status, or network
3. Click any scan for details:
   - Agents discovered
   - Duration
   - Configuration used
   - Export results

---

## 📊 Understanding Results

### Confidence Scores

CogniWatch uses Bayesian inference to calculate confidence.

**Confidence Levels:**

| Level | Score | Badge | Meaning | Action |
|-------|-------|-------|---------|--------|
| **Critical** | 95-100% | 🔴 | Definitive match | Immediate review |
| **High** | 75-94% | 🟠 | Strong indicators | Prioritize review |
| **Medium** | 50-74% | 🟡 | Possible match | Validate manually |
| **Low** | <50% | ⚪ | Weak signals | Investigate if relevant |

### How Confidence is Calculated

**Example: OpenClaw Detection**

```
┌─────────────────────────────────────┐
│  Agent at 192.168.1.100:8080       │
├─────────────────────────────────────┤
│                                     │
│  Port Match (30%)                   │
│  └─ Port 8080 open: +30%           │
│                                     │
│  HTTP Headers (15%)                 │
│  └─ X-OpenClaw-Version: 1.0: +15%  │
│                                     │
│  API Endpoints (25%)                │
│  └─ /api/v1/gateway/status: +25%   │
│                                     │
│  WebSocket (15%)                    │
│  └─ /ws/agent handshake: +15%      │
│                                     │
│  Behavioral (9%)                    │
│  └─ Periodic heartbeat: +9%        │
│                                     │
├─────────────────────────────────────┤
│  Total: 94% → HIGH CONFIDENCE      │
└─────────────────────────────────────┘
```

### Detection Layers

**What each layer means:**

1. **Port Match** — Default framework port detected
   - Reliability: Medium (ports can be changed)
   - Weight: 30%

2. **HTTP Headers** — Framework-specific headers
   - Example: `X-OpenClaw-Version: 1.0`
   - Reliability: High
   - Weight: 15-40%

3. **API Endpoints** — Known API paths respond correctly
   - Example: `/api/v1/agents` returns expected JSON
   - Reliability: Very High
   - Weight: 25%

4. **WebSocket Protocol** — WebSocket handshake analysis
   - Reliability: High
   - Weight: 15%

5. **Behavioral Analysis** — Request patterns and timing
   - Example: Periodic heartbeat every 30 seconds
   - Reliability: Medium
   - Weight: 5-15%

### Agent Status

| Status | Icon | Description |
|--------|------|-------------|
| **Active** | 🟢 | Agent responding, recently seen (<5 min) |
| **Offline** | ⚫ | Agent not responding, was seen before |
| **Unknown** | ⚪ | First detection, status not yet determined |

---

## 🤖 Working with Agents

### Viewing Agent Details

**Click any agent** in the list to see:

1. **Overview Tab**
   - Framework and version
   - IP address and port
   - Confidence score breakdown
   - Detection timestamp
   - Last seen timestamp

2. **Endpoints Tab**
   - All discovered API endpoints
   - HTTP/HTTPS/WebSocket protocols
   - Response times
   - Status codes

3. **Telemetry Tab**
   - Connection graphs (24h, 7d, 30d)
   - API call volume
   - WebSocket message counts
   - Error rates

4. **Detection Details Tab**
   - Layer-by-layer confidence breakdown
   - Patterns matched
   - Raw scan data

5. **Notes & Tags Tab**
   - Add custom notes
   - Manage tags
   - Export agent data

### Tagging Agents

**Organize agents with tags:**

1. Select agent(s)
2. Click **Tags** → **Edit Tags**
3. Add/remove tags:
   - `production`
   - `development`
   - `critical`
   - `gateway`
   - `worker`
4. Click **Save**

**Use tags for:**
- Filtering views
- Bulk operations
- Alert routing
- Reporting

### Adding Notes

**Document important details:**

1. Open agent detail view
2. Click **Notes** tab
3. Add note:
   ```
   Primary production gateway
   Owner: ops@example.com
   Maintenance window: Sundays 2-4 AM
   ```
4. Click **Save**

### Exporting Agent Data

**Export formats:**

- **JSON** — Full data structure, programmatic use
- **CSV** — Spreadsheet compatible
- **PDF** — Printable report

**Steps:**
1. Select agent(s) with checkboxes
2. Click **Export** button
3. Choose format
4. Download file

---

## 📈 Telemetry & Monitoring

### Real-Time Metrics

**Navigate to Telemetry → Real-Time**

View live agent activity:
- Connections per second
- API calls per minute
- WebSocket messages
- Error rates

**Graph types:**
- Line charts (trends over time)
- Bar charts (comparisons)
- Heatmaps (activity density)

### Historical Analysis

**Time ranges:**
- **Last Hour** — Immediate trends
- **Last 24h** — Daily patterns
- **Last 7 Days** — Weekly trends
- **Last 30 Days** — Monthly overview

**Metrics available:**
- Total connections
- API call volume
- WebSocket message count
- Average response time
- Error rate percentage
- Uptime percentage

### Comparative Views

**Compare agents or frameworks:**

1. Navigate to **Telemetry** → **Compare**
2. Select agents/frameworks to compare
3. Choose metric:
   - Connections
   - API calls
   - Response time
4. View side-by-side comparison

### Alert Thresholds

**Set custom alert thresholds:**

1. Navigate to **Settings** → **Alerts**
2. Configure thresholds:
   ```
   API Call Spike: >500% of baseline
   Response Time: >1000ms
   Error Rate: >5%
   Offline Duration: >1 hour
   ```
3. Set notification method:
   - Email
   - Slack webhook
   - Both

---

## 🚨 Security Alerts

### Alert Types

| Type | Severity | Description |
|------|----------|-------------|
| **New Agent Detected** | High | Previously unseen agent found |
| **Unusual Activity** | Medium | Deviation from baseline behavior |
| **Agent Offline** | Medium | Known agent stopped responding |
| **Security Anomaly** | High | Potential security concern |
| **High Confidence Detection** | Low | Critical framework detected |
| **Scan Completed** | Info | Scheduled or manual scan finished |

### Managing Alerts

**Alert workflow:**

1. **New Alert** → Requires attention
2. **Acknowledge** → Under review
3. **Resolve** → Issue addressed

**Steps:**

1. Navigate to **Alerts**
2. Filter by status/severity
3. Click alert for details
4. Take action:
   - **Acknowledge** — Add note: "Investigating"
   - **Resolve** — Add resolution notes
   - **Escalate** — Notify team (if configured)

### Alert Notifications

**Configure notifications:**

1. Navigate to **Settings** → **Notifications**
2. Enable channels:
   - **Email:** Enter recipient addresses
   - **Slack:** Enter webhook URL
3. Select alert severities:
   - Critical: ✅ All channels
   - High: ✅ Email + Slack
   - Medium: ✅ Email
   - Low: ⚪ None (or all for debugging)

---

## ⚙️ Settings Configuration

### General Settings

**Navigate to Settings → General**

```
Application Name: CogniWatch
Theme: Dark / Light / Auto
Language: English
Timezone: UTC / Local
Date Format: YYYY-MM-DD / MM/DD/YYYY
```

### Scanner Settings

**Navigate to Settings → Scanner**

```
Default Network: 192.168.1.0/24
Scan Interval: 6 hours
Rate Limit: 100 packets/sec
Timeout: 300 seconds
Auto-scan on startup: Yes
Detection Layers:
  ☑ HTTP Headers
  ☑ API Endpoints
  ☑ WebSocket
  ☑ TLS/JA3
  ☑ Behavioral
```

### Security Settings

**Navigate to Settings → Security**

```
Authentication:
  ☑ Require login
  Token Expiry: 24 hours
  Session Timeout: 8 hours

Rate Limiting:
  ☑ Enabled
  Requests/minute: 60
  Burst limit: 100

Password Policy:
  Minimum length: 12 characters
  Require uppercase: Yes
  Require numbers: Yes
  Require special chars: Yes
```

### Network Settings

**Navigate to Settings → Network**

```
Web UI Host: 0.0.0.0
Web UI Port: 9000
Allowed Origins: http://localhost:9000, http://192.168.1.0/24
Reverse Proxy: Nginx / Traefik / None
HTTPS: Enabled / Disabled
```

### Notification Settings

**Navigate to Settings → Notifications**

```
Email:
  Enabled: Yes
  SMTP Server: smtp.example.com
  Port: 587
  Username: alerts@example.com
  Password: ••••••••
  Recipients: security@example.com

Slack:
  Enabled: Yes
  Webhook URL: https://hooks.slack.com/...
  Channel: #security-alerts
```

### Backup Settings

**Navigate to Settings → Backup**

```
Automatic Backups:
  ☑ Enabled
  Frequency: Daily
  Time: 3:00 AM
  Retention: 30 days

Backup Location: /backup/cogniwatch
Encryption: ☑ Enabled
```

---

## 🎯 Best Practices

### Scanning Best Practices

✅ **DO:**
- Scan only networks you own or have authorization for
- Start with quick scans for baseline
- Use full scans monthly for comprehensive inventory
- Schedule scans during maintenance windows
- Review high-confidence detections promptly

❌ **DON'T:**
- Scan external networks without authorization
- Use aggressive rates on production networks
- Ignore medium/low confidence detections
- Run scans during peak business hours

### Security Best Practices

✅ **DO:**
- Change default passwords immediately
- Enable HTTPS for remote access
- Use API keys for automation (not admin credentials)
- Rotate credentials regularly
- Review audit logs weekly
- Backup database before upgrades

❌ **DON'T:**
- Share credentials via email/chat
- Expose web UI to public internet without authentication
- Use weak passwords
- Skip security updates

### Performance Best Practices

✅ **DO:**
- Use appropriate scan rates for network size
- Monitor database size and prune old telemetry
- Run during off-peak hours
- Use tags to organize large agent inventories

❌ **DON'T:**
- Scan /8 networks in single scan (break into smaller ranges)
- Store telemetry indefinitely (use retention policies)
- Ignore resource usage alerts

---

## ❓ FAQ

### General Questions

**Q: How often should I scan?**  
A: For most environments, every 6-24 hours is sufficient. High-security environments may scan every 1-4 hours.

**Q: Will scanning disrupt my network?**  
A: No, if you use conservative rate limits (default: 100 packets/sec). For sensitive networks, reduce to 50 packets/sec.

**Q: Can CogniWatch detect cloud agents?**  
A: Not yet. Cloud scanning (AWS, Azure, GCP) is planned for Phase B (Q2 2026).

**Q: What if an agent changes ports?**  
A: CogniWatch will detect it on the next scan. The agent will appear as a new discovery with updated port information.

### Detection Questions

**Q: Why is confidence only 60%?**  
A: Lower confidence means fewer detection layers matched. Manually verify by checking the agent directly, or wait for additional behavioral data.

**Q: Can CogniWatch detect custom frameworks?**  
A: Yes! You can add custom signatures. See [FRAMEWORK-SIGNATURES.md](FRAMEWORK-SIGNATURES.md) for details.

**Q: What's the most reliable detection layer?**  
A: API endpoint validation is most reliable (framework must respond correctly), followed by HTTP headers.

### Troubleshooting Questions

**Q: Scanner finds no agents, but I know they exist**  
A: Check:
- Network range is correct for your network
- Firewall isn't blocking outbound scans
- Agent frameworks are actually running
- Try a full scan with banner grabbing enabled

**Q: Web UI won't load**  
A: Check:
- Service is running: `systemctl status cogniwatch`
- Port is not blocked by firewall
- You're using correct URL (http://localhost:9000)
- No other service is using port 9000

**Q: How do I reset my password?**  
A: If you have database access:
```bash
sqlite3 /opt/cogniwatch/data/cogniwatch.db
UPDATE users SET password_hash='<new_hash>' WHERE username='admin';
```
Or contact your administrator.

### License & Legal Questions

**Q: Can I use CogniWatch commercially?**  
A: Yes! CogniWatch is MIT licensed — use it for anything. See [LICENSE](../LICENSE) for details.

**Q: Is scanning legal?**  
A: Only if you own the network or have explicit authorization. Unauthorized scanning may violate computer crime laws. Always get permission first.

---

## 📞 Support

**Documentation:**
- [Quick Start](QUICKSTART.md) — 5-minute setup
- [API Reference](API.md) — Complete API docs
- [Deployment Guide](DEPLOYMENT.md) — Production deployment
- [Security Report](SECURITY.md) — OWASP compliance

**Getting Help:**
- GitHub Issues: https://github.com/neo/cogniwatch/issues
- Email: support@cogniwatch.dev
- Documentation: https://docs.cogniwatch.dev

---

<p align="center">
  <strong>Ready to become a power user?</strong> Check out the <a href="API.md">API Reference</a> for automation tips!
</p>
