# ADVANCED_DETECTION_DESIGN.md
## CogniWatch Deep Fingerprinting System

**Version:** 1.0  
**Created:** 2026-03-07  
**Classification:** Core IP - Confidential

---

## Executive Summary

This document outlines 25+ advanced detection techniques for AI agent fingerprinting, moving far beyond basic port scanning to achieve Shodan-level sophistication. These techniques combine TLS/SSL analysis, HTTP/2 fingerprinting, behavioral patterns, content analysis, AI-specific signatures, and network-level detection to create a comprehensive agent identification system.

**Target Confidence:** 95%+ agent detection accuracy with <2% false positive rate when all techniques are combined.

---

## 1. HTTP/HTTPS FINGERPRINTING

### 1.1 JA3/JA3S TLS Fingerprinting
**Priority:** HIGH | **Confidence Boost:** +15%

**Method:** Extract and hash TLS ClientHello parameters to create unique fingerprints.

**Implementation:**
```python
import hashlib

def ja3_fingerprint(client_hello):
    """
    JA3 fingerprint extraction from TLS ClientHello
    Returns 32-character MD5 hash
    """
    version = client_hello.ssl_version
    ciphers = '-'.join(str(c) for c in client_hello.cipher_suites)
    extensions = '-'.join(str(e) for e in client_hello.extensions)
    curves = '-'.join(str(c) for c in client_hello.elliptic_curves)
    curve_formats = '-'.join(str(f) for f in client_hello.ec_point_formats)
    
    ja3_string = f"{version},{ciphers},{extensions},{curves},{curve_formats}"
    return hashlib.md5(ja3_string.encode()).hexdigest()

def ja3s_fingerprint(server_hello):
    """
    JA3S - Server response fingerprinting
    """
    version = server_hello.ssl_version
    cipher = str(server_hello.cipher_suite)
    extensions = '-'.join(str(e) for e in server_hello.extensions)
    
    ja3s_string = f"{version},{cipher},{extensions}"
    return hashlib.md5(ja3s_string.encode()).hexdigest()

# Combined confidence scoring
def tls_confidence(ja3_client, ja3s_server, known_agents):
    if (ja3_client, ja3s_server) in known_agents:
        return 0.95  # 95% confidence match
    return 0.3  # Unknown client
```

**Reference Implementation:** 
- Salesforce JA3: https://github.com/salesforce/ja3
- Adopted by: Cloudflare, AWS WAF, Suricata, Elastic Packetbeat

**Known Agent Signatures:**
- Python requests: `de350869b8c85de67a350c8d186f11e6`
- curl default: `ada70206e40642a3e4461f35503241d5`
- Tor Client: `e7d705a3286e19ea42f587b344ee6865`

---

### 1.2 HTTP/2 Frame Ordering Fingerprinting
**Priority:** HIGH | **Confidence Boost:** +12%

**Method:** Analyze HTTP/2 SETTINGS frame parameters, WINDOW_UPDATE, PRIORITY frames, and pseudo-header ordering.

**Implementation:**
```python
class HTTP2Fingerprint:
    def __init__(self):
        self.settings_map = {
            1: 'HEADER_TABLE_SIZE',
            2: 'ENABLE_PUSH',
            3: 'MAX_CONCURRENT_STREAMS',
            4: 'INITIAL_WINDOW_SIZE',
            5: 'MAX_FRAME_SIZE',
            6: 'MAX_HEADER_LIST_SIZE'
        }
    
    def extract_fingerprint(self, connection):
        """
        Extract HTTP/2 fingerprint components
        Format: S[;]|WU|P[,]#|PS[,]
        """
        # 1. SETTINGS frame parameters
        settings = connection.settings_frame
        settings_str = ';'.join(f"{k}:{v}" for k, v in settings.items())
        
        # 2. WINDOW_UPDATE initial value
        window_update = connection.window_update or 0
        
        # 3. PRIORITY frame structure
        priorities = []
        for priority in connection.priority_frames:
            # Format: StreamID:Exclusivity:DependentStreamID:Weight
            p_str = f"{priority.stream_id}:{priority.exclusive}:{priority.depends_on}:{priority.weight}"
            priorities.append(p_str)
        priority_str = ','.join(priorities) if priorities else '0'
        
        # 4. Pseudo-header ordering
        # :method, :authority, :scheme, :path
        pseudo_order = ''.join(h[0] for h in connection.pseudo_headers)
        # e.g., 'masp' for :method, :authority, :scheme, :path
        
        fingerprint = f"{settings_str}|{window_update}|{priority_str}|{pseudo_order}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
```

**Browser Fingerprints:**
- Chrome: `1:65536;2:0;3:1000;4:65536;5:16384|0|0|masp`
- Firefox: `1:65536;2:0;3:100;4:131072;5:16384|12517377|0|masp`
- Safari: `1:65536;2:1;3:100;4:4194304;5:16384|0|0|masp`

**Reference:** Akamai HTTP/2 Fingerprinting (BlackHat EU 2017)

