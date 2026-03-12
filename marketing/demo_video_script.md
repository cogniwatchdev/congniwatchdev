# CogniWatch Demo Video Script

**Video Length:** 5 minutes  
**Target Audience:** Security researchers, AI/ML engineers, DevOps teams  
**Style:** Professional, technical, data-driven (not hype)  
**Voiceover:** Calm, confident, authoritative

---

## 0:00-0:30 — Hook: "What If You Could See Every AI Agent?"

### Visual
- **[0:00-0:05]** Black screen. White text fades in:
  > "What if you could see every AI agent on the internet?"
- **[0:05-0:10]** Quick montage:
  - Network topology diagram with glowing nodes
  - Server racks with blinking lights
  - Terminal windows with scrolling logs
- **[0:10-0:15]** CogniWatch logo reveal with tagline:
  > "CogniWatch — Shodan for AI Agents"
- **[0:15-0:30]** Fast cuts of the dashboard in action:
  - Agent list populating
  - Confidence scores animating
  - Real-time telemetry graphs updating

### Voiceover
> "AI agents are being deployed everywhere. LangGraph, AutoGen, CrewAI, Agent-Zero, OpenClaw. But your security tools can't see them.
>
> Traditional scanners miss AI agents because they don't look like traditional services. They use WebSocket, custom HTTP headers, non-standard ports. You're flying blind.
>
> Until now."

### B-Roll Suggestions
- Abstract network visualization (nodes connecting, data flowing)
- Time-lapse of code deployment
- Security operations center (SOC) footage (stock or simulated)

### Screen Recording Notes
- Use high-resolution dashboard captures (1080p minimum)
- Enable smooth transitions between dashboard sections
- Highlight confidence score animations with subtle zoom effects

---

## 0:30-1:00 — Problem: The AI Visibility Gap

### Visual
- **[0:30-0:40]** Split screen:
  - Left: Traditional security dashboard (Nmap, Wireshark) — shows generic network data
  - Right: Same network with AI agents — invisible, no indicators
- **[0:40-0:50]** Text overlay on dark background:
  > "12 AI agents discovered"  
  > "3 running with default credentials"  
  > "7 exposing APIs without authentication"  
  > "0 known to the security team"
- **[0:50-1:00]** CogniWatch dashboard fades in, overlaying the "blind" network view

### Voiceover
> "Last month, we scanned a typical development network. The results were sobering:
>
> Twelve AI agents discovered. Three running with default credentials. Seven exposing APIs without authentication. Zero known to the security team.
>
> This isn't unusual. AI agents communicate differently than traditional services. They deploy without oversight. They leave traces, but no tool connects the dots.
>
> The visibility gap is real. And it's a security risk."

### B-Roll Suggestions
- Screen recording of Nmap output showing only open ports (no agent info)
- Developer deploying an AI agent with one command
- Security analyst looking confused at a generic monitoring dashboard

### Screen Recording Notes
- Show actual Nmap/Wireshark output for authenticity
- Use red X overlays on "blind spots" in traditional tools
- Transition to CogniWatch with a "reveal" effect (fade in or slide)

---

## 1:00-2:00 — Demo: Live Scan, Detection in Action

### Visual
- **[1:00-1:10]** CogniWatch dashboard. Cursor clicks "Scan Network" button.
- **[1:10-1:20]** Scanner progress bar. Real-time log output showing:
  ```
  [SCAN] Probing 192.168.1.0/24
  [DETECT] 192.168.1.100:8080 — HTTP header match: X-OpenClaw-Version
  [DETECT] 192.168.1.105:5000 — API endpoint: /instances (200 OK)
  [DETECT] 192.168.1.110:3000 — WebSocket handshake pattern detected
  ```
- **[1:20-1:35]** Agent list populates:
  - Agent 1: OpenClaw Gateway, 192.168.1.100:8080, **Confidence: 94%**
  - Agent 2: Agent-Zero Instance, 192.168.1.105:5000, **Confidence: 87%**
  - Agent 3: LangGraph Orchestrator, 192.168.1.110:3000, **Confidence: 91%**
