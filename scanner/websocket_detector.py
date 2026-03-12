#!/usr/bin/env python3
"""
CogniWatch - WebSocket Detection Module
Analyze WebSocket connections for AI agent framework detection

Detection layers:
- WebSocket upgrade handshake analysis
- Message structure patterns (JSON-RPC, custom protocols)
- Connection persistence behavior
- Subprotocol negotiation (sec-websocket-protocol)
"""

import websocket
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WebSocketHandshake:
    """WebSocket handshake analysis result"""
    upgrade_accepted: bool = False
    server_header: Optional[str] = None
    sec_websocket_accept: Optional[str] = None
    sec_websocket_protocol: Optional[str] = None
    connection_header: Optional[str] = None
    upgrade_header: Optional[str] = None
    additional_headers: Dict[str, str] = field(default_factory=dict)
    handshake_time_ms: float = 0.0


@dataclass
class MessagePattern:
    """Analyzed message pattern"""
    message_type: str  # request, response, notification, error
    structure_type: str  # json_rpc, custom, plain_json, binary
    direction: str  # sent, received
    size_bytes: int = 0
    fields_found: List[str] = field(default_factory=list)
    ai_indicators: List[str] = field(default_factory=list)


@dataclass
class WebSocketAnalysisResult:
    """Complete WebSocket analysis result"""
    url: str
    connection_success: bool = False
    handshake: Optional[WebSocketHandshake] = None
    connection_duration_ms: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    message_patterns: List[MessagePattern] = field(default_factory=list)
    subprotocol_negotiated: Optional[str] = None
    connection_persistent: bool = False
    timeout_count: int = 0
    error_count: int = 0
    framework_indicators: List[str] = field(default_factory=list)
    confidence_signals: Dict[str, float] = field(default_factory=dict)
    detected_framework: Optional[str] = None
    protocol_type: Optional[str] = None  # json_rpc, graphql_ws, custom


