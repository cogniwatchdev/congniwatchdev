#!/usr/bin/env python3
"""
CogniWatch - Advanced Agent Framework Fingerprinting
Signature-driven detection using loaded framework signatures
"""

import requests
import websocket
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

# Import signature loader
try:
    from signature_loader import SignatureLoader, FrameworkSignature, ConfidenceConfig
except ImportError:
    from .signature_loader import SignatureLoader, FrameworkSignature, ConfidenceConfig


@dataclass
class DetectionResult:
    """Result of framework detection attempt"""
    framework: str
    confidence: float  # 0.0 - 1.0
    signals: Dict[str, bool] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    method: str = "unknown"
    signature: Optional[FrameworkSignature] = None
    matched_patterns: Dict[str, List[str]] = field(default_factory=dict)
    
    def is_confirmed(self) -> bool:
        return self.confidence >= 0.85
    
    def is_likely(self) -> bool:
        return 0.6 <= self.confidence < 0.85
    
    def is_possible(self) -> bool:
        return 0.3 <= self.confidence < 0.6
    
    def get_confidence_badge(self) -> str:
        """Return badge name for UI display: confirmed, likely, possible, or unknown"""
        if self.confidence >= 0.85:
            return 'confirmed'
        elif self.confidence >= 0.60:
            return 'likely'
        elif self.confidence >= 0.30:
            return 'possible'
        else:
            return 'unknown'
    
    def get_confidence_icon(self) -> str:
        """Return emoji icon for confidence level"""
        badge = self.get_confidence_badge()
        icons = {
            'confirmed': '✅',
            'likely': '⚠️',
            'possible': '❓',
            'unknown': '❌'
        }
        return icons.get(badge, '❓')