- **[1:35-1:50]** Click on first agent → Detail modal opens:
  - Detection factors list
  - Confidence breakdown (bar chart)
  - JA3 fingerprint hash
  - First/last seen timestamps
- **[1:50-2:00]** Telemetry tab: Real-time graph showing API calls, connections, message throughput

### Voiceover
> "Let's see CogniWatch in action.
>
> We initiate a network scan. CogniWatch probes for AI agents using 27 distinct detection techniques.
>
> Watch the detections roll in.
>
> OpenClaw Gateway on 192.168.1.100 — detected via HTTP headers, API endpoints, WebSocket patterns, and JA3 fingerprinting. Confidence: 94%.
>
> Agent-Zero instance on 192.168.1.105 — API endpoint detection, behavioral analysis. Confidence: 87%.
>
> LangGraph orchestrator on 192.168.1.110 — protocol fingerprinting, TLS signatures. Confidence: 91%.
>
> Click into any agent and see exactly why it was detected. Every signal, every technique, every data point.
>
> And here's the telemetry tab — live connections, API call frequency, message patterns. Real-time visibility into agent behavior."

### B-Roll Suggestions
- Close-up of keyboard typing the scan command
- Network cables being plugged in (metaphor for connectivity)
- Developer nodding in approval while watching dashboard

### Screen Recording Notes
- Record actual scan at 60fps for smooth progress bar animation
- Zoom in on detection log lines as they appear
- Use cursor highlights or circles around confidence scores and key metrics
- Enable "record system audio" if dashboard has notification sounds

---

## 2:00-3:00 — Deep Dive: Multi-Layer Detection Explained

### Visual
- **[2:00-2:10]** Animated diagram showing 5 detection layers:
  ```
  Layer 1: Protocol Fingerprinting
  Layer 2: API Endpoint Detection
  Layer 3: Behavioral Analysis
  Layer 4: JA3/TLS Fingerprinting
  Layer 5: Confidence Scoring
  ```
- **[2:10-2:25]** Layer 1 animation:
  - HTTP request/response with highlighted headers
  - WebSocket handshake diagram
  - Text: "X-OpenClaw-Version", "Sec-WebSocket-Protocol"
- **[2:25-2:35]** Layer 2 animation:
  - API endpoint paths lighting up on a framework map
  - Table showing framework-specific endpoints (OpenClaw, Agent-Zero, LangGraph, etc.)
- **[2:35-2:45]** Layer 3 animation:
  - Message flow diagram (agent-to-agent communication)
  - Timing pattern visualization (polling intervals, heartbeats)
- **[2:45-2:55]** Layer 4 animation:
  - TLS handshake sequence
  - JA3 hash appearing: `a05d9c6e8f3b2c1d4e5f6a7b8c9d0e1f`
  - Match to framework library (uvicorn, uvloop)
- **[2:55-3:00]** Layer 5 animation:
  - Bayesian inference formula (simplified)
  - Confidence score building from multiple signals

### Voiceover
> "So how does CogniWatch actually detect AI agents?
>
> Five layers of detection, 27 distinct techniques.
>
> **Layer 1: Protocol Fingerprinting.** AI agents leave signatures in HTTP headers, WebSocket handshakes, and response patterns. Framework-specific headers like `X-OpenClaw-Version` are dead giveaways.
>
> **Layer 2: API Endpoint Detection.** Every framework has telltale endpoints. `/sessions` for OpenClaw. `/instances` for Agent-Zero. `/langgraph/health` for LangGraph. CogniWatch probes these and analyzes responses.
>
> **Layer 3: Behavioral Analysis.** AI agents behave differently than traditional services. They poll at specific intervals. They use JSON-RPC for tool calls. They follow supervisor-worker patterns. CogniWatch learns these behaviors.
>
> **Layer 4: JA3/TLS Fingerprinting.** This is powerful. Every AI agent framework uses specific TLS libraries with predictable configurations. JA3 hashes the TLS handshake — no decryption needed — and matches it to known frameworks.
>
> **Layer 5: Confidence Scoring.** Bayesian inference combines all signals into a single confidence score. Multiple strong signals? 95%+ confidence. Weak signals? Low confidence, likely false positive. You can act on high-confidence detections."