---

### 1.3 Server Header Analysis & Version Detection
**Priority:** MEDIUM | **Confidence Boost:** +8%

**Method:** Parse and analyze Server, X-Powered-By, and custom headers for framework identification.

```python
import re

SERVER_PATTERNS = {
    'openai': [r'openai', r'gpt'],
    'anthropic': [r'anthropic', r'claude'],
    'ollama': [r'ollama'],
    'vllm': [r'vllm'],
    'fastapi': [r'uvicorn', r'fastapi'],
    'flask': [r'werkzeug', r'flask'],
    'express': [r'express'],
    'nginx': [r'nginx'],
}

def analyze_server_headers(headers):
    """
    Detect AI frameworks from server headers
    """
    detections = []
    server = headers.get('Server', '').lower()
    powered_by = headers.get('X-Powered-By', '').lower()
    
    for framework, patterns in SERVER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, server) or re.search(pattern, powered_by):
                detections.append({
                    'framework': framework,
                    'confidence': 0.8,
                    'source': 'server_header'
                })
    
    return detections
```

---

### 1.4 Response Timing Patterns
**Priority:** MEDIUM | **Confidence Boost:** +10%

**Method:** Measure Time-To-First-Byte (TTFB) and response completion patterns.

```python
import time
import statistics

class ResponseTimingAnalyzer:
    def __init__(self):
        self.baseline_human = {'mean': 150, 'std': 50}  # ms
        self.baseline_ai = {'mean': 800, 'std': 300}  # ms
    
    def analyze_timing(self, request_log):
        """
        Analyze response timing patterns
        AI agents show distinct latency profiles
        """
        ttfb_values = [r['ttfb_ms'] for r in request_log]
        
        mean_ttfb = statistics.mean(ttfb_values)
        std_ttfb = statistics.stdev(ttfb_values) if len(ttfb_values) > 1 else 0
        
        # AI agents typically have higher, more consistent latency
        ai_score = 0
        if mean_ttfb > 500:
            ai_score += 0.4  # High latency suggests LLM processing
        if std_ttfb < 100:
            ai_score += 0.3  # Low variance suggests automated system
        
        # Token generation pattern (streaming APIs)
        if self._detect_token_streaming(request_log):
            ai_score += 0.3
        
        return min(ai_score, 1.0)
    
    def _detect_token_streaming(self, request_log):
        """
        Detect SSE/chunked encoding patterns typical of LLM APIs
        """
        streaming_count = sum(1 for r in request_log if r.get('transfer_encoding') == 'chunked')
        return streaming_count / len(request_log) > 0.7
```

---

### 1.5 Error Page Fingerprinting (404, 500)
**Priority:** LOW | **Confidence Boost:** +5%

**Method:** Analyze error page structure, content, and headers.

```python
def fingerprint_error_page(response):
    """
    Error pages often reveal framework/AI agent signatures
    """
    fingerprints = []
    
    # Check for AI framework error patterns
    if response.status_code == 500:
        body = response.text.lower()
        
        if 'traceback' in body and 'python' in body:
            fingerprints.append({'type': 'python_error', 'confidence': 0.7})
        
        if 'exception' in body and 'stack trace' in body:
            fingerprints.append({'type': 'java_error', 'confidence': 0.6})
        
        # AI-specific error patterns
        if 'token' in body and ('exceeded' in body or 'limit' in body):
            fingerprints.append({'type': 'llm_token_error', 'confidence': 0.85})
    
    # 404 page structure
    if response.status_code == 404:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for framework-specific 404 pages
        if soup.find('div', {'class': 'django-debug'}):
            fingerprints.append({'type': 'django', 'confidence': 0.9})
    
    return fingerprints
```

---

## 2. BEHAVIORAL DETECTION

### 2.1 API Response Timing Profiles
**Priority:** HIGH | **Confidence Boost:** +14%

**Method:** Build temporal profiles of request patterns. AI agents show distinct timing signatures.

```python
import numpy as np
from scipy import stats

class BehavioralProfiler:
    def __init__(self):
        self.request_intervals = []
        self.response_sizes = []
    
    def add_request(self, timestamp, response_size, latency_ms):
        if self.request_intervals:
            interval = timestamp - self.request_intervals[-1]
            self.request_intervals.append(interval)
        self.response_sizes.append(response_size)
    
    def calculate_agent_probability(self):
        """
        AI agents exhibit:
        - Regular request intervals (low coefficient of variation)
        - Consistent response sizes
        - Higher latency with low variance
        """
        if len(self.request_intervals) < 5:
            return 0.5  # Insufficient data
        
        # Coefficient of variation for request timing
        cv_intervals = np.std(self.request_intervals) / np.mean(self.request_intervals)
        
        # AI agents tend to have CV < 0.3 (very regular)
        timing_score = max(0, 1 - (cv_intervals * 2))
        
        # Response size variance
        cv_sizes = np.std(self.response_sizes) / np.mean(self.response_sizes)
        size_score = max(0, 1 - (cv_sizes * 1.5))
        
        # Combined score
        agent_probability = (timing_score * 0.6) + (size_score * 0.4)
        return agent_probability
```

