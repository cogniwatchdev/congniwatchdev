#!/usr/bin/env python3
"""
CogniWatch - Integrated Multi-Layer Detector
Combines all detection modules for comprehensive agent framework identification

Integration of:
- HTTP Fingerprinting
- API Behavioral Analysis
- WebSocket Detection
- TLS/SSL Fingerprinting
- Confidence Scoring Engine
- Telemetry Collection
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from datetime import datetime

try:
    from .http_fingerprinter import HTTPFingerprinter, HTTPFingerprint
    from .api_analyzer import APIAnalyzer, APIAnalysisResult
    from .websocket_detector import WebSocketDetector, WebSocketAnalysisResult
    from .tls_fingerprinter import TLSFingerprinter, TLSFingerprintResult
    from .confidence_engine import ConfidenceEngine, LayerSignal, DetectionLayer
    from .telemetry_collector import TelemetryCollector, TelemetryResult
    from .agent_card_detector import AgentCardDetector
    from .itt_fingerprinter import ITTFingerprinter, ITTFingerprint
except ImportError:
    from http_fingerprinter import HTTPFingerprinter, HTTPFingerprint
    from api_analyzer import APIAnalyzer, APIAnalysisResult
    from websocket_detector import WebSocketDetector, WebSocketAnalysisResult
    from tls_fingerprinter import TLSFingerprinter, TLSFingerprintResult
    from confidence_engine import ConfidenceEngine, LayerSignal, DetectionLayer
    from telemetry_collector import TelemetryCollector, TelemetryResult
    from agent_card_detector import AgentCardDetector
    from itt_fingerprinter import ITTFingerprinter, ITTFingerprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LayerResults:
    """Results from all detection layers"""
    agent_card: Optional[Dict] = None  # A2A Agent Card detection
    http: Optional[HTTPFingerprint] = None
    api: Optional[APIAnalysisResult] = None
    websocket: Optional[WebSocketAnalysisResult] = None
    tls: Optional[TLSFingerprintResult] = None
    telemetry: Optional[TelemetryResult] = None


@dataclass
class IntegratedDetectionResult:
    """Comprehensive detection result from all layers"""
    host: str
    port: int
    timestamp: str
    detection_time_ms: float = 0.0
    
    # Layer results
    layer_results: LayerResults = field(default_factory=LayerResults)
    
    # Confidence scoring
    top_framework: Optional[str] = None
    confidence: float = 0.0
    confidence_level: str = "unknown"
    detection_type: str = "unknown"  # NEW: agent_gateway, llm_backend, inference_service
    framework_scores: List[Dict] = field(default_factory=list)
    
    # Collected signals
    all_signals: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    
    # Telemetry
    telemetry: Optional[TelemetryResult] = None
    
    # Overall assessment
    detection_quality: str = "poor"
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'host': self.host,
            'port': self.port,
            'timestamp': self.timestamp,
            'detection_time_ms': self.detection_time_ms,
            'top_framework': self.top_framework,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level,
            'detection_type': self.detection_type,  # NEW: Include detection type
            'detection_quality': self.detection_quality,
            'recommendation': self.recommendation,
            'framework_scores': self.framework_scores,
            'all_signals': self.all_signals,
            'evidence': self.evidence,
            'layer_results': {
                'http': self.layer_results.http.__dict__ if self.layer_results.http else None,
                'api': {
                    'detected_framework': self.layer_results.api.detected_framework,
                    'endpoints_responding': self.layer_results.api.endpoints_responding,
                    'framework_indicators': self.layer_results.api.framework_indicators,
                } if self.layer_results.api else None,
                'websocket': {
                    'connection_success': self.layer_results.websocket.connection_success,
                    'detected_framework': self.layer_results.websocket.detected_framework,
                } if self.layer_results.websocket else None,
                'tls': {
                    'connection_success': self.layer_results.tls.connection_success,
                    'tls_version': self.layer_results.tls.handshake_info.tls_version if self.layer_results.tls.handshake_info else None,
                } if self.layer_results.tls else None,
            },
            'telemetry': self.telemetry.__dict__ if self.telemetry else None,
        }


class IntegratedDetector:
    """
    Multi-layer integrated detector combining all detection modules.
    
    Provides comprehensive agent framework identification with
    confidence scoring and telemetry collection.
    
    Detection layers (in order of execution):
    1. Agent Card Detection (A2A) - FASTEST, HIGHEST CONFIDENCE
    2. HTTP Fingerprinting
    3. API Behavioral Analysis
    4. WebSocket Detection
    5. TLS Fingerprinting
    6. Telemetry Collection
    """
    
    def __init__(self, timeout: float = 5.0, enable_layers: Optional[List[str]] = None):
        """
        Initialize integrated detector.
        
        Args:
            timeout: Default timeout for all operations
            enable_layers: List of layers to enable (default: all)
        """
        self.timeout = timeout
        self.enabled_layers = enable_layers or ['agent_card', 'http', 'api', 'websocket', 'tls', 'telemetry', 'itt']
        
        # Initialize all detectors
        self.agent_card_detector = AgentCardDetector(timeout=timeout)
        self.http_fingerprinter = HTTPFingerprinter(timeout=timeout)
        self.api_analyzer = APIAnalyzer(timeout=timeout)
        self.websocket_detector = WebSocketDetector(timeout=timeout)
        self.tls_fingerprinter = TLSFingerprinter(timeout=timeout)
        self.telemetry_collector = TelemetryCollector(timeout=timeout)
        self.itt_fingerprinter = ITTFingerprinter()
        self.confidence_engine = ConfidenceEngine()
    
    def detect(self, host: str, port: int, 
               https: bool = False,
               ws_path: Optional[str] = None,
               api_key: Optional[str] = None) -> IntegratedDetectionResult:
        """
        Perform comprehensive multi-layer detection.
        
        Args:
            host: Target host
            port: Target port
            https: Use HTTPS for HTTP/TLS detection
            ws_path: WebSocket path (default: '/')
            api_key: Optional API key for authenticated endpoints
            
        Returns:
            IntegratedDetectionResult with all analysis
        """
        start_time = datetime.now()
        
        result = IntegratedDetectionResult(
            host=host,
            port=port,
            timestamp=datetime.utcnow().isoformat()
        )
        
        base_url = f"{'https' if https else 'http'}://{host}:{port}"
        ws_url = f"wss://{host}:{port}" if https else f"ws://{host}:{port}"
        if ws_path:
            ws_url = f"{ws_url}{ws_path}"
        
        layer_signals = []
        
        # Layer 1: Agent Card Detection (A2A) - RUN FIRST, FASTEST, HIGHEST CONFIDENCE
        if 'agent_card' in self.enabled_layers:
            logger.info(f"🔍 Running A2A Agent Card detection on {base_url}")
            agent_card_result = self.agent_card_detector.scan(host, port, https)
            
            if agent_card_result["detected"]:
                # Store raw result
                result.layer_results.agent_card = agent_card_result
                
                # Create high-confidence signal
                signal = self._convert_agent_card_to_signal(agent_card_result)
                if signal:
                    layer_signals.append(signal)
                    # Early return if direct identification found (100% confidence)
                    # Skip remaining layers for speed
                    logger.info(f"✓ Agent card detected: {agent_card_result['primary_card']['name']}")
        
        # Layer 2: HTTP Fingerprinting
        if 'http' in self.enabled_layers:
            logger.info(f"🔍 Running HTTP fingerprinting on {base_url}")
            result.layer_results.http = self.http_fingerprinter.fingerprint(base_url)
            
            if result.layer_results.http:
                signal = self._convert_http_to_signal(result.layer_results.http)
                if signal:
                    layer_signals.append(signal)
        
        # Layer 2: API Behavioral Analysis
        if 'api' in self.enabled_layers:
            logger.info(f"🔍 Running API behavioral analysis on {base_url}")
            result.layer_results.api = self.api_analyzer.analyze(base_url)
            
            if result.layer_results.api:
                signal = self._convert_api_to_signal(result.layer_results.api)
                if signal:
                    layer_signals.append(signal)
        
        # Layer 3: WebSocket Detection
        if 'websocket' in self.enabled_layers:
            logger.info(f"🔍 Running WebSocket detection on {ws_url}")
            ws_paths = [ws_path] if ws_path else ['/', '/ws', '/socket', '/api/ws']
            
            for path in ws_paths:
                test_ws_url = f"{ws_url.rstrip('/')}{path}"
                ws_result = self.websocket_detector.detect(test_ws_url)
                
                if ws_result.connection_success:
                    result.layer_results.websocket = ws_result
                    signal = self._convert_websocket_to_signal(ws_result)
                    if signal:
                        layer_signals.append(signal)
                    break
        
        # Layer 4: TLS Fingerprinting (for HTTPS)
        if 'tls' in self.enabled_layers and https:
            logger.info(f"🔍 Running TLS fingerprinting on {host}:{port}")
            result.layer_results.tls = self.tls_fingerprinter.fingerprint(host, port)
            
            if result.layer_results.tls:
                signal = self._convert_tls_to_signal(result.layer_results.tls)
                if signal:
                    layer_signals.append(signal)
        elif 'tls' in self.enabled_layers:
            # Try TLS even on HTTP port (might be misconfigured)
            result.layer_results.tls = self.tls_fingerprinter.fingerprint(host, port)
            if result.layer_results.tls and result.layer_results.tls.connection_success:
                signal = self._convert_tls_to_signal(result.layer_results.tls)
                if signal:
                    layer_signals.append(signal)
        
        # Layer 5: Telemetry Collection
        if 'telemetry' in self.enabled_layers:
            logger.info(f"🔍 Collecting telemetry from {base_url}")
            result.telemetry = self.telemetry_collector.collect(
                host, port, 
                https=https, 
                api_key=api_key
            )
            
            if result.telemetry and result.telemetry.metadata:
                signal = self._convert_telemetry_to_signal(result.telemetry)
                if signal:
                    layer_signals.append(signal)
        
        # Layer 6: ITT (Inter-Token Time) Fingerprinting - NOT IMPLEMENTED
        # if 'itt' in self.enabled_layers:
        #     logger.info(f"🔍 Running ITT fingerprinting on {base_url}")
        #     itt_result = self.detect_itt(base_url)
        #     
        #     if itt_result:
        #         result.layer_results.itt = itt_result
        #         signal = self._convert_itt_to_signal(itt_result)
        #         if signal:
        #             layer_signals.append(signal)
        
        # Calculate confidence scores
        if layer_signals:
            # Check for nearby gateways (for LLM correlation bonus)
            nearby_gateways = self._find_nearby_gateways(host)
            
            confidence_result = self.confidence_engine.calculate(
                host, port, layer_signals,
                nearby_gateways=nearby_gateways
            )
            
            result.top_framework = confidence_result.top_framework
            result.confidence = confidence_result.top_confidence
            result.confidence_level = self._confidence_level_str(result.confidence)
            result.detection_type = confidence_result.detection_type  # NEW: Set detection type
            result.detection_quality = confidence_result.detection_quality
            result.recommendation = confidence_result.recommendation
            
            result.framework_scores = [
                {
                    'framework': fs.framework,
                    'bayesian_probability': fs.bayesian_probability,
                    'confidence_level': fs.confidence_level,
                    'detection_type': fs.detection_type,  # NEW: Include type per framework
                    'signals_count': fs.signals_count,
                }
                for fs in confidence_result.frameworks_detected[:5]
            ]
        
        # Aggregate all signals and evidence
        result.all_signals = self._aggregate_signals(result.layer_results, result.telemetry)
        result.evidence = self._aggregate_evidence(result.layer_results, result.telemetry)
        
        result.detection_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return result
    
    def _convert_agent_card_to_signal(self, card_result: Dict) -> Optional[LayerSignal]:
        """
        Convert A2A Agent Card detection to confidence engine signal.
        
        This is the HIGHEST CONFIDENCE signal - direct self-identification.
        
        Args:
            card_result: Result dict from AgentCardDetector.scan()
            
        Returns:
            LayerSignal with 1.0 confidence for direct identification
        """
        if not card_result.get("detected"):
            return None
        
        # Extract info from primary card
        primary_card = card_result.get("primary_card", {})
        frameworks = card_result.get("frameworks_identified", {})
        
        # Build evidence list
        evidence = [
            f"✓ Agent Card Found: {primary_card.get('name', 'Unknown')}",
            f"Source: {primary_card.get('source_url', 'Unknown')}",
        ]
        
        if primary_card.get('version'):
            evidence.append(f"Version: {primary_card['version']}")
        
        if primary_card.get('author'):
            evidence.append(f"Author: {primary_card['author']}")
        
        if frameworks:
            evidence.append(f"Frameworks identified: {', '.join(frameworks.keys())}")
        
        # Get the highest confidence framework
        top_framework = max(frameworks.keys(), key=lambda k: frameworks[k]) if frameworks else None
        
        # Create signal with VERY HIGH confidence (direct identification)
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.SIGNATURE_MATCH,  # Direct identification
            confidence=1.0,  # 100% confidence - agent self-identified
            signals={
                'agent_card': True,
                'agent_name': primary_card.get('name'),
                'agent_version': primary_card.get('version'),
                'agent_author': primary_card.get('author'),
                'frameworks_identified': frameworks,
                'all_cards_count': card_result.get('agent_cards_found', 0),
                'source_urls': card_result.get('source_urls', []),
            },
            evidence=evidence,
            quality_score=1.0  # Maximum quality - direct identification
        )
    
    def _convert_http_to_signal(self, fingerprint: HTTPFingerprint) -> Optional[LayerSignal]:
        """Convert HTTP fingerprint to confidence engine signal"""
        if not fingerprint.framework_indicators:
            return None
        
        confidence = max(fingerprint.confidence_signals.values()) if fingerprint.confidence_signals else 0.5
        
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.HTTP_FINGERPRINT,
            confidence=confidence,
            signals={
                'framework_indicators': fingerprint.framework_indicators,
                'confidence_signals': fingerprint.confidence_signals,
                'server_header': fingerprint.server_header,
            },
            evidence=[
                f"Server header: {fingerprint.server_header or 'Not set'}",
                f"Title: {fingerprint.title or 'Not found'}",
                *fingerprint.framework_indicators[:5],
            ],
            quality_score=0.9 if fingerprint.response_size > 0 else 0.5
        )
    
    def _convert_api_to_signal(self, analysis: APIAnalysisResult) -> Optional[LayerSignal]:
        """Convert API analysis to confidence engine signal"""
        if not analysis.framework_indicators:
            return None
        
        confidence = max(analysis.confidence_signals.values()) if analysis.confidence_signals else 0.5
        
        evidence = [
            f"API endpoints responding: {analysis.endpoints_responding}",
        ]
        
        if analysis.detected_framework:
            evidence.append(f"Detected framework: {analysis.detected_framework}")
        
        evidence.extend(analysis.framework_indicators[:5])
        
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.API_BEHAVIORAL,
            confidence=confidence,
            signals={
                'framework': analysis.detected_framework,
                'framework_indicators': analysis.framework_indicators,
                'confidence_signals': analysis.confidence_signals,
                'metadata': analysis.metadata,
            },
            evidence=evidence,
            quality_score=0.95 if analysis.endpoints_responding > 2 else 0.7
        )
    
    def _convert_websocket_to_signal(self, ws_result: WebSocketAnalysisResult) -> Optional[LayerSignal]:
        """Convert WebSocket detection to confidence engine signal"""
        if not ws_result.framework_indicators:
            # Still return signal if connection succeeded
            if not ws_result.connection_success:
                return None
            confidence = 0.4
        else:
            confidence = max(ws_result.confidence_signals.values()) if ws_result.confidence_signals else 0.6
        
        evidence = [
            f"WebSocket connection: {'success' if ws_result.connection_success else 'failed'}",
        ]
        
        if ws_result.detected_framework:
            evidence.append(f"Framework: {ws_result.detected_framework}")
        
        if ws_result.protocol_type:
            evidence.append(f"Protocol: {ws_result.protocol_type}")
        
        evidence.extend(ws_result.framework_indicators[:5])
        
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.WEBSOCKET,
            confidence=confidence,
            signals={
                'framework': ws_result.detected_framework,
                'connection_success': ws_result.connection_success,
                'protocol_type': ws_result.protocol_type,
            },
            evidence=evidence,
            quality_score=0.8 if ws_result.connection_success else 0.3
        )
    
    def _convert_tls_to_signal(self, tls_result: TLSFingerprintResult) -> Optional[LayerSignal]:
        """Convert TLS fingerprint to confidence engine signal"""
        if not tls_result.connection_success:
            return None
        
        confidence = max(tls_result.confidence_signals.values()) if tls_result.confidence_signals else 0.3
        
        evidence = []
        
        if tls_result.handshake_info:
            evidence.append(f"TLS Version: {tls_result.handshake_info.tls_version or 'Unknown'}")
        
        if tls_result.certificate_info:
            if tls_result.certificate_info.is_self_signed:
                evidence.append("Self-signed certificate")
            if tls_result.certificate_info.subject.get('commonName'):
                evidence.append(f"Cert CN: {tls_result.certificate_info.subject['commonName']}")
        
        evidence.extend(tls_result.framework_indicators[:5])
        
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.TLS_FINGERPRINT,
            confidence=confidence,
            signals={
                'tls_library': tls_result.tls_library_guess,
                'framework_indicators': tls_result.framework_indicators,
            },
            evidence=evidence,
            quality_score=0.7
        )
    
    def _convert_telemetry_to_signal(self, telemetry: TelemetryResult) -> Optional[LayerSignal]:
        """Convert telemetry to confidence engine signal"""
        confidence = telemetry.confidence_score
        
        if confidence < 0.3:
            return None
        
        evidence = []
        
        if telemetry.metadata and telemetry.metadata.framework:
            evidence.append(f"Framework: {telemetry.metadata.framework}")
        
        if telemetry.metadata and telemetry.metadata.version:
            evidence.append(f"Version: {telemetry.metadata.version}")
        
        if telemetry.activity and telemetry.activity.health_status:
            evidence.append(f"Health: {telemetry.activity.health_status}")
        
        return self.confidence_engine.create_signal(
            layer=DetectionLayer.SIGNATURE_MATCH,
            confidence=confidence,
            signals={
                'metadata': telemetry.metadata.__dict__ if telemetry.metadata else None,
            },
            evidence=evidence,
            quality_score=0.85
        )
    
    # ITT Fingerprinting - NOT IMPLEMENTED (itt_fingerprinter module not available)
    # def detect_itt(self, base_url: str, prompt: str = "Say hello in one sentence",
    #                endpoint: str = "/v1/chat/completions") -> Optional[ITTFingerprint]:
    #     """
    #     Detect LLM model via ITT fingerprinting.
    #     
    #     Makes streaming request to LLM endpoint, measures token timing patterns.
    #     
    #     Args:
    #         base_url: Base URL (e.g., http://localhost:11434)
    #         prompt: Prompt to send (default: simple greeting)
    #         endpoint: API endpoint (default: /v1/chat/completions)
    #     
    #     Returns:
    #         ITTFingerprint if detection successful, None otherwise
    #     """
    #     import requests
    #     
    #     try:
    #         # Send streaming request
    #         full_url = f"{base_url.rstrip('/')}{endpoint}"
    #         response = requests.post(
    #             full_url,
    #             json={
    #                 "messages": [{"role": "user", "content": prompt}],
    #                 "stream": True,
    #                 "max_tokens": 100,
    #             },
    #             stream=True,
    #             timeout=30,
    #         )
    #         
    #         # Measure ITT and detect model
    #         result = self.itt_fingerprinter.detect_model(
    #             response.iter_lines(),
    #             min_tokens=30,
    #             max_tokens=100
    #         )
    #         
    #         if result.get("detected") and result.get("fingerprint"):
    #             logger.info(f"ITT detected: {result['model']} ({result['confidence']:.1%} confidence)")
    #             # Convert dict fingerprint to ITTFingerprint object
    #             fp_data = result["fingerprint"]
    #             return ITTFingerprint(
    #                 model_name=result.get("model", "unknown"),
    #                 mean_itt_ms=fp_data["mean_itt_ms"],
    #                 std_itt_ms=fp_data["std_itt_ms"],
    #                 median_itt_ms=fp_data["median_itt_ms"],
    #                 p50_ms=fp_data["p50_ms"],
    #                 p90_ms=fp_data["p90_ms"],
    #                 p99_ms=fp_data["p99_ms"],
    #                 tokens_per_second_avg=fp_data["tokens_per_second_avg"],
    #                 sample_size=fp_data["sample_size"],
    #                 coefficient_of_variation=fp_data["coefficient_of_variation"]
    #             )
    #         else:
    #             logger.warning(f"ITT detection failed: {result.get('reason', 'unknown')}")
    #             return None
    #             
    #     except Exception as e:
    #         logger.warning(f"ITT fingerprinting failed: {e}")
    #         return None
    
    # def _convert_itt_to_signal(self, fingerprint: ITTFingerprint) -> Optional[LayerSignal]:
    #     """
    #     Convert ITT fingerprint detection to confidence engine signal.
    #     
    #     ITT provides very high confidence when a match is found, as timing
    #     patterns are unique to each model architecture.
    #     
    #     Args:
    #         fingerprint: ITT fingerprint result
    #     
    #     Returns:
    #         LayerSignal with high confidence based on match quality
    #     """
    #     if not fingerprint or fingerprint.model_name == "unknown":
    #         return None
    #     
    #     # Map model name to framework
    #     model = fingerprint.model_name.lower()
    #     
    #     # Confidence based on coefficient of variation match
    #     # Lower CV difference = higher confidence
    #     confidence = 0.95 - (fingerprint.coefficient_of_variation * 0.3)
    #     confidence = max(0.7, min(0.98, confidence))  # Clamp to [0.7, 0.98]
    #     
    #     evidence = [
    #         f"ITT Detection: {fingerprint.model_name}",
    #         f"Mean ITT: {fingerprint.mean_itt_ms:.2f}ms",
    #         f"Std ITT: {fingerprint.std_itt_ms:.2f}ms",
    #         f"Coefficient of Variation: {fingerprint.coefficient_of_variation:.3f}",
    #         f"Samples: {fingerprint.sample_size} tokens",
    #         f"Tokens/sec avg: {fingerprint.tokens_per_second_avg:.1f}",
    #     ]
    #     
    #     # Determine framework from model name
    #     framework = None
    #     if 'gpt' in model or 'openai' in model:
    #         framework = 'openai'
    #     elif 'claude' in model or 'anthropic' in model:
    #         framework = 'anthropic'
    #     elif 'llama' in model or 'meta' in model:
    #         framework = 'llama'
    #     elif 'mistral' in model:
    #         framework = 'mistral'
    #     elif 'qwen' in model or 'alibaba' in model:
    #         framework = 'qwen'
    #     elif 'gemma' in model or 'google' in model:
    #         framework = 'gemma'
    #     elif 'mixtral' in model:
    #         framework = 'mixtral'
    #     
    #         return self.confidence_engine.create_signal(
    #             layer=DetectionLayer.SIGNATURE_MATCH,  # Direct model identification
    #             confidence=confidence,
    #             signals={
    #                 'itt_detection': True,
    #                 'model_name': fingerprint.model_name,
    #                 'mean_itt_ms': fingerprint.mean_itt_ms,
    #                 'std_itt_ms': fingerprint.std_itt_ms,
    #                 'coefficient_of_variation': fingerprint.coefficient_of_variation,
    #                 'sample_size': fingerprint.sample_size,
    #                 'framework': framework,
    #             },
    #             evidence=evidence,
    #             quality_score=0.95  # Very high quality - timing-based identification
    #         )
    
    def _find_nearby_gateways(self, host: str) -> List[Tuple[str, int]]:
        """
        Find agent gateways on the same host or nearby.
        
        Used for LLM correlation bonus - if an LLM backend is on the same
        host as an agent gateway, it's likely being used by agents.
        
        Args:
            host: Target host to search around
            
        Returns:
            List of (host, port) tuples for detected gateways
        """
        # Common agent gateway ports
        gateway_ports = [18789, 5000, 50080, 8081, 9000]
        gateways = []
        
        for port in gateway_ports:
            # Quick check if gateway is running on this port
            # In production, this would query a service registry or cache
            # For now, we'll do a simple HTTP check
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((host, port))
                if result == 0:
                    gateways.append((host, port))
                sock.close()
            except Exception:
                pass
        
        return gateways
    
    def _aggregate_signals(self, layer_results: LayerResults, 
                           telemetry: Optional[TelemetryResult]) -> List[str]:
        """Aggregate all signals from all layers"""
        signals = []
        
        # Agent Card (highest priority)
        if layer_results.agent_card and layer_results.agent_card.get("frameworks_identified"):
            for framework in layer_results.agent_card["frameworks_identified"].keys():
                signals.append(f"agent_card_{framework}")
        
        if layer_results.http and layer_results.http.framework_indicators:
            signals.extend(layer_results.http.framework_indicators)
        
        if layer_results.api and layer_results.api.framework_indicators:
            signals.extend(layer_results.api.framework_indicators)
        
        if layer_results.websocket and layer_results.websocket.framework_indicators:
            signals.extend(layer_results.websocket.framework_indicators)
        
        if layer_results.tls and layer_results.tls.framework_indicators:
            signals.extend(layer_results.tls.framework_indicators)
        
        # ITT fingerprinting - NOT IMPLEMENTED
        # if layer_results.itt and layer_results.itt.model_name != "unknown":
        #     signals.append(f"itt_model_{layer_results.itt.model_name}")
        #     if 'gpt' in layer_results.itt.model_name.lower():
        #         signals.append("framework_openai")
        #     elif 'claude' in layer_results.itt.model_name.lower():
        #         signals.append("framework_anthropic")
        #     elif 'llama' in layer_results.itt.model_name.lower():
        #         signals.append("framework_llama")
        
        if telemetry and telemetry.metadata and telemetry.metadata.framework:
            signals.append(f"telemetry_framework_{telemetry.metadata.framework}")
        
        return list(set(signals))
    
    def _aggregate_evidence(self, layer_results: LayerResults,
                            telemetry: Optional[TelemetryResult]) -> List[str]:
        """Aggregate all evidence from all layers"""
        evidence = []
        
        # Agent Card (highest priority evidence)
        if layer_results.agent_card and layer_results.agent_card.get("detected"):
            primary_card = layer_results.agent_card.get("primary_card", {})
            evidence.append(f"✓ Agent Card: {primary_card.get('name', 'Unknown')}")
            if primary_card.get('version'):
                evidence.append(f"Version: {primary_card['version']}")
            if primary_card.get('author'):
                evidence.append(f"Author: {primary_card['author']}")
        
        if layer_results.http:
            if layer_results.http.server_header:
                evidence.append(f"HTTP Server: {layer_results.http.server_header}")
            if layer_results.http.title:
                evidence.append(f"HTTP Title: {layer_results.http.title}")
        
        if layer_results.api:
            evidence.append(f"API endpoints responding: {layer_results.api.endpoints_responding}")
        
        if layer_results.websocket:
            status = "connected" if layer_results.websocket.connection_success else "failed"
            evidence.append(f"WebSocket: {status}")
        
        if layer_results.tls:
            status = "secured" if layer_results.tls.connection_success else "not secured"
            evidence.append(f"TLS: {status}")
        
        # ITT fingerprinting evidence - NOT IMPLEMENTED
        # if layer_results.itt and layer_results.itt.model_name != "unknown":
        #     evidence.append(f"✓ ITT Detection: {layer_results.itt.model_name}")
        #     evidence.append(f"  Mean ITT: {layer_results.itt.mean_itt_ms:.2f}ms")
        #     evidence.append(f"  Samples: {layer_results.itt.sample_size} tokens")
        
        if telemetry and telemetry.metadata:
            if telemetry.metadata.version:
                evidence.append(f"Version: {telemetry.metadata.version}")
        
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