### B-Roll Suggestions
- Animated flowcharts for each layer
- Code snippets showing framework-specific headers
- Whiteboard-style explanation of Bayesian inference (optional)

### Screen Recording Notes
- Use smooth transitions between layers
- Animate text and diagrams (fade, slide, scale)
- Synchronize voiceover timing with visual elements

---

## 3:00-4:00 — Use Cases: Who Needs This?

### Visual
- **[3:00-3:15]** Use Case 1: Security Teams
  - SOC analyst looking at CogniWatch dashboard
  - Alert notification: "New AI agent detected with default credentials"
  - Text overlay: "Security Teams — Know what's in your network"
- **[3:15-3:30]** Use Case 2: AI/ML Engineers
  - Developer deploying multiple agents
  - CogniWatch showing all deployed agents and their status
  - Text overlay: "AI Engineers — Monitor your deployments"
- **[3:30-3:45]** Use Case 3: DevOps/SRE
  - Infrastructure diagram with multiple AI services
  - CogniWatch telemetry showing resource usage and connections
  - Text overlay: "DevOps/SRE — Track infrastructure at scale"
- **[3:45-4:00]** Use Case 4: Researchers
  - Researcher analyzing agent distribution across networks
  - CogniWatch data export (JSON, CSV)
  - Text overlay: "Researchers — Study AI deployment patterns"

### Voiceover
> "Who needs CogniWatch?
>
> **Security teams.** You can't secure what you can't detect. CogniWatch gives you visibility into AI agent deployments across your infrastructure. Find agents running with default credentials. Identify exposed APIs. Close blind spots.
>
> **AI and ML engineers.** You're deploying agents everywhere. CogniWatch helps you track what's running, where, and how it's behaving. Monitor your own deployments. Debug connectivity issues. Ensure compliance.
>
> **DevOps and SRE teams.** Managing AI infrastructure at scale? CogniWatch provides real-time telemetry on connections, API calls, and resource usage. Integrate with your monitoring stack. Alert on anomalies.
>
> **Researchers.** Studying AI deployment patterns? CogniWatch can discover agents across networks and export data for analysis. Understand how AI agents are distributed in the wild.
>
> If you touch AI infrastructure, you need visibility. CogniWatch provides it."

### B-Roll Suggestions
- Stock footage of different personas (security analyst, developer, DevOps engineer, researcher)
- Real-world office environments
- Close-ups of screens showing CogniWatch in different contexts

### Screen Recording Notes
- Show CogniWatch from different user perspectives (security view vs. developer view)
- Highlight relevant features for each use case
- Use split-screen to show multiple concurrent users

---

## 4:00-5:00 — CTA: Deploy Now

### Visual
- **[4:00-4:10]** Terminal window. Commands appear as they're typed:
  ```bash
  git clone https://github.com/neo/cogniwatch.git
  cd cogniwatch
  docker compose up -d
  ```
- **[4:10-4:20]** Progress bar: Docker images pulling, containers starting
- **[4:20-4:30]** Browser opens to `http://localhost:3000` — CogniWatch dashboard loads
- **[4:30-4:40]** Dashboard tour: Quick pan over agent list, telemetry, settings
- **[4:40-4:50]** GitHub page: https://github.com/neo/cogniwatch
  - Stars count, recent commits, contributors
  - "Deploy, contribute, report bugs" text overlay
- **[4:50-5:00]** Final screen:
  - CogniWatch logo
  - "Shodan for AI Agents"
  - Links: GitHub | Documentation | Demo
  - Version: v1.0.0 | Released: March 7, 2026

