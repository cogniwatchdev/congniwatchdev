#!/usr/bin/env python3
"""
CogniWatch - Service Correlation Engine

Identifies and merges related services (gateway + backend) on the same host
into single agent entities to avoid duplicate counting and improve accuracy.

Correlation Logic:
- Host with Gateway (18789) + LLM Backend (11434) → Single correlated agent
- Host with only LLM Backend → Backend service only
- Host with only Gateway → Gateway without known backend

Reference: DETECTION_TAXONOMY.md correlation rules
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Service port definitions for correlation
GATEWAY_PORTS = {
    18789: "OpenClaw",
    18790: "OpenClaw",
    18791: "OpenClaw",
    50080: "Agent-Zero",
    50081: "Agent-Zero",
}

BACKEND_PORTS = {
    11434: "Ollama",
    5000: "General LLM",
    8000: "General LLM",
    8080: "General LLM",
    11435: "Ollama",
}

# Framework compatibility matrix (which backends work with which gateways)
GATEWAY_BACKEND_COMPAT = {
    "OpenClaw": ["Ollama", "General LLM"],
    "Agent-Zero": ["Ollama", "General LLM"],
    "CrewAI": ["Ollama", "General LLM"],
    "AutoGen": ["Ollama", "General LLM"],
    "LangGraph": ["Ollama", "General LLM"],
}


@dataclass
class ServiceDetection:
    """Single service detection from scanner"""
    host: str
    port: int
    framework: str
    confidence: float
    detection_type: str  # 'gateway' or 'backend'
    raw_detection: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'port': self.port,
            'framework': self.framework,
            'confidence': self.confidence,
            'detection_type': self.detection_type,
        }


@dataclass
class CorrelatedAgent:
    """Correlated agent entity (gateway + optional backend)"""
    id: str
    host: str
    type: str  # 'agent_gateway', 'backend_only', 'gateway_only'
    confidence: float
    confidence_badge: str  # 'confirmed', 'likely', 'possible', 'unknown'
    
    # Gateway info
    gateway: Optional[Dict[str, Any]] = None
    
    # Backend info
    backend: Optional[Dict[str, Any]] = None
    
    # Metadata
    correlation_source: str = "correlation_engine"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            'id': self.id,
            'host': self.host,
            'type': self.type,
            'confidence': self.confidence,
            'confidence_badge': self.confidence_badge,
            'timestamp': self.timestamp,
            'correlation_source': self.correlation_source,
        }
        
        if self.gateway:
            result['gateway'] = self.gateway
            
        if self.backend:
            result['backend'] = self.backend
            
        return result


class CorrelationEngine:
    """
    Correlates multiple service detections on the same host into unified agent entities.
    
    This prevents double-counting when a host runs both:
    - An agent gateway (e.g., OpenClaw on 18789)
    - An LLM backend (e.g., Ollama on 11434)
    
    These should be reported as ONE agent with backend info, not TWO separate agents.
    """
    
    # Confidence thresholds for badges
    CONFIDENCE_THRESHOLDS = {
        'confirmed': 0.85,
        'likely': 0.60,
        'possible': 0.30,
        'unknown': 0.0,
    }
    
    def __init__(self):
        self.gateway_ports = GATEWAY_PORTS
        self.backend_ports = BACKEND_PORTS
        self.compat_matrix = GATEWAY_BACKEND_COMPAT
    
    def _classify_port(self, port: int) -> Optional[str]:
        """Determine if port is gateway or backend"""
        if port in self.gateway_ports:
            return 'gateway'
        elif port in self.backend_ports:
            return 'backend'
        return None
    
    def _get_confidence_badge(self, confidence: float) -> str:
        """Map confidence score to badge label"""
        if confidence >= self.CONFIDENCE_THRESHOLDS['confirmed']:
            return 'confirmed'
        elif confidence >= self.CONFIDENCE_THRESHOLDS['likely']:
            return 'likely'
        elif confidence >= self.CONFIDENCE_THRESHOLDS['possible']:
            return 'possible'
        return 'unknown'
    
    def _generate_agent_id(self, host: str, gateway_port: Optional[int] = None) -> str:
        """Generate unique agent ID"""
        if gateway_port:
            return f"agent-{host.replace('.', '-')}-{gateway_port}"
        return f"agent-{host.replace('.', '-')}-unknown"
    
    def correlate_services(self, detections: List[Dict]) -> List[Dict]:
        """
        Correlate multiple service detections into unified agent entities.
        
        Args:
            detections: List of detection results from scanner
                       Each dict should have: host, port, framework, confidence
                       
        Returns:
            List of correlated agent entities
        """
        logger.info(f"🔗 Starting correlation of {len(detections)} detections")
        
        # Convert raw detections to ServiceDetection objects
        services = []
        for det in detections:
            if not isinstance(det, ServiceDetection):
                det_type = self._classify_port(det.get('port', 0))
                service = ServiceDetection(
                    host=det.get('host', ''),
                    port=det.get('port', 0),
                    framework=det.get('framework', 'Unknown'),
                    confidence=det.get('confidence', 0.0),
                    detection_type=det_type or 'unknown',
                    raw_detection=det,
                )
            else:
                service = det
            services.append(service)
        
        # Group services by host
        hosts: Dict[str, List[ServiceDetection]] = {}
        for service in services:
            if service.host not in hosts:
                hosts[service.host] = []
            hosts[service.host].append(service)
        
        # Process each host's services
        correlated_agents = []
        
        for host, host_services in hosts.items():
            # Separate gateways and backends
            gateways = [s for s in host_services if s.detection_type == 'gateway']
            backends = [s for s in host_services if s.detection_type == 'backend']
            
            logger.info(f"  Host {host}: {len(gateways)} gateway(s), {len(backends)} backend(s)")
            
            # Correlation logic
            if gateways and backends:
                # Case 1: Gateway + Backend on same host → MERGE
                logger.info(f"  ✅ Correlating gateway + backend on {host}")
                
                for gateway in gateways:
                    # Find compatible backend
                    compatible_backends = []
                    gateway_framework = gateway.framework
                    
                    for backend in backends:
                        backend_framework = backend.framework
                        compatible_frameworks = self.compat_matrix.get(gateway_framework, [])
                        
                        if backend_framework in compatible_frameworks or \
                           backend_framework == "General LLM" or \
                           gateway_framework == backend_framework:
                            compatible_backends.append(backend)
                    
                    if compatible_backends:
                        # Use highest confidence backend
                        best_backend = max(compatible_backends, key=lambda b: b.confidence)
                        
                        # Create correlated agent
                        agent = self._create_correlated_agent(gateway, best_backend)
                        correlated_agents.append(agent)
                        
                        # Remove used backend from pool
                        backends.remove(best_backend)
                    else:
                        # No compatible backend found, create gateway-only agent
                        agent = self._create_gateway_only_agent(gateway)
                        correlated_agents.append(agent)
                
                # Any remaining backends without gateways
                for backend in backends:
                    agent = self._create_backend_only_agent(backend)
                    correlated_agents.append(agent)
                    
            elif gateways and not backends:
                # Case 2: Gateway only → Gateway without known backend
                logger.info(f"  ⚠️  Gateway-only detection on {host}")
                for gateway in gateways:
                    agent = self._create_gateway_only_agent(gateway)
                    correlated_agents.append(agent)
                    
            elif backends and not gateways:
                # Case 3: Backend only → Backend service without gateway
                logger.info(f"  ℹ️  Backend-only detection on {host}")
                for backend in backends:
                    agent = self._create_backend_only_agent(backend)
                    correlated_agents.append(agent)
        
        logger.info(f"✅ Correlation complete: {len(detections)} detections → {len(correlated_agents)} agents")
        
        # Convert to dict format for API
        return [agent.to_dict() for agent in correlated_agents]
    
    def _create_correlated_agent(self, gateway: ServiceDetection, backend: ServiceDetection) -> CorrelatedAgent:
        """Create correlated agent with both gateway and backend"""
        # Calculate combined confidence (boost for correlation)
        combined_confidence = max(gateway.confidence, backend.confidence)
        combined_confidence = min(combined_confidence + 0.10, 0.99)  # Boost up to 10%
        
        agent = CorrelatedAgent(
            id=self._generate_agent_id(gateway.host, gateway.port),
            host=gateway.host,
            type='agent_gateway',
            confidence=combined_confidence,
            confidence_badge=self._get_confidence_badge(combined_confidence),
            gateway={
                'port': gateway.port,
                'framework': gateway.framework,
                'confidence': gateway.confidence,
            },
            backend={
                'port': backend.port,
                'framework': backend.framework,
                'model': backend.raw_detection.get('model', 'unknown'),
                'confidence': backend.confidence,
            },
        )
        
        logger.info(f"  📊 Created correlated agent: {agent.id} "
                   f"(confidence: {combined_confidence:.0%}, badge: {agent.confidence_badge})")
        
        return agent
    
    def _create_gateway_only_agent(self, gateway: ServiceDetection) -> CorrelatedAgent:
        """Create gateway-only agent (backend unknown)"""
        agent = CorrelatedAgent(
            id=self._generate_agent_id(gateway.host, gateway.port),
            host=gateway.host,
            type='gateway_only',
            confidence=gateway.confidence,
            confidence_badge=self._get_confidence_badge(gateway.confidence),
            gateway={
                'port': gateway.port,
                'framework': gateway.framework,
                'confidence': gateway.confidence,
                'backend_status': 'unknown',  # Backend exists but not detected
            },
        )
        
        logger.info(f"  📊 Created gateway-only agent: {agent.id} "
                   f"(confidence: {gateway.confidence:.0%}, badge: {agent.confidence_badge})")
        
        return agent
    
    def _create_backend_only_agent(self, backend: ServiceDetection) -> CorrelatedAgent:
        """Create backend-only agent (no gateway detected)"""
        agent = CorrelatedAgent(
            id=self._generate_agent_id(backend.host),
            host=backend.host,
            type='backend_only',
            confidence=backend.confidence * 0.8,  # Lower confidence without gateway
            confidence_badge=self._get_confidence_badge(backend.confidence * 0.8),
            backend={
                'port': backend.port,
                'framework': backend.framework,
                'model': backend.raw_detection.get('model', 'unknown'),
                'confidence': backend.confidence,
                'gateway_status': 'not_detected',  # Gateway not found
            },
        )
        
        logger.info(f"  📊 Created backend-only agent: {agent.id} "
                   f"(confidence: {agent.confidence:.0%}, badge: {agent.confidence_badge})")
        
        return agent


def correlate_detections(detections: List[Dict]) -> List[Dict]:
    """
    Standalone function for easy integration.
    
    Args:
        detections: List of detection dicts from scanner
        
    Returns:
        List of correlated agent entity dicts
    """
    engine = CorrelationEngine()
    return engine.correlate_services(detections)


# Test the correlation engine
if __name__ == "__main__":
    # Test scenario: Host has both OpenClaw (18789) and Ollama (11434)
    test_detections = [
        {
            'host': '192.168.0.245',
            'port': 18789,
            'framework': 'OpenClaw',
            'confidence': 0.95,
        },
        {
            'host': '192.168.0.245',
            'port': 11434,
            'framework': 'Ollama',
            'confidence': 0.90,
        },
        {
            'host': '192.168.0.100',
            'port': 11434,
            'framework': 'Ollama',
            'confidence': 0.88,
        },
        {
            'host': '192.168.0.50',
            'port': 18789,
            'framework': 'OpenClaw',
            'confidence': 0.92,
        },
    ]
    
    print("Input detections:")
    for det in test_detections:
        print(f"  - {det['host']}:{det['port']} ({det['framework']}, {det['confidence']:.0%})")
    
    print("\nRunning correlation...")
    correlated = correlate_detections(test_detections)
    
    print(f"\nCorrelated agents ({len(correlated)}):")
    for agent in correlated:
        print(f"\n  Agent ID: {agent['id']}")
        print(f"  Type: {agent['type']}")
        print(f"  Host: {agent['host']}")
        print(f"  Confidence: {agent['confidence']:.0%} ({agent['confidence_badge']})")
        
        if 'gateway' in agent:
            gw = agent['gateway']
            print(f"  Gateway: {gw['framework']} on port {gw['port']}")
        
        if 'backend' in agent:
            be = agent['backend']
            print(f"  Backend: {be['framework']} on port {be['port']}")
