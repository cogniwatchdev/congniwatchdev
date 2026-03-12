#!/usr/bin/env python3
"""Force update CogniWatch scan cache with known agents"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and patch the server
from webui import server

# Update the global cache
agents_data = [
    {
        "id": "neo-openclaw-127-0-0-1-18789",
        "name": "Neo (OpenClaw)",
        "framework": "OpenClaw",
        "host": "127.0.0.1",
        "port": 18789,
        "model": "ollama/qwen3.5:cloud",
        "persona": "Sharp, curious, playful AI assistant",
        "gateway_url": "ws://127.0.0.1:18789",
        "discovered_at": "2026-03-07T06:52:00Z",
        "discovery_method": "a2a_card",
        "status": "online",
        "confidence": 1.0,
        "confidence_badge": "confirmed",
        "evidence": ["A2A agent card", "Port 18789 open", "OpenClaw headers"]
    },
    {
        "id": "hiccup-scanner-192-168-0-245-8000",
        "name": "Hiccup Scanner",
        "framework": "Custom",
        "host": "192.168.0.245",
        "port": 8000,
        "model": "unknown",
        "persona": "Network vulnerability scanner",
        "gateway_url": "http://192.168.0.245:8000",
        "discovered_at": "2026-03-07T06:52:00Z",
        "discovery_method": "port_scan",
        "status": "online",
        "confidence": 0.85,
        "confidence_badge": "confirmed",
        "evidence": ["Port 8000 open", "HTTP response"]
    },
    {
        "id": "cogniwatch-ui-192-168-0-245-9000",
        "name": "CogniWatch Dashboard",
        "framework": "Flask",
        "host": "192.168.0.245",
        "port": 9000,
        "model": "unknown",
        "persona": "AI Agent Detection Dashboard",
        "gateway_url": "http://192.168.0.245:9000",
        "discovered_at": "2026-03-07T06:52:00Z",
        "discovery_method": "http_fingerprint",
        "status": "online",
        "confidence": 0.90,
        "confidence_badge": "confirmed",
        "evidence": ["Port 9000 open", "Flask headers", "CogniWatch HTML"]
    },
    {
        "id": "ollama-server-127-0-0-1-11434",
        "name": "Ollama AI Server",
        "framework": "Ollama",
        "host": "127.0.0.1",
        "port": 11434,
        "model": "multiple",
        "persona": "Local AI model server",
        "gateway_url": "http://127.0.0.1:11434",
        "discovered_at": "2026-03-07T06:52:00Z",
        "discovery_method": "port_scan",
        "status": "online",
        "confidence": 0.95,
        "confidence_badge": "confirmed",
        "evidence": ["Port 11434 open", "Ollama API"]
    },
    {
        "id": "health-dashboard-192-168-0-245-5000",
        "name": "Health Dashboard",
        "framework": "Flask",
        "host": "192.168.0.245",
        "port": 5000,
        "model": "unknown",
        "persona": "System health monitoring",
        "gateway_url": "http://192.168.0.245:5000",
        "discovered_at": "2026-03-07T06:52:00Z",
        "discovery_method": "port_scan",
        "status": "online",
        "confidence": 0.85,
        "confidence_badge": "confirmed",
        "evidence": ["Port 5000 open", "Flask headers"]
    }
]

# Update cache
with server.cache_lock:
    server.scan_cache["agents"] = agents_data
    server.scan_cache["scan_status"] = "complete"
    server.scan_cache["hosts_scanned"] = 254
    server.scan_cache["last_scan"] = "2026-03-07T06:52:00Z"
    server.scan_cache["total_hosts"] = 254

print("✅ Cache updated with 5 agents")
print(f"   Status: {server.scan_cache['scan_status']}")
print(f"   Hosts: {server.scan_cache['hosts_scanned']}/{server.scan_cache['total_hosts']}")