---

### 2.2 WebSocket Handshake Fingerprinting
**Priority:** MEDIUM | **Confidence Boost:** +11%

**Method:** Analyze WebSocket upgrade requests and frame structures.

```python
def fingerprint_websocket_handshake(request):
    """
    WebSocket handshakes reveal client implementation details
    """
    fingerprint = {}
    headers = request.headers
    
    # Sec-WebSocket-Key is always present, but format varies
    ws_key = headers.get('Sec-WebSocket-Key', '')
    fingerprint['key_length'] = len(ws_key)
    fingerprint['key_encoding'] = 'base64' if re.match(r'^[A-Za-z0-9+/=]{24}$', ws_key) else 'other'
    
    # Sec-WebSocket-Extensions can reveal client library
    extensions = headers.get('Sec-WebSocket-Extensions', '')
    if 'permessage-deflate' in extensions:
        fingerprint['compression'] = True
    if 'client_max_window_bits' in extensions:
        fingerprint['window_bits'] = re.search(r'client_max_window_bits=(\d+)', extensions).group(1)
    
    # User-Agent + WebSocket = likely automated
    user_agent = headers.get('User-Agent', '').lower()
    ws_libraries = ['websockets/', 'ws/', 'socket.io', 'websocket-client']
    
    for lib in ws_libraries:
        if lib in user_agent:
            fingerprint['library'] = lib
            fingerprint['agent_confidence'] = 0.8
    
    return fingerprint
```

---

### 2.3 Rate Limiting Behavior Analysis
**Priority:** MEDIUM | **Confidence Boost:** +9%

**Method:** Observe how clients respond to rate limiting (429 responses).

```python
class RateLimitAnalyzer:
    def __init__(self):
        self.responses = []
    
    def observe_rate_limit_response(self, request_id, response):
        """
        AI agents respond differently to rate limiting:
        - Some backoff exponentially
        - Others retry immediately
        - Some switch endpoints
        """
        observation = {
            'request_id': request_id,
            'status': response.status_code,
            'retry_after': response.headers.get('Retry-After'),
            'time_until_retry': None
        }
        self.responses.append(observation)
    
    def calculate_compliance_score(self):
        """
        Humans: Often stop or slow down significantly
        Bots: Systematic backoff or persistent retrying
        """
        if len(self.responses) < 3:
            return 0.5
        
        # Check for systematic backoff pattern
        retry_delays = []
        for i in range(1, len(self.responses)):
            delay = self.responses[i]['timestamp'] - self.responses[i-1]['timestamp']
            retry_delays.append(delay)
        
        # Exponential backoff detection
        if len(retry_delays) >= 3:
            ratios = [retry_delays[i] / retry_delays[i-1] for i in range(1, len(retry_delays))]
            if all(1.8 < r < 2.2 for r in ratios):  # ~2x backoff
                return 0.85  # Systematic bot behavior
        
        # Immediate retry (no delay)
        if any(delay < 1 for delay in retry_delays):
            return 0.7  # Impatient bot
        
        return 0.3  # Likely human
```

---

### 2.4 Session Persistence Patterns
**Priority:** LOW | **Confidence Boost:** +6%

**Method:** Analyze cookie handling, session duration, and connection reuse.

```python
def analyze_session_persistence(session_data):
    """
    AI agents often:
    - Don't maintain cookies across sessions
    - Use short-lived sessions
    - Create new connections frequently
    """
    score = 0
    
    # Cookie handling
    if not session_data.get('cookies'):
        score += 0.3  # No cookies = likely automated
    
    # Session duration
    if session_data.get('duration_seconds', 0) < 60:
        score += 0.2  # Very short sessions
    
    # Connection reuse
    if session_data.get('connections_created', 0) > 10:
        score += 0.2  # Many connections
    
    # User-Agent rotation
    if len(session_data.get('user_agents', [])) > 2:
        score += 0.3  # UA rotation suggests evasion attempt
    
    return min(score, 1.0)
```

---

## 3. CONTENT ANALYSIS

### 3.1 HTML DOM Structure Analysis
**Priority:** MEDIUM | **Confidence Boost:** +10%

**Method:** Analyze DOM tree depth, structure, and element distribution.

