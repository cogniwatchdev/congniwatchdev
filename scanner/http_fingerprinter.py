#!/usr/bin/env python3
"""
CogniWatch - HTTP Fingerprinting Module
Extract and analyze HTTP response signatures for agent framework detection

Detection layers:
- Server header analysis
- X-Powered-By extraction
- Technology stack identification
- HTML DOM structure analysis (title, meta tags, script sources)
- JavaScript bundle hash matching
- CSS class naming pattern detection
- Response size and timing analysis
"""

import requests
import hashlib
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HTTPFingerprint:
    """HTTP fingerprint analysis result"""
    server_header: Optional[str] = None
    x_powered_by: Optional[str] = None
    technology_stack: List[str] = field(default_factory=list)
    title: Optional[str] = None
    meta_tags: Dict[str, str] = field(default_factory=dict)
    script_sources: List[str] = field(default_factory=list)
    js_bundle_hashes: Dict[str, str] = field(default_factory=dict)
    css_class_patterns: List[str] = field(default_factory=list)
    response_size: int = 0
    response_time_ms: float = 0.0
    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    content_type: Optional[str] = None
    html_structure: Dict[str, Any] = field(default_factory=dict)
    framework_indicators: List[str] = field(default_factory=list)
    confidence_signals: Dict[str, float] = field(default_factory=dict)