class AdvancedDetector:
    """
    Signature-driven agent framework detection.
    Uses loaded framework signatures instead of hardcoded patterns.
    
    Detection layers:
    1. HTTP Response Analysis (title, headers, body keywords)
    2. API Endpoint Probing (framework-specific paths)
    3. WebSocket Protocol Testing (optional)
    4. Confidence Scoring (per signature specs)
    """
    
    def __init__(self, signatures_path: str, timeout: float = 3.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CogniWatch/1.0 (Agent Framework Scanner)'
        })
        
        # Load signatures
        try:
            self.signature_loader = SignatureLoader(signatures_path)
            self.confidence_config = self.signature_loader.get_confidence_config()
        except FileNotFoundError:
            print(f"⚠️  Warning: Signatures file not found at {signatures_path}")
            print(f"   Using default detection patterns")
            self.signature_loader = None
            self.confidence_config = ConfidenceConfig()
    
    def detect(self, host: str, port: int) -> List[DetectionResult]:
        """
        Comprehensive signature-driven detection for a single endpoint
        Returns list of possible frameworks with confidence scores
        """
        results = []
        base_url = f"http://{host}:{port}"
        
        # Get frameworks that might be on this port
        candidate_frameworks = []
        if self.signature_loader:
            candidate_frameworks = self.signature_loader.get_framework_by_port(port)
            # If no port match, scan all frameworks (fallback)
            if not candidate_frameworks:
                candidate_frameworks = self.signature_loader.get_all_frameworks()
        
        # Layer 1: HTTP Response Analysis (signature-driven)
        http_results = self._analyze_http_response_signature_driven(base_url, candidate_frameworks)
        results.extend(http_results)
        
        # Layer 2: API Endpoint Probing (signature-driven)
        api_results = self._probe_api_endpoints_signature_driven(base_url, candidate_frameworks)
        results.extend(api_results)
        
        # Layer 3: WebSocket Protocol Testing (if enabled)
        ws_result = self._test_websocket_protocol(host, port)
        if ws_result:
            results.append(ws_result)
        
        # Merge and deduplicate results
        return self._merge_results(results)
    
    def _analyze_http_response_signature_driven(self, base_url: str, 
                                                  frameworks: List[FrameworkSignature]) -> List[DetectionResult]:
        """Analyze HTTP response using loaded signatures"""
        results = []
        
        try:
            response = self.session.get(base_url, timeout=self.timeout)
            html = response.text.lower()
            headers = response.headers
            
            for framework in frameworks:
                confidence = self.confidence_config.base_confidence
                signals = {}
                evidence = []
                matched_patterns = {
                    'title': [],
                    'body_keywords': [],
                    'headers': []
                }
                
                # Check title patterns
                title_patterns = framework.get_title_patterns()
                for pattern in title_patterns:
                    if pattern.lower() in html:
                        confidence += self.confidence_config.title_match
                        signals[f'title_match_{pattern.lower()}'] = True
                        matched_patterns['title'].append(pattern)
                        evidence.append(f"Title match: '{pattern}'")
                        break  # Only count once per framework
                
                # Check body keywords
                body_keywords = framework.get_body_keywords()
                keyword_matches = 0
                for keyword in body_keywords:
                    if keyword.lower() in html:
                        keyword_matches += 1
                        matched_patterns['body_keywords'].append(keyword)
                
                if keyword_matches > 0:
                    # Cap body keyword bonus at 0.3 (3 keywords max)
                    body_bonus = min(keyword_matches * self.confidence_config.body_keyword_match, 0.3)
                    confidence += body_bonus
                    signals['body_keywords_matched'] = True
                    evidence.append(f"Body keywords matched: {keyword_matches} patterns")
                
                # Check header patterns
                header_patterns = framework.get_header_patterns()
                header_matched = False
                
                # Server header check
                server_header = headers.get('Server', '')
                server_patterns = header_patterns.get('server_contains', [])
                for pattern in server_patterns:
                    if pattern.lower() in server_header.lower():
                        confidence += self.confidence_config.header_match
                        signals[f'header_server_{pattern}'] = True
                        matched_patterns['headers'].append(f'Server: {pattern}')
                        header_matched = True
                        evidence.append(f"Server header match: '{pattern}'")
                        break
                
                # Custom headers check
                custom_headers = header_patterns.get('custom_headers', [])
                for custom_header in custom_headers:
                    if custom_header in headers:
                        confidence += self.confidence_config.header_match
                        signals[f'header_custom_{custom_header}'] = True
                        matched_patterns['headers'].append(custom_header)
                        evidence.append(f"Custom header present: {custom_header}")
                
                # Only return result if we found meaningful signals
                if confidence > self.confidence_config.base_confidence:
                    confidence = min(confidence, self.confidence_config.max_confidence)
                    
                    result = DetectionResult(
                        framework=framework.name.lower(),
                        confidence=confidence,
                        signals=signals,
                        evidence=evidence,
                        method="http_signature_analysis",
                        signature=framework,
                        matched_patterns=matched_patterns
                    )
                    results.append(result)
            
        except Exception as e:
            # Connection failed
            pass
        
        return results
    
    def _probe_api_endpoints_signature_driven(self, base_url: str,
                                                frameworks: List[FrameworkSignature]) -> List[DetectionResult]:
        """Probe API endpoints using loaded signatures"""
        results = []
        
        for framework in frameworks:
            confidence = self.confidence_config.base_confidence
            signals = {}
            evidence = []
            endpoints_tested = 0
            endpoints_matched = 0
            
            for endpoint in framework.api_endpoints:
                path = endpoint.get('path', '')
                method = endpoint.get('method', 'GET')
                confidence_boost = endpoint.get('confidence_boost', 0.10)
                
                try:
                    url = f"{base_url}{path}"
                    endpoints_tested += 1
                    
                    if method == 'GET':
                        response = self.session.get(url, timeout=self.timeout)
                    elif method == 'POST':
                        response = self.session.post(url, json={}, timeout=self.timeout)
                    else:
                        continue
                    
                    if response.status_code == 200:
                        endpoints_matched += 1
                        
                        # Try to parse as JSON
                        try:
                            data = response.json()
                            expected = endpoint.get('expected_response', {})
                            structure = expected.get('structure', '')
                            
                            # Check if response structure matches expectations
                            if self._check_response_structure(data, structure):
                                confidence += confidence_boost
                                signals[f'api_endpoint_{path}'] = True
                                evidence.append(f"API endpoint {path} responded with expected structure")
                            else:
                                # Endpoint exists but structure doesn't match perfectly
                                confidence += confidence_boost * 0.5
                                evidence.append(f"API endpoint {path} exists (partial match)")
                                
                        except json.JSONDecodeError:
                            # Not JSON, but endpoint exists
                            confidence += confidence_boost * 0.3
                            evidence.append(f"API endpoint {path} exists (non-JSON)")
                    
                except Exception:
                    # Endpoint not available
                    pass
            
            # Calculate final confidence
            if endpoints_matched > 0:
                # Apply framework's total confidence boost cap
                max_boost = framework.total_confidence_boost
                confidence = min(confidence, self.confidence_config.base_confidence + max_boost)
                confidence = min(confidence, self.confidence_config.max_confidence)
                
                if confidence > self.confidence_config.base_confidence:
                    result = DetectionResult(
                        framework=framework.name.lower(),
                        confidence=confidence,
                        signals=signals,
                        evidence=evidence,
                        method="api_signature_probing",
                        signature=framework
                    )
                    results.append(result)
        
        return results
    
    def _check_response_structure(self, data: Any, expected_structure: str) -> bool:
        """Check if response data matches expected structure description"""
        if not isinstance(data, dict):
            return False
        
        data_str = str(data).lower()
        expected_lower = expected_structure.lower()
        
        # Simple heuristic: check if key terms from expected structure appear in data
        structure_terms = {
            'session': ['session', 'sessionkey', 'sessions'],
            'agent': ['agent', 'agents', 'agentid'],
            'status': ['status', 'state', 'health'],
            'array': ['[', 'list', 'array'],
            'object': ['{', 'object', 'dict'],
            'kickoff': ['kickoff', 'kickoff_id'],
            'run': ['run', 'run_id'],
            'thread': ['thread', 'thread_id'],
            'assistant': ['assistant', 'assistant_id'],
            'crew': ['crew', 'crews'],
            'workflow': ['workflow', 'workflows'],
            'healthy': ['healthy', 'health', 'ok', 'status'],
        }
        
        for term, keywords in structure_terms.items():
            if term in expected_lower:
                for keyword in keywords:
                    if keyword in data_str:
                        return True
        
        # Fallback: if we got JSON, it's a reasonable structure match
        return True
    
    def _test_websocket_protocol(self, host: str, port: int) -> Optional[DetectionResult]:
        """Test WebSocket protocol and message formats"""
        try:
            ws_url = f"ws://{host}:{port}/"
            
            # Try to establish WebSocket connection
            ws = websocket.create_connection(ws_url, timeout=self.timeout)
            
            # Send OpenClaw-style status request
            ws.send(json.dumps({"action": "status"}))
            response = ws.recv()
            
            evidence = []
            confidence = self.confidence_config.base_confidence
            signals = {}
            
            # Analyze response
            try:
                data = json.loads(response)
                
                # Check for common patterns
                if 'sessions' in data or 'gateway' in data or 'status' in data:
                    confidence += 0.3
                    evidence.append("WebSocket responded with status data")
                
                # Check for session-related keys
                response_str = str(data).lower()
                if 'sessionkey' in response_str or 'agentid' in response_str:
                    confidence += 0.3
                    evidence.append("Session/agent metadata in WebSocket response")
                
                ws.close()
                
                if confidence > self.confidence_config.base_confidence:
                    return DetectionResult(
                        framework="openclaw",
                        confidence=min(confidence, self.confidence_config.max_confidence),
                        signals={'websocket_responsive': True},
                        evidence=evidence,
                        method="websocket_test"
                    )
                
            except json.JSONDecodeError:
                # Got non-JSON response
                ws.close()
                    
        except Exception:
            # WebSocket not available
            pass
        
        return None
    
    def _merge_results(self, results: List[DetectionResult]) -> List[DetectionResult]:
        """Merge and deduplicate detection results"""
        if not results:
            return []
        
        # Group by framework
        framework_results = {}
        for result in results:
            fw_key = result.framework.lower()
            if fw_key not in framework_results:
                framework_results[fw_key] = []
            framework_results[fw_key].append(result)
        
        # Merge results for each framework
        merged = []
        for framework, framework_result_list in framework_results.items():
            # Take highest confidence
            best = max(framework_result_list, key=lambda x: x.confidence)
            
            # Merge evidence and signals from all results
            all_evidence = []
            all_signals = {}
            all_patterns = {'title': [], 'body_keywords': [], 'headers': []}
            
            for result in framework_result_list:
                all_evidence.extend(result.evidence)
                all_signals.update(result.signals)
                if hasattr(result, 'matched_patterns') and result.matched_patterns:
                    for key, patterns in result.matched_patterns.items():
                        if key in all_patterns:
                            all_patterns[key].extend(patterns)
            
            # Boost confidence if multiple methods agree
            if len(framework_result_list) > 1:
                best.confidence = min(best.confidence + 0.1, self.confidence_config.max_confidence)
            
            best.evidence = list(set(all_evidence))
            best.signals = all_signals
            best.matched_patterns = all_patterns
            best.method = "multi-signal"
            
            merged.append(best)
        
        # Sort by confidence (descending)
        return sorted(merged, key=lambda x: x.confidence, reverse=True)


