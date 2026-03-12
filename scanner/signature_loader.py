#!/usr/bin/env python3
"""
CogniWatch - Framework Signature Loader
Loads JSON signature files for agent framework detection
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FrameworkSignature:
    """Represents a framework detection signature"""
    framework: str
    name: str
    version: str
    category: str
    ports: Dict
    http_fingerprints: Dict
    api_endpoints: Dict
    websocket: Dict
    config_files: List[str]
    process_names: List[str]
    network_signatures: Dict
    confidence: Dict
    detection_priority: int
    notes: str
    variants: List[str] = field(default_factory=list)


@dataclass
class ConfidenceConfig:
    """Confidence scoring configuration"""
    base_confidence: float = 0.05  # Starting confidence before any signals
    port_match: float = 0.30
    http_pattern: float = 0.15
    http_multiple: float = 0.10
    api_validated: float = 0.25
    websocket_match: float = 0.15
    framework_specific: float = 0.05
    max_confidence: float = 0.98  # Maximum achievable confidence
    threshold_confirmed: float = 0.85
    threshold_likely: float = 0.60
    threshold_possible: float = 0.30


class SignatureLoader:
    """
    Loads and manages framework detection signatures.
    
    Supports two formats:
    1. Consolidated: framework_signatures.json (preferred) - contains all frameworks
    2. Legacy: Individual JSON files in signatures/ directory
    
    Each signature defines:
    - Default ports
    - HTTP response fingerprints
    - API endpoints to probe
    - WebSocket protocol details
    - Confidence scoring weights
    """
    
    def __init__(self, signatures_path: str):
        self.signatures_path = Path(signatures_path)
        self.signatures: Dict[str, FrameworkSignature] = {}
        self.port_index: Dict[int, List[str]] = {}  # port -> [frameworks]
        self.load_all_signatures()
    
    def load_all_signatures(self):
        """Load signatures from consolidated file or directory"""
        if self.signatures_path.is_file():
            # Load from consolidated file
            self._load_consolidated(self.signatures_path)
        elif self.signatures_path.is_dir():
            # Check for consolidated file in directory first
            consolidated = self.signatures_path / "framework_signatures.json"
            if consolidated.exists():
                self._load_consolidated(consolidated)
            else:
                # Load individual files from directory
                for json_file in self.signatures_path.glob("*.json"):
                    try:
                        signature = self._load_signature_legacy(json_file)
                        self.signatures[signature.framework] = signature
                        self._index_by_port(signature)
                        print(f"✅ Loaded signature: {signature.name} ({signature.framework})")
                    except Exception as e:
                        print(f"⚠️  Failed to load {json_file}: {e}")
        else:
            raise FileNotFoundError(f"Signatures path not found: {self.signatures_path}")
        
        print(f"📊 Total signatures loaded: {len(self.signatures)}")
        print(f"📊 Port index entries: {len(self.port_index)}")
    
    def _load_consolidated(self, filepath: Path):
        """Load from consolidated framework_signatures.json file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for fw_data in data.get('frameworks', []):
            try:
                signature = self._convert_to_signature(fw_data)
                self.signatures[signature.framework] = signature
                self._index_by_port(signature)
                print(f"✅ Loaded signature: {signature.name} ({signature.framework})")
            except Exception as e:
                print(f"⚠️  Failed to convert framework {fw_data.get('name', 'unknown')}: {e}")
    
    def _convert_to_signature(self, fw_data: dict) -> FrameworkSignature:
        """Convert consolidated format to FrameworkSignature"""
        name = fw_data.get('name', 'Unknown')
        detection = fw_data.get('detection', {})
        ports = fw_data.get('ports', [])
        icon = fw_data.get('icon', {})
        
        # Convert ports list to dict format
        ports_dict = {
            'primary': ports[0] if ports else 8000,
            'alternative': ports[1:] if len(ports) > 1 else []
        }
        
        # Convert detection patterns to http_fingerprints format
        http_patterns = detection.get('http_patterns', {})
        http_fingerprints = {
            'title_patterns': http_patterns.get('title_contains', []),
            'header_patterns': {
                'server': http_patterns.get('headers', {}).get('server_contains', [''])[0] if http_patterns.get('headers', {}).get('server_contains') else '',
            },
            'body_patterns': http_patterns.get('body_keywords', [])
        }
        
        # API endpoints are already in correct format
        api_endpoints = detection.get('api_endpoints', [])
        
        # Build websocket config
        websocket = {
            'enabled': False,  # Default to disabled
            'path': '/',
            'protocol': 'generic',
            'handshake_patterns': []
        }
        
        return FrameworkSignature(
            framework=name.lower(),
            name=name,
            version=fw_data.get('version', '1.0+'),
            category=fw_data.get('category', 'agent-framework'),
            ports=ports_dict,
            http_fingerprints=http_fingerprints,
            api_endpoints=api_endpoints,
            websocket=websocket,
            config_files=[],
            process_names=[],
            network_signatures={},
            confidence=detection.get('confidence', {}),
            detection_priority=3,
            notes=detection.get('notes', ''),
            variants=[]
        )
    
    def _load_signature_legacy(self, filepath: Path) -> FrameworkSignature:
        """Load from legacy individual JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return FrameworkSignature(
            framework=data['framework'],
            name=data['name'],
            version=data.get('version', '1.0+'),
            category=data['category'],
            ports=data['ports'],
            http_fingerprints=data['http_fingerprints'],
            api_endpoints=list(data['api_endpoints'].values()) if isinstance(data['api_endpoints'], dict) else data['api_endpoints'],
            websocket=data['websocket'],
            config_files=data.get('config_files', []),
            process_names=data.get('process_names', []),
            network_signatures=data.get('network_signatures', {}),
            confidence=data['confidence'],
            detection_priority=data.get('detection_priority', 3),
            notes=data.get('notes', ''),
            variants=data.get('variants', [])
        )
    
    def _index_by_port(self, signature: FrameworkSignature):
        """Index signature by its ports for fast lookup"""
        ports = signature.ports
        
        # Index primary port
        primary = ports.get('primary')
        if primary:
            if primary not in self.port_index:
                self.port_index[primary] = []
            self.port_index[primary].append(signature.framework)
        
        # Index alternative ports
        for alt_port in ports.get('alternative', []):
            if alt_port not in self.port_index:
                self.port_index[alt_port] = []
            self.port_index[alt_port].append(signature.framework)
    
    def get_framework_by_port(self, port: int) -> List[FrameworkSignature]:
        """Get all frameworks that might be running on this port"""
        frameworks = self.port_index.get(port, [])
        return [self.signatures[fw] for fw in frameworks if fw in self.signatures]
    
    def get_all_frameworks(self) -> List[FrameworkSignature]:
        """Get all loaded signatures"""
        return list(self.signatures.values())
    
    def get_signature(self, framework: str) -> Optional[FrameworkSignature]:
        """Get signature for a specific framework"""
        return self.signatures.get(framework)
    
    def get_confidence_config(self) -> ConfidenceConfig:
        """Get default confidence configuration"""
        # Use first loaded signature's config as default
        if self.signatures:
            first = list(self.signatures.values())[0]
            conf = first.confidence
            # Handle both dict format and ConfidenceConfig object
            if hasattr(conf, 'get'):
                return ConfidenceConfig(
                    base_confidence=conf.get('base_confidence', 0.05),
                    port_match=conf.get('port_match', 0.30),
                    http_pattern=conf.get('http_pattern', 0.15),
                    http_multiple=conf.get('http_multiple', 0.10),
                    api_validated=conf.get('api_validated', 0.25),
                    websocket_match=conf.get('websocket_match', 0.15),
                    framework_specific=conf.get('framework_specific', 0.05),
                    max_confidence=conf.get('max_confidence', 0.98),
                    threshold_confirmed=conf.get('threshold_confirmed', 0.85),
                    threshold_likely=conf.get('threshold_likely', 0.60),
                    threshold_possible=conf.get('threshold_possible', 0.30)
                )
            else:
                return conf
        return ConfidenceConfig()
    
    def get_priority_frameworks(self, max_priority: int = 1) -> List[FrameworkSignature]:
        """Get frameworks with highest detection priority (1 = highest)"""
        return [s for s in self.signatures.values() if s.detection_priority <= max_priority]
    
    def list_all_ports(self) -> List[int]:
        """Get all indexed ports for scanning"""
        return sorted(self.port_index.keys())


if __name__ == "__main__":
    # Test signature loader
    import sys
    
    if len(sys.argv) < 2:
        signatures_dir = "./signatures"
    else:
        signatures_dir = sys.argv[1]
    
    loader = SignatureLoader(signatures_dir)
    
    print(f"\n📊 Loaded {len(loader.signatures)} signatures")
    print(f"📊 Indexed {len(loader.port_index)} ports")
    
    print("\n🎯 Priority 1 Frameworks:")
    for sig in loader.get_priority_frameworks(1):
        print(f"  - {sig.name} ({sig.framework}) - Port {sig.ports['primary']}")
    
    print("\n🔌 All indexed ports:")
    print(f"  {loader.list_all_ports()}")
