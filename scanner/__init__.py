#!/usr/bin/env python3
"""
CogniWatch Scanner Package
Network discovery and ClawJacked attack detection

Modules:
- network_scanner: Core network scanning for AI agent frameworks
- websocket_monitor: WebSocket anomaly detection (ClawJacked pattern #1)
- auth_monitor: Authentication brute-force detection (ClawJacked pattern #2)
- device_monitor: Device registration auditing (ClawJacked pattern #3)
- confidence_engine: Confidence scoring engine
- correlation_engine: Detection correlation and merging
"""

from .network_scanner import NetworkScanner, FRAMEWORK_FINGERPRINTS, CONFIDENCE_THRESHOLDS
from .websocket_monitor import WebSocketMonitor, GATEWAY_PORTS as WS_GATEWAY_PORTS
from .auth_monitor import AuthMonitor, GATEWAY_PORTS as AUTH_GATEWAY_PORTS
from .device_monitor import DeviceMonitor
from .confidence_engine import ConfidenceEngine
from .correlation_engine import correlate_detections

__all__ = [
    'NetworkScanner',
    'FRAMEWORK_FINGERPRINTS',
    'CONFIDENCE_THRESHOLDS',
    'WebSocketMonitor',
    'WS_GATEWAY_PORTS',
    'AuthMonitor',
    'AUTH_GATEWAY_PORTS',
    'DeviceMonitor',
    'ConfidenceEngine',
    'correlate_detections'
]