### Voiceover
> "Ready to see what's in your network?
>
> Deploy CogniWatch in five minutes:
>
> Clone the repository. Run Docker Compose. Open your browser.
>
> That's it. You're now monitoring for AI agents.
>
> CogniWatch is open-source — MIT license. Deploy it on your VPS. Contribute framework signatures. Report bugs. Build integrations.
>
> GitHub: github.com/neo/cogniwatch
>
> Documentation, API reference, deployment guides — all in the repo.
>
> Try it tonight. Scan your network. See what's really there.
>
> CogniWatch. Shodan for AI Agents."

### B-Roll Suggestions
- Developer typing commands (hands on keyboard, terminal on screen)
- Docker whale logo animation
- GitHub star animation (incrementing)
- Fade to black with logo

### Screen Recording Notes
- Record terminal at high resolution (1080p, 60fps)
- Use large, readable fonts for commands
- Speed up Docker pull/start if it takes too long (2x-4x)
- End with smooth fade-out and logo reveal

---

## Production Notes

### Audio
- **Voiceover:** Record in quiet environment. Use pop filter. Aim for -16 LUFS loudness.
- **Background Music:** Minimal, ambient electronic. Low volume (-25dB under voice). Fade out during key explanations.
- **Sound Effects:** Subtle UI interaction sounds (clicks, notifications) — optional, keep minimal.

### Visual Style
- **Color Palette:** Dark theme (matching CogniWatch UI) with teal/cyan accents
- **Fonts:** Monospace for code/terminal (Fira Code, JetBrains Mono). Sans-serif for text (Inter, Roboto).
- **Animations:** Smooth, professional. Avoid flashy effects. Prioritize clarity over style.

### Editing Tips
- Cut on action (e.g., when cursor clicks, transition to result)
- Use J-cuts (audio from next scene starts before visual)
- Keep pace brisk but not rushed
- Add subtle zoom/p Ken Burns effect to static screens

### Accessibility
- **Captions:** Full SRT file with all voiceover + important on-screen text
- **Alt Text:** For thumbnails and social media previews
- **Color Contrast:** Ensure all text is readable (WCAG AA minimum)

### Distribution
- **YouTube:** 1080p, 16:9, add end screen with GitHub link
- **Twitter/X:** 1-minute highlight cut (vertical 9:16 or square 1:1)
- **LinkedIn:** Full 5-minute version (native upload, not YouTube link)
- **GitHub README:** Embed YouTube video or host on GitHub Releases

---

## Optional Add-Ons

### 1-Minute Teaser Cut
- **[0:00-0:10]** Hook: "What if you could see every AI agent?"
- **[0:10-0:25]** Problem: Quick stats (12 agents, 0 known)
- **[0:25-0:40]** Demo: Fast montage of dashboard + detections
- **[0:40-0:50]** CTA: Deploy commands + GitHub link
- **[0:50-1:00]** Logo reveal

### Extended 10-Minute Version
- Add 5-minute section: "Building CogniWatch — Architecture Deep Dive"
- Cover: Scanner design, database schema, API architecture, security hardening
- Target: Developers who want to contribute or audit the code

### Screencast Variant
- Single continuous screen recording (no B-roll)
- Narrated walkthrough of full scan + agent analysis
- More casual, "over-the-shoulder" style
- Good for technical YouTube channels or conference talks

---

## Assets to Create Later

### Animated GIFs (for README, social media)
1. **Dashboard overview** — 5-second loop of agent list populating
2. **Confidence scoring** — Bar chart animating to 94%
3. **Telemetry graphs** — Real-time data flowing

### Thumbnail Designs
- **YouTube:** CogniWatch logo + "Shodan for AI Agents" + dashboard screenshot
- **Twitter:** Bold text "95% Detection Confidence" + agent list closeup
- **LinkedIn:** Professional title card with dashboard background

### Branding Elements
- Logo variations (light/dark mode)
- Social media profile pics (Twitter, GitHub, Discord)
- Banner images (GitHub repo, LinkedIn, Twitter)

---

**Final Note:** Keep it authentic. This isn't hype — it's a real tool solving a real problem. Let the tech speak for itself.
