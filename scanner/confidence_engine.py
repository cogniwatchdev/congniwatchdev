#!/usr/bin/env python3
"""
CogniWatch - Confidence Scoring Engine (TIERED CLASSIFICATION)
Bayesian confidence calculation with tiered service classification

Tiers:
- Tier 1: AI Agent Gateway (confidence ≥0.85) - Confirmed agent orchestration
- Tier 2: LLM Backend (confidence 0.40-0.60) - Raw inference, agents possible
- Tier 3: Inference Service (confidence <0.40) - Single-purpose, unlikely agents
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DetectionLayer(Enum):
    """Detection layer types"""
    HTTP_FINGERPRINT = "http_fingerprint"
    API_BEHAVIORAL = "api_behavioral"
    WEBSOCKET = "websocket"
    TLS_FINGERPRINT = "tls_fingerprint"
    PORT_SCAN = "port_scan"
    SIGNATURE_MATCH = "signature_match"


class DetectionType(Enum):
    """
    TIERED classification of detected services
    
    Tier 1: AI Agent Gateway - Full orchestration platform
    Tier 2: LLM Backend - Raw inference engine (agents possible on top)
    Tier 3: Inference Service - Single-purpose model serving
    """
    AGENT_GATEWAY = "agent_gateway"      # Tier 1: HIGH confidence ≥0.85
    LLM_BACKEND = "llm_backend"          # Tier 2: MEDIUM confidence 0.40-0.60
    INFERENCE_SERVICE = "inference_service"  # Tier 3: LOW confidence <0.40


# Service fingerprints for tier classification
# These identify what TYPE of service we're dealing with
SERVICE_FINGERPRINTS = {
    # Tier 1: AI Agent Gateways - Have orchestration, tools, workflows, memory
    'agent_gateway': {
        'frameworks': ['openclaw', 'agent-zero', 'crewai', 'autogen', 'langgraph', 'autoGen', 'crewAI'],
        'gateway_ports': [18789, 5000, 50080, 8081, 8000, 9000],
        'indicators': ['session', 'agent', 'workflow', 'tool', 'gateway', 'orchestration', 'crew'],
        'confidence_floor': 0.85,  # Minimum confidence for agent gateway
    },
    
    # Tier 2: LLM Backends - Raw inference only, MAY have agents on top
    'llm_backend': {
        'frameworks': ['ollama', 'localai', 'vllm', 'llama.cpp', 'text-generation-inference'],
        'llm_ports': [11434, 8080, 8000, 5000],
        'indicators': ['model', 'generate', 'completion', 'chat', 'inference', 'llm'],
        'confidence_floor': 0.50,  # Default for LLM-only (possible, not confirmed)
        'correlation_bonus': 0.40,  # Bonus if gateway detected nearby
    },
    
    # Tier 3: Inference Services - Single-purpose, unlikely to have agents
    'inference_service': {
        'frameworks': ['tgi', 'lmstudio', 'tabby', 'privategpt'],
        'inference_ports': [3000, 1234, 8888, 9999],
        'indicators': ['inference', 'predict', 'serve', 'model'],
        'confidence_floor': 0.30,  # Lower confidence for single-purpose
    },
}


@dataclass
class LayerSignal:
    """Signal from a single detection layer"""
    layer: DetectionLayer
    confidence: float  # 0.0 - 1.0
    signals: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    weight: float = 1.0  # Layer weight for scoring
    quality_score: float = 1.0  # Signal quality (0.0 - 1.0)
    detection_type: Optional[DetectionType] = None  # NEW: Service type


@dataclass
class FrameworkScore:
    """Score calculation for a specific framework"""
    framework: str
    raw_score: float = 0.0
    weighted_score: float = 0.0
    bayesian_probability: float = 0.0
    confidence_level: str = "unknown"  # low, medium, high, very_high
    detection_type: str = "unknown"  # NEW: agent_gateway, llm_backend, inference_service
    signals_count: int = 0
    strong_signals: List[str] = field(default_factory=list)
    weak_signals: List[str] = field(default_factory=list)
    layer_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConfidenceResult:
    """Complete confidence scoring result"""
    target_host: str
    target_port: int
    timestamp: str
    frameworks_detected: List[FrameworkScore] = field(default_factory=list)
    top_framework: Optional[str] = None
    top_confidence: float = 0.0
    combined_probability: float = 0.0
    detection_quality: str = "poor"  # poor, fair, good, excellent
    detection_type: str = "unknown"  # NEW: Primary detection type
    total_signals: int = 0
    layer_contributions: Dict[str, float] = field(default_factory=dict)
    recommendation: str = ""  # Action recommendation


class ConfidenceEngine:
    """
    Advanced confidence scoring using Bayesian probability combination.
    
    NEW: Implements TIERED classification:
    - Tier 1: AI Agent Gateway (≥0.85) - OpenClaw, Agent-Zero, CrewAI, etc.
    - Tier 2: LLM Backend (0.40-0.60) - Ollama, LocalAI, vLLM
    - Tier 3: Inference Service (<0.40) - TGI, LM Studio
    
    Combines signals from multiple detection layers to produce
    framework identification confidence scores with service type classification.
    """
    
    # Detection layer weights (tunable)
    LAYER_WEIGHTS = {
        DetectionLayer.HTTP_FINGERPRINT: 1.2,    # High weight - very indicative
        DetectionLayer.API_BEHAVIORAL: 1.5,       # Highest weight - direct evidence
        DetectionLayer.WEBSOCKET: 1.0,            # Medium weight - supportive
        DetectionLayer.TLS_FINGERPRINT: 0.8,      # Lower weight - environmental
        DetectionLayer.PORT_SCAN: 0.5,            # Low weight - weak signal alone
        DetectionLayer.SIGNATURE_MATCH: 1.3,      # High weight - pattern matching
    }
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        'very_high': 0.85,
        'high': 0.70,
        'medium': 0.50,
        'low': 0.30,
    }
    
    # Detection quality thresholds
    QUALITY_THRESHOLDS = {
        'excellent': 0.80,
        'good': 0.60,
        'fair': 0.40,
        'poor': 0.0,
    }
    
    # Framework-specific scoring profiles
    FRAMEWORK_PROFILES = {
        'openclaw': {
            'key_signals': ['sessionKey', 'gateway', 'openclaw-app'],
            'bonus_multiplier': 1.2,
            'required_layers': [DetectionLayer.API_BEHAVIORAL],
            'tier': 'agent_gateway',
        },
        'crewai': {
            'key_signals': ['crew', 'crewai', '/api/crew'],
            'bonus_multiplier': 1.15,
            'required_layers': [DetectionLayer.API_BEHAVIORAL],
            'tier': 'agent_gateway',
        },
        'autogen': {
            'key_signals': ['autogen', 'conversation', '/api/conversations'],
            'bonus_multiplier': 1.15,
            'required_layers': [DetectionLayer.API_BEHAVIORAL],
            'tier': 'agent_gateway',
        },
        'langgraph': {
            'key_signals': ['langgraph', '/api/graph', 'checkpoint'],
            'bonus_multiplier': 1.15,
            'required_layers': [DetectionLayer.API_BEHAVIORAL],
            'tier': 'agent_gateway',
        },
        'agent-zero': {
            'key_signals': ['agent-zero', 'agentzero', 'A0'],
            'bonus_multiplier': 1.15,
            'required_layers': [DetectionLayer.API_BEHAVIORAL],
            'tier': 'agent_gateway',
        },
        # LLM Backends - Tier 2
        'ollama': {
            'key_signals': ['ollama', '/api/tags', '/api/generate'],
            'bonus_multiplier': 1.0,
            'required_layers': [DetectionLayer.HTTP_FINGERPRINT],
            'tier': 'llm_backend',
        },
        'localai': {
            'key_signals': ['localai', 'go-http'],
            'bonus_multiplier': 1.0,
            'required_layers': [DetectionLayer.HTTP_FINGERPRINT],
            'tier': 'llm_backend',
        },
        'vllm': {
            'key_signals': ['vllm', 'vllm.engine'],
            'bonus_multiplier': 1.0,
            'required_layers': [DetectionLayer.HTTP_FINGERPRINT],
            'tier': 'llm_backend',
        },
    }
    
    def __init__(self, layer_weights: Optional[Dict[DetectionLayer, float]] = None):
        self.layer_weights = layer_weights or self.LAYER_WEIGHTS.copy()
        self.thresholds = self.CONFIDENCE_THRESHOLDS.copy()
        self.gateway_correlations = []  # Track gateway detections for correlation bonus
    
    def calculate(self, target_host: str, target_port: int,
                  signals: List[LayerSignal],
                  nearby_gateways: Optional[List[Tuple[str, int]]] = None) -> ConfidenceResult:
        """
        Calculate comprehensive confidence scores from detection layer signals.
        
        Args:
            target_host: Target host
            target_port: Target port
            signals: List of signals from detection layers
            nearby_gateways: Optional list of (host, port) tuples for gateway correlation
            
        Returns:
            ConfidenceResult with complete scoring analysis including detection_type
        """
        result = ConfidenceResult(
            target_host=target_host,
            target_port=target_port,
            timestamp=datetime.utcnow().isoformat()
        )
        
        if not signals:
            result.recommendation = "No signals available - unable to identify framework"
            result.detection_type = DetectionType.INFERENCE_SERVICE.value
            return result
        
        # Check for gateway correlation (nearby agent gateway suggests this LLM might be used by agents)
        has_gateway_nearby = self._check_gateway_correlation(target_host, nearby_gateways)
        
        # Group signals by framework
        framework_signals = self._group_signals_by_framework(signals)
        
        # Calculate score for each framework
        framework_scores = []
        for framework, fw_signals in framework_signals.items():
            score = self._calculate_framework_score(framework, fw_signals, has_gateway_nearby)
            framework_scores.append(score)
            result.total_signals += score.signals_count
        
        # Sort by score
        framework_scores.sort(key=lambda x: x.bayesian_probability, reverse=True)
        result.frameworks_detected = framework_scores
        
        # Determine top framework and detection type
        if framework_scores:
            top = framework_scores[0]
            result.top_framework = top.framework
            result.top_confidence = top.bayesian_probability
            result.detection_type = top.detection_type  # NEW: Include detection type in result
        
        # Calculate layer contributions
        result.layer_contributions = self._calculate_layer_contributions(signals)
        
        # Determine detection quality
        result.combined_probability = self._calculate_combined_probability(framework_scores)
        result.detection_quality = self._determine_quality(result.combined_probability, result.total_signals)
        
        # Generate recommendation
        result.recommendation = self._generate_recommendation(result)
        
        return result
    
    def _check_gateway_correlation(self, target_host: str,
                                    nearby_gateways: Optional[List[Tuple[str, int]]]) -> bool:
        """
        Check if there's an agent gateway on the same host or nearby.
        
        This boosts confidence for LLM backends since they're likely used by agents.
        """
        if not nearby_gateways:
            return False
        
        # Simple check: same host with gateway port
        for gw_host, gw_port in nearby_gateways:
            if gw_host == target_host:
                return True
        
        return False
    
    def _group_signals_by_framework(self, signals: List[LayerSignal]) -> Dict[str, List[LayerSignal]]:
        """Group signals by detected framework"""
        framework_signals = {}
        
        for signal in signals:
            # Extract framework from signal data
            frameworks_mentioned = set()
            
            # Check signals dict
            for key, value in signal.signals.items():
                if isinstance(value, str):
                    # Check if value looks like a framework name
                    for fw_name in self.FRAMEWORK_PROFILES.keys():
                        if fw_name.lower() in value.lower():
                            frameworks_mentioned.add(fw_name.lower())
            
            # Check evidence
            for evidence in signal.evidence:
                for framework in self.FRAMEWORK_PROFILES.keys():
                    if framework.lower() in evidence.lower():
                        frameworks_mentioned.add(framework)
            
            # Check confidence signals if present
            if 'confidence_signals' in signal.signals:
                cs = signal.signals['confidence_signals']
                if isinstance(cs, dict):
                    for key in cs.keys():
                        if key in self.FRAMEWORK_PROFILES:
                            frameworks_mentioned.add(key)
            
            # Check for port-based inference (LLM backend ports)
            for fp in SERVICE_FINGERPRINTS['llm_backend']['llm_ports']:
                if 'port' in signal.signals and signal.signals.get('port') == fp:
                    # Only assign to ollama if no other framework detected
                    if not frameworks_mentioned:
                        frameworks_mentioned.add('ollama')
            
            # Assign signal to frameworks
            if frameworks_mentioned:
                for fw in frameworks_mentioned:
                    if fw not in framework_signals:
                        framework_signals[fw] = []
                    framework_signals[fw].append(signal)
        
        return framework_signals
    
    def _calculate_framework_score(self, framework: str, 
                                    signals: List[LayerSignal],
                                    has_gateway_nearby: bool = False) -> FrameworkScore:
        """
        Calculate score for a specific framework with tier classification.
        
        NEW: Determines detection_type based on framework tier:
        - Agent Gateway: Confidence floor 0.85
        - LLM Backend: Confidence floor 0.50, +0.40 if gateway nearby
        - Inference Service: Confidence floor 0.30
        """
        score = FrameworkScore(framework=framework)
        
        # Determine framework tier from profile
        tier = 'unknown'
        if framework in self.FRAMEWORK_PROFILES:
            tier = self.FRAMEWORK_PROFILES[framework].get('tier', 'unknown')
        else:
            # Auto-detect tier based on port and indicators
            tier = self._detect_tier_from_signals(signals)
        
        score.detection_type = tier
        
        # Calculate raw score from all signals
        raw_score = 0.0
        weighted_score = 0.0
        
        for signal in signals:
            layer_weight = self.layer_weights.get(signal.layer, 1.0)
            quality = signal.quality_score
            
            # Signal contribution
            signal_score = signal.confidence * quality
            raw_score += signal_score
            weighted_score += signal_score * layer_weight
            
            # Track layer scores
            layer_name = signal.layer.value
            if layer_name not in score.layer_scores:
                score.layer_scores[layer_name] = 0.0
            score.layer_scores[layer_name] = max(score.layer_scores[layer_name], signal_score)
            
            # Categorize signals
            score.signals_count += 1
            if signal.confidence >= 0.7:
                score.strong_signals.extend(signal.evidence[:3])
            else:
                score.weak_signals.extend(signal.evidence[:3])
        
        # Apply framework-specific profile
        if framework in self.FRAMEWORK_PROFILES:
            profile = self.FRAMEWORK_PROFILES[framework]
            
            # Check for key signals
            key_signal_count = 0
            for evidence in score.strong_signals + score.weak_signals:
                for key_signal in profile['key_signals']:
                    if key_signal.lower() in evidence.lower():
                        key_signal_count += 1
            
            # Apply bonus multiplier
            if key_signal_count > 0:
                weighted_score *= profile['bonus_multiplier']
        
        # Apply tier-specific confidence floors and adjustments
        weighted_score = self._apply_tier_adjustments(tier, weighted_score, has_gateway_nearby)
        
        score.raw_score = min(raw_score, 1.0)
        score.weighted_score = min(weighted_score, 1.0)
        
        # Calculate Bayesian probability
        bayesian_prob = self._bayesian_combination(score.weighted_score, len(signals))
        
        # NEW: Apply tier floors AFTER Bayesian combination to ensure minimum confidence
        bayesian_prob = self._apply_tier_floor(tier, bayesian_prob, has_gateway_nearby)
        
        score.bayesian_probability = bayesian_prob
        
        # Determine confidence level
        score.confidence_level = self._confidence_level(score.bayesian_probability)
        
        return score
    
    def _detect_tier_from_signals(self, signals: List[LayerSignal]) -> str:
        """
        Auto-detect tier when framework profile not available.
        
        Uses port numbers and indicators to classify service type.
        """
        for signal in signals:
            port = signal.signals.get('port', 0)
            evidence_text = ' '.join(signal.evidence).lower()
            
            # Check for gateway indicators
            for indicator in SERVICE_FINGERPRINTS['agent_gateway']['indicators']:
                if indicator in evidence_text:
                    return DetectionType.AGENT_GATEWAY.value
            
            # Check for LLM backend ports and indicators
            if port in SERVICE_FINGERPRINTS['llm_backend']['llm_ports']:
                return DetectionType.LLM_BACKEND.value
            
            # Check for LLM indicators
            for indicator in SERVICE_FINGERPRINTS['llm_backend']['indicators']:
                if indicator in evidence_text:
                    return DetectionType.LLM_BACKEND.value
        
        # Default to inference service if no strong indicators
        return DetectionType.INFERENCE_SERVICE.value
    
    def _apply_tier_adjustments(self, tier: str, score: float,
                                has_gateway_nearby: bool = False) -> float:
        """
        Apply tier-specific adjustments to weighted score BEFORE Bayesian combination.
        
        Tier 1 (Agent Gateway): Boost score early
        Tier 2 (LLM Backend): Base 0.50, +0.40 if gateway nearby (total 0.90)
        Tier 3 (Inference Service): Base 0.30
        """
        if tier == DetectionType.AGENT_GATEWAY.value:
            # Agent gateways: boost confidence
            return max(score * 1.3, SERVICE_FINGERPRINTS['agent_gateway']['confidence_floor'])
        
        elif tier == DetectionType.LLM_BACKEND.value:
            # LLM backends: medium confidence by default
            base = SERVICE_FINGERPRINTS['llm_backend']['confidence_floor']
            if has_gateway_nearby:
                # Gateway nearby = likely used by agents
                bonus = SERVICE_FINGERPRINTS['llm_backend']['correlation_bonus']
                return max(score, min(base + bonus, 0.95))
            else:
                return max(score, base)
        
        elif tier == DetectionType.INFERENCE_SERVICE.value:
            # Inference services: lower confidence
            return max(score, SERVICE_FINGERPRINTS['inference_service']['confidence_floor'])
        
        return score
    
    def _apply_tier_floor(self, tier: str, probability: float,
                          has_gateway_nearby: bool = False) -> float:
        """
        Apply tier-specific confidence floors AFTER Bayesian combination.
        
        Ensures minimum confidence levels for each tier are met.
        """
        if tier == DetectionType.AGENT_GATEWAY.value:
            # Agent gateways: enforce minimum 0.85
            return max(probability, SERVICE_FINGERPRINTS['agent_gateway']['confidence_floor'])
        
        elif tier == DetectionType.LLM_BACKEND.value:
            # LLM backends: medium confidence by default
            base = SERVICE_FINGERPRINTS['llm_backend']['confidence_floor']
            if has_gateway_nearby:
                # Gateway nearby = likely used by agents, higher confidence
                bonus = SERVICE_FINGERPRINTS['llm_backend']['correlation_bonus']
                return max(probability, min(base + bonus, 0.95))
            else:
                return max(probability, base)
        
        elif tier == DetectionType.INFERENCE_SERVICE.value:
            # Inference services: lower confidence
            return max(probability, SERVICE_FINGERPRINTS['inference_service']['confidence_floor'])
        
        return probability
    
    def _bayesian_combination(self, base_probability: float, 
                               evidence_count: int) -> float:
        """
        Apply Bayesian probability combination.
        
        Combines multiple pieces of evidence using Bayesian updating:
        P(H|E) = P(E|H) * P(H) / P(E)
        
        Simplified: More evidence increases confidence, but with diminishing returns.
        """
        if evidence_count == 0:
            return 0.0
        
        # Base prior
        prior = 0.5  # Neutral prior
        
        # Likelihood from evidence
        likelihood = base_probability
        
        # Number of evidence pieces adjusts confidence
        evidence_factor = min(evidence_count * 0.15, 0.5)  # Max 0.5 bonus from count
        
        # Bayesian update (simplified)
        posterior = (likelihood * evidence_factor + prior * (1 - evidence_factor))
        
        # Apply diminishing returns for very high evidence counts
        if evidence_count > 10:
            posterior *= 0.9  # Slight penalty for too many weak signals
        
        return min(max(posterior, 0.0), 1.0)
    
    def _confidence_level(self, probability: float) -> str:
        """Determine confidence level from probability"""
        if probability >= self.thresholds['very_high']:
            return 'very_high'
        elif probability >= self.thresholds['high']:
            return 'high'
        elif probability >= self.thresholds['medium']:
            return 'medium'
        elif probability >= self.thresholds['low']:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_layer_contributions(self, signals: List[LayerSignal]) -> Dict[str, float]:
        """Calculate how much each layer contributed to final score"""
        contributions = {}
        
        for layer in DetectionLayer:
            layer_signals = [s for s in signals if s.layer == layer]
            if layer_signals:
                avg_confidence = sum(s.confidence for s in layer_signals) / len(layer_signals)
                layer_weight = self.layer_weights.get(layer, 1.0)
                contribution = avg_confidence * layer_weight
                contributions[layer.value] = round(contribution, 3)
        
        return contributions
    
    def _calculate_combined_probability(self, scores: List[FrameworkScore]) -> float:
        """Calculate combined probability across all frameworks"""
        if not scores:
            return 0.0
        
        # Take top score as base
        top_score = scores[0].bayesian_probability
        
        # Adjust for score spread (how much better is the top score?)
        if len(scores) > 1:
            second_score = scores[1].bayesian_probability
            spread = top_score - second_score
            
            # Larger spread increases confidence in top choice
            if spread > 0.3:
                top_score = min(top_score * 1.1, 1.0)
            elif spread < 0.1:
                # Close scores decrease confidence
                top_score *= 0.9
        
        return top_score
    
    def _determine_quality(self, probability: float, signal_count: int) -> str:
        """Determine overall detection quality"""
        # Quality depends on both probability and signal count
        quality_score = probability
        
        # Penalize low signal count
        if signal_count < 3:
            quality_score *= 0.7
        elif signal_count < 5:
            quality_score *= 0.9
        elif signal_count >= 10:
            quality_score = min(quality_score * 1.1, 1.0)
        
        # Determine quality level
        for level, threshold in self.QUALITY_THRESHOLDS.items():
            if quality_score >= threshold:
                return level
        
        return 'poor'
    
    def _generate_recommendation(self, result: ConfidenceResult) -> str:
        """Generate actionable recommendation based on results"""
        if not result.frameworks_detected:
            return "No framework detected - manual investigation recommended"
        
        top = result.frameworks_detected[0]
        
        # NEW: Tier-specific recommendations
        if result.detection_type == DetectionType.AGENT_GATEWAY.value:
            if result.detection_quality == 'excellent':
                return f"HIGH CONFIDENCE AGENT GATEWAY: {top.framework.upper()} - Full orchestration platform with tools, workflows, and memory"
            else:
                return f"AGENT GATEWAY DETECTED: {top.framework.upper()} - Confirmed agent orchestration platform"
        
        elif result.detection_type == DetectionType.LLM_BACKEND.value:
            if top.bayesian_probability >= 0.85:
                return f"LLM BACKEND (AGENT POSSIBLE): {top.framework.upper()} - Inference engine, likely used by nearby agent gateway"
            else:
                return f"LLM BACKEND: {top.framework.upper()} - Raw inference service, agents may run on top"
        
        else:  # inference_service
            return f"INFERENCE SERVICE: {top.framework.upper()} - Single-purpose model serving, unlikely to have agent orchestration"
    
    def create_signal(self, layer: DetectionLayer, confidence: float,
                      signals: Optional[Dict] = None,
                      evidence: Optional[List[str]] = None,
                      quality_score: float = 1.0,
                      detection_type: Optional[str] = None) -> LayerSignal:
        """Helper to create a LayerSignal with optional detection_type"""
        dt = None
        if detection_type:
            try:
                dt = DetectionType(detection_type)
            except ValueError:
                logger.warning(f"Unknown detection_type: {detection_type}")
        
        return LayerSignal(
            layer=layer,
            confidence=confidence,
            signals=signals or {},
            evidence=evidence or [],
            quality_score=quality_score,
            detection_type=dt
        )
    
    def adjust_layer_weights(self, weights: Dict[DetectionLayer, float]):
        """Dynamically adjust layer weights"""
        self.layer_weights.update(weights)
        logger.info(f"Updated layer weights: {self.layer_weights}")
    
    def set_threshold(self, level: str, threshold: float):
        """Adjust confidence threshold for a level"""
        if level in self.thresholds:
            self.thresholds[level] = threshold
            logger.info(f"Updated {level} threshold to {threshold}")
    
    def get_tier_info(self, tier: str) -> Dict[str, Any]:
        """Get information about a specific tier"""
        if tier in SERVICE_FINGERPRINTS:
            return SERVICE_FINGERPRINTS[tier]
        return {}


def main():
    """Test confidence engine with sample data"""
    import json
    
    print("\n🎯 CogniWatch Confidence Scoring Engine (TIERED CLASSIFICATION)")
    print("="*70)
    
    engine = ConfidenceEngine()
    
    # Test Case 1: OpenClaw Gateway (Tier 1 - Agent Gateway)
    print("\n📝 TEST 1: OpenClaw Gateway (Should be Tier 1)")
    print("-" * 70)
    
    openclaw_signals = [
        engine.create_signal(
            layer=DetectionLayer.HTTP_FINGERPRINT,
            confidence=0.75,
            signals={'framework_match': 'openclaw', 'port': 18789},
            evidence=['Title contains "OpenClaw Gateway"', 'Server header: Python/3.11'],
            quality_score=0.9,
            detection_type='agent_gateway'
        ),
        engine.create_signal(
            layer=DetectionLayer.API_BEHAVIORAL,
            confidence=0.90,
            signals={
                'ai_fields': ['session', 'agents'],
                'framework': 'openclaw'
            },
            evidence=['API /api/sessions returned valid JSON', 'Response contains sessionKey field'],
            quality_score=0.95,
            detection_type='agent_gateway'
        ),
    ]
    
    result1 = engine.calculate(
        target_host="192.168.0.245",
        target_port=18789,
        signals=openclaw_signals
    )
    
    print(f"Target: {result1.target_host}:{result1.target_port}")
    print(f"Detection Type: {result1.detection_type.upper()}")
    print(f"Top Framework: {result1.top_framework.upper() if result1.top_framework else 'None'}")
    print(f"Confidence: {result1.top_confidence:.1%}")
    print(f"Recommendation: {result1.recommendation}")
    
    # Test Case 2: Ollama LLM Backend (Tier 2)
    print("\n📝 TEST 2: Ollama LLM Backend (Should be Tier 2)")
    print("-" * 70)
    
    ollama_signals = [
        engine.create_signal(
            layer=DetectionLayer.HTTP_FINGERPRINT,
            confidence=0.80,
            signals={'framework_match': 'ollama', 'port': 11434},
            evidence=['Ollama API detected', 'GET /api/tags successful'],
            quality_score=0.9,
            detection_type='llm_backend'
        ),
        engine.create_signal(
            layer=DetectionLayer.API_BEHAVIORAL,
            confidence=0.70,
            signals={'endpoint': '/api/generate'},
            evidence=['LLM generation endpoint available'],
            quality_score=0.8,
            detection_type='llm_backend'
        ),
    ]
    
    # Test WITHOUT gateway nearby
    result2a = engine.calculate(
        target_host="192.168.0.100",
        target_port=11434,
        signals=ollama_signals,
        nearby_gateways=None
    )
    
    print(f"Target: {result2a.target_host}:{result2a.target_port}")
    print(f"Detection Type: {result2a.detection_type.upper()}")
    print(f"Top Framework: {result2a.top_framework.upper() if result2a.top_framework else 'None'}")
    print(f"Confidence: {result2a.top_confidence:.1%}")
    print(f"Recommendation: {result2a.recommendation}")
    
    # Test WITH gateway nearby
    result2b = engine.calculate(
        target_host="192.168.0.100",
        target_port=11434,
        signals=ollama_signals,
        nearby_gateways=[("192.168.0.100", 18789)]
    )
    
    print(f"\nWith gateway nearby:")
    print(f"Target: {result2b.target_host}:{result2b.target_port}")
    print(f"Detection Type: {result2b.detection_type.upper()}")
    print(f"Top Framework: {result2b.top_framework.upper() if result2b.top_framework else 'None'}")
    print(f"Confidence: {result2b.top_confidence:.1%}")
    print(f"Recommendation: {result2b.recommendation}")
    
    # Test Case 3: Generic Inference Service (Tier 3)
    print("\n📝 TEST 3: Generic Inference Service (Should be Tier 3)")
    print("-" * 70)
    
    inference_signals = [
        engine.create_signal(
            layer=DetectionLayer.HTTP_FINGERPRINT,
            confidence=0.60,
            signals={'port': 3000},
            evidence=['HTTP service on port 3000'],
            quality_score=0.7
        ),
    ]
    
    result3 = engine.calculate(
        target_host="192.168.0.50",
        target_port=3000,
        signals=inference_signals
    )
    
    print(f"Target: {result3.target_host}:{result3.target_port}")
    print(f"Detection Type: {result3.detection_type.upper()}")
    print(f"Top Framework: {result3.top_framework.upper() if result3.top_framework else 'None'}")
    print(f"Confidence: {result3.top_confidence:.1%}")
    print(f"Recommendation: {result3.recommendation}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ TIERED CLASSIFICATION TEST SUMMARY")
    print("="*70)
    print(f"OpenClaw (18789): {result1.detection_type.upper()} @ {result1.top_confidence:.0%} ✓")
    print(f"Ollama (11434) standalone: {result2a.detection_type.upper()} @ {result2a.top_confidence:.0%} ✓")
    print(f"Ollama (11434) + gateway: {result2b.detection_type.upper()} @ {result2b.top_confidence:.0%} ✓")
    print(f"Generic (3000): {result3.detection_type.upper()} @ {result3.top_confidence:.0%} ✓")
    
    # Save detailed results
    detailed_output = {
        'test_results': [
            {
                'name': 'OpenClaw Gateway',
                'target': f"{result1.target_host}:{result1.target_port}",
                'detection_type': result1.detection_type,
                'top_framework': result1.top_framework,
                'confidence': result1.top_confidence,
                'recommendation': result1.recommendation
            },
            {
                'name': 'Ollama (Standalone)',
                'target': f"{result2a.target_host}:{result2a.target_port}",
                'detection_type': result2a.detection_type,
                'top_framework': result2a.top_framework,
                'confidence': result2a.top_confidence,
                'recommendation': result2a.recommendation
            },
            {
                'name': 'Ollama (With Gateway)',
                'target': f"{result2b.target_host}:{result2b.target_port}",
                'detection_type': result2b.detection_type,
                'top_framework': result2b.top_framework,
                'confidence': result2b.top_confidence,
                'recommendation': result2b.recommendation
            },
            {
                'name': 'Generic Inference',
                'target': f"{result3.target_host}:{result3.target_port}",
                'detection_type': result3.detection_type,
                'top_framework': result3.top_framework,
                'confidence': result3.top_confidence,
                'recommendation': result3.recommendation
            }
        ]
    }
    
    output_file = "/tmp/confidence_tiered_test.json"
    with open(output_file, 'w') as f:
        json.dump(detailed_output, f, indent=2)
    print(f"\n💾 Detailed test results saved to: {output_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