```python
from bs4 import BeautifulSoup
import hashlib

class DOMAnalyzer:
    def analyze_structure(self, html_content):
        """
        AI agent frameworks produce distinct DOM patterns
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        features = {
            'depth': self._get_max_depth(soup.body),
            'total_nodes': len(soup.find_all()),
            'script_count': len(soup.find_all('script')),
            'div_ratio': len(soup.find_all('div')) / max(len(soup.find_all()), 1),
            'class_entropy': self._calculate_class_entropy(soup),
        }
        
        # Generate structural hash
        structure_hash = hashlib.md5(self._get_structure_signature(soup).encode()).hexdigest()
        
        return features, structure_hash
    
    def _get_max_depth(self, element, current_depth=0):
        if not element:
            return current_depth
        children = element.find_all(recursive=False)
        if not children:
            return current_depth
        return max(self._get_max_depth(child, current_depth + 1) for child in children)
    
    def _calculate_class_entropy(self, soup):
        """
        Framework-specific class naming patterns
        """
        classes = []
        for elem in soup.find_all(class_=True):
            classes.extend(elem.get('class', []))
        
        # Calculate Shannon entropy
        from collections import Counter
        import math
        
        counts = Counter(classes)
        total = sum(counts.values())
        entropy = -sum((count/total) * math.log2(count/total) for count in counts.values())
        
        return entropy
    
    def _get_structure_signature(self, soup):
        """
        Create structural signature for comparison
        """
        signature = []
        for elem in soup.body.find_all(recursive=True):
            sig = elem.name
            if elem.get('class'):
                sig += '.' + '.'.join(elem.get('class'))
            if elem.get('id'):
                sig += '#' + elem.get('id')
            signature.append(sig)
        
        return '|'.join(signature)
```

---

### 3.2 JavaScript Bundle Fingerprinting
**Priority:** HIGH | **Confidence Boost:** +13%

**Method:** Hash JS bundles and compare against known framework signatures.

```python
import hashlib
import re

JS_FRAMEWORK_SIGNATURES = {
    'react': {
        'patterns': [r'react.*\.js', r'__reactFiber', r'react-dom'],
        'hashes': []  # Known React bundle hashes
    },
    'vue': {
        'patterns': [r'vue.*\.js', r'__vue__', r'vue-router'],
    },
    'next.js': {
        'patterns': [r'_next/static', r'__next'],
    },
    'gradio': {
        'patterns': [r'gradio.*\.js', r'gradio-app'],
        'confidence': 0.95  # Gradio = likely AI interface
    },
    'streamlit': {
        'patterns': [r'streamlit.*\.js', r'_stc'],
        'confidence': 0.9  # Streamlit = likely AI/data app
    }
}

def fingerprint_js_bundles(response):
    """
    Extract and hash JavaScript bundles
    """
    detections = []
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all script tags
    scripts = soup.find_all('script', src=True)
    
    for script in scripts:
        src = script.get('src', '')
        
        # Check patterns
        for framework, config in JS_FRAMEWORK_SIGNATURES.items():
            for pattern in config['patterns']:
                if re.search(pattern, src, re.IGNORECASE):
                    detections.append({
                        'framework': framework,
                        'source': src,
                        'confidence': config.get('confidence', 0.8)
                    })
        
        # Fetch and hash if possible (for deeper analysis)
        # hash = hashlib.md5(requests.get(src).content).hexdigest()
    
    return detections
```

---

### 3.3 CSS Class Naming Conventions
**Priority:** LOW | **Confidence Boost:** +5%

**Method:** Analyze CSS class naming patterns for framework identification.

```python
def analyze_css_patterns(html_content):
    """
    Different frameworks use distinct CSS naming conventions:
    - React: BEM (block__element--modifier)
    - Vue: Often single-word or kebab-case
    - Tailwind: Utility classes (flex, items-center, etc.)
    - AI frameworks: Often auto-generated hashes
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    all_classes = []
    
    for elem in soup.find_all(class_=True):
        all_classes.extend(elem.get('class', []))
    
    patterns = {
        'tailwind': r'^(flex|grid|mx|my|px|py|text|bg|border)',
        'bem': r'^[a-z]+__[a-z]+--[a-z]+$',
        'emmet': r'^[a-z]\.[a-z]\.[a-z]',
        'hash': r'^[a-z0-9]{7,}$',  # Auto-generated hashes
    }
    
    detections = {}
    for class_name in all_classes:
        for framework, pattern in patterns.items():
            if re.match(pattern, class_name):
                detections[framework] = detections.get(framework, 0) + 1
    
    # Normalize
    total = sum(detections.values())
    return {k: v/total for k, v in detections.items()} if total > 0 else {}
```

---

### 3.4 Meta Tags & OpenGraph Signatures
**Priority:** LOW | **Confidence Boost:** +4%

**Method:** Extract and analyze meta tags for framework/AI indicators.

```python
def analyze_meta_tags(html_content):
    """
    Meta tags can reveal:
    - Framework generators
    - AI model providers
    - Deployment platforms
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    signatures = []
    
    # Generator tag
    generator = soup.find('meta', attrs={'name': 'generator'})
    if generator and generator.get('content'):
        signatures.append({
            'type': 'generator',
            'value': generator.get('content'),
            'confidence': 0.9
        })
    
    # OpenGraph tags
    og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
    for tag in og_tags:
        content = tag.get('content', '')
        if any(x in content.lower() for x in ['ai', 'bot', 'assistant', 'chat']):
            signatures.append({
                'type': 'og_indicator',
                'value': content,
                'confidence': 0.6
            })
    
    # Check for AI platform signatures
    ai_indicators = {
        'huggingface': r'huggingface\.co',
        'replicate': r'replicate\.com',
        'modal': r'modal\.com',
        'gradio': r'gradio\.app',
    }
    
    for platform, pattern in ai_indicators.items():
        if re.search(pattern, html_content, re.IGNORECASE):
            signatures.append({
                'type': 'platform',
                'value': platform,
                'confidence': 0.85
            })
    
    return signatures
```