class HTTPFingerprinter:
    """
    Advanced HTTP fingerprinting for agent framework detection.
    
    Analyzes HTTP responses to extract framework-specific signatures
    across multiple dimensions.
    """
    
    # Known framework patterns
    FRAMEWORK_PATTERNS = {
        'react': {
            'script_patterns': [r'react.*\.js', r'_next/static', r'react-dom'],
            'dom_patterns': [r'data-reactroot', r'data-reactid'],
            'confidence': 0.8
        },
        'vue': {
            'script_patterns': [r'vue.*\.js', r'vue-router'],
            'dom_patterns': [r'data-v-', r'__vue__'],
            'css_patterns': [r'\[v-cloak\]'],
            'confidence': 0.8
        },
        'angular': {
            'script_patterns': [r'angular.*\.js', r'core\.js', r'zone\.js'],
            'dom_patterns': [r'_nghost-', r'_ngcontent-'],
            'confidence': 0.85
        },
        'nextjs': {
            'script_patterns': [r'_next/static'],
            'meta_patterns': [r'next-head'],
            'confidence': 0.9
        },
        'nuxt': {
            'script_patterns': [r'_nuxt/'],
            'meta_patterns': [r'__NUXT__'],
            'css_patterns': [r'\.nuxt-link'],
            'confidence': 0.9
        },
        'svelte': {
            'script_patterns': [r'svelte.*\.js'],
            'dom_patterns': [r'data-svelte-h', r'data-sveltekit-'],
            'confidence': 0.85
        },
        'openclaw': {
            'dom_patterns': [r'<openclaw-', r'openclaw-app', r'OpenClaw'],
            'title_patterns': [r'OpenClaw.*Gateway', r'OpenClaw.*Control'],
            'confidence': 0.95
        },
        'crewai': {
            'title_patterns': [r'CrewAI'],
            'api_patterns': [r'/api/crew', r'/api/agents'],
            'confidence': 0.9
        },
        'autogen': {
            'title_patterns': [r'AutoGen', r'AG2'],
            'api_patterns': [r'/api/agents', r'/api/conversations'],
            'confidence': 0.9
        },
        'langgraph': {
            'title_patterns': [r'LangGraph'],
            'api_patterns': [r'/api/graph', r'/api/state'],
            'confidence': 0.9
        }
    }
    
    # Server header mappings
    SERVER_MAPPINGS = {
        'python': ['Python', 'python'],
        'uvicorn': ['uvicorn', 'Uvicorn'],
        'aiohttp': ['aiohttp', 'AioHTTP'],
        'nginx': ['nginx', 'Nginx'],
        'gunicorn': ['gunicorn', 'Gunicorn'],
        'flask': ['Werkzeug', 'Flask'],
        'fastapi': ['uvicorn', 'FastAPI'],
        'nodejs': ['node', 'Node.js', 'Express']
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CogniWatch/1.0 (Agent Framework Scanner)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def fingerprint(self, url: str) -> Optional[HTTPFingerprint]:
        """
        Perform comprehensive HTTP fingerprinting of a URL.
        
        Args:
            url: Target URL to fingerprint
            
        Returns:
            HTTPFingerprint object with analysis results, or None if failed
        """
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response_time_ms = (time.time() - start_time) * 1000
            
            content_type = response.headers.get('Content-Type', '')
            response_size = len(response.content)
            
            fingerprint = HTTPFingerprint(
                status_code=response.status_code,
                headers=dict(response.headers),
                response_size=response_size,
                response_time_ms=round(response_time_ms, 2),
                content_type=content_type
            )
            
            # Extract server header info
            fingerprint.server_header = response.headers.get('Server')
            fingerprint.x_powered_by = response.headers.get('X-Powered-By')
            
            # Analyze server header for technology stack
            if fingerprint.server_header:
                fingerprint.technology_stack = self._analyze_server_header(fingerprint.server_header)
            
            # Parse HTML if present
            if 'text/html' in content_type:
                self._analyze_html_structure(response.text, fingerprint)
            elif 'application/json' in content_type:
                self._analyze_json_response(response.text, fingerprint)
            
            # Calculate confidence signals
            self._calculate_confidence_signals(fingerprint)
            
            return fingerprint
            
        except requests.Timeout:
            logger.warning(f"HTTP fingerprint timeout for {url}")
            return None
        except requests.ConnectionError:
            logger.warning(f"HTTP connection error for {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP fingerprint error for {url}: {e}")
            return None
    
    def _analyze_server_header(self, server_header: str) -> List[str]:
        """Analyze server header to identify technology stack"""
        technologies = []
        
        for tech, patterns in self.SERVER_MAPPINGS.items():
            for pattern in patterns:
                if pattern.lower() in server_header.lower():
                    technologies.append(tech)
                    break
        
        return technologies
    
    def _analyze_html_structure(self, html: str, fingerprint: HTTPFingerprint):
        """Analyze HTML DOM structure for framework indicators"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                fingerprint.title = title_tag.string.strip()
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', meta.get('property', ''))
                content = meta.get('content', '')
                if name and content:
                    fingerprint.meta_tags[name] = content
            
            # Extract script sources
            for script in soup.find_all('script', src=True):
                src = script.get('src', '')
                if src:
                    fingerprint.script_sources.append(src)
            
            # Calculate JS bundle hashes
            for script in soup.find_all('script', src=True):
                src = script.get('src', '')
                if src and not src.startswith('http'):
                    # Internal script, could hash if we fetch it
                    bundle_name = src.split('/')[-1]
                    if bundle_name:
                        # We'd need to fetch the script to hash it
                        # For now, just note the filename pattern
                        pass
            
            # Extract CSS class patterns
            css_pattern_map = {}
            for tag in soup.find_all(class_=True):
                classes = tag.get('class', [])
                for cls in classes:
                    css_pattern_map[cls] = css_pattern_map.get(cls, 0) + 1
            
            # Find distinctive class patterns
            distinctive_patterns = [
                k for k, v in css_pattern_map.items()
                if re.match(r'^[a-z]+-[a-z0-9]+(-[a-z0-9]+)+$', k)  # kebab-case patterns
            ]
            fingerprint.css_class_patterns = distinctive_patterns[:20]  # Limit to top 20
            
            # Extract HTML structure info
            fingerprint.html_structure = {
                'total_tags': len(soup.find_all()),
                'script_count': len(soup.find_all('script')),
                'link_count': len(soup.find_all('link')),
                'form_count': len(soup.find_all('form')),
                'unique_classes': len(css_pattern_map)
            }
            
            # Detect framework indicators from DOM
            self._detect_framework_in_dom(html, fingerprint)
            
        except Exception as e:
            logger.debug(f"HTML structure analysis error: {e}")
    
    def _detect_framework_in_dom(self, html: str, fingerprint: HTTPFingerprint):
        """Detect framework presence in HTML content"""
        html_lower = html.lower()
        
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            indicators_found = []
            
            # Check DOM patterns
            for pattern in patterns.get('dom_patterns', []):
                if re.search(pattern, html, re.IGNORECASE):
                    indicators_found.append(f'dom:{pattern}')
            
            # Check title patterns
            if fingerprint.title:
                for pattern in patterns.get('title_patterns', []):
                    if re.search(pattern, fingerprint.title, re.IGNORECASE):
                        indicators_found.append(f'title:{pattern}')
            
            # Check meta tag patterns
            for pattern in patterns.get('meta_patterns', []):
                for tag_name, tag_content in fingerprint.meta_tags.items():
                    if re.search(pattern, tag_name, re.IGNORECASE) or \
                       re.search(pattern, tag_content, re.IGNORECASE):
                        indicators_found.append(f'meta:{pattern}')
            
            # Check script source patterns
            for pattern in patterns.get('script_patterns', []):
                for src in fingerprint.script_sources:
                    if re.search(pattern, src, re.IGNORECASE):
                        indicators_found.append(f'script:{pattern}')
            
            # Check CSS patterns if we have them
            for pattern in patterns.get('css_patterns', []):
                for css_class in fingerprint.css_class_patterns:
                    if re.search(pattern, css_class, re.IGNORECASE):
                        indicators_found.append(f'css:{pattern}')
            
            if indicators_found:
                fingerprint.framework_indicators.append(framework)
                # Store confidence for this framework
                base_confidence = patterns.get('confidence', 0.5)
                # Boost confidence for multiple indicators
                boost = min(len(indicators_found) * 0.05, 0.3)
                fingerprint.confidence_signals[framework] = base_confidence + boost
    
    def _analyze_json_response(self, json_text: str, fingerprint: HTTPFingerprint):
        """Analyze JSON response for agent framework signatures"""
        import json
        
        try:
            data = json.loads(json_text)
            
            # Look for common agent/API patterns
            if isinstance(data, dict):
                # Check for common agent framework fields
                agent_fields = ['agent', 'agents', 'session', 'sessions', 'model', 'messages',
                               'assistant', 'thread', 'run', 'crew', 'workflow']
                
                for field in agent_fields:
                    if field in data or field in str(data).lower():
                        fingerprint.framework_indicators.append(f'api_field:{field}')
                        fingerprint.confidence_signals[field] = 0.6
            
            # Check response size patterns
            response_size = len(json_text)
            if response_size < 1000:
                fingerprint.confidence_signals['small_json'] = 0.3
            elif response_size > 100000:
                fingerprint.confidence_signals['large_json'] = 0.4
                
        except json.JSONDecodeError:
            logger.debug("Response is not valid JSON")
    
    def _calculate_confidence_signals(self, fingerprint: HTTPFingerprint):
        """Calculate additional confidence signals from fingerprint data"""
        
        # Response size analysis
        if fingerprint.response_size < 500:
            fingerprint.confidence_signals['tiny_response'] = 0.2
        elif fingerprint.response_size > 1000000:
            fingerprint.confidence_signals['large_response'] = 0.3
        elif 5000 <= fingerprint.response_size <= 50000:
            # Typical web app size
            fingerprint.confidence_signals['typical_webapp'] = 0.4
        
        # Response time analysis
        if fingerprint.response_time_ms < 100:
            fingerprint.confidence_signals['fast_response'] = 0.3
        elif fingerprint.response_time_ms > 2000:
            fingerprint.confidence_signals['slow_response'] = 0.3
        
        # Content type signals
        if fingerprint.content_type and 'application/json' in fingerprint.content_type:
            fingerprint.confidence_signals['json_api'] = 0.5
        elif fingerprint.content_type and 'text/html' in fingerprint.content_type:
            # Check if it's a SPA (small HTML + many scripts)
            if fingerprint.html_structure.get('script_count', 0) > 3:
                fingerprint.confidence_signals['spa_candidate'] = 0.5
        
        # Custom headers
        custom_headers = ['X-Powered-By', 'X-Frame-Options', 'X-Content-Type-Options',
                         'X-Generator', 'Server-Hardware', 'X-Backend-Server']
        custom_header_count = sum(1 for h in custom_headers if h in fingerprint.headers)
        if custom_header_count > 0:
            fingerprint.confidence_signals['custom_headers'] = min(custom_header_count * 0.1, 0.4)
    
    def batch_fingerprint(self, urls: List[str]) -> Dict[str, HTTPFingerprint]:
        """Fingerprint multiple URLs in batch"""
        results = {}
        for url in urls:
            result = self.fingerprint(url)
            if result:
                results[url] = result
        return results
    
    def compare_fingerprints(self, fp1: HTTPFingerprint, fp2: HTTPFingerprint) -> float:
        """
        Compare two fingerprints for similarity.
        Returns similarity score (0.0 - 1.0)
        """
        similarity = 0.0
        comparisons = 0
        
        # Server header match
        if fp1.server_header and fp2.server_header:
            if fp1.server_header.lower() == fp2.server_header.lower():
                similarity += 1.0
            comparisons += 1
        
        # Technology stack overlap
        if fp1.technology_stack and fp2.technology_stack:
            t1 = set(fp1.technology_stack)
            t2 = set(fp2.technology_stack)
            if t1 and t2:
                tech_overlap = len(t1 & t2) / max(len(t1 | t2), 1)
                similarity += tech_overlap
                comparisons += 1
        
        # Title match
        if fp1.title and fp2.title:
            if fp1.title.lower() == fp2.title.lower():
                similarity += 1.0
            comparisons += 1
        
        # Framework indicators match
        if fp1.framework_indicators and fp2.framework_indicators:
            f1 = set(fp1.framework_indicators)
            f2 = set(fp2.framework_indicators)
            if f1 and f2:
                fw_overlap = len(f1 & f2) / max(len(f1 | f2), 1)
                similarity += fw_overlap
                comparisons += 1
        
        if comparisons > 0:
            return similarity / comparisons
        return 0.0


def main():
    """Test HTTP fingerprinter on local targets"""
    import json
    
    print("\n🔍 CogniWatch HTTP Fingerprinter\n")
    
    fingerprinter = HTTPFingerprinter(timeout=3.0)
    
    # Test targets
    targets = [
        "http://192.168.0.245:18789",  # Neo gateway
        "http://localhost:8000",
        "http://localhost:5000",
    ]
    
    for url in targets:
        print(f"\n{'='*60}")
        print(f"Target: {url}")
        print('='*60)
        
        fp = fingerprinter.fingerprint(url)
        
        if fp:
            print(f"\n📊 Status Code: {fp.status_code}")
            print(f"📏 Response Size: {fp.response_size:,} bytes")
            print(f"⏱️  Response Time: {fp.response_time_ms:.2f}ms")
            print(f"🌐 Server: {fp.server_header or 'Not set'}")
            print(f"💡 X-Powered-By: {fp.x_powered_by or 'Not set'}")
            print(f"📋 Content-Type: {fp.content_type or 'Unknown'}")
            
            if fp.title:
                print(f"📑 Title: {fp.title}")
            
            if fp.technology_stack:
                print(f"🛠️  Tech Stack: {', '.join(fp.technology_stack)}")
            
            if fp.framework_indicators:
                print(f"🎯 Framework Indicators: {', '.join(fp.framework_indicators)}")
            
            if fp.confidence_signals:
                print(f"\n📈 Confidence Signals:")
                for signal, confidence in sorted(fp.confidence_signals.items(), 
                                                   key=lambda x: x[1], reverse=True):
                    print(f"   • {signal}: {confidence:.2f}")
            
            # Save full fingerprint to file
            output = {
                'url': url,
                'server_header': fp.server_header,
                'x_powered_by': fp.x_powered_by,
                'technology_stack': fp.technology_stack,
                'title': fp.title,
                'meta_tags': fp.meta_tags,
                'response_size': fp.response_size,
                'response_time_ms': fp.response_time_ms,
                'status_code': fp.status_code,
                'framework_indicators': fp.framework_indicators,
                'confidence_signals': fp.confidence_signals
            }
            
            output_file = f"/tmp/fingerprint_{url.replace('http://', '').replace(':', '_').replace('.', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"\n💾 Full fingerprint saved to: {output_file}")
            
        else:
            print("❌ Fingerprinting failed (service unreachable)")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