def main():
    """Test integrated detector on local targets"""
    print("\n🔍 CogniWatch Integrated Multi-Layer Detector\n")
    
    detector = IntegratedDetector(timeout=3.0)
    
    # Test targets
    targets = [
        {
            'host': '192.168.0.245',
            'port': 18789,
            'https': False,
            'ws_path': '/',
        },
    ]
    
    for target in targets:
        print(f"\n{'='*60}")
        print(f"Target: {target['host']}:{target['port']}")
        print('='*60)
        
        result = detector.detect(**target)
        
        print(f"\n⏱️  Detection Time: {result.detection_time_ms:.2f}ms")
        print(f"\n🎯 Top Framework: {result.top_framework.upper() if result.top_framework else 'None'}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Confidence Level: {result.confidence_level}")
        print(f"   Detection Quality: {result.detection_quality}")
        
        if result.framework_scores:
            print(f"\n📈 All Detected Frameworks:")
            for i, fs in enumerate(result.framework_scores[:5], 1):
                print(f"   {i}. {fs['framework']} - {fs['bayesian_probability']:.1%} ({fs['confidence_level']})")
        
        print(f"\n📋 Evidence:")
        for ev in result.evidence[:10]:
            print(f"   • {ev}")
        
        print(f"\n🔍 Layer Results:")
        if result.layer_results.http:
            print(f"   HTTP: ✅ Fingerprinted ({result.layer_results.http.response_size} bytes)")
        if result.layer_results.api:
            print(f"   API: ✅ {result.layer_results.api.endpoints_responding} endpoints responding")
        if result.layer_results.websocket:
            status = "✅ Connected" if result.layer_results.websocket.connection_success else "❌ Failed"
            print(f"   WebSocket: {status}")
        if result.layer_results.tls:
            status = "✅ Secured" if result.layer_results.tls.connection_success else "❌ Not secured"
            print(f"   TLS: {status}")
        if result.telemetry:
            print(f"   Telemetry: ✅ Collected (confidence: {result.telemetry.confidence_score:.2f})")
        
        print(f"\n💡 Recommendation: {result.recommendation}")
        
        # Save detailed results
        output_file = f"/tmp/integrated_detection_{target['host'].replace('.', '_')}_{target['port']}.json"
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {output_file}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