---

## 4. AI-SPECIFIC SIGNATURES

### 4.1 Model Identifier Leakage
**Priority:** HIGH | **Confidence Boost:** +18%

**Method:** Detect model names, versions, and provider signatures in responses.

```python
import re

MODEL_SIGNATURES = {
    'openai': {
        'patterns': [
            r'gpt-4', r'gpt-3\.5', r'gpt-4o', r'chatgpt',
            r'model.*:.*gpt', r'openai',
        ],
        'headers': ['x-openai-*'],
        'confidence': 0.95
    },
    'anthropic': {
        'patterns': [
            r'claude', r'anthropic',
            r'model.*:.*claude',
        ],
        'headers': ['x-anthropic-*'],
        'confidence': 0.95
    },
    'ollama': {
        'patterns': [
            r'llama', r'mistral', r'codellama',
            r'ollama',
        ],
        'headers': ['x-ollama-*'],
        'confidence': 0.9
    },
    'google': {
        'patterns': [
            r'gemini', r'palm', r'bard',
            r'model.*:.*gemini',
        ],
        'headers': ['x-google-*'],
        'confidence': 0.9
    },
    'local_model': {
        'patterns': [
            r'thebloke/', r'merge/', r'uncensored',
            r'gguf', r'awq',
        ],
        'confidence': 0.8
    }
}

def detect_model_signatures(response):
    """
    Scan response for model identifiers
    """
    detections = []
    
    # Check response body
    body = response.text[:5000]  # First 5KB
    headers = response.headers
    
    for provider, config in MODEL_SIGNATURES.items():
        # Body patterns
        for pattern in config['patterns']:
            if re.search(pattern, body, re.IGNORECASE):
                detections.append({
                    'provider': provider,
                    'type': 'body_match',
                    'pattern': pattern,
                    'confidence': config['confidence']
                })
        
        # Header patterns
        for header_pattern in config['headers']:
            header_name = header_pattern.replace('*', '')
            if header_name in headers:
                detections.append({
                    'provider': provider,
                    'type': 'header_match',
                    'header': header_name,
                    'confidence': config['confidence']
                })
    
    return detections
```

---

### 4.2 Token Counting Patterns
**Priority:** MEDIUM | **Confidence Boost:** +11%

**Method:** Analyze response size and structure for token generation patterns.

```python
def analyze_token_patterns(response):
    """
    LLM responses have distinct characteristics:
    - Proportional to token count (not fixed)
    - Often include markdown formatting
    - May include thinking/reasoning sections
    """
    body = response.text
    score = 0
    
    # Token-to-character ratio (LLMs ~4 chars per token average)
    char_count = len(body)
    if 1000 < char_count < 100000:  # Reasonable response length
        score += 0.2
    
    # Markdown formatting (common in LLM outputs)
    markdown_indicators = [
        r'^\s*#{1,6}\s+',  # Headers
        r'^\s*[-*]\s+',    # Lists
        r'\*\*.*\*\*',     # Bold
        r'`[^`]+`',        # Inline code
        r'```[\s\S]*?```', # Code blocks
    ]
    
    markdown_count = sum(1 for pattern in markdown_indicators if re.search(pattern, body, re.MULTILINE))
    if markdown_count >= 3:
        score += 0.3  # Heavy markdown usage
    
    # Reasoning/thinking patterns
    thinking_patterns = [
        r'<thinking>[\s\S]*?</thinking>',
        r"let'?s (think|analyze|consider)",
        r'here\'s (a|my|the) (thought|analysis)',
    ]
    
    for pattern in thinking_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            score += 0.3
            break
    
    # Temperature/creativity markers
    if re.search(r'(perhaps|maybe|possibly|likely)', body, re.IGNORECASE):
        score += 0.1  # Hedging language
    
    return min(score, 1.0)
```

---

### 4.3 Streaming Response Patterns (SSE/Chunked)
**Priority:** HIGH | **Confidence Boost:** +15%

**Method:** Detect Server-Sent Events and chunked encoding patterns.

```python
import json

