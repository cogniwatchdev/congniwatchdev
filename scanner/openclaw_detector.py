#!/usr/bin/env python3
"""
OpenClaw Detection Module for CogniWatch

Detects OpenClaw Gateway instances with 95%+ confidence by analyzing:
- HTTP response headers (CSP, security headers)
- API endpoint signatures
- Authentication patterns
- Error response formats
- Deployment fingerprints

Author: CIPHER Project
Version: 1.0.0
Date: 2026-03-07
"""

import requests
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DEFINITIVE = "definitive"


@dataclass
class DetectionResult:
    """Result of OpenClaw detection scan"""
    host: str
    port: int
    confidence: float
    level: ConfidenceLevel
    signals: Dict[str, bool]
    details: Dict[str, str]
    
    def is_openclaw(self, threshold: float = 95.0) -> bool:
        """Check if detection meets confidence threshold"""
        return self.confidence >= threshold
    
    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "confidence": self.confidence,
            "level": self.level.value,
            "is_openclaw": self.is_openclaw(),
            "signals": self.signals,
            "details": self.details
        }


class OpenClawDetector:
    """
    Detects OpenClaw Gateway instances with high confidence.
    
    Usage:
        detector = OpenClawDetector()
        result = detector.scan("192.168.0.245", 18789)
        if result.is_openclaw():
            print(f"OpenClaw detected with {result.confidence}% confidence")
    """
    
    # Signal weights for confidence calculation
    WEIGHTS = {
        'http_headers': 25,
        'api_endpoints': 25,
        'auth_patterns': 20,
        'error_format': 15,
        'deployment': 10,
        'session_format': 5
    }
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize detector.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CogniWatch-Scanner/1.0'
        })
    
    def scan(self, host: str, port: int = 18789, https: bool = False) -> DetectionResult:
        """
        Scan a host for OpenClaw signatures.
        
        Args:
            host: Hostname or IP address
            port: Port number (default 18789)
            https: Use HTTPS instead of HTTP
            
        Returns:
            DetectionResult with confidence score
        """
        protocol = "https" if https else "http"
        base_url = f"{protocol}://{host}:{port}"
        
        signals = {}
        details = {}
        
        # 1. Check HTTP headers
        try:
            resp = self.session.get(base_url, timeout=self.timeout, allow_redirects=False)
            signals.update(self._check_http_headers(resp))
            details['http_response'] = f"{resp.status_code} {resp.reason}"
        except requests.RequestException as e:
            details['http_error'] = str(e)
        
        # 2. Check API endpoints
        signals.update(self._check_api_endpoints(base_url))
        
        # 3. Check auth patterns
        signals.update(self._check_auth_patterns(base_url))
        
        # 4. Check error formats
        signals.update(self._check_error_formats(base_url))
        
        # 5. Check deployment fingerprints
        signals.update(self._check_deployment(host, port))
        
        # Calculate confidence
        confidence = self._calculate_confidence(signals)
        level = self._get_confidence_level(confidence)
        
        return DetectionResult(
            host=host,
            port=port,
            confidence=confidence,
            level=level,
            signals=signals,
            details=details
        )
    
    def _check_http_headers(self, response: requests.Response) -> Dict[str, bool]:
        """
        Check HTTP response headers for OpenClaw signatures.
        
        Signatures:
        - CSP with WebSocket support
        - X-Frame-Options: DENY
        - No Server header
        - Cache-Control: no-cache
        """
        headers = response.headers
        signals = {}
        
        # Check CSP for WebSocket support
        csp = headers.get('Content-Security-Policy', '')
        signals['csp_websocket'] = 'connect-src' in csp and ('ws:' in csp or 'wss:' in csp)
        signals['csp_strict'] = 'base-uri \'none\'' in csp and 'object-src \'none\'' in csp
        
        # Check security headers
        signals['x_frame_options_deny'] = headers.get('X-Frame-Options', '').upper() == 'DENY'
        signals['x_content_type_nosniff'] = headers.get('X-Content-Type-Options', '').lower() == 'nosniff'
        signals['referrer_policy'] = 'no-referrer' in headers.get('Referrer-Policy', '').lower()
        
        # Check for missing Server header (OpenClaw hides it)
        signals['no_server_header'] = 'Server' not in headers
        
        # Check cache control
        signals['cache_control_no_cache'] = headers.get('Cache-Control', '').lower() == 'no-cache'
        
        # Check Content-Type
        signals['html_content_type'] = 'text/html' in headers.get('Content-Type', '')
        
        return signals
    
    def _check_api_endpoints(self, base_url: str) -> Dict[str, bool]:
        """
        Check for OpenClaw API endpoints.
        
        Endpoints:
        - /api/channels
        - /v1/chat/completions
        - /tools/invoke
        """
        signals = {}
        
        # Check /api/channels
        try:
            resp = self.session.get(f"{base_url}/api/channels", timeout=self.timeout)
            # Even 401 is a signal - means endpoint exists
            signals['api_channels_exists'] = resp.status_code in [200, 401, 403]
            if resp.status_code == 401:
                signals['api_channels_auth_required'] = True
        except:
            signals['api_channels_exists'] = False
        
        # Check /v1/chat/completions (OpenAI-compatible)
        try:
            resp = self.session.post(
                f"{base_url}/v1/chat/completions",
                json={"model": "test", "messages": []},
                timeout=self.timeout
            )
            signals['v1_chat_completions_exists'] = resp.status_code in [200, 401, 403, 400]
        except:
            signals['v1_chat_completions_exists'] = False
        
        # Check /tools/invoke
        try:
            resp = self.session.post(
                f"{base_url}/tools/invoke",
                json={"tool": "test", "args": {}},
                timeout=self.timeout
            )
            signals['tools_invoke_exists'] = resp.status_code in [200, 401, 403, 404]
        except:
            signals['tools_invoke_exists'] = False
        
        # Check /api/sessions
        try:
            resp = self.session.get(f"{base_url}/api/sessions", timeout=self.timeout)
            signals['api_sessions_exists'] = resp.status_code in [200, 401, 403]
        except:
            signals['api_sessions_exists'] = False
        
        # Check /v1/responses (OpenResponses API)
        try:
            resp = self.session.post(
                f"{base_url}/v1/responses",
                json={"model": "test", "input": "test"},
                timeout=self.timeout
            )
            signals['v1_responses_exists'] = resp.status_code in [200, 401, 403, 400]
        except:
            signals['v1_responses_exists'] = False
        
        return signals
    
    def _check_auth_patterns(self, base_url: str) -> Dict[str, bool]:
        """
        Check authentication patterns.
        
        Patterns:
        - Bearer token requirement
        - X-OpenClaw-Token header support
        - 401 response format
        """
        signals = {}
        
        # Test bearer auth requirement
        try:
            resp = self.session.get(f"{base_url}/api/channels", timeout=self.timeout)
            signals['bearer_auth_required'] = resp.status_code == 401
        except:
            signals['bearer_auth_required'] = False
        
        # Test X-OpenClaw-Token header (hooks only)
        try:
            resp = self.session.post(
                f"{base_url}/hooks/test",
                headers={'X-OpenClaw-Token': 'test'},
                timeout=self.timeout
            )
            # If it accepts the header (even if token is wrong), it's a signal
            signals['x_openclaw_token_supported'] = resp.status_code != 400
        except:
            signals['x_openclaw_token_supported'] = False
        
        # Check for custom headers in OPTIONS request
        try:
            resp = self.session.options(f"{base_url}/api/channels", timeout=self.timeout)
            signals['custom_headers_supported'] = 'X-OpenClaw-Token' in resp.headers.get('Access-Control-Allow-Headers', '')
        except:
            signals['custom_headers_supported'] = False
        
        return signals
    
    def _check_error_formats(self, base_url: str) -> Dict[str, bool]:
        """
        Check error response formats.
        
        OpenClaw error format:
        {"error":{"message":"<msg>","type":"<type>"}}
        """
        signals = {}
        
        # Trigger 401 error
        try:
            resp = self.session.get(f"{base_url}/api/channels", timeout=self.timeout)
            if resp.status_code == 401:
                try:
                    error_data = resp.json()
                    # Check for OpenClaw error schema
                    has_error = 'error' in error_data
                    has_message = 'message' in error_data.get('error', {})
                    has_type = 'type' in error_data.get('error', {})
                    signals['error_schema_match'] = has_error and has_message and has_type
                    
                    # Check specific error type value
                    error_type = error_data.get('error', {}).get('type', '')
                    signals['unauthorized_type'] = error_type == 'unauthorized'
                except json.JSONDecodeError:
                    signals['error_schema_match'] = False
                    signals['unauthorized_type'] = False
            else:
                signals['error_schema_match'] = False
                signals['unauthorized_type'] = False
        except:
            signals['error_schema_match'] = False
            signals['unauthorized_type'] = False
        
        # Trigger 404 error
        try:
            resp = self.session.get(f"{base_url}/api/nonexistent-endpoint-xyz", timeout=self.timeout)
            if resp.status_code == 404:
                try:
                    error_data = resp.json()
                    signals['404_json_format'] = 'error' in error_data
                except:
                    signals['404_json_format'] = False
            else:
                signals['404_json_format'] = False
        except:
            signals['404_json_format'] = False
        
        return signals
    
    def _check_deployment(self, host: str, port: int) -> Dict[str, bool]:
        """
        Check deployment fingerprints.
        
        Fingerprints:
        - Default port 18789
        - Systemd service patterns
        - Process names
        """
        signals = {}
        
        # Check default port
        signals['default_port_18789'] = port == 18789
        
        # Note: These would require local system access
        # For remote detection, we can only check network-level signatures
        signals['systemd_service'] = False  # Would need local access
        signals['docker_container'] = False  # Would need Docker API access
        
        return signals
    
    def _calculate_confidence(self, signals: Dict[str, bool]) -> float:
        """
        Calculate confidence score from detected signals.
        
        Args:
            signals: Dictionary of signal name -> detected boolean
            
        Returns:
            Confidence percentage (0-100)
        """
        score = 0.0
        
        # HTTP Headers (25 points)
        if signals.get('csp_websocket'):
            score += 10
        if signals.get('csp_strict'):
            score += 5
        if signals.get('x_frame_options_deny'):
            score += 5
        if signals.get('no_server_header'):
            score += 3
        if signals.get('cache_control_no_cache'):
            score += 2
        
        # API Endpoints (25 points)
        if signals.get('api_channels_exists'):
            score += 8
        if signals.get('api_channels_auth_required'):
            score += 3  # Bonus for auth requirement
        if signals.get('v1_chat_completions_exists'):
            score += 8
        if signals.get('tools_invoke_exists'):
            score += 5
        if signals.get('api_sessions_exists'):
            score += 4
        
        # Auth Patterns (20 points)
        if signals.get('bearer_auth_required'):
            score += 10
        if signals.get('x_openclaw_token_supported'):
            score += 10
        
        # Error Format (15 points)
        if signals.get('error_schema_match'):
            score += 10
        if signals.get('unauthorized_type'):
            score += 5
        
        # Deployment (10 points)
        if signals.get('default_port_18789'):
            score += 5
        if signals.get('systemd_service'):
            score += 3
        if signals.get('docker_container'):
            score += 2
        
        # Session Format (5 points) - would need session inspection
        if signals.get('session_key_format'):
            score += 5
        
        # Bonus signals
        if signals.get('html_content_type'):
            score += 2
        if signals.get('referrer_policy'):
            score += 1
        if signals.get('x_content_type_nosniff'):
            score += 1
        
        return min(score, 100.0)
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert confidence score to level enum"""
        if confidence >= 95:
            return ConfidenceLevel.DEFINITIVE
        elif confidence >= 80:
            return ConfidenceLevel.HIGH
        elif confidence >= 60:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


def test_local_openclaw():
    """Test detector against local OpenClaw instance"""
    detector = OpenClawDetector()
    
    print("Scanning localhost:18789 for OpenClaw...")
    result = detector.scan("localhost", 18789)
    
    print(f"\n{'='*60}")
    print(f"OpenClaw Detection Result")
    print(f"{'='*60}")
    print(f"Host: {result.host}:{result.port}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Level: {result.level.value.upper()}")
    print(f"Is OpenClaw: {result.is_openclaw()}")
    print(f"\nDetected Signals:")
    
    for signal, detected in result.signals.items():
        status = "✓" if detected else "✗"
        print(f"  {status} {signal}")
    
    print(f"\nDetails:")
    for key, value in result.details.items():
        print(f"  {key}: {value}")
    
    return result


def test_network_scan(hosts: List[str]) -> List[DetectionResult]:
    """
    Scan multiple hosts for OpenClaw.
    
    Args:
        hosts: List of hostnames/IPs to scan
        
    Returns:
        List of DetectionResult objects
    """
    detector = OpenClawDetector(timeout=3.0)
    results = []
    
    for host in hosts:
        print(f"\nScanning {host}...")
        try:
            result = detector.scan(host)
            results.append(result)
            
            if result.is_openclaw():
                print(f"  ✓ OpenClaw detected with {result.confidence:.1f}% confidence")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Scan provided hosts
        hosts = sys.argv[1:]
        results = test_network_scan(hosts)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Scan Summary")
        print(f"{'='*60}")
        
        openclaw_found = [r for r in results if r.is_openclaw()]
        print(f"Hosts scanned: {len(results)}")
        print(f"OpenClaw instances found: {len(openclaw_found)}")
        
        if openclaw_found:
            print(f"\nOpenClaw instances:")
            for r in openclaw_found:
                print(f"  - {r.host}:{r.port} ({r.confidence:.1f}%)")
    else:
        # Test local instance
        test_local_openclaw()
