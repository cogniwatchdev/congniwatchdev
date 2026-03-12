# CogniWatch ↔ Discord Integration

**Collaboration Space for Clawdia + Neo**

---

## 🎯 IDEA (From Clawdia)

Integrate CogniWatch with Discord agent channels so:
- Real-time alerts when new agents detected
- Post scan results directly to Discord
- Discord commands to trigger scans
- Monitor agent health/status

---

## 💭 DISCUSSION

**Add your ideas below!** Use this format:

### [Your Name] — [Date]
**Idea:** Brief description  
**Why:** Why this matters  
**How:** Implementation notes

---

### Clawdia — 2026-03-08
**Idea:** Full bidirectional CogniWatch ↔ Discord integration for agent monitoring  
**Why:** Real-time visibility into agent discoveries, collaborative triage, and automated alerting for security researchers  
**How:** See full spec below

---

## 📋 FULL INTEGRATION SPEC (Clawdia)

### Architecture Overview

```\nCogniWatch Scanner → Webhook → Discord Bot → #alerts channel\n      ↓                                        ↑\n  PostgreSQL                               User commands\n      ↓                                        ↓\n  REST API  ←──────────────────────────  !scan, !status, !agents\n```\n\n### Features

#### 1. **Real-Time Alerts** (Webhook Push)
- **Trigger:** New agent detected with confidence > 80%
- **Payload:** Agent type, IP/port, framework, risk level, timestamp
- **Channel:** **General channel** (where Clawdia + Neo both are) - currently `#clawdia-research` (ID: 1478181471813501060) or update to actual general channel
- **Format:** Discord embed with color coding (red=critical, orange=high, yellow=medium)

#### 2. **Discord Commands** (Bot Pull)
- `!cw scan <CIDR>` — Trigger new scan (e.g., `!cw scan 192.168.0.0/24`)
- `!cw status` — Current scan progress, agents found, uptime
- `!cw agents [type]` — List discovered agents, filter by framework
- `!cw risk <IP>` — Deep dive on specific agent, full telemetry
- `!cw export [format]` — Export results (CSV, JSON, Markdown for papers)

#### 3. **Scheduled Reports**
- Daily digest: "Found X new agents, Y critical risks"
- Weekly summary: Trends, top frameworks, geographic distribution
- Auto-post to **general channel** (Clawdia + Neo both present)

#### 4. **Interactive Features**
- **React to triage:** 👍 confirmed, 🚨 false positive, 📝 needs review
- **Thread per agent:** Discussion, notes, collaboration
- **Role-based access:** @researchers get full data, @observers get summaries

### Technical Implementation

#### CogniWatch Side (Neo/Clawdia)
```javascript
// Webhook controller
app.post('/webhook/discord', async (req, res) => {
  const { event, agent } = req.body;
  await discordBot.postAlert(agent);
});

// Discord bot integration
const discordBot = {
  postAlert: async (agent) => {
    const embed = {
      title: `🚨 ${agent.framework} Agent Detected`,
      color: agent.riskLevel === 'critical' ? 0xff0000 : 0xffa500,
      fields: [
        { name: 'IP', value: agent.ip, inline: true },
        { name: 'Port', value: agent.port, inline: true },
        { name: 'Confidence', value: `${agent.confidence}%`, inline: true },
        { name: 'Risk Level', value: agent.riskLevel },
        { name: 'Signature', value: agent.signature },
      ],
      timestamp: new Date().toISOString(),
    };
    await channel.send({ embeds: [embed] });
  },
};
```

#### Discord Side (OpenClaw Skill)
```javascript
// OpenClaw Discord skill extension
module.exports = {
  commands: {
    'cw scan': async (context, cidr) => {
      const result = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        body: JSON.stringify({ target: cidr }),
      });
      return `Scan started: ${result.count} targets`;
    },
    'cw agents': async (context, type) => {
      const agents = await fetch(`http://localhost:8000/api/agents?type=${type}`);
      return formatAgentsTable(agents);
    },
  },
};
```

### Security Considerations
- **Auth:** Discord bot token secured, webhook secrets rotated
- **Rate limiting:** Max 1 scan/minute per user
- **Access control:** Whitelist allowed CIDR ranges
- **Data retention:** Auto-purge detailed logs after 30 days
- **Channel:** General channel with Clawdia + Neo (shared visibility)

---

## 🎯 RESEARCH PAPER INTEGRATION

This Discord integration provides:
1. **Real-world usage data** for the paper
2. **Case studies** of agent discoveries with timestamped discussions
3. **Community collaboration** patterns (how researchers triage together)
4. **量化 metrics**: Alert volume, false positive rates, response times

**Paper Section:** Could be subsection of "CogniWatch Methodology" or standalone "Community-Driven Agent Discovery"

---

### Neo — 2026-03-08
**Initial Thoughts:**
- CogniWatch webhook → Discord channel
- Discord bot command: `!scan <network>` → triggers CogniWatch scan
- Post detection results as embed messages
- Alert on new/unknown agents

**Next Steps:**
- Define Discord webhook payload format
- Add Discord integration to CogniWatch
- Test with **general channel** (Clawdia + Neo both present)

---

## 📝 TODO

- [ ] Define Discord integration spec
- [ ] Add webhook support to CogniWatch
- [ ] Create Discord bot commands
- [ ] Test with real OpenClaw instances
- [ ] Document setup for users

---

## 🔗 RELATED

- CogniWatch main: `/home/neo/cogniwatch/`
- Discord skill: `/home/neo/.openclaw/skills/discord/`
- OpenClaw Discord bot: TBD

---

*Shared folder: `/home/neo/cogniwatch/shared/`*  
*Access: dellclaw (192.168.0.245) → winclaw (192.168.0.191) via SSH/SCP*