def analyze_streaming_pattern(response):
    """
    LLM APIs commonly use:
    - Server-Sent Events (SSE)
    - Transfer-Encoding: chunked
    - Streaming JSON
    """
    score = 0
    headers = response.headers
    
    # Check for chunked encoding
    if headers.get('Transfer-Encoding', '').lower() == 'chunked':
        score += 0.3
    
    # Check for SSE
    content_type = headers.get('Content-Type', '')
    if 'text/event-stream' in content_type:
        score += 0.4
        
        # Parse SSE events
        if hasattr(response, 'iter_lines'):
            event_count = 0
            for line in response.iter_lines():
                if line.startswith(b'data:'):
                    event_count += 1
                    try:
                        data = json.loads(line[5:].decode())
                        # Check for LLM-specific fields
                        if any(k in data for k in ['choices', 'delta', 'content', 'finish_reason']):
                            score += 0.3
                            break
                    except:
                        pass
                
                if event_count > 5:  # Sample first 5 events
                    break
    
    # Check for streaming API patterns
    if 'stream' in str(response.url).lower():
        score += 0.2
    
    return min(score, 1.0)
```

---

### 4.4 Prompt/Response Structure Analysis
**Priority:** HIGH | **Confidence Boost:** +16%

**Method:** Analyze request/response JSON structures for LLM API patterns.

```python
def analyze_api_structure(request, response):
    """
    LLM APIs have distinct request/response structures:
    
    OpenAI format:
    Request: {"model": "...", "messages": [...], "temperature": ...}
    Response: {"id": "...", "choices": [{"message": {...}}], "usage": {...}}
    
    Anthropic format:
    Request: {"model": "...", "messages": [...], "max_tokens": ...}
    Response: {"id": "...", "content": [...], "usage": {...}}
    """
    score = 0
    
    try:
        req_json = request.json() if request.body else {}
        res_json = response.json()
    except:
        return 0  # Not JSON
    
    # Check request structure
    req_indicators = [
        'messages', 'prompt', 'system', 'user',  # Message fields
        'temperature', 'top_p', 'max_tokens',    # LLM parameters
        'model', 'stream', 'stop'                # Control fields
    ]
    
    req_matches = sum(1 for field in req_indicators if field in req_json)
    if req_matches >= 3:
        score += 0.5
    
    # Check response structure
    res_indicators = [
        'choices', 'message', 'assistant',   # OpenAI
        'content', 'delta',                  # Streaming
        'usage', 'prompt_tokens', 'completion_tokens',  # Token usage
        'finish_reason', 'index'             # Control fields
    ]
    
    res_matches = sum(1 for field in res_indicators if field in res_json)
    if res_matches >= 3:
        score += 0.5
    
    # Check for token usage (strong indicator)
    if 'usage' in res_json:
        usage = res_json['usage']
        if 'prompt_tokens' in usage or 'completion_tokens' in usage:
            score += 0.3
    
    return min(score, 1.0)
```

---

## 5. NETWORK-LEVEL DETECTION

### 5.1 TCP Stack Fingerprinting (p0f-style)
**Priority:** MEDIUM | **Confidence Boost:** +10%

**Method:** Passive TCP/IP stack analysis.

```python
# Simplified p0f-style fingerprinting
TCP_SIGNATURES = {
    'Linux 5.x': {
        'window_size': 64240,
        'ttl': 64,
        'df': True,
        'options': ['mss', 'nop', 'nop', 'sack', 'nop', 'nop', 'timestamp']
    },
    'Windows 10': {
        'window_size': 65535,
        'ttl': 128,
        'df': True,
        'options': ['mss', 'nop', 'nop', 'sack', 'nop', 'nop', 'timestamp', 'nop', 'nop', 'nop', 'nop']
    },
    'macOS': {
        'window_size': 65535,
        'ttl': 64,
        'df': True,
        'options': ['mss', 'nop', 'nop', 'sack', 'timestamp']
    }
}

def tcp_stack_fingerprint(tcp_packet):
    """
    Extract TCP stack characteristics
    """
    signature = {
        'window_size': tcp_packet.window_size,
        'ttl': tcp_packet.ttl,
        'df_flag': tcp_packet.df_flag,
        'options': [opt.name for opt in tcp_packet.options]
    }
    
    # Compare against known signatures
    matches = []
    for os, expected in TCP_SIGNATURES.items():
        score = 0
        if abs(signature['window_size'] - expected['window_size']) < 100:
            score += 0.3
        if signature['ttl'] == expected['ttl']:
            score += 0.3
        if signature['df_flag'] == expected['df']:
            score += 0.2
        if signature['options'] == expected['options']:
            score += 0.2
        
        if score > 0.7:
            matches.append({'os': os, 'score': score})
    
    return matches
```

---

### 5.2 Connection Pooling Behavior
**Priority:** LOW | **Confidence Boost:** +6%

**Method:** Analyze connection reuse patterns.

```python
class ConnectionAnalyzer:
    def __init__(self):
        self.connections = {}
    
    def track_connection(self, client_ip, port, timestamp, reused):
        if client_ip not in self.connections:
            self.connections[client_ip] = []
        
        self.connections[client_ip].append({
            'timestamp': timestamp,
            'reused': reused
        })
    
    def analyze_pooling_behavior(self, client_ip):
        """
        AI agents often:
        - Reuse connections aggressively (performance)
        - Or create new connections for isolation
        """
        if client_ip not in self.connections:
            return 0.5
        
        conn_history = self.connections[client_ip]
        if len(conn_history) < 3:
            return 0.5
        
        reuse_rate = sum(1 for c in conn_history if c['reused']) / len(conn_history)
        
        # Very high or very low reuse suggests automation
        if reuse_rate > 0.9:
            return 0.7  # Aggressive connection reuse
        elif reuse_rate < 0.1:
            return 0.6  # Always new connections
        
        return 0.3  # Normal human pattern