def main():
    """Test detector on local services"""
    print("\n👁️ CogniWatch Advanced Framework Detector (Signature-Driven)\n")
    
    # Determine signatures file path - use consolidated framework_signatures.json
    script_dir = Path(__file__).parent
    signatures_file = script_dir / "framework_signatures.json"
    
    detector = AdvancedDetector(str(signatures_file), timeout=3.0)
    
    # Test on Neo gateway
    print(f"Testing target: 192.168.0.245:18789\n")
    print('='*60)
    
    host = "192.168.0.245"
    port = 18789
    
    print(f"Scanning {host}:{port}...")
    results = detector.detect(host, port)
    
    if results:
        for i, result in enumerate(results, 1):
            confidence_pct = int(result.confidence * 100)
            badge = "✅" if result.is_confirmed() else "⚠️" if result.is_likely() else "❓"
            
            print(f"\n{badge} Detection #{i}:")
            print(f"  Framework: {result.framework.upper()}")
            print(f"  Confidence: {confidence_pct}%")
            print(f"  Method: {result.method}")
            print(f"  Signals: {len(result.signals)}")
            print(f"  Evidence:")
            for ev in result.evidence[:8]:
                print(f"    - {ev}")
    else:
        print("  ❓ No framework detected - service may be offline or unreachable")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
