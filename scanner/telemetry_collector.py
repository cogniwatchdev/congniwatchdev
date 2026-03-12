#!/usr/bin/env python3
"""
CogniWatch - Telemetry Collection Module
Capture comprehensive telemetry from detected AI agents

Captures:
- Agent metadata (framework version, model info, capabilities)
- Performance metrics (avg response time, tokens/sec if visible)
- Security posture (auth required, CORS config, rate limiting)
- Network topology (behind proxy, load balancer, CDN)
- Activity indicators (active sessions, concurrent requests)
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Agent framework metadata"""
    framework: Optional[str] = None
    version: Optional[str] = None
    model_info: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    api_version: Optional[str] = None
    language: Optional[str] = None
    runtime: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    tokens_per_second: Optional[float] = None
    success_rate: float = 1.0
    error_rate: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    samples: int = 0


@dataclass
class SecurityPosture:
    """Security configuration assessment"""
    authentication_required: bool = False
    auth_type: Optional[str] = None  # api_key, bearer, basic, none
    cors_enabled: bool = False
    cors_origins: List[str] = field(default_factory=list)
    rate_limiting_detected: bool = False
    rate_limit_headers: Dict[str, str] = field(default_factory=dict)
    https_only: bool = False
    security_headers: Dict[str, str] = field(default_factory=dict)
    open_ports: List[int] = field(default_factory=list)
    exposure_level: str = "unknown"  # minimal, moderate, high
    vulnerabilities: List[str] = field(default_factory=list)


@dataclass
class NetworkTopology:
    """Network topology information"""
    behind_proxy: bool = False
    proxy_type: Optional[str] = None  # nginx, cloudflare, aws_lb, unknown
    behind_load_balancer: bool = False
    behind_cdn: bool = False
    cdn_provider: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    dns_records: List[str] = field(default_factory=list)
    hop_count: int = 0  # Estimated hops (via TTL analysis)
    geo_location: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class ActivityIndicators:
    """Current activity indicators"""
    active_sessions: int = 0
    concurrent_requests: int = 0
    uptime_seconds: Optional[int] = None
    last_activity: Optional[datetime] = None
    requests_today: int = 0
    tokens_used_today: Optional[int] = None
    health_status: str = "unknown"  # healthy, degraded, unhealthy
    recent_errors: List[str] = field(default_factory=list)


@dataclass
class TelemetryResult:
    """Complete telemetry collection result"""
    host: str
    port: int
    timestamp: str
    collection_time_ms: float = 0.0
    metadata: Optional[AgentMetadata] = None
    performance: Optional[PerformanceMetrics] = None
    security: Optional[SecurityPosture] = None
    topology: Optional[NetworkTopology] = None
    activity: Optional[ActivityIndicators] = None
    errors: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


