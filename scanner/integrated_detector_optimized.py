#!/usr/bin/env python3
"""
CogniWatch - OPTIMIZED Integrated Multi-Layer Detector

Optimizations:
- Parallel layer execution (HTTP + API + TLS run concurrently)
- LRU caching for detection results
- Early exit optimization
- Memory-efficient result streaming
- Lazy module loading
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from collections import OrderedDict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy imports - only load when needed
class LazyLoader:
    def __init__(self, module_path: str, module_name: str):
        self.module_path = module_path
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name):
        if self._module is None:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            self._module = __import__(self.module_name, fromlist=[''])
        return getattr(self._module, name)


@dataclass
class LayerResults:
    """Results from all detection layers"""
    http: Optional[Any] = None
    api: Optional[Any] = None
    websocket: Optional[Any] = None
    tls: Optional[Any] = None
    telemetry: Optional[Any] = None


@dataclass
class IntegratedDetectionResult:
    """Comprehensive detection result"""
    host: str
    port: int
    timestamp: str
    detection_time_ms: float = 0.0
    layer_results: LayerResults = field(default_factory=LayerResults)
    top_framework: Optional[str] = None
    confidence: float = 0.0
    confidence_level: str = "unknown"
    framework_scores: List[Dict] = field(default_factory=list)
    all_signals: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    telemetry: Optional[Any] = None
    detection_quality: str = "poor"
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'host': self.host,
            'port': self.port,
            'timestamp': self.timestamp,
            'detection_time_ms': self.detection_time_ms,
            'top_framework': self.top_framework,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level,
            'detection_quality': self.detection_quality,
            'recommendation': self.recommendation,
            'framework_scores': self.framework_scores,
            'all_signals': self.all_signals,
            'evidence': self.evidence,
        }


class DetectionCache:
    """LRU cache for detection results with TTL"""
    
    def __init__(self, max_size=10000, ttl_seconds=300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.now() - entry['timestamp']).total_seconds()
        return age > self.ttl_seconds
    
    def get(self, key: str) -> Optional[IntegratedDetectionResult]:
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry):
                    self.cache.move_to_end(key)
                    self.hits += 1
                    return entry['result']
                else:
                    # Remove expired entry
                    del self.cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, result: IntegratedDetectionResult):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            
            self.cache[key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def clear(self):
        with self.lock:
            self.cache.clear()


class IntegratedDetector:
    """
    Optimized multi-layer integrated detector.
    
    Key optimizations:
    1. Parallel layer execution (independent layers run concurrently)
    2. Detection caching (avoid redundant probes)
    3. Early exit (skip detection if port closed)
    4. Lazy loading (load modules only when needed)
    5. Memory-efficient processing
    """
    
    def __init__(self, timeout: float = 3.0, enable_layers: Optional[List[str]] = None,
                 enable_caching: bool = True, enable_parallel: bool = True):
        """
        Initialize optimized detector.
        
        Args:
            timeout: Default timeout for operations
            enable_layers: Layers to enable (default: all)
            enable_caching: Enable result caching
            enable_parallel: Enable parallel layer execution
        """
        self.timeout = timeout
        self.enabled_layers = enable_layers or ['http', 'api', 'websocket', 'tls', 'telemetry']
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel
        
        # Lazy-loaded modules
        self._http_fingerprinter = None
        self._api_analyzer = None
        self._websocket_detector = None
        self._tls_fingerprinter = None
        self._telemetry_collector = None
        self._confidence_engine = None
        
        # Cache
        self.cache = DetectionCache(max_size=10000, ttl_seconds=300)
    
    @property
    def http_fingerprinter(self):
        """Lazy load HTTP fingerprinter"""
        if self._http_fingerprinter is None:
            from .http_fingerprinter import HTTPFingerprinter
            self._http_fingerprinter = HTTPFingerprinter(timeout=self.timeout)
        return self._http_fingerprinter
    
    @property
    def api_analyzer(self):
        """Lazy load API analyzer"""
        if self._api_analyzer is None:
            from .api_analyzer import APIAnalyzer
            self._api_analyzer = APIAnalyzer(timeout=self.timeout)
        return self._api_analyzer
    
    @property
    def websocket_detector(self):
        """Lazy load WebSocket detector"""
        if self._websocket_detector is None:
            from .websocket_detector import WebSocketDetector
            self._websocket_detector = WebSocketDetector(timeout=self.timeout)
        return self._websocket_detector
    
    @property
    def tls_fingerprinter(self):
        """Lazy load TLS fingerprinter"""
        if self._tls_fingerprinter is None:
            from .tls_fingerprinter import TLSFingerprinter
            self._tls_fingerprinter = TLSFingerprinter(timeout=self.timeout)
        return self._tls_fingerprinter
    
    @property
    def telemetry_collector(self):
        """Lazy load telemetry collector"""
        if self._telemetry_collector is None:
            from .telemetry_collector import TelemetryCollector
            self._telemetry_collector = TelemetryCollector(timeout=self.timeout)
        return self._telemetry_collector
    
    @property
    def confidence_engine(self):
        """Lazy load confidence engine"""
        if self._confidence_engine is None:
            from .confidence_engine import ConfidenceEngine
            self._confidence_engine = ConfidenceEngine()
        return self._confidence_engine
    
    def detect(self, host: str, port: int, 
               https: bool = False,
               ws_path: Optional[str] = None,
               api_key: Optional[str] = None,
               skip_cache: bool = False) -> IntegratedDetectionResult:
        """
        Perform comprehensive multi-layer detection with optimizations.
        
        OPTIMIZATIONS:
        1. Check cache first (skip if cached)
        2. Early exit if port is closed
        3. Run independent layers in parallel
        4. Cache results for future calls
        
        Args:
            host: Target host
            port: Target port
            https: Use HTTPS
            ws_path: WebSocket path
            api_key: API key for authenticated endpoints
            skip_cache: Skip cache check (force fresh detection)
            
        Returns:
            IntegratedDetectionResult
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"{host}:{port}:{https}"
        if not skip_cache and self.enable_caching:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"✅ Cache hit for {host}:{port}")
                return cached
        
        logger.debug(f"🔍 Detecting {host}:{port}")
        
        result = IntegratedDetectionResult(
            host=host,
            port=port,
            timestamp=datetime.utcnow().isoformat()
        )
        
        base_url = f"https://{host}:{port}" if https else f"http://{host}:{port}"
        ws_url = f"wss://{host}:{port}" if https else f"ws://{host}:{port}"
        if ws_path:
            ws_url = f"{ws_url}{ws_path}"
        
        # Early exit: Check if port is open before running detection layers
        port_open = self._check_port_open(host, port)
        if not port_open:
            result.detection_time_ms = (datetime.now() - start_time).total_seconds()
            result.recommendation = "Port is closed - skip further detection"
            return result
        
        layer_signals = []
        layer_results = LayerResults()
        
        if self.enable_parallel:
            # PARALLEL EXECUTION: Run independent layers concurrently
            layer_results, layer_signals = self._detect_parallel(
                host, port, base_url, ws_url, https, ws_path, api_key
            )
        else:
            # SEQUENTIAL EXECUTION (fallback)
            layer_results, layer_signals = self._detect_sequential(
                host, port, base_url, ws_url, https, ws_path, api_key
            )
        
        result.layer_results = layer_results
        
        # Calculate confidence scores
        if layer_signals:
            confidence_result = self.confidence_engine.calculate(host, port, layer_signals)
            
            result.top_framework = confidence_result.top_framework
            result.confidence = confidence_result.top_confidence
            result.confidence_level = self._confidence_level_str(result.confidence)
            result.detection_quality = confidence_result.detection_quality
            result.recommendation = confidence_result.recommendation
            
            result.framework_scores = [
                {
                    'framework': fs.framework,
                    'bayesian_probability': fs.bayesian_probability,
                    'confidence_level': fs.confidence_level,
                    'signals_count': fs.signals_count,
                }
                for fs in confidence_result.frameworks_detected[:5]
            ]
        
        # Aggregate signals and evidence
        result.all_signals = self._aggregate_signals(result.layer_results)
        result.evidence = self._aggregate_evidence(result.layer_results)
        
        result.detection_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Cache result
        if self.enable_caching:
            self.cache.set(cache_key, result)
        
        return result
    
    def _check_port_open(self, host: str, port: int) -> bool:
        """Quick port check (early exit optimization)"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Fast timeout
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _detect_parallel(self, host: str, port: int, base_url: str, ws_url: str,
                        https: bool, ws_path: Optional[str], 
                        api_key: Optional[str]) -> Tuple[LayerResults, List]:
        """Run detection layers in parallel where possible"""
        
        layer_results = LayerResults()
        layer_signals = []
        
        # Independent layers can run in parallel
        independent_layers = []
        
        if 'http' in self.enabled_layers:
            independent_layers.append(('http', self._run_http_detection, (base_url,)))
        
        if 'api' in self.enabled_layers:
            independent_layers.append(('api', self._run_api_detection, (base_url,)))
        
        if 'tls' in self.enabled_layers:
            independent_layers.append(('tls', self._run_tls_detection, (host, port)))
        
        # Run independent layers in parallel
        if independent_layers:
            with ThreadPoolExecutor(max_workers=len(independent_layers)) as executor:
                futures = {
                    executor.submit(func, *args): name
                    for name, func, args in independent_layers
                }
                
                for future in as_completed(futures):
                    layer_name = futures[future]
                    try:
                        result, signal = future.result()
                        setattr(layer_results, layer_name, result)
                        if signal:
                            layer_signals.append(signal)
                    except Exception as e:
                        logger.debug(f"{layer_name} detection failed: {e}")
        
        # WebSocket detection (sequential - needs specific path)
        if 'websocket' in self.enabled_layers:
            ws_result, ws_signal = self._run_websocket_detection(ws_url, ws_path)
            layer_results.websocket = ws_result
            if ws_signal:
                layer_signals.append(ws_signal)
        
        # Telemetry (can run in parallel but usually quick enough)
        if 'telemetry' in self.enabled_layers:
            telemetry_result, telemetry_signal = self._run_telemetry_collection(
                host, port, https, api_key
            )
            layer_results.telemetry = telemetry_result
            if telemetry_signal:
                layer_signals.append(telemetry_signal)
        
        return layer_results, layer_signals
    
    def _detect_sequential(self, host: str, port: int, base_url: str, ws_url: str,
                          https: bool, ws_path: Optional[str],
                          api_key: Optional[str]) -> Tuple[LayerResults, List]:
        """Run detection layers sequentially (fallback)"""
        logger.info(f"🔍 Running SEQUENTIAL detection on {base_url}")
        
        layer_results = LayerResults()
        layer_signals = []
        
        # Layer 1: HTTP Fingerprinting
        if 'http' in self.enabled_layers:
            result, signal = self._run_http_detection(base_url)
            layer_results.http = result
            if signal:
                layer_signals.append(signal)
        
        # Layer 2: API Behavioral Analysis
        if 'api' in self.enabled_layers:
            result, signal = self._run_api_detection(base_url)
            layer_results.api = result
            if signal:
                layer_signals.append(signal)
        
        # Layer 3: WebSocket Detection
        if 'websocket' in self.enabled_layers:
            result, signal = self._run_websocket_detection(ws_url, ws_path)
            layer_results.websocket = result
            if signal:
                layer_signals.append(signal)
        
        # Layer 4: TLS Fingerprinting
        if 'tls' in self.enabled_layers:
            result, signal = self._run_tls_detection(host, port)
            layer_results.tls = result
            if signal:
                layer_signals.append(signal)
        
        # Layer 5: Telemetry Collection
        if 'telemetry' in self.enabled_layers:
            result, signal = self._run_telemetry_collection(host, port, https, api_key)
            layer_results.telemetry = result
            if signal:
                layer_signals.append(signal)
        
        return layer_results, layer_signals
    
    def _run_http_detection(self, base_url: str) -> Tuple:
        """Run HTTP fingerprinting"""
        result = self.http_fingerprinter.fingerprint(base_url)
        signal = self._convert_http_to_signal(result) if result else None
        return result, signal
    
    def _run_api_detection(self, base_url: str) -> Tuple:
        """Run API analysis"""
        result = self.api_analyzer.analyze(base_url)
        signal = self._convert_api_to_signal(result) if result else None
        return result, signal
    
    def _run_websocket_detection(self, ws_url: str, ws_path: Optional[str]) -> Tuple:
        """Run WebSocket detection"""
        ws_paths = [ws_path] if ws_path else ['/', '/ws', '/socket', '/api/ws']
        
        for path in ws_paths:
            test_url = f"{ws_url.rstrip('/')}{path}"
            result = self.websocket_detector.detect(test_url)
            
            if result.connection_success:
                signal = self._convert_websocket_to_signal(result) if result else None
                return result, signal
        
        return self.websocket_detector.WebSocketAnalysisResult(connection_success=False), None
    
    def _run_tls_detection(self, host: str, port: int) -> Tuple:
        """Run TLS fingerprinting"""
        result = self.tls_fingerprinter.fingerprint(host, port)
        signal = self._convert_tls_to_signal(result) if result else None
        return result, signal
    
    def _run_telemetry_collection(self, host: str, port: int, 
                                  https: bool, api_key: Optional[str]) -> Tuple:
        """Run telemetry collection"""
        result = self.telemetry_collector.collect(host, port, https=https, api_key=api_key)
        signal = self._convert_telemetry_to_signal(result) if result and result.metadata else None
        return result, signal
    
    # Signal conversion methods (same as original, keeping for compatibility)
    def _convert_http_to_signal(self, fingerprint):
        """Convert HTTP fingerprint to signal"""
        if not fingerprint or not fingerprint.framework_indicators:
            return None
        
        confidence = max(fingerprint.confidence_signals.values()) if fingerprint.confidence_signals else 0.5
        
        return self.confidence_engine.create_signal(
            layer=self.confidence_engine.DetectionLayer.HTTP_FINGERPRINT,
            confidence=confidence,
            signals={
                'framework_indicators': fingerprint.framework_indicators,
                'server_header': fingerprint.server_header,
            },
            evidence=[
                f"Server: {fingerprint.server_header or 'Not set'}",
                f"Title: {fingerprint.title or 'Not found'}",
            ],
            quality_score=0.9 if fingerprint.response_size > 0 else 0.5
        )
    
    def _convert_api_to_signal(self, analysis):
        """Convert API analysis to signal"""
        if not analysis or not analysis.framework_indicators:
            return None
        
        confidence = max(analysis.confidence_signals.values()) if analysis.confidence_signals else 0.5
        
        return self.confidence_engine.create_signal(
            layer=self.confidence_engine.DetectionLayer.API_BEHAVIORAL,
            confidence=confidence,
            signals={
                'framework': analysis.detected_framework,
                'framework_indicators': analysis.framework_indicators,
            },
            evidence=[f"API endpoints: {analysis.endpoints_responding}"],
            quality_score=0.95 if analysis.endpoints_responding > 2 else 0.7
        )
    
    def _convert_websocket_to_signal(self, ws_result):
        """Convert WebSocket detection to signal"""
        if not ws_result or not ws_result.connection_success:
            return None
        
        confidence = max(ws_result.confidence_signals.values()) if ws_result.confidence_signals else 0.6
        
        return self.confidence_engine.create_signal(
            layer=self.confidence_engine.DetectionLayer.WEBSOCKET,
            confidence=confidence,
            signals={
                'framework': ws_result.detected_framework,
                'connection_success': ws_result.connection_success,
            },
            evidence=[f"WebSocket: {'connected' if ws_result.connection_success else 'failed'}"],
            quality_score=0.8 if ws_result.connection_success else 0.3
        )
    
    def _convert_tls_to_signal(self, tls_result):
        """Convert TLS fingerprint to signal"""
        if not tls_result or not tls_result.connection_success:
            return None
        
        confidence = max(tls_result.confidence_signals.values()) if tls_result.confidence_signals else 0.3
        
        return self.confidence_engine.create_signal(
            layer=self.confidence_engine.DetectionLayer.TLS_FINGERPRINT,
            confidence=confidence,
            signals={
                'tls_library': tls_result.tls_library_guess,
            },
            evidence=[f"TLS: {'secured' if tls_result.connection_success else 'not secured'}"],
            quality_score=0.7
        )
    
    def _convert_telemetry_to_signal(self, telemetry):
        """Convert telemetry to signal"""
        if not telemetry or not telemetry.metadata:
            return None
        
        confidence = telemetry.confidence_score
        if confidence < 0.3:
            return None
        
        return self.confidence_engine.create_signal(
            layer=self.confidence_engine.DetectionLayer.SIGNATURE_MATCH,
            confidence=confidence,
            signals={
                'metadata': telemetry.metadata.__dict__ if telemetry.metadata else None,
            },
            evidence=[f"Framework: {telemetry.metadata.framework}"],
            quality_score=0.85
        )
    
    def _aggregate_signals(self, layer_results: LayerResults) -> List[str]:
        """Aggregate all signals from all layers"""
        signals = []
        
        if layer_results.http and layer_results.http.framework_indicators:
            signals.extend(layer_results.http.framework_indicators)
        
        if layer_results.api and layer_results.api.framework_indicators:
            signals.extend(layer_results.api.framework_indicators)
        
        if layer_results.websocket and layer_results.websocket.framework_indicators:
            signals.extend(layer_results.websocket.framework_indicators)
        
        if layer_results.tls and layer_results.tls.framework_indicators:
            signals.extend(layer_results.tls.framework_indicators)
        
        return list(set(signals))
    
    def _aggregate_evidence(self, layer_results: LayerResults) -> List[str]:
        """Aggregate all evidence from all layers"""
        evidence = []
        
        if layer_results.http:
            if layer_results.http.server_header:
                evidence.append(f"HTTP Server: {layer_results.http.server_header}")
            if layer_results.http.title:
                evidence.append(f"HTTP Title: {layer_results.http.title}")
        
        if layer_results.api and layer_results.api.endpoints_responding:
            evidence.append(f"API endpoints: {layer_results.api.endpoints_responding}")
        
        if layer_results.websocket:
            status = "connected" if layer_results.websocket.connection_success else "failed"
            evidence.append(f"WebSocket: {status}")
        
        if layer_results.tls:
            status = "secured" if layer_results.tls.connection_success else "not secured"
            evidence.append(f"TLS: {status}")
        
        return evidence
    
    def _confidence_level_str(self, confidence: float) -> str:
        """Convert confidence score to level string"""
        if confidence >= 0.85:
            return 'very_high'
        elif confidence >= 0.70:
            return 'high'
        elif confidence >= 0.50:
            return 'medium'
        elif confidence >= 0.30:
            return 'low'
        else:
            return 'very_low'
    
    def clear_cache(self):
        """Clear detection cache"""
        self.cache.clear()


def main():
    """Test optimized detector"""
    print("\n🔍 CogniWatch OPTIMIZED Integrated Detector\n")
    print("Optimizations:")
    print("  • Parallel layer execution")
    print("  • LRU detection cache")
    print("  • Early exit optimization")
    print("  • Lazy module loading\n")
    
    detector = IntegratedDetector(
        timeout=2.0,
        enable_caching=True,
        enable_parallel=True
    )
    
    # Test target
    targets = [
        {'host': '192.168.0.245', 'port': 18789, 'https': False},
    ]
    
    for target in targets:
        print(f"\n{'='*60}")
        print(f"Target: {target['host']}:{target['port']}")
        print('='*60)
        
        # First call (cache miss)
        result1 = detector.detect(**target)
        print(f"\n⏱️  First detection: {result1.detection_time_ms:.2f}ms")
        print(f"🎯 Framework: {result1.top_framework}")
        print(f"   Confidence: {result1.confidence:.1%}")
        
        # Second call (cache hit)
        result2 = detector.detect(**target, skip_cache=False)
        print(f"\n⏱️  Cached detection: {result2.detection_time_ms:.2f}ms")
        print(f"   (Should be ~0ms)")
        
        print(f"\n📊 Cache hit rate: {detector.cache.hit_rate:.1%}")
        print(f"   Cache entries: {len(detector.cache.cache)}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
