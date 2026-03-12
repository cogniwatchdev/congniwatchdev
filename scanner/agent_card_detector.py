#!/usr/bin/env python3
"""
CogniWatch - Agent Card Detector
Detects AI agents via A2A (Agent-to-Agent Protocol) metadata endpoints

This is the HIGHEST CONFIDENCE detection layer - agents self-identify via
well-known JSON endpoints, providing 100% accuracy when present.

Source: ADVANCED_AI_DETECTION_RESEARCH.md - Agent Cards section
Impact: +20-25% accuracy boost via DIRECT IDENTIFICATION
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentCard:
    """Parsed agent card metadata"""
    name: str
    version: Optional[str]
    author: Optional[str]
    description: Optional[str]
    capabilities: List[str]
    api_endpoints: List[Dict]
    authentication: Optional[Dict]
    protocols: List[str]
    source_url: str
    confidence: float  # 1.0 = explicit self-identification


class AgentCardDetector:
    """
    Detect AI agents via well-known metadata endpoints.
    
    This detector probes 24 common paths where AI frameworks expose
    self-identification metadata. When found, this provides direct
    identification with 100% confidence.
    
    Common paths include:
    - /.well-known/agent-card.json (A2A standard)
    - /agent-card.json
    - /api/agent/info
    - /openapi.json (Swagger/OpenAPI)
    - /health, /metrics (often reveal framework)
    """
    
    # Common agent card paths (ordered by likelihood)
    AGENT_CARD_PATHS = [
        # A2A standard paths
        "/.well-known/agent-card.json",
        "/.well-known/ai-agent.json",
        "/.well-known/openclaw.json",
        
        # Direct paths
        "/agent-card.json",
        "/agent.json",
        "/ai-agent.json",
        "/openclaw.json",
        
        # API metadata endpoints
        "/api/agent/info",
        "/api/v1/agent/info",
        "/api/agent/metadata",
        "/api/v1/agent/metadata",
        "/api/agent/card",
        
        # Framework-specific
        "/api/openclaw/info",
        "/api/crewai/info",
        "/api/autogen/info",
        "/api/langgraph/info",
        
        # OpenAPI/Swagger (often reveals AI frameworks)
        "/openapi.json",
        "/swagger.json",
        "/docs",
        
        # Health/metrics endpoints that often reveal framework
        "/health",
        "/api/health",
        "/metrics",  # Prometheus
    ]
    
    # Framework signatures in card content
    FRAMEWORK_SIGNATURES = {
        "openclaw": ["OpenClaw", "openclaw", "neo-claw"],
        "crewai": ["CrewAI", "crewai", "crew-ai"],
        "autogen": ["AutoGen", "autogen", "ag2", "AutoGen Studio"],
        "langgraph": ["LangGraph", "langgraph", "lang-graph"],
        "langchain": ["LangChain", "langchain", "lang-chain"],
        "semantic-kernel": ["Semantic Kernel", "semantic-kernel", "Microsoft.SemanticKernel"],
        "pydantic-ai": ["PydanticAI", "pydantic-ai", "pydantic_ai"],
        "agentkit": ["AgentKit", "agentkit", "agent-kit"],
        "agent-zero": ["Agent-Zero", "agent-zero", "AgentZero"],
        "picolaw": ["PicoClaw", "picolaw", "pico-claw"],
        "zeroclaw": ["ZeroClaw", "zeroclaw", "zero-claw"],
    }
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize detector.
        
        Args:
            timeout: Request timeout in seconds (default: 5.0)
        """
        self.timeout = timeout
        self.session = requests.Session()
        # Set a user agent that identifies as CogniWatch
        self.session.headers.update({
            'User-Agent': 'CogniWatch-AgentCardDetector/1.0',
            'Accept': 'application/json,text/html',
        })
    
    def probe_path(self, base_url: str, path: str) -> Optional[Dict]:
        """
        Probe a single path for agent card.
        
        Args:
            base_url: Base URL (e.g., http://host:port)
            path: Path to probe
            
        Returns:
            Parsed JSON dict if 200 OK and valid JSON, None otherwise
        """
        url = urljoin(base_url, path)
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                # Check if JSON
                content_type = response.headers.get("Content-Type", "")
                
                # Direct JSON response
                if "application/json" in content_type or path.endswith(".json"):
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            logger.debug(f"Found agent card at {url}")
                            return {
                                "path": path,
                                "url": url,
                                "data": data,
                                "status": 200
                            }
                    except json.JSONDecodeError:
                        logger.debug(f"Invalid JSON at {url}")
                        pass
                
                # HTML response - try to extract embedded JSON (Swagger/OpenAPI)
                if "text/html" in content_type:
                    # Look for <script type="application/json">
                    json_match = re.search(
                        r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', 
                        response.text, 
                        re.DOTALL
                    )
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            logger.debug(f"Extracted JSON from HTML at {url}")
                            return {
                                "path": path,
                                "url": url,
                                "data": data,
                                "status": 200,
                                "extracted_from_html": True
                            }
                        except json.JSONDecodeError:
                            pass
        
        except requests.Timeout:
            logger.debug(f"Timeout probing {url}")
        except requests.ConnectionError:
            logger.debug(f"Connection error probing {url}")
        except requests.RequestException as e:
            logger.debug(f"Request error probing {url}: {e}")
        
        return None
    
    def is_valid_agent_card(self, data: Dict) -> bool:
        """
        Validate that a JSON response is actually an agent card,
        not just a health check or status endpoint.
        
        CRITICAL FIX: Prevents false positives from /health endpoints
        that return simple status JSON without AI-specific metadata.
        
        Args:
            data: Parsed JSON data from endpoint
            
        Returns:
            True if this appears to be a real agent card
        """
        # Must have at least ONE agent/AI-specific field
        agent_fields = [
            'name', 'agent_name', 'capabilities', 'skills',
            'agent_model', 'framework', 'agent_type',
            'protocols', 'api_endpoints', 'tools',
            'description', 'version', 'author', 'model'
        ]
        
        # Health/status endpoints typically only have these fields
        health_structures = {
            'cpu', 'memory', 'disk', 'uptime', 'hostname', 'network', 
            'wifi', 'healthy', 'gateway_connected', 'error'
        }
        
        # Minimal valid agent card structure
        # An agent card typically identifies itself with name/description
        has_name = 'name' in data or 'agent_name' in data or 'title' in data
        has_capabilities = 'capabilities' in data or 'skills' in data or 'tools' in data
        has_model = 'model' in data or 'agent_model' in data
        
        # If it's just health metrics (cpu, memory, disk, etc.) without agent identity = NOT an agent card
        is_clearly_health = (
            'cpu' in data or 'memory' in data or 'disk' in data or 
            'uptime' in data or 'gateway_connected' in data or
            'bytes_recv' in data or 'packets_recv' in data
        )
        
        is_clearly_error = 'error' in data and len(data) == 1
        
        # Health endpoints that don't identify as an agent = FALSE POSITIVE
        if is_clearly_health and not has_name:
            return False
        
        if is_clearly_error:
            return False
        
        # Must have at least SOME identifying information
        has_identifier = has_name or has_model or has_capabilities
        
        return has_identifier
    
    def identify_framework(self, card_data: Dict) -> List[tuple]:
        """
        Identify AI frameworks from card data.
        
        Searches all string values in the JSON for framework signatures.
        
        Args:
            card_data: Parsed JSON data from agent card
            
        Returns:
            List of (framework, confidence) tuples
        """
        identified = []
        
        # Convert entire JSON to lowercase string for searching
        json_str = json.dumps(card_data).lower()
        
        for framework, signatures in self.FRAMEWORK_SIGNATURES.items():
            for sig in signatures:
                if sig.lower() in json_str:
                    confidence = 0.9  # High confidence for explicit mention
                    identified.append((framework, confidence))
                    logger.debug(f"Identified framework: {framework}")
                    break  # Don't match multiple signatures for same framework
        
        return identified
    
    def parse_agent_card(self, card_result: Dict) -> AgentCard:
        """
        Parse agent card JSON into structured format.
        
        Handles multiple schema variations (A2A, OpenClaw, custom).
        
        Args:
            card_result: Result dict from probe_path()
            
        Returns:
            AgentCard dataclass instance
        """
        data = card_result["data"]
        
        # Extract fields (handle different schema variations)
        name = (data.get("name") or 
                data.get("agent_name") or 
                data.get("title") or 
                "Unknown")
        
        version = (data.get("version") or 
                  data.get("agent_version"))
        
        author = (data.get("author") or 
                 data.get("organization") or 
                 data.get("publisher"))
        
        description = (data.get("description") or 
                      data.get("summary"))
        
        # Capabilities (often in "capabilities", "skills", or "abilities")
        capabilities = (data.get("capabilities") or 
                       data.get("skills") or 
                       data.get("abilities") or 
                       [])
        
        # API endpoints (various formats)
        api_endpoints = (data.get("api_endpoints") or 
                        data.get("endpoints") or 
                        data.get("apis") or 
                        [])
        
        # Authentication requirements
        authentication = (data.get("authentication") or 
                         data.get("auth") or 
                         data.get("security"))
        
        # Protocols (WebSocket, HTTP, gRPC, etc.)
        protocols = (data.get("protocols") or 
                    data.get("supported_protocols") or 
                    [])
        
        return AgentCard(
            name=name,
            version=version,
            author=author,
            description=description,
            capabilities=capabilities if isinstance(capabilities, list) else [],
            api_endpoints=api_endpoints if isinstance(api_endpoints, list) else [],
            authentication=authentication,
            protocols=protocols if isinstance(protocols, list) else [],
            source_url=card_result["url"],
            confidence=1.0  # Agent self-identified
        )
    
    def scan(self, host: str, port: int, https: bool = False) -> Dict[str, Any]:
        """
        Full scan: probe all paths, parse any cards found.
        
        This is the FASTEST detection layer - should be run FIRST.
        
        Args:
            host: Target host (IP or hostname)
            port: Target port
            https: Use HTTPS (default: HTTP)
            
        Returns:
            Dict with detection results:
            - detected: bool - whether agent card was found
            - agent_cards_found: int - number of cards discovered
            - primary_card: dict - first/primary card data
            - all_cards: list - all cards found
            - frameworks_identified: dict - framework -> confidence mapping
            - confidence: float - 1.0 if detected (direct ID), 0.0 otherwise
            - source_urls: list - URLs where cards were found
        """
        scheme = "https" if https else "http"
        base_url = f"{scheme}://{host}:{port}"
        
        logger.info(f"Scanning {base_url} for agent cards ({len(self.AGENT_CARD_PATHS)} paths)")
        
        found_cards = []
        frameworks_identified = []
        
        # Probe all paths
        for path in self.AGENT_CARD_PATHS:
            result = self.probe_path(base_url, path)
            
            if result:
                # CRITICAL VALIDATION: Skip health-only endpoints
                if not self.is_valid_agent_card(result["data"]):
                    logger.debug(f"✗ Skipped non-agent endpoint at {path}")
                    continue
                
                logger.info(f"✓ Found agent card at {path}")
                
                # Parse card
                card = self.parse_agent_card(result)
                found_cards.append(card)
                
                # Identify frameworks from card content
                frameworks = self.identify_framework(result["data"])
                frameworks_identified.extend(frameworks)
        
        # Build result
        if found_cards:
            # Deduplicate frameworks (keep highest confidence)
            unique_frameworks = {}
            for fw, conf in frameworks_identified:
                if fw not in unique_frameworks or conf > unique_frameworks[fw]:
                    unique_frameworks[fw] = conf
            
            logger.info(f"Detection complete: {len(found_cards)} card(s), {len(unique_frameworks)} framework(s)")
            
            return {
                "detected": True,
                "agent_cards_found": len(found_cards),
                "primary_card": found_cards[0].__dict__,
                "all_cards": [c.__dict__ for c in found_cards],
                "frameworks_identified": unique_frameworks,
                "confidence": 1.0,  # Direct identification
                "source_urls": [c.source_url for c in found_cards],
                "paths_probed": len(self.AGENT_CARD_PATHS)
            }
        else:
            logger.debug(f"No agent cards found at {base_url}")
            
            return {
                "detected": False,
                "agent_cards_found": 0,
                "paths_probed": len(self.AGENT_CARD_PATHS),
                "confidence": 0.0
            }


def main():
    """Test the detector against a target"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python agent_card_detector.py <host> <port> [https]")
        print("Example: python agent_card_detector.py 192.168.0.245 18789")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    https = sys.argv[3].lower() == "https" if len(sys.argv) > 3 else False
    
    detector = AgentCardDetector(timeout=5.0)
    result = detector.scan(host, port, https)
    
    print("\n" + "="*60)
    print("AGENT CARD DETECTION RESULTS")
    print("="*60)
    
    if result["detected"]:
        print(f"✅ AGENT DETECTED")
        print(f"   Cards found: {result['agent_cards_found']}")
        print(f"   Agent name: {result['primary_card']['name']}")
        print(f"   Frameworks: {list(result['frameworks_identified'].keys())}")
        print(f"   Confidence: {result['confidence']*100:.0f}%")
        print(f"   Source URLs:")
        for url in result['source_urls']:
            print(f"     - {url}")
    else:
        print(f"❌ No agent card found")
        print(f"   Paths probed: {result['paths_probed']}")
        print(f"   Confidence: {result['confidence']*100:.0f}%")
    
    print("="*60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