class WebSocketDetector:
    """
    Advanced WebSocket detection for agent framework identification.
    
    Analyzes WebSocket connections to detect framework-specific
    communication patterns and protocols.
    """
    
    # Known WebSocket subprotocols used by AI frameworks
    KNOWN_SUBPROTOCOLS = {
        'graphql-ws': ['GraphQL', 'Apollo'],
        'json-rpc': ['JSON-RPC', 'Generic RPC'],
        'graphql-transport-ws': ['GraphQL'],
        'wamp': ['WAMP', 'Autobahn'],
        'stomp': ['STOMP', 'Spring'],
        'mqtt': ['MQTT'],
    }
    
    # Test messages to send
    TEST_MESSAGES = [
        # JSON-RPC style
        {"jsonrpc": "2.0", "method": "status", "id": 1},
        {"jsonrpc": "2.0", "method": "ping", "id": 2},
        
        # Simple status requests
        {"action": "status"},
        {"type": "status"},
        {"command": "ping"},
        
        # GraphQL subscriptions style
        {"type": "connection_init", "payload": {}},
        
        # Agent-specific
        {"action": "get_agents"},
        {"action": "list_sessions"},
        {"query": "status"},
    ]
    
    # Framework-specific message patterns
    FRAMEWORK_MESSAGE_PATTERNS = {
        'openai': ['id', 'model', 'choices', 'usage', 'object'],
        'crewai': ['crew', 'agent', 'task', 'process', 'memory'],
        'autogen': ['conversation', 'message', 'agent', 'sender'],
        'langgraph': ['graph', 'state', 'checkpoint', 'node'],
        'openclaw': ['sessionKey', 'gateway', 'agent_id', 'action'],
        'socket_io': ['engine.io', 'socket.io', '_sid'],
    }
    
    def __init__(self, timeout: float = 5.0, max_messages: int = 10):
        self.timeout = timeout
        self.max_messages = max_messages
        websocket.enableTrace(False)  # Disable verbose logging
    
    def detect(self, ws_url: str, subprotocols: Optional[List[str]] = None) -> WebSocketAnalysisResult:
        """
        Perform comprehensive WebSocket detection.
        
        Args:
            ws_url: WebSocket URL to test (ws:// or wss://)
            subprotocols: Optional list of subprotocols to negotiate
            
        Returns:
            WebSocketAnalysisResult with complete analysis
        """
        result = WebSocketAnalysisResult(url=ws_url)
        ws = None
        
        try:
            # Build subprotocol header if provided
            header = []
            if subprotocols:
                protocol_str = ', '.join(subprotocols)
                header.append(f"Sec-WebSocket-Protocol: {protocol_str}")
            
            # Enable callback tracking
            messages_received = []
            handshake_data = {}
            
            def on_open(ws):
                logger.debug("WebSocket connection opened")
            
            def on_message(ws, message):
                messages_received.append(message)
                result.messages_received += 1
                
                # Analyze message
                pattern = self._analyze_message(message, 'received')
                if pattern:
                    result.message_patterns.append(pattern)
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
                result.error_count += 1
            
            def on_close(ws, close_status_code, close_msg):
                logger.debug(f"WebSocket closed: {close_status_code} - {close_msg}")
            
            # Capture handshake headers
            class HeaderCaptureWSApp(websocket.WebSocketApp):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.handshake_headers = {}
                
                def handshake(self, sock, url, headers, **opt):
                    result = super().handshake(sock, url, headers, **opt)
                    # Try to capture response headers
                    return result
            
            # Create WebSocket connection
            start_time = time.time()
            ws = websocket.WebSocketApp(
                ws_url,
                header=header,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            
            # Run in thread with timeout
            ws_thread = threading.Thread(
                target=ws.run_forever,
                kwargs={'ping_timeout': self.timeout}
            )
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(0.5)
            
            if ws.sock and ws.sock.connected:
                result.connection_success = True
                handshake_time = (time.time() - start_time) * 1000
                
                # Capture handshake info
                result.handshake = WebSocketHandshake(
                    upgrade_accepted=True,
                    handshake_time_ms=round(handshake_time, 2)
                )
                
                # Test sending messages
                self._send_test_messages(ws, result)
                
                # Check connection persistence
                time.sleep(0.5)
                if ws.sock and ws.sock.connected:
                    result.connection_persistent = True
                
                result.connection_duration_ms = (time.time() - start_time) * 1000
                
            else:
                result.connection_success = False
            
            # Clean up
            if ws:
                ws.close()
            ws_thread.join(timeout=1.0)
            
        except websocket.WebSocketAddressException as e:
            logger.warning(f"WebSocket address error: {e}")
            result.error_count += 1
        except websocket.WebSocketConnectionClosedException as e:
            logger.warning(f"WebSocket closed unexpectedly: {e}")
            result.connection_persistent = False
        except Exception as e:
            logger.error(f"WebSocket detection error: {e}")
            result.error_count += 1
        
        # Analyze results
        self._analyze_websocket_results(result)
        
        return result
    
    def _send_test_messages(self, ws, result: WebSocketAnalysisResult):
        """Send test messages and analyze responses"""
        for test_msg in self.TEST_MESSAGES[:self.max_messages]:
            try:
                msg_str = json.dumps(test_msg)
                ws.send(msg_str)
                result.messages_sent += 1
                
                # Analyze sent message
                pattern = self._analyze_message(msg_str, 'sent')
                if pattern:
                    result.message_patterns.append(pattern)
                
                # Small delay to allow response
                time.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"Failed to send test message: {e}")
                result.timeout_count += 1
    
    def _analyze_message(self, message: str, direction: str) -> Optional[MessagePattern]:
        """Analyze a WebSocket message for patterns"""
        if not message:
            return None
        
        pattern = MessagePattern(
            message_type='unknown',
            structure_type='unknown',
            direction=direction,
            size_bytes=len(message)
        )
        
        # Try to parse as JSON
        try:
            data = json.loads(message)
            
            if isinstance(data, dict):
                # Check for JSON-RPC
                if 'jsonrpc' in data and 'id' in data:
                    pattern.structure_type = 'json_rpc'
                    if 'result' in data or 'error' in data:
                        pattern.message_type = 'response'
                    else:
                        pattern.message_type = 'request'
                
                # Check for GraphQL
                elif 'type' in data and data['type'] in ['connection_init', 'connection_ack', 'subscribe', 'data']:
                    pattern.structure_type = 'graphql_ws'
                    pattern.message_type = 'request' if 'type' in data else 'response'
                
                # Generic JSON
                else:
                    pattern.structure_type = 'plain_json'
                    pattern.message_type = 'notification'
                
                # Extract fields
                pattern.fields_found = list(data.keys()) if isinstance(data, dict) else []
                
                # Check for AI indicators
                data_lower = str(data).lower()
                for framework, keywords in self.FRAMEWORK_MESSAGE_PATTERNS.items():
                    for keyword in keywords:
                        if keyword.lower() in data_lower:
                            pattern.ai_indicators.append(framework)
                
            elif isinstance(data, list):
                pattern.structure_type = 'json_array'
                pattern.message_type = 'response'
            
        except json.JSONDecodeError:
            # Not JSON - could be binary or text
            if isinstance(message, bytes):
                pattern.structure_type = 'binary'
            else:
                pattern.structure_type = 'text'
                pattern.message_type = 'notification'
        
        return pattern
    
    def _analyze_websocket_results(self, result: WebSocketAnalysisResult):
        """Analyze collected WebSocket data for framework detection"""
        
        # Collect all AI indicators from messages
        all_ai_indicators = []
        for pattern in result.message_patterns:
            all_ai_indicators.extend(pattern.ai_indicators)
        
        # Count framework mentions
        framework_counts = {}
        for indicator in all_ai_indicators:
            framework_counts[indicator] = framework_counts.get(indicator, 0) + 1
        
        # Determine most likely framework
        if framework_counts:
            result.detected_framework = max(framework_counts.items(), key=lambda x: x[1])[0]
            confidence = min(framework_counts[result.detected_framework] * 0.1, 0.8)
            result.confidence_signals['framework_match'] = confidence
        
        # Check subprotocol
        if result.handshake and result.handshake.sec_websocket_protocol:
            result.subprotocol_negotiated = result.handshake.sec_websocket_protocol
            
            # Map subprotocol to framework
            for proto, frameworks in self.KNOWN_SUBPROTOCOLS.items():
                if proto.lower() in result.subprotocol_negotiated.lower():
                    result.protocol_type = proto
                    result.confidence_signals['subprotocol_match'] = 0.4
                    break
        
        # Analyze message structure patterns
        structure_types = [p.structure_type for p in result.message_patterns]
        if 'json_rpc' in structure_types:
            result.protocol_type = 'json_rpc'
            result.confidence_signals['json_rpc_protocol'] = 0.3
        elif 'graphql_ws' in structure_types:
            result.protocol_type = 'graphql_ws'
            result.confidence_signals['graphql_protocol'] = 0.3
        
        # Connection persistence as signal
        if result.connection_persistent:
            result.confidence_signals['persistent_connection'] = 0.2
        
        # Multiple successful messages
        if result.messages_received > 3:
            result.confidence_signals['active_communication'] = 0.3
        
        # Store framework indicators
        result.framework_indicators = list(set(all_ai_indicators))
        
        # Normalize confidence
        total_confidence = sum(result.confidence_signals.values())
        if total_confidence > 0:
            result.confidence_signals['total'] = min(total_confidence, 1.0)
    
    def probe_url(self, base_url: str, paths: Optional[List[str]] = None) -> List[WebSocketAnalysisResult]:
        """Probe potential WebSocket endpoints on a base URL"""
        if paths is None:
            paths = ['/', '/ws', '/websocket', '/socket', '/api/ws', '/api/websocket']
        
        results = []
        base_ws = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        
        for path in paths:
            ws_url = f"{base_ws.rstrip('/')}{path}"
            logger.debug(f"Probing WebSocket: {ws_url}")
            result = self.detect(ws_url)
            
            if result.connection_success:
                results.append(result)
        
        return results
    
    def quick_check(self, ws_url: str) -> bool:
        """Quick check if WebSocket endpoint is available"""
        try:
            ws = websocket.create_connection(ws_url, timeout=self.timeout)
            ws.close()
            return True
        except:
            return False


