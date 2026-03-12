#!/usr/bin/env python3
"""
CogniWatch - API Behavioral Analysis Module
Probe and analyze API endpoints for AI agent framework detection

Detection layers:
- Probe known AI agent endpoints
- Analyze response structure (JSON schemas, field names, nesting)
- Detect AI-specific fields (model, tokens, usage, session_id)
- Streaming response detection (SSE, chunked transfer encoding)
- Error response fingerprinting (401 vs 403 vs 404 patterns)
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIEndpointResult:
    """Result of probing a single API endpoint"""
    endpoint: str
    status_code: int = 0
    response_time_ms: float = 0.0
    response_size: int = 0
    content_type: Optional[str] = None
    response_body: Optional[str] = None
    json_data: Optional[Dict] = None
    error_details: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    ai_fields_found: List[str] = field(default_factory=list)
    structure_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class APIAnalysisResult:
    """Complete API behavioral analysis result"""
    base_url: str
    endpoints_tested: int = 0
    endpoints_responding: int = 0
    total_time_ms: float = 0.0
    streaming_detected: bool = False
    streaming_type: Optional[str] = None
    error_patterns: Dict[int, List[str]] = field(default_factory=dict)
    endpoint_results: List[APIEndpointResult] = field(default_factory=list)
    framework_indicators: List[str] = field(default_factory=list)
    confidence_signals: Dict[str, float] = field(default_factory=dict)
    detected_framework: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0  # Overall confidence score


class APIAnalyzer:
    """
    Advanced API behavioral analysis for agent framework detection.
    
    Probes endpoints and analyzes response patterns to identify
    specific AI agent frameworks and their capabilities.
    """
    
    # Known AI agent framework endpoints
    AI_ENDPOINTS = {
        # Common status/health endpoints
        'status': ['/api/status', '/status', '/health', '/healthz', '/api/health', '/ping'],
        
        # Agent-specific endpoints
        'agents': ['/api/agents', '/agents', '/api/agent/list', '/v1/agents'],
        
        # Session endpoints
        'sessions': ['/api/sessions', '/sessions', '/api/session/list', '/v1/sessions'],
        
        # Chat/completion endpoints
        'chat': ['/v1/chat/completions', '/api/chat', '/chat', '/api/v1/chat'],
        
        # Model endpoints
        'models': ['/api/models', '/models', '/v1/models'],
        
        # Framework-specific endpoints
        'crewai': ['/api/crew', '/api/crews', '/crew/api/status'],
        'autogen': ['/api/conversations', '/api/agents', '/autogen/api/status'],
        'langgraph': ['/api/graph', '/api/state', '/langgraph/api/status'],
        'openclaw': ['/api/sessions', '/api/agents', '/api/nodes', '/webhooks'],
    }
    
    # AI-specific JSON fields to detect
    AI_FIELDS = {
        'model': ['model', 'model_name', 'model_id'],
        'tokens': ['tokens', 'usage', 'total_tokens', 'prompt_tokens', 'completion_tokens'],
        'usage': ['usage', 'token_usage', 'tokenCount', 'token_count'],
        'session': ['session', 'session_id', 'sessionKey', 'session_key'],
        'agent': ['agent', 'agent_id', 'agentId', 'agent_name'],
        'message': ['messages', 'message', 'msgs', 'conversation'],
        'assistant': ['assistant', 'assistant_id', 'assistant_name'],
        'thread': ['thread', 'thread_id', 'threadKey'],
        'run': ['run', 'run_id', 'runId', 'execution'],
        'crew': ['crew', 'crew_id', 'crew_name', 'crews'],
        'workflow': ['workflow', 'workflow_id', 'process', 'graph'],
        'tool': ['tools', 'tool_calls', 'tool_call', 'function_call'],
        'reasoning': ['reasoning', 'thought', 'chain_of_thought', 'reasoning_content'],
        'cost': ['cost', 'estimated_cost', 'price', 'total_cost']
    }
    
    # Framework-specific field patterns
    FRAMEWORK_FIELD_PATTERNS = {
        'openai': ['id', 'object', 'created', 'model', 'choices', 'usage'],
        'crewai': ['crew', 'agents', 'tasks', 'process', 'verbose', 'memory'],
        'autogen': ['conversation', 'messages', 'agent', 'sender', 'recipient'],
        'langgraph': ['graph', 'state', 'nodes', 'edges', 'checkpoint'],
        'openclaw': ['sessionKey', 'gateway', 'paired_nodes', 'webhook', 'agent_id'],
        'llamaindex': ['query', 'response', 'source_nodes', 'metadata'],
    }
    
    # Error response patterns
    ERROR_PATTERNS = {
        400: ['bad request', 'invalid', 'error', 'message'],
        401: ['unauthorized', 'authentication required', 'token', 'api key'],
        403: ['forbidden', 'access denied', 'permission'],
        404: ['not found', 'missing', 'does not exist'],
        429: ['rate limit', 'too many requests', 'throttled'],
        500: ['internal server error', 'exception', 'crash'],
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CogniWatch/1.0 (API Behavioral Analyzer)',
            'Accept': 'application/json,text/html,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def analyze(self, base_url: str, 
                endpoints: Optional[List[str]] = None,
                include_common: bool = True) -> APIAnalysisResult:
        """
        Perform comprehensive API behavioral analysis.
        
        Args:
            base_url: Base URL to analyze
            endpoints: Specific endpoints to probe (optional)
            include_common: Include common AI endpoints if endpoints not specified
            
        Returns:
            APIAnalysisResult with complete analysis
        """
        start_time = time.time()
        
        result = APIAnalysisResult(base_url=base_url)
        
        # Determine which endpoints to probe
        if endpoints:
            probe_list = endpoints
        elif include_common:
            # Flatten all common endpoints
            probe_list = []
            for endpoint_list in self.AI_ENDPOINTS.values():
                probe_list.extend(endpoint_list)
            probe_list = list(set(probe_list))  # Remove duplicates
        else:
            probe_list = []
        
        result.endpoints_tested = len(probe_list)
        
        # Probe each endpoint
        for endpoint in probe_list:
            endpoint_result = self._probe_endpoint(base_url, endpoint)
            result.endpoint_results.append(endpoint_result)
            
            if endpoint_result.status_code in [200, 201, 204]:
                result.endpoints_responding += 1
            
            # Detect streaming
            if self._is_streaming_response(endpoint_result):
                result.streaming_detected = True
                result.streaming_type = endpoint_result.headers.get('Content-Type', '')
            
            # Collect error patterns
            if endpoint_result.status_code >= 400 and endpoint_result.error_details:
                error_code = endpoint_result.status_code
                if error_code not in result.error_patterns:
                    result.error_patterns[error_code] = []
                result.error_patterns[error_code].append(endpoint_result.error_details)
        
        result.total_time_ms = (time.time() - start_time) * 1000
        
        # Analyze collected data
        self._analyze_results(result)
        
        return result
    
    def _probe_endpoint(self, base_url: str, endpoint: str) -> APIEndpointResult:
        """Probe a single API endpoint"""
        url = f"{base_url}{endpoint}"
        result = APIEndpointResult(endpoint=endpoint)
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout, stream=True)
            result.response_time_ms = (time.time() - start_time) * 1000
            
            result.status_code = response.status_code
            result.headers = dict(response.headers)
            result.content_type = response.headers.get('Content-Type', '')
            
            # Read response body
            if 'application/json' in result.content_type or 'text/' in result.content_type:
                try:
                    result.response_body = response.text
                    result.response_size = len(result.response_body)
                    
                    # Try to parse as JSON
                    if 'application/json' in result.content_type:
                        result.json_data = response.json()
                except Exception as e:
                    result.error_details = f"Response parsing error: {e}"
            else:
                result.response_size = len(response.content)
                
        except requests.Timeout:
            result.error_details = "Request timeout"
            result.status_code = 0
        except requests.ConnectionError:
            result.error_details = "Connection failed"
            result.status_code = 0
        except Exception as e:
            result.error_details = str(e)
            result.status_code = 0
        
        # Analyze response for AI patterns
        if result.json_data:
            self._analyze_json_response(result)
        elif result.response_body:
            self._analyze_text_response(result)
        
        return result
    
    def _analyze_json_response(self, result: APIEndpointResult):
        """Analyze JSON response for AI-specific patterns"""
        if not result.json_data:
            return
        
        # Look for AI fields
        json_str = json.dumps(result.json_data).lower()
        
        for field_category, field_names in self.AI_FIELDS.items():
            for field_name in field_names:
                if field_name.lower() in json_str:
                    result.ai_fields_found.append(field_category)
                    if f"ai_field_{field_category}" not in result.structure_patterns:
                        result.structure_patterns.append(f"ai_field_{field_category}")
        
        # Check for framework-specific patterns
        for framework, patterns in self.FRAMEWORK_FIELD_PATTERNS.items():
            match_count = sum(1 for p in patterns if p.lower() in json_str)
            if match_count >= 2:  # At least 2 pattern matches
                result.structure_patterns.append(f"framework_{framework}")
                result.confidence += 0.1 * match_count
        
        # Analyze JSON structure depth and complexity
        if isinstance(result.json_data, dict):
            depth = self._calculate_json_depth(result.json_data)
            result.structure_patterns.append(f"json_depth_{depth}")
            
            num_keys = len(result.json_data)
            if num_keys > 10:
                result.structure_patterns.append("complex_json")
            
            # Look for common API response structures
            if 'data' in result.json_data and isinstance(result.json_data['data'], list):
                result.structure_patterns.append("list_response")
                result.confidence += 0.1
            if 'error' in result.json_data:
                result.structure_patterns.append("error_response")
        
        # Remove duplicates
        result.ai_fields_found = list(set(result.ai_fields_found))
    
    def _analyze_text_response(self, result: APIEndpointResult):
        """Analyze text response for patterns"""
        if not result.response_body:
            return
        
        text_lower = result.response_body.lower()
        
        # Look for HTML patterns typical of agent frameworks
        if '<html' in text_lower:
            result.structure_patterns.append("html_response")
            
            # Check for SPA indicators
            if 'div id=' in text_lower or 'div id="' in text_lower:
                result.structure_patterns.append("spa_candidate")
        
    def _calculate_json_depth(self, obj, current_depth=0) -> int:
        """Calculate nesting depth of JSON object"""
        if isinstance(obj, dict) and obj:
            return max(self._calculate_json_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list) and obj:
            return max(self._calculate_json_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _is_streaming_response(self, result: APIEndpointResult) -> bool:
        """Detect if response uses streaming (SSE or chunked)"""
        if not result.headers:
            return False
        
        content_type = result.headers.get('Content-Type', '')
        
        # SSE detection
        if 'text/event-stream' in content_type:
            return True
        
        # Chunked encoding
        if result.headers.get('Transfer-Encoding', '').lower() == 'chunked':
            return True
        
        # Check for typical SSE content pattern
        if result.response_body and 'data:' in result.response_body[:1000]:
            return True
        
        return False
    
    def _analyze_results(self, result: APIAnalysisResult):
        """Analyze collected results to identify framework and patterns"""
        
        # Aggregate all endpoint data
        all_ai_fields = []
        all_structure_patterns = []
        
        for endpoint_result in result.endpoint_results:
            all_ai_fields.extend(endpoint_result.ai_fields_found)
            all_structure_patterns.extend(endpoint_result.structure_patterns)
            result.confidence += endpoint_result.confidence
        
        # Remove duplicates
        all_ai_fields = list(set(all_ai_fields))
        all_structure_patterns = list(set(all_structure_patterns))
        
        # Determine framework indicators
        framework_scores = {}
        
        # Score based on endpoint patterns
        pattern_framework_map = {
            'framework_openai': 'openai',
            'framework_crewai': 'crewai',
            'framework_autogen': 'autogen',
            'framework_langgraph': 'langgraph',
            'framework_openclaw': 'openclaw',
        }
        
        for pattern, framework in pattern_framework_map.items():
            if pattern in all_structure_patterns:
                framework_scores[framework] = framework_scores.get(framework, 0) + 0.3
        
        # Score based on AI fields
        if 'session' in all_ai_fields or 'agents' in all_ai_fields:
            framework_scores['general_agent'] = framework_scores.get('general_agent', 0) + 0.2
        
        if 'crew' in all_ai_fields or 'tasks' in all_ai_fields:
            framework_scores['crewai'] = framework_scores.get('crewai', 0) + 0.4
        elif 'conversation' in all_ai_fields or 'messages' in all_ai_fields:
            framework_scores['autogen'] = framework_scores.get('autogen', 0) + 0.4
        
        # Pick highest scoring framework
        if framework_scores:
            result.detected_framework = max(framework_scores.items(), key=lambda x: x[1])[0]
            result.confidence_signals['framework_match'] = max(framework_scores.values())
        
        # Store aggregated indicators
        result.framework_indicators = list(set(all_ai_fields + [f"http_{p}" for p in result.error_patterns.keys()]))
        
        # Add confidence signals
        if result.endpoints_responding > 0:
            result.confidence_signals['endpoints_responding'] = min(result.endpoints_responding * 0.1, 0.5)
        
        if result.streaming_detected:
            result.confidence_signals['streaming_api'] = 0.3
        
        if len(all_ai_fields) > 2:
            result.confidence_signals['multiple_ai_fields'] = min(len(all_ai_fields) * 0.1, 0.4)
        
        # Normalize confidence
        result.confidence = min(result.confidence, 1.0)
        
        # Extract metadata
        for endpoint_result in result.endpoint_results:
            if endpoint_result.json_data and isinstance(endpoint_result.json_data, dict):
                # Look for version info
                for key in ['version', 'api_version', 'v']:
                    if key in endpoint_result.json_data:
                        result.metadata['api_version'] = endpoint_result.json_data[key]
                        break
                
                # Look for server info
                for key in ['server', 'gateway', 'service']:
                    if key in endpoint_result.json_data:
                        result.metadata[key] = endpoint_result.json_data[key]
    
    def probe_specific_framework(self, base_url: str, framework: str) -> APIAnalysisResult:
        """Probe endpoints specific to a known framework"""
        framework_endpoints = self.AI_ENDPOINTS.get(framework.lower(), [])
        framework_endpoints += self.AI_ENDPOINTS['status']  # Always include status endpoints
        
        return self.analyze(base_url, endpoints=framework_endpoints)
    
    def compare_error_responses(self, base_url: str, endpoint: str) -> Dict[int, str]:
        """
        Probe the same endpoint with different auth scenarios to fingerprint error responses.
        Useful for identifying specific frameworks by their error message patterns.
        """
        error_fingerprints = {}
        
        urls_to_test = [
            (f"{base_url}{endpoint}", {}),  # No auth
            (f"{base_url}{endpoint}", {'headers': {'Authorization': 'Bearer invalid'}}),
        ]
        
        for url, kwargs in urls_to_test:
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                if response.status_code >= 400:
                    # Extract error message pattern
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', 
                                    error_data.get('message', str(error_data)))
                    except:
                        error_msg = response.text[:200]
                    
                    error_fingerprints[response.status_code] = error_msg
            except:
                pass
        
        return error_fingerprints


def main():
    """Test API analyzer on local targets"""
    import json
    
    print("\n🔍 CogniWatch API Behavioral Analyzer\n")
    
    analyzer = APIAnalyzer(timeout=3.0)
    
    # Test targets
    targets = [
        "http://192.168.0.245:18789",  # Neo gateway
        "http://localhost:8000",
    ]
    
    for base_url in targets:
        print(f"\n{'='*60}")
        print(f"Analyzing: {base_url}")
        print('='*60)
        
        result = analyzer.analyze(base_url)
        
        print(f"\n📊 Summary:")
        print(f"   Endpoints tested: {result.endpoints_tested}")
        print(f"   Endpoints responding: {result.endpoints_responding}")
        print(f"   Analysis time: {result.total_time_ms:.2f}ms")
        print(f"   Streaming detected: {result.streaming_detected}")
        if result.streaming_type:
            print(f"   Streaming type: {result.streaming_type}")
        
        if result.detected_framework:
            print(f"\n🎯 Detected Framework: {result.detected_framework.upper()}")
        
        if result.framework_indicators:
            print(f"\n🔗 Framework Indicators:")
            for indicator in result.framework_indicators[:15]:
                print(f"   • {indicator}")
        
        if result.confidence_signals:
            print(f"\n📈 Confidence Signals:")
            for signal, confidence in sorted(result.confidence_signals.items(), 
                                              key=lambda x: x[1], reverse=True):
                print(f"   • {signal}: {confidence:.2f}")
        
        if result.metadata:
            print(f"\n📋 Metadata:")
            for key, value in result.metadata.items():
                print(f"   • {key}: {value}")
        
        # Save detailed results
        detailed_output = {
            'base_url': base_url,
            'endpoints_tested': result.endpoints_tested,
            'endpoints_responding': result.endpoints_responding,
            'detected_framework': result.detected_framework,
            'framework_indicators': result.framework_indicators,
            'confidence_signals': result.confidence_signals,
            'metadata': result.metadata,
            'streaming_detected': result.streaming_detected,
            'error_patterns': result.error_patterns,
            'endpoint_results': [
                {
                    'endpoint': er.endpoint,
                    'status_code': er.status_code,
                    'ai_fields_found': er.ai_fields_found,
                    'structure_patterns': er.structure_patterns,
                    'confidence': er.confidence
                }
                for er in result.endpoint_results if er.status_code != 0
            ]
        }
        
        output_file = f"/tmp/api_analysis_{base_url.replace('http://', '').replace(':', '_').replace('.', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(detailed_output, f, indent=2)
        print(f"\n💾 Detailed analysis saved to: {output_file}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
