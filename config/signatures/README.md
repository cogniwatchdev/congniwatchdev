# Signature Configuration Reference

This directory contains framework signature configurations for CogniWatch's detection engine.

## Current Signatures (10 frameworks)

### ✅ Tier 1 (High Priority)
1. **openclaw.json** — OpenClaw ecosystem (OpenClaw, NanoClaw, PicoClaw, ZeroClaw, IronClaw)
2. **agent-zero.json** — Agent-Zero self-hosted assistant
3. **langgraph.json** — LangGraph (LangChain's agent platform)
4. **autogen-studio.json** — Microsoft AutoGen Studio

### ✅ Tier 2 (Medium Priority)
5. **crewai.json** — CrewAI role-based orchestration
6. **google-adk.json** — Google Agent Development Kit
7. **pydantic-ai.json** — Pydantic AI production framework
8. **semantic-kernel.json** — Microsoft Semantic Kernel

### ✅ Tier 3 (Emerging/Niche)
9. **smolagents.json** — Hugging Face Smolagents
10. **strands-agents.json** — AWS Strands Agents

## Port Summary

| Port | Framework(s) | Tier |
|------|-------------|------|
| 18789 | OpenClaw (all variants) | 1 |
| 8787 | OpenClaw (legacy) | 1 |
| 50001 | Agent-Zero (default) | 1 |
| 50080 | Agent-Zero (alternate) | 1 |
| 8123 | LangGraph | 1 |
| 8080 | AutoGen Studio, Strands | 1/3 |
| 8000-8004 | Google ADK, Microsoft AF | 2 |
| 5005 | Rasa | 3 |

## Confidence Scoring

Each signature includes confidence weights:

```json
"confidence": {
  "port_match": 0.30,        // 30% for port detection
  "http_pattern": 0.15,      // 15% for HTTP header/body match
  "http_multiple": 0.10,     // 10% bonus for multiple HTTP matches
  "api_validated": 0.25,     // 25% for confirmed API response
  "websocket_match": 0.15,   // 15% for WebSocket protocol
  "framework_specific": 0.05, // 5% for unique indicators (mDNS, etc.)
  "threshold_confirmed": 0.85, // ≥85% = "Confirmed"
  "threshold_likely": 0.60,    // ≥60% = "Likely"
  "threshold_possible": 0.30   // ≥30% = "Possible"
}
```

## Adding New Signatures

See [`docs/FRAMEWORK-SIGNATURES.md`](../../docs/FRAMEWORK-SIGNATURES.md) for:
- JSON schema reference
- Testing/validation process
- GitHub PR template

## Last Updated

March 7, 2026 — 10 signatures covering 23+ frameworks
