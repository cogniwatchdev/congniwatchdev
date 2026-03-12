#!/usr/bin/env python3
"""
CogniWatch - Network Agent Discovery Scanner
Scan LAN for AI agent frameworks (OpenClaw, Agent-Zero, PicoClaw, etc.)

INCLUDES: ClawJacked attack detection patterns:
1. WebSocket Anomaly Detection - Detect connection spikes from localhost
2. Auth Brute-Force Detection - Detect repeated failed password attempts
3. Device Registration Auditing - Detect auto-approved device pairings
"""

import socket
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Import ClawJacked detection modules
try:
    from .websocket_monitor import WebSocketMonitor
    from .auth_monitor import AuthMonitor
    from .device_monitor import DeviceMonitor
    from .framework_icons import get_framework_icon
except ImportError:
    from websocket_monitor import WebSocketMonitor
    from auth_monitor import AuthMonitor
    from device_monitor import DeviceMonitor
    try:
        from framework_icons import get_framework_icon
    except ImportError:
        # Fallback icon function
        def get_framework_icon(name):
            return ("🤖", "text-gray", "#8892b0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Known agent framework ports and fingerprints
FRAMEWORK_FINGERPRINTS = {
    "openclaw": {
        "ports": [18789, 18790, 18791],
        "http_paths": ["/", "/status"],
        "websocket_paths": ["/"],
        "response_patterns": ["openclaw", "OpenClaw"],
        "api_endpoint": "http://{host}:{port}/api/sessions",
        "confidence_boost": 0.2  # Bonus if multiple signals match
    },
    "agent-zero": {
        "ports": [50080, 50081],
        "http_paths": ["/", "/api/status"],
        "response_patterns": ["Agent Zero", "agent-zero", "AgentZero"],
        "api_endpoint": "http://{host}:{port}/api/agents",
        "confidence_boost": 0.2
    },
    "crewai": {
        "ports": [8000, 8001, 8080],
        "http_paths": ["/", "/api/crew", "/api/agents"],
        "response_patterns": ["CrewAI", "crewai", "crew.ai"],
        "api_endpoint": "http://{host}:{port}/api/crew",
        "confidence_boost": 0.2
    },
    "autogen": {
        "ports": [8080, 8081, 5000],
        "http_paths": ["/", "/api/status"],
        "response_patterns": ["AutoGen", "autogen", "AG2", "AutoGen Studio"],
        "api_endpoint": "http://{host}:{port}/api/agents",
        "confidence_boost": 0.2
    },
    "langgraph": {
        "ports": [8123, 8000, 8080],
        "http_paths": ["/", "/api/graph", "/api/state"],
        "response_patterns": ["LangGraph", "langgraph", "langchain"],
        "api_endpoint": "http://{host}:{port}/api/graph",
        "confidence_boost": 0.2
    },
    "picoclaw": {
        "ports": [5000, 8080],
        "http_paths": ["/", "/api/agent", "/status"],
        "response_patterns": ["PicoClaw", "pico-claw", "RP2040", "RP2350"],
        "api_endpoint": "http://{host}:{port}/api/info",
        "confidence_boost": 0.2
    },
    "zeroclaw": {
        "ports": [9000, 9001],
        "http_paths": ["/", "/health"],
        "response_patterns": ["ZeroClaw", "zeroclaw", "ZeroClaw Agent"],
        "api_endpoint": "http://{host}:{port}/api/status",
        "confidence_boost": 0.2
    }
}

CONFIDENCE_THRESHOLDS = {
    "confirmed": 0.85,   # ✅ Green badge - multiple signals, very reliable
    "likely": 0.60,      # ⚠️ Yellow badge - some signals, probably correct
    "possible": 0.30,    # ❓ Gray badge - weak signals, maybe correct
    "unknown": 0.0       # ❌ No detection
}

class NetworkScanner:
    """Scan network for AI agent frameworks"""
    
    def __init__(self, network: str = "192.168.0.0/24", timeout: float = 2.0):
        self.network = network
        self.timeout = timeout
        self.discovered_agents = []
        self.scanned_hosts = set()
        
    def scan_port(self, host: str, port: int) -> bool:
        """Check if TCP port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Port scan error for {host}:{port}: {e}")
            return False
    
    def probe_http(self, host: str, port: int, path: str = "/") -> Optional[str]:
        """Probe HTTP endpoint and return response"""
        try:
            url = f"http://{host}:{port}{path}"
            response = requests.get(url, timeout=self.timeout)
            return response.text[:2000]  # First 2KB
        except Exception as e:
            logger.debug(f"HTTP probe failed for {host}:{port}{path}: {e}")
            return None
    
    def probe_websocket(self, host: str, port: int, path: str = "/") -> bool:
        """Check if WebSocket is available"""
        try:
            url = f"ws://{host}:{port}{path}"
            # Simple TCP check - real WS would need handshake
            return self.scan_port(host, port)
        except Exception as e:
            logger.debug(f"WebSocket probe failed for {host}:{port}{path}: {e}")
            return False
    
    def fingerprint_framework(self, host: str, port: int, response: str) -> Optional[str]:
        """Identify framework from HTTP response"""
        if not response:
            return None
            
        response_lower = response.lower()
        
        for framework, fingerprint in FRAMEWORK_FINGERPRINTS.items():
            for pattern in fingerprint["response_patterns"]:
                if pattern.lower() in response_lower:
                    return framework
                    
        return None
    
    def query_framework_api(self, host: str, port: int, framework: str) -> Optional[Dict]:
        """Query framework-specific API for agent info"""
        try:
            fingerprint = FRAMEWORK_FINGERPRINTS.get(framework)
            if not fingerprint:
                return None
                
            api_url = fingerprint["api_endpoint"].format(host=host, port=port)
            response = requests.get(api_url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"API query failed for {framework} at {host}:{port}: {e}")
            
        return None
    
    def scan_host(self, host: str) -> List[Dict]:
        """Scan single host for agent frameworks with confidence scoring"""
        agents = []
        found_ports = {}  # Track which ports we've already identified
        
        logger.info(f"🔍 Scanning host: {host}")
        
        # Scan all known framework ports
        for framework, fingerprint in FRAMEWORK_FINGERPRINTS.items():
            for port in fingerprint["ports"]:
                # Skip if we already found something on this port
                if port in found_ports:
                    continue
                    
                if self.scan_port(host, port):
                    logger.info(f"  ✅ Open port: {host}:{port} (possible {framework})")
                    
                    # Start with base confidence (port match alone = 30%)
                    confidence = 0.30
                    signals = {"port_match": True}
                    evidence = [f"Port {port} matches {framework} default"]
                    
                    # Probe HTTP to confirm
                    http_matched = False
                    for path in fingerprint["http_paths"]:
                        response = self.probe_http(host, port, path)
                        
                        if response:
                            # Check for response patterns
                            pattern_matches = sum(
                                1 for pattern in fingerprint["response_patterns"]
                                if pattern.lower() in response.lower()
                            )
                            
                            if pattern_matches > 0:
                                http_matched = True
                                signals["http_match"] = True
                                evidence.append(f"Found {pattern_matches}/{len(fingerprint['response_patterns'])} response patterns")
                                
                                # Each pattern match adds 0.15-0.25 confidence
                                confidence += min(0.15 * pattern_matches, 0.40)
                                
                                # Bonus if multiple patterns match
                                if pattern_matches >= 2:
                                    confidence += fingerprint.get("confidence_boost", 0.15)
                                    evidence.append("Multiple patterns matched (+boost)")
                                
                                break
                    
                    # Try API endpoint
                    api_matched = False
                    try:
                        api_url = fingerprint["api_endpoint"].format(host=host, port=port)
                        api_response = requests.get(api_url, timeout=self.timeout)
                        
                        if api_response.status_code == 200:
                            try:
                                data = api_response.json()
                                api_matched = True
                                signals["api_match"] = True
                                evidence.append(f"API endpoint {fingerprint['api_endpoint']} returned valid JSON")
                                confidence += 0.25
                                
                                # Check for framework-specific API signatures
                                if framework == "openclaw" and ("sessions" in data or "sessionKey" in str(data)):
                                    confidence += 0.15
                                    evidence.append("API response contains OpenClaw-specific fields")
                                elif framework == "crewai" and ("crew" in str(data).lower() or "agents" in str(data).lower()):
                                    confidence += 0.15
                                    evidence.append("API response contains CrewAI-specific fields")
                                elif framework == "autogen" and ("agents" in str(data).lower() or "conversations" in str(data).lower()):
                                    confidence += 0.15
                                    evidence.append("API response contains AutoGen-specific fields")
                                    
                            except json.JSONDecodeError:
                                # API returned non-JSON (still a valid signal)
                                signals["api_exists"] = True
                                evidence.append(f"API endpoint exists (non-JSON response)")
                                confidence += 0.10
                                
                    except Exception:
                        pass  # API not available
                    
                    # Cap confidence at 0.99
                    confidence = min(confidence, 0.99)
                    
                    # Determine confidence badge
                    if confidence >= CONFIDENCE_THRESHOLDS["confirmed"]:
                        badge = "confirmed"
                        badge_icon = "✅"
                    elif confidence >= CONFIDENCE_THRESHOLDS["likely"]:
                        badge = "likely"
                        badge_icon = "⚠️"
                    elif confidence >= CONFIDENCE_THRESHOLDS["possible"]:
                        badge = "possible"
                        badge_icon = "❓"
                    else:
                        badge = "unknown"
                        badge_icon = "❌"
                        continue  # Skip unknown detections
                    
                    logger.info(f"  {badge_icon} {badge.upper()}: {framework} at {host}:{port} ({confidence:.0%})")
                    
                    # Determine final framework name
                    detected_framework = framework
                    
                    # Special case: port 9000 is CogniWatch itself
                    if port == 9000 and "cogniwatch" in str(evidence).lower():
                        logger.info(f"  ℹ️  CogniWatch instance detected (skipping)")
                        continue
                    
                    # Get framework icon and color
                    icon_info = get_framework_icon(detected_framework)
                    
                    agent = {
                        "host": host,
                        "port": port,
                        "framework": detected_framework,
                        "detected_at": datetime.now().isoformat(),
                        "confidence": confidence,
                        "confidence_badge": badge,
                        "signals": signals,
                        "evidence": evidence,
                        "status": "active",
                        "icon": icon_info[0],
                        "icon_color": icon_info[2],
                        "icon_class": icon_info[1]
                    }
                    
                    agents.append(agent)
                    self.discovered_agents.append(agent)
                    found_ports[port] = {
                        "framework": detected_framework,
                        "confidence": confidence
                    }
                    
                    # Don't scan other paths for this port
                    break
                                
        return agents
    
    def get_network_hosts(self) -> List[str]:
        """Generate list of hosts to scan from network CIDR"""
        hosts = []
        
        if "/" in self.network:
            # Parse CIDR notation (e.g., 192.168.0.0/24)
            base, prefix = self.network.split("/")
            prefix = int(prefix)
            
            # Calculate number of hosts
            num_hosts = 2 ** (32 - prefix)
            
            # Parse base IP
            base_parts = [int(p) for p in base.split(".")]
            
            # For /24 networks, scan .1 to .254
            if prefix == 24:
                for i in range(1, 255):
                    host = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{i}"
                    hosts.append(host)
                    
        else:
            # Single IP
            hosts.append(self.network)
            
        return hosts
    
    def scan_network(self, parallel: int = 100) -> List[Dict]:
        """Scan entire network for agents using parallel scanning"""
        logger.info(f"🚀 Starting network scan: {self.network}")
        logger.info(f"⚡ Parallel threads: {parallel}")
        logger.info(f"📊 Scanning frameworks: {list(FRAMEWORK_FINGERPRINTS.keys())}")
        
        hosts = self.get_network_hosts()
        logger.info(f"🔍 Will scan {len(hosts)} hosts")
        
        start_time = datetime.now()
        
        # Parallel scan using ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def scan_single_host(host):
            try:
                return self.scan_host(host)
            except Exception as e:
                logger.debug(f"Error scanning {host}: {e}")
                return []
        
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            # Submit all hosts
            future_to_host = {executor.submit(scan_single_host, host): host for host in hosts}
            
            # Collect results as they complete
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    self.scanned_hosts.add(host)
                    
                    # Progress update every 25 hosts
                    if len(self.scanned_hosts) % 25 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = len(self.scanned_hosts) / elapsed if elapsed > 0 else 0
                        logger.info(f"📈 Progress: {len(self.scanned_hosts)}/{len(hosts)} hosts ({rate:.1f} hosts/sec) - {len(self.discovered_agents)} agents found")
                        
                except Exception as e:
                    logger.debug(f"Error processing result for {host}: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Scan complete!")
        logger.info(f"📈 Scanned {len(self.scanned_hosts)} hosts in {elapsed:.1f}s ({len(self.scanned_hosts)/elapsed:.1f} hosts/sec)")
        logger.info(f"🎯 Discovered {len(self.discovered_agents)} agents")
        
        # Apply correlation engine to merge gateway+backend on same host
        logger.info(f"🔗 Running correlation engine to merge related services...")
        try:
            from .correlation_engine import correlate_detections
        except ImportError:
            from correlation_engine import correlate_detections
        
        correlated_agents = correlate_detections(self.discovered_agents)
        
        logger.info(f"📊 Correlation result: {len(self.discovered_agents)} raw → {len(correlated_agents)} correlated agents")
        
        return correlated_agents
    
    def run_clawjacked_detection(self, hosts: List[str] = None) -> Dict:
        """
        Run all ClawJacked attack detection patterns
        
        Returns:
            Dict with detection results from all three monitors:
            - websocket_anomalies: List of WebSocket anomaly detections
            - auth_brute_force: List of auth brute-force detections
            - device_registrations: List of suspicious device registrations
            - overall_risk: CRITICAL/HIGH/MEDIUM/LOW
            - clawjacked_confidence: Overall confidence score
        """
        if hosts is None:
            hosts = ["127.0.0.1"]
        
        logger.info(f"🔒 Running ClawJacked attack detection on {len(hosts)} hosts...")
        
        # Initialize monitors
        ws_monitor = WebSocketMonitor()
        auth_monitor = AuthMonitor()
        device_monitor = DeviceMonitor()
        
        # Run all detection modules
        websocket_results = ws_monitor.scan_all_gateways(hosts)
        auth_results = auth_monitor.scan_all_gateways(hosts)
        device_results = device_monitor.scan_all_gateways(hosts)
        
        # Aggregate results
        detections = {
            "websocket_anomalies": [],
            "auth_brute_force": [],
            "device_registrations": [],
            "overall_risk": "LOW",
            "clawjacked_confidence": 0.0,
            "summary": {
                "websocket_alerts": 0,
                "auth_alerts": 0,
                "device_alerts": 0,
                "total_alerts": 0
            }
        }
        
        # Process WebSocket anomalies (HIGH confidence: 0.8)
        for result in websocket_results:
            if result.get("anomaly_detected"):
                detections["websocket_anomalies"].append({
                    "host": result["host"],
                    "port": result["port"],
                    "connections_per_min": result["connection_count"],
                    "confidence": 0.8,
                    "severity": "HIGH",
                    "evidence": result["evidence"],
                    "recommendation": result["recommendation"]
                })
                detections["summary"]["websocket_alerts"] += 1
        
        # Process Auth brute-force (CRITICAL confidence: 0.95)
        for result in auth_results:
            if result.get("brute_force_detected"):
                detections["auth_brute_force"].append({
                    "host": result["host"],
                    "port": result["port"],
                    "failed_attempts": result["failure_count"],
                    "confidence": 0.95,
                    "severity": "CRITICAL",
                    "evidence": result["evidence"],
                    "recommendation": result["recommendation"],
                    "auto_block_available": result.get("auto_block_available", False)
                })
                detections["summary"]["auth_alerts"] += 1
        
        # Process device registrations (HIGH confidence: 0.85)
        for result in device_results:
            if result.get("suspicious_registrations"):
                detections["device_registrations"].append({
                    "host": result["host"],
                    "port": result["port"],
                    "suspicious_count": len(result["suspicious_registrations"]),
                    "auto_approved_count": result["auto_approved_count"],
                    "localhost_count": result["localhost_registrations"],
                    "confidence": 0.85,
                    "severity": result["severity"],
                    "evidence": result["evidence"],
                    "recommendation": result["recommendation"],
                    "suspicious_devices": result["suspicious_registrations"]
                })
                detections["summary"]["device_alerts"] += 1
        
        # Calculate total alerts and overall risk
        detections["summary"]["total_alerts"] = (
            detections["summary"]["websocket_alerts"] +
            detections["summary"]["auth_alerts"] +
            detections["summary"]["device_alerts"]
        )
        
        # Determine overall risk level
        if detections["summary"]["auth_alerts"] > 0:
            detections["overall_risk"] = "CRITICAL"
            detections["clawjacked_confidence"] = 0.95
        elif detections["summary"]["device_alerts"] > 0:
            detections["overall_risk"] = "HIGH"
            detections["clawjacked_confidence"] = 0.85
        elif detections["summary"]["websocket_alerts"] > 0:
            detections["overall_risk"] = "HIGH"
            detections["clawjacked_confidence"] = 0.8
        else:
            detections["overall_risk"] = "LOW"
            detections["clawjacked_confidence"] = 0.1
        
        logger.info(f"🔒 ClawJacked detection complete: {detections['summary']['total_alerts']} alerts found")
        logger.info(f"   Overall risk: {detections['overall_risk']} (confidence: {detections['clawjacked_confidence']:.0%})")
        
        return detections


def main():
    """Test network scanner with ClawJacked detection"""
    print("\n👁️ CogniWatch Network Agent Scanner\n")
    print("Scanning for AI agent frameworks...\n")
    
    scanner = NetworkScanner(network="192.168.0.0/24", timeout=1.0)
    agents = scanner.scan_network()
    
    if agents:
        print(f"\n🎉 DISCOVERED {len(agents)} AGENTS:\n")
        
        for agent in agents:
            # Check if this is a correlated agent
            if 'type' in agent:  # Correlated agent schema
                print(f"┌─────────────────────────────────────────────")
                print(f"│ 🤖 Agent Type: {agent['type'].upper()}")
                print(f"│ 📍 Host: {agent['host']}")
                print(f"│ 📡 Confidence: {agent['confidence']:.0%} ({agent['confidence_badge']})")
                
                if agent.get('gateway'):
                    gw = agent['gateway']
                    print(f"│ 🚪 Gateway: {gw['framework']} (port {gw['port']})")
                
                if agent.get('backend'):
                    be = agent['backend']
                    print(f"│ 🧠 Backend: {be['framework']} (port {be['port']})")
                
                print(f"└─────────────────────────────────────────────\n")
            else:  # Legacy format
                print(f"┌─────────────────────────────────────────────")
                print(f"│ 🤖 Framework: {agent['framework'].upper()}")
                print(f"│ 📍 Location: {agent['host']}:{agent['port']}")
                print(f"│ ⏰ Detected: {agent['detected_at']}")
                print(f"│ 📡 Status: {agent['status']}")
                if agent.get('api_info'):
                    print(f"│ 📊 API Info: {json.dumps(agent['api_info'], indent=2)[:200]}")
                print(f"└─────────────────────────────────────────────\n")
    else:
        print("\n⚠️ No agents discovered on network")
        print("Possible reasons:")
        print("  - No agent frameworks running")
        print("  - Firewalls blocking scans")
        print("  - Wrong network range")
        print("  - Agents using non-standard ports")
    
    # Run ClawJacked attack detection
    print("\n" + "="*60)
    print("🔒 CLAWJACKED ATTACK DETECTION\n")
    
    # Test against known gateway ports
    gateway_hosts = ["127.0.0.1"]
    clawjacked_results = scanner.run_clawjacked_detection(gateway_hosts)
    
    if clawjacked_results["summary"]["total_alerts"] > 0:
        print(f"\n🚨 CLAWJACKED DETECTION ALERTS: {clawjacked_results['summary']['total_alerts']}\n")
        print(f"⚠️  Overall Risk: {clawjacked_results['overall_risk']}")
        print(f"🎯 Confidence: {clawjacked_results['clawjacked_confidence']:.0%}\n")
        
        # Show WebSocket anomalies
        if clawjacked_results["websocket_anomalies"]:
            print(f"📡 WEBSOCKET ANOMALIES ({len(clawjacked_results['websocket_anomalies'])}):\n")
            for alert in clawjacked_results["websocket_anomalies"]:
                print(f"┌─────────────────────────────────────────────")
                print(f"│ 🚪 {alert['host']}:{alert['port']}")
                print(f"│ 📊 Connections: {alert['connections_per_min']}/min")
                print(f"│ 🎯 Confidence: {alert['confidence']:.0%}")
                print(f"│ 💡 {alert['recommendation']}")
                print(f"└─────────────────────────────────────────────\n")
        
        # Show Auth brute-force
        if clawjacked_results["auth_brute_force"]:
            print(f"🔑 AUTH BRUTE-FORCE ({len(clawjacked_results['auth_brute_force'])}):\n")
            for alert in clawjacked_results["auth_brute_force"]:
                print(f"┌─────────────────────────────────────────────")
                print(f"│ 🚪 {alert['host']}:{alert['port']}")
                print(f"│ ❌ Failed attempts: {alert['failed_attempts']}")
                print(f"│ 🎯 Confidence: {alert['confidence']:.0%}")
                print(f"│ 🛡️  Auto-block: {'✅ Available' if alert['auto_block_available'] else '❌ Not available'}")
                print(f"│ 💡 {alert['recommendation']}")
                print(f"└─────────────────────────────────────────────\n")
        
        # Show device registration issues
        if clawjacked_results["device_registrations"]:
            print(f"📱 DEVICE REGISTRATION ISSUES ({len(clawjacked_results['device_registrations'])}):\n")
            for alert in clawjacked_results["device_registrations"]:
                print(f"┌─────────────────────────────────────────────")
                print(f"│ 🚪 {alert['host']}:{alert['port']}")
                print(f"│ 📊 Suspicious: {alert['suspicious_count']}")
                print(f"│ ✅ Auto-approved: {alert['auto_approved_count']}")
                print(f"│ 🏠 Localhost: {alert['localhost_count']}")
                print(f"│ 🎯 Confidence: {alert['confidence']:.0%}")
                print(f"│ 💡 {alert['recommendation']}")
                print(f"└─────────────────────────────────────────────\n")
    else:
        print("\n✅ No ClawJacked attack patterns detected")
        print(f"   Risk level: {clawjacked_results['overall_risk']}")
    
    # Save results with ClawJacked detections included
    output_file = "discovered_agents.json"
    with open(output_file, "w") as f:
        json.dump({
            "scan_time": datetime.now().isoformat(),
            "network": scanner.network,
            "hosts_scanned": len(scanner.scanned_hosts),
            "agents_found": len(agents),
            "agents": agents,
            "clawjacked_detection": clawjacked_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