class TelemetryCollector:
    """
    Comprehensive telemetry collection from AI agent frameworks.
    
    Gathers metadata, performance metrics, security posture,
    network topology, and activity indicators.
    """
    
    # Common health/status endpoints
    HEALTH_ENDPOINTS = [
        '/health', '/healthz', '/status', '/api/status', '/ping', '/ready'
    ]
    
    # Metadata endpoints
    METADATA_ENDPOINTS = [
        '/api/info', '/api/metadata', '/api/version', '/version', '/info',
        '/api/openapi.json', '/api/docs', '/swagger.json'
    ]
    
    # Security headers to check
    SECURITY_HEADERS = [
        'X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection',
        'Content-Security-Policy', 'Strict-Transport-Security',
        'Referrer-Policy', 'Permissions-Policy'
    ]
    
    # Rate limit headers
    RATE_LIMIT_HEADERS = [
        'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset',
        'RateLimit-Limit', 'RateLimit-Remaining', 'Retry-After'
    ]
    
    # CDN/Proxy indicators
    CDN_INDICATORS = {
        'cloudflare': ['cf-ray', 'cf-cache-status', 'server-timing'],
        'aws_lb': ['x-amzn-requestid', 'x-amzn-trace-id'],
        'nginx': ['x-powered-by', 'server'],
        'akamai': ['x-akamai-transformed', 'x-check-cacheable'],
        'fastly': ['x-served-by', 'x-cache'],
        'google_cloud': ['via', 'x-google-gfe'],
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CogniWatch/1.0 (Telemetry Collector)'
        })
    
    def collect(self, host: str, port: int, 
                https: bool = False,
                api_key: Optional[str] = None) -> TelemetryResult:
        """
        Collect comprehensive telemetry from target.
        
        Args:
            host: Target host
            port: Target port
            https: Use HTTPS
            api_key: Optional API key for authenticated endpoints
            
        Returns:
            TelemetryResult with all collected data
        """
        start_time = datetime.now()
        result = TelemetryResult(
            host=host,
            port=port,
            timestamp=datetime.utcnow().isoformat()
        )
        
        base_url = f"{'https' if https else 'http'}://{host}:{port}"
        
        # Add API key to headers if provided
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        
        # Collect metadata
        try:
            result.metadata = self._collect_metadata(base_url)
        except Exception as e:
            result.errors.append(f"Metadata collection error: {e}")
        
        # Collect performance metrics
        try:
            result.performance = self._collect_performance_metrics(base_url)
        except Exception as e:
            result.errors.append(f"Performance metrics error: {e}")
        
        # Collect security posture
        try:
            result.security = self._collect_security_posture(base_url)
        except Exception as e:
            result.errors.append(f"Security posture error: {e}")
        
        # Collect network topology
        try:
            result.topology = self._collect_network_topology(host, port, base_url)
        except Exception as e:
            result.errors.append(f"Network topology error: {e}")
        
        # Collect activity indicators
        try:
            result.activity = self._collect_activity_indicators(base_url)
        except Exception as e:
            result.errors.append(f"Activity indicators error: {e}")
        
        result.collection_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate overall confidence score
        result.confidence_score = self._calculate_confidence_score(result)
        
        return result
    
    def _collect_metadata(self, base_url: str) -> AgentMetadata:
        """Collect agent metadata from info endpoints"""
        metadata = AgentMetadata()
        
        for endpoint in self.METADATA_ENDPOINTS:
            try:
                url = f"{base_url}{endpoint}"
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Extract version info
                        for key in ['version', 'api_version', 'v']:
                            if key in data:
                                metadata.version = str(data[key])
                                break
                        
                        # Extract framework name
                        for key in ['framework', 'service', 'name', 'application']:
                            if key in data:
                                metadata.framework = str(data[key])
                                break
                        
                        # Extract model info
                        for key in ['model', 'model_name', 'llm_model']:
                            if key in data:
                                metadata.model_info = str(data[key])
                                break
                        
                        # Extract capabilities
                        if 'capabilities' in data:
                            metadata.capabilities = list(data['capabilities'])
                        elif 'features' in data:
                            metadata.capabilities = list(data['features'])
                        
                        # Extract runtime info
                        if 'runtime' in data:
                            metadata.runtime = str(data['runtime'])
                        if 'language' in data:
                            metadata.language = str(data['language'])
                        
                        # Store all additional info
                        metadata.additional_info = data
                        
                        # Got good data, stop searching
                        if metadata.framework or metadata.version:
                            break
                            
                    except json.JSONDecodeError:
                        # Not JSON, try to parse text
                        metadata.additional_info['raw_response'] = response.text[:500]
                        
            except Exception as e:
                logger.debug(f"Metadata endpoint {endpoint} failed: {e}")
                continue
        
        # If still no framework detected, try to infer from other sources
        if not metadata.framework:
            # Check if it's an OpenAI-compatible API
            if '/v1/chat/completions' in str(metadata.additional_info):
                metadata.framework = 'openai_compatible'
        
        return metadata
    
    def _collect_performance_metrics(self, base_url: str) -> PerformanceMetrics:
        """Collect performance metrics through repeated requests"""
        metrics = PerformanceMetrics()
        latencies = []
        successful = 0
        failed = 0
        
        # Make several requests to measure performance
        test_endpoints = ['/'] + self.HEALTH_ENDPOINTS
        
        for endpoint in test_endpoints[:5]:
            for i in range(3):  # 3 attempts per endpoint
                try:
                    url = f"{base_url}{endpoint}"
                    start = time.time()
                    response = self.session.get(url, timeout=self.timeout)
                    latency_ms = (time.time() - start) * 1000
                    
                    latencies.append(latency_ms)
                    
                    if response.status_code < 400:
                        successful += 1
                    else:
                        failed += 1
                        
                    # Look for token usage in response
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            usage = data.get('usage', {})
                            if isinstance(usage, dict):
                                # Could calculate tokens/sec if we had request timing
                                pass
                    except:
                        pass
                        
                except Exception as e:
                    failed += 1
                    logger.debug(f"Performance test request failed: {e}")
        
        if latencies:
            latencies.sort()
            metrics.samples = len(latencies)
            metrics.avg_response_time_ms = sum(latencies) / len(latencies)
            metrics.min_response_time_ms = min(latencies)
            metrics.max_response_time_ms = max(latencies)
            metrics.p50_latency_ms = latencies[int(len(latencies) * 0.5)]
            metrics.p95_latency_ms = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else metrics.max_response_time_ms
            metrics.p99_latency_ms = latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else metrics.max_response_time_ms
        
        total = successful + failed
        if total > 0:
            metrics.success_rate = successful / total
            metrics.error_rate = failed / total
        
        return metrics
    
    def _collect_security_posture(self, base_url: str) -> SecurityPosture:
        """Analyze security configuration"""
        security = SecurityPosture()
        
        try:
            # Make request to analyze headers
            response = self.session.get(base_url, timeout=self.timeout, allow_redirects=False)
            headers = response.headers
            
            # Check for authentication requirements
            if response.status_code == 401:
                security.authentication_required = True
                
                # Try to determine auth type
                www_auth = headers.get('WWW-Authenticate', '')
                if 'Bearer' in www_auth:
                    security.auth_type = 'bearer'
                elif 'Basic' in www_auth:
                    security.auth_type = 'basic'
                else:
                    security.auth_type = 'unknown'
            elif response.status_code == 403:
                security.authentication_required = True
                security.auth_type = 'api_key'  # Likely
            
            # Check CORS
            if 'Access-Control-Allow-Origin' in headers:
                security.cors_enabled = True
                security.cors_origins.append(headers['Access-Control-Allow-Origin'])
            
            # Check rate limiting
            for header in self.RATE_LIMIT_HEADERS:
                if header in headers:
                    security.rate_limiting_detected = True
                    security.rate_limit_headers[header] = headers[header]
            
            # Check security headers
            for header in self.SECURITY_HEADERS:
                if header in headers:
                    security.security_headers[header] = headers[header]
            
            # Check HTTPS redirect
            if response.status_code in [301, 302, 307, 308]:
                location = headers.get('Location', '')
                if location.startswith('https://'):
                    security.https_only = True
            
        except Exception as e:
            logger.debug(f"Security analysis error: {e}")
        
        # Analyze exposed ports (would need port scan for full picture)
        security.open_ports = [security.port] if hasattr(security, 'port') else []
        
        # Calculate exposure level
        vulnerabilities = []
        
        if not security.https_only:
            vulnerabilities.append("No HTTPS enforcement")
        
        if not security.security_headers:
            vulnerabilities.append("Missing security headers")
        
        if security.cors_enabled and '*' in security.cors_origins:
            vulnerabilities.append("Permissive CORS (wildcard)")
        
        if not security.rate_limiting_detected:
            vulnerabilities.append("No rate limiting detected")
        
        security.vulnerabilities = vulnerabilities
        
        # Determine exposure level
        if len(vulnerabilities) >= 3:
            security.exposure_level = 'high'
        elif len(vulnerabilities) >= 2:
            security.exposure_level = 'moderate'
        else:
            security.exposure_level = 'minimal'
        
        return security
    
    def _collect_network_topology(self, host: str, port: int, base_url: str) -> NetworkTopology:
        """Analyze network topology"""
        topology = NetworkTopology()
        topology.ip_address = host
        topology.hostname = host
        
        try:
            response = self.session.get(base_url, timeout=self.timeout, allow_redirects=False)
            headers = response.headers
            
            # Check for proxy/CDN indicators
            for provider, indicator_headers in self.CDN_INDICATORS.items():
                for header in indicator_headers:
                    if header.lower() in [h.lower() for h in headers.keys()]:
                        topology.behind_proxy = True
                        topology.proxy_type = provider
                        
                        if provider in ['cloudflare', 'akamai', 'fastly']:
                            topology.behind_cdn = True
                            topology.cdn_provider = provider
                        elif provider in ['aws_lb', 'nginx']:
                            topology.behind_load_balancer = True
                        break
            
            # Check for common proxy headers
            if 'X-Forwarded-For' in headers or 'X-Real-IP' in headers:
                topology.behind_proxy = True
                if not topology.proxy_type:
                    topology.proxy_type = 'unknown'
            
            # Check for load balancer indicators
            if 'X-Request-ID' in headers or 'X-Correlation-ID' in headers:
                topology.behind_load_balancer = True
                
        except Exception as e:
            logger.debug(f"Network topology error: {e}")
        
        # Basic DNS lookup (simplified)
        import socket
        try:
            ip = socket.gethostbyname(host)
            topology.ip_address = ip
        except:
            pass
        
        return topology
    
    def _collect_activity_indicators(self, base_url: str) -> ActivityIndicators:
        """Collect current activity indicators"""
        activity = ActivityIndicators()
        
        try:
            # Try health endpoint
            for endpoint in self.HEALTH_ENDPOINTS:
                try:
                    url = f"{base_url}{endpoint}"
                    response = self.session.get(url, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        activity.health_status = 'healthy'
                        
                        try:
                            data = response.json()
                            
                            # Look for session info
                            if 'sessions' in data:
                                sessions = data['sessions']
                                if isinstance(sessions, int):
                                    activity.active_sessions = sessions
                                elif isinstance(sessions, list):
                                    activity.active_sessions = len(sessions)
                            
                            # Look for active connections
                            if 'connections' in data:
                                activity.concurrent_requests = data['connections']
                            
                            # Look for uptime
                            if 'uptime' in data:
                                activity.uptime_seconds = int(data['uptime'])
                            
                            # Look for request counts
                            if 'requests' in data:
                                activity.requests_today = int(data['requests'])
                            
                        except json.JSONDecodeError:
                            pass
                        
                        activity.last_activity = datetime.utcnow()
                        break
                        
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Activity indicators error: {e}")
        
        return activity
    
    def _calculate_confidence_score(self, result: TelemetryResult) -> float:
        """Calculate overall confidence score for collected telemetry"""
        score = 0.0
        components = 0
        
        if result.metadata and (result.metadata.framework or result.metadata.version):
            score += 0.25
            components += 1
        
        if result.performance and result.performance.samples > 0:
            score += 0.20
            components += 1
        
        if result.security and result.security.exposure_level != 'unknown':
            score += 0.20
            components += 1
        
        if result.topology and (result.topology.behind_proxy or result.topology.behind_cdn):
            score += 0.15
            components += 1
        
        if result.activity and result.activity.health_status != 'unknown':
            score += 0.20
            components += 1
        
        if components > 0:
            return score / components * (1 + min(components * 0.1, 0.5))
        
        return 0.0
    
    def batch_collect(self, targets: List[Tuple[str, int]], 
                      max_workers: int = 5) -> List[TelemetryResult]:
        """Collect telemetry from multiple targets"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {
                executor.submit(self.collect, host, port): (host, port)
                for host, port in targets
            }
            
            for future in as_completed(future_to_target):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    host, port = future_to_target[future]
                    logger.error(f"Telemetry collection failed for {host}:{port}: {e}")
        
        return results


def main():
    """Test telemetry collector on local targets"""
    import json
    
    print("\n📊 CogniWatch Telemetry Collector\n")
    
    collector = TelemetryCollector(timeout=3.0)
    
    # Test targets
    targets = [
        ("192.168.0.245", 18789),  # Neo gateway
        ("localhost", 8000),
    ]
    
    for host, port in targets:
        print(f"\n{'='*60}")
        print(f"Target: {host}:{port}")
        print('='*60)
        
        result = collector.collect(host, port)
        
        print(f"\n⏱️  Collection Time: {result.collection_time_ms:.2f}ms")
        print(f"📈 Confidence Score: {result.confidence_score:.2f}")
        
        if result.metadata:
            print(f"\n🤖 Metadata:")
            if result.metadata.framework:
                print(f"   Framework: {result.metadata.framework}")
            if result.metadata.version:
                print(f"   Version: {result.metadata.version}")
            if result.metadata.model_info:
                print(f"   Model: {result.metadata.model_info}")
            if result.metadata.capabilities:
                print(f"   Capabilities: {', '.join(result.metadata.capabilities[:5])}")
        
        if result.performance:
            print(f"\n⚡ Performance:")
            print(f"   Avg Response: {result.performance.avg_response_time_ms:.2f}ms")
            print(f"   P50 Latency: {result.performance.p50_latency_ms:.2f}ms")
            print(f"   P95 Latency: {result.performance.p95_latency_ms:.2f}ms")
            print(f"   Success Rate: {result.performance.success_rate:.1%}")
            print(f"   Samples: {result.performance.samples}")
        
        if result.security:
            print(f"\n🔒 Security Posture:")
            print(f"   Auth Required: {result.security.authentication_required}")
            if result.security.auth_type:
                print(f"   Auth Type: {result.security.auth_type}")
            print(f"   CORS Enabled: {result.security.cors_enabled}")
            print(f"   Rate Limiting: {result.security.rate_limiting_detected}")
            print(f"   Exposure Level: {result.security.exposure_level}")
            if result.security.vulnerabilities:
                print(f"   Vulnerabilities: {', '.join(result.security.vulnerabilities)}")
        
        if result.topology:
            print(f"\n🌐 Network Topology:")
            print(f"   IP: {result.topology.ip_address}")
            print(f"   Behind Proxy: {result.topology.behind_proxy}")
            print(f"   Behind CDN: {result.topology.behind_cdn}")
            if result.topology.cdn_provider:
                print(f"   CDN Provider: {result.topology.cdn_provider}")
            print(f"   Behind LB: {result.topology.behind_load_balancer}")
        
        if result.activity:
            print(f"\n📊 Activity:")
            print(f"   Health Status: {result.activity.health_status}")
            print(f"   Active Sessions: {result.activity.active_sessions}")
            print(f"   Concurrent Requests: {result.activity.concurrent_requests}")
            if result.activity.uptime_seconds:
                hours = result.activity.uptime_seconds // 3600
                print(f"   Uptime: {hours}h")
        
        if result.errors:
            print(f"\n⚠️  Errors:")
            for error in result.errors:
                print(f"   • {error}")
        
        # Save detailed results
        detailed_output = {
            'host': host,
            'port': port,
            'timestamp': result.timestamp,
            'collection_time_ms': result.collection_time_ms,
            'confidence_score': result.confidence_score,
            'metadata': result.metadata.__dict__ if result.metadata else None,
            'performance': result.performance.__dict__ if result.performance else None,
            'security': result.security.__dict__ if result.security else None,
            'topology': result.topology.__dict__ if result.topology else None,
            'activity': result.activity.__dict__ if result.activity else None,
            'errors': result.errors
        }
        
        output_file = f"/tmp/telemetry_{host.replace('.', '_')}_{port}.json"
        with open(output_file, 'w') as f:
            json.dump(detailed_output, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {output_file}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