```

---

### 5.3 Keep-Alive Patterns
**Priority:** LOW | **Confidence Boost:** +5%

**Method:** Analyze HTTP keep-alive behavior.

```python
def analyze_keepalive(connection_log):
    """
    AI agents may use different keep-alive strategies:
    - Short-lived connections (isolation)
    - Long-lived connections (performance)
    """
    if not connection_log:
        return 0.5
    
    durations = [conn['duration'] for conn in connection_log]
    avg_duration = sum(durations) / len(durations)
    
    if avg_duration < 5:  # Very short connections
        return 0.6
    elif avg_duration > 300:  # Very long connections
        return 0.5
    
    return 0.3  # Normal range
```

---

### 5.4 Packet Timing Analysis
**Priority:** LOW | **Confidence Boost:** +5%

**Method:** Analyze inter-packet timing for automation detection.

```python
import numpy as np

def analyze_packet_timing(packets):
    """
    AI agents have consistent packet timing
    """
    if len(packets) < 5:
        return 0.5
    
    intervals = [packets[i+1]['time'] - packets[i]['time'] for i in range(len(packets)-1)]
    
    # Calculate coefficient of variation
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    cv = std_interval / mean_interval if mean_interval > 0 else float('inf')
    
    # Low CV = consistent timing = likely automated
    if cv < 0.1:
        return 0.8  # Very consistent
    elif cv < 0.3:
        return 0.6  # Somewhat consistent
    else:
        return 0.3  # Variable = likely human