def main():
    """Test WebSocket detector on local targets"""
    import json
    
    print("\n🔍 CogniWatch WebSocket Detector\n")
    
    detector = WebSocketDetector(timeout=3.0)
    
    # Test targets
    targets = [
        "ws://192.168.0.245:18789",  # Neo gateway
        "ws://localhost:8000",
        "ws://localhost:5000",
    ]
    
    for ws_url in targets:
        print(f"\n{'='*60}")
        print(f"Target: {ws_url}")
        print('='*60)
        
        result = detector.detect(ws_url)
        
        if result.connection_success:
            print(f"\n✅ WebSocket connection successful!")
            print(f"   Connection duration: {result.connection_duration_ms:.2f}ms")
            print(f"   Messages sent: {result.messages_sent}")
            print(f"   Messages received: {result.messages_received}")
            print(f"   Connection persistent: {result.connection_persistent}")
            
            if result.handshake:
                print(f"\n📋 Handshake Info:")
                print(f"   Server: {result.handshake.server_header or 'Not set'}")
                print(f"   Protocol: {result.subprotocol_negotiated or 'Default'}")
                print(f"   Handshake time: {result.handshake.handshake_time_ms:.2f}ms")
            
            if result.protocol_type:
                print(f"\n🔌 Protocol Type: {result.protocol_type}")
            
            if result.detected_framework:
                print(f"\n🎯 Detected Framework: {result.detected_framework.upper()}")
            
            if result.framework_indicators:
                print(f"\n🔗 Framework Indicators:")
                for indicator in result.framework_indicators:
                    print(f"   • {indicator}")
            
            if result.confidence_signals:
                print(f"\n📈 Confidence Signals:")
                for signal, confidence in sorted(result.confidence_signals.items(), 
                                                  key=lambda x: x[1], reverse=True):
                    print(f"   • {signal}: {confidence:.2f}")
            
            if result.message_patterns:
                print(f"\n💬 Message Patterns Analyzed: {len(result.message_patterns)}")
                for i, pattern in enumerate(result.message_patterns[:5]):
                    print(f"   [{i+1}] {pattern.direction} - {pattern.structure_type} - {pattern.message_type}")
                    if pattern.ai_indicators:
                        print(f"       AI indicators: {', '.join(pattern.ai_indicators)}")
            
            # Save detailed results
            detailed_output = {
                'url': ws_url,
                'connection_success': result.connection_success,
                'connection_duration_ms': result.connection_duration_ms,
                'messages_sent': result.messages_sent,
                'messages_received': result.messages_received,
                'protocol_type': result.protocol_type,
                'detected_framework': result.detected_framework,
                'framework_indicators': result.framework_indicators,
                'confidence_signals': result.confidence_signals,
                'subprotocol': result.subprotocol_negotiated,
                'connection_persistent': result.connection_persistent
            }
            
            output_file = f"/tmp/ws_detection_{ws_url.replace('ws://', '').replace(':', '_').replace('.', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(detailed_output, f, indent=2)
            print(f"\n💾 Detailed results saved to: {output_file}")
            
        else:
            print(f"❌ WebSocket connection failed")
            if result.error_count > 0:
                print(f"   Errors encountered: {result.error_count}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