```

---

## 6. IMPLEMENTATION PRIORITY

| Rank | Technique | Priority | Confidence | Effort | Notes |
|------|-----------|----------|------------|--------|-------|
| 1 | JA3/JA3S TLS Fingerprinting | HIGH | +15% | Low | Industry standard, widely adopted |
| 2 | Model Identifier Leakage | HIGH | +18% | Low | Direct detection, high accuracy |
| 3 | Prompt/Response Structure | HIGH | +16% | Medium | Requires JSON parsing |
| 4 | Streaming Response Patterns | HIGH | +15% | Medium | SSE/chunked analysis |
| 5 | API Timing Profiles | HIGH | +14% | Medium | Temporal analysis |
| 6 | HTTP/2 Frame Ordering | HIGH | +12% | Medium | Requires HTTP/2 parsing |
| 7 | WebSocket Fingerprinting | MEDIUM | +11% | Medium | Specialized protocol |
| 8 | Token Counting Patterns | MEDIUM | +11% | Low | Content analysis |
| 9 | DOM Structure Analysis | MEDIUM | +10% | Medium | Requires HTML parsing |
| 10 | TCP Stack Fingerprinting | MEDIUM | +10% | High | Requires packet capture |
| 11 | Rate Limiting Behavior | MEDIUM | +9% | Low | Behavioral observation |
| 12 | Server Header Analysis | MEDIUM | +8% | Low | Simple regex matching |
| 13 | Connection Pooling | LOW | +6% | Medium | Requires tracking |
| 14 | Session Persistence | LOW | +6% | Low | Cookie analysis |
| 15 | CSS Naming Patterns | LOW | +5% | Low | Content parsing |
| 16 | Error Page Fingerprinting | LOW | +5% | Low | Edge case analysis |
| 17 | Meta Tags/OpenGraph | LOW | +4% | Low | Simple extraction |
| 18 | Packet Timing | LOW | +5% | High | Requires deep packet inspection |
| 19 | Keep-Alive Patterns | LOW | +5% | Low | Connection tracking |
| 20 | JS Bundle Hashing | HIGH | +13% | Medium | Requires fetching bundles |
| 21 | TLS Extension Randomization | MEDIUM | +8% | Medium | Detect GREASE patterns |
| 22 | HTTP Header Canonicalization | MEDIUM | +7% | Low | Header ordering analysis |
| 23 | Certificate Chain Analysis | MEDIUM | +9% | Low | CA/issuer patterns |
| 24 | QUIC/HTTP3 Fingerprinting | MEDIUM | +10% | High | Next-gen protocol |
| 25 | Canvas/WebGL Fingerprinting | MEDIUM | +11% | Medium | Browser-specific |
| 26 | Font Enumeration | LOW | +6% | Low | System fonts reveal OS |
| 27 | Audio Context Fingerprinting | LOW | +7% | Medium | Audio stack analysis |

---

## 7. REFERENCE IMPLEMENTATIONS

### 7.1 Shodan Methodology
**Source:** https://developer.shodan.io/api

Shodan uses:
- Service banner grabbing
- Response pattern matching
- Protocol handshakes
- Vulnerability signature detection

**Key Techniques:**
1. Scan 2,000+ ports per IP
2. Full protocol handshakes (HTTP, SSH, FTP, etc.)
3. Extract service banners and metadata
4. Match against vulnerability database
5. Tag services by type (ICS, malware, uncommon)

---

### 7.2 Censys Methodology
**Source:** https://jhalderm.com/pub/papers/censys-ccs15.pdf

Censys Internet-wide scanning:
- Daily scans of entire IPv4 space
- 3,500+ ports, 100+ protocols
- ZGrab for application-layer probing
- Full TLS handshakes and certificate analysis
- Service prediction on all 65K ports

**Key Techniques:**
1. ZMap for fast IP discovery
2. ZGrab for protocol-specific probing
3. Certificate transparency logs
4. Service/version inference
5. Historical tracking for change detection

---

### 7.3 Wappalyzer Detection Patterns
**Source:** https://github.com/wappalyzer/wappalyzer

Wappalyzer technology detection:
- Regex-based pattern matching
- Multi-vector analysis (HTML, JS, headers, cookies)
- Confidence scoring per detection
- Technology categorization

**Example Pattern:**
```json
{
  "React": {
    "js": {
      "React\\.version": "",
      "react\\.render": ""
    },
    "html": "<[^>]+data-react",
    "headers": {
      "X-Powered-By": "^React"
    },
    "cookies": {
      "react_session": ""
    },
    "confidence": 90
  }
}
```

---

### 7.4 BuiltWith Methodology
**Source:** https://builtwith.com

BuiltWith technology profiler:
- Multi-layer detection (client + server side)
- Technology usage tracking over time
- Technology switching detection
- Infrastructure correlation

---

### 7.5 Nmap Service Detection
**Source:** https://nmap.org/book/service-detection.html

Nmap `-sV` service detection:
- Probe matching against database of 3,000+ services
- Version detection with intensity levels
- RPC service enumeration
- SSL/TLS certificate analysis

**Service Database:**
- Service name
- Protocol
- Product name
- Version
- Extra info (hostname, etc.)

---

## 8. COMBINED CONFIDENCE SCORING

```python
class AgentDetector:
    def __init__(self):
        self.techniques = []
        self.weights = {
            'tls_fingerprint': 0.15,
            'model_signature': 0.18,
            'api_structure': 0.16,
            'streaming': 0.15,
            'timing': 0.14,
            'http2': 0.12,
            'js_bundle': 0.10
        }
    
    def add_detection(self, technique, confidence):
        self.techniques.append({
            'technique': technique,
            'confidence': confidence
        })
    
    def calculate_overall_confidence(self):
        """
        Combine multiple detection signals
        """
        if not self.techniques:
            return 0.0
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for detection in self.techniques:
            technique = detection['technique']
            confidence = detection['confidence']
            
            # Get weight for this technique
            weight = self.weights.get(technique, 0.05)
            
            weighted_score += confidence * weight
            total_weight += weight
        
        # Normalize to 0-1 range
        if total_weight > 0:
            return weighted_score / total_weight
        return 0.0
    
    def classify(self):
        score = self.calculate_overall_confidence()
        
        if score >= 0.85:
            return 'AGENT', 'High confidence AI agent detected'
        elif score >= 0.65:
            return 'LIKELY_AGENT', 'Probable agent behavior'
        elif score >= 0.45:
            return 'UNCERTAIN', 'Mixed signals'
        elif score >= 0.25:
            return 'LIKELY_HUMAN', 'Probably human'
        else:
            return 'HUMAN', 'Human-like behavior'
```

---

## 9. CONCLUSION

This design document provides a comprehensive framework for AI agent detection at Shodan-level sophistication. Key principles:

1. **Multi-vector Analysis:** No single technique is definitive; combine 20+ signals
2. **Passive Detection:** Most techniques work without active probing
3. **Confidence Scoring:** Each technique contributes weighted confidence
4. **Continuous Learning:** Update signatures as new agents/frameworks emerge
5. **Defense in Depth:** Network + content + behavioral analysis

**Estimated Implementation Timeline:**
- Phase 1 (Weeks 1-2): TLS/HTTP fingerprinting (techniques 1-7)
- Phase 2 (Weeks 3-4): Content analysis (techniques 8-17)
- Phase 3 (Weeks 5-6): AI-specific signatures (techniques 18-27)
- Phase 4 (Weeks 7-8): Network-level detection + integration
- Phase 5 (Weeks 9-10): Testing, tuning, confidence calibration

**Target Performance:**
- True Positive Rate: >95%
- False Positive Rate: <2%
- Time to Detection: <500ms per request
- Signature Update Frequency: Weekly

---

*This document represents core intellectual property of CogniWatch. Confidential – do not distribute.*
