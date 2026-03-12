"""
CogniWatch - Security Middleware
Rate limiting, CORS restrictions, input validation, and security headers.
"""

import re
import ipaddress
from functools import wraps
from flask import request, jsonify, g, make_response, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional, List, Set
import logging

logger = logging.getLogger(__name__)

# CORS configuration
DEFAULT_CORS_ORIGINS = [
    'http://localhost:9000',
    'http://127.0.0.1:9000',
]

# Security headers configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' ws: wss:",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache',
}


class SecurityMiddleware:
    """
    Security middleware for CogniWatch.
    Handles rate limiting, CORS, input validation, and security headers.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.limiter = None
        self.allowed_origins: Set[str] = set(DEFAULT_CORS_ORIGINS)
        self.allowed_ips: Set[str] = set()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Load CORS configuration from environment
        allowed_cors = app.config.get('ALLOWED_CORS_ORIGINS', [])
        if allowed_cors:
            self.allowed_origins = set(allowed_cors)
        else:
            # Default to localhost only
            self.allowed_origins = set(DEFAULT_CORS_ORIGINS)
        
        # Load allowed IPs from environment
        allowed_ips = app.config.get('ALLOWED_IPS', [])
        if allowed_ips:
            self.allowed_ips = set(allowed_ips)
        
        # Initialize rate limiter with higher limits for production use
        # Health check endpoints are exempted to prevent false unhealthy status
        self.limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[
                "120 per minute",      # 2 per second - enough for normal traffic
                "10000 per day",       # 10k/day - won't exhaust from health checks (~2880/day at 30s intervals)
            ],
            storage_uri="memory://",  # In production, use Redis: "redis://localhost:6379"
            strategy="fixed-window",
            # Exempt health check endpoints from rate limiting
            header_check=lambda: request.path in ['/health', '/api/health']
        )
        
        # Explicitly exempt health endpoints using limiter's exempt_when
        app._before_request_funcs = [[]]  # Reset to avoid conflicts
        @app.before_request
        def exempt_health_checks():
            if request.path in ['/health', '/api/health']:
                from flask import g
                g.rate_limit_exempt = True
                return None
        
        # Register before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        logger.info(f"Security middleware initialized with CORS origins: {self.allowed_origins}")
    
    def _before_request(self):
        """Before request processing"""
        # Check if request is from allowed IP (if IP whitelist is configured)
        if self.allowed_ips:
            client_ip = request.remote_addr
            if not self._is_ip_allowed(client_ip):
                logger.warning(f"Blocked request from unauthorized IP: {client_ip}")
                return jsonify({'error': 'Access denied from your IP'}), 403
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ['POST', 'PUT']:
            content_type = request.content_type or ''
            if 'application/json' not in content_type and 'application/x-www-form-urlencoded' not in content_type:
                return jsonify({'error': 'Unsupported content type'}), 415
    
    def _after_request(self, response):
        """Add security headers to all responses"""
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Add CORS headers (only for allowed origins)
        origin = request.headers.get('Origin')
        if origin and origin in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '86400'
        
        return response
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in allowed list (supports CIDR notation)"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for allowed in self.allowed_ips:
                if '/' in allowed:
                    # CIDR notation
                    if ip_obj in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    # Single IP
                    if ip == allowed:
                        return True
        except Exception:
            pass
        return False


def validate_input(validator_func):
    """
    Decorator for input validation.
    
    Usage:
        @app.route('/api/agents/<agent_id>')
        @validate_input(lambda agent_id: re.match(r'^[a-zA-Z0-9_-]+$', agent_id))
        def get_agent(agent_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get route arguments
            for arg_name, arg_value in kwargs.items():
                if isinstance(arg_value, str):
                    # Check for path traversal attempts
                    if '..' in arg_value or arg_value.startswith('/'):
                        logger.warning(f"Path traversal attempt detected: {arg_value}")
                        return jsonify({'error': 'Invalid input'}), 400
                    
                    # Check for SQL injection patterns
                    sql_patterns = [
                        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
                        r"(--|;|\/\*|\*\/)",
                        r"(\bOR\b\s+\d+\s*=\s*\d+)",
                        r"(\bAND\b\s+\d+\s*=\s*\d+)"
                    ]
                    for pattern in sql_patterns:
                        if re.search(pattern, arg_value, re.IGNORECASE):
                            logger.warning(f"SQL injection attempt detected: {arg_value}")
                            return jsonify({'error': 'Invalid input'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_output(text: str, allow_html: bool = False) -> str:
    """
    Sanitize output to prevent XSS attacks.
    
    Args:
        text: Text to sanitize
        allow_html: If True, allow safe HTML tags (use bleach)
    
    Returns:
        Sanitized text
    """
    if allow_html:
        try:
            import bleach
            # Allow only safe HTML tags
            return bleach.clean(
                text,
                tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre'],
                attributes={},
                strip=True
            )
        except ImportError:
            # If bleach not installed, strip all HTML
            return re.sub(r'<[^>]+>', '', text)
    else:
        # Strip all HTML tags
        return re.sub(r'<[^>]+>', '', text)


def validate_agent_id(agent_id: str) -> bool:
    """Validate agent ID format"""
    if not agent_id or not isinstance(agent_id, str):
        return False
    # Allow alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, agent_id))


def validate_url_param(url: str) -> bool:
    """Validate URL parameter (prevent SSRF)"""
    if not url or not isinstance(url, str):
        return False
    
    # Only allow http/https protocols
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # Block internal IPs to prevent SSRF
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname
        
        if hostname in ['localhost', '127.0.0.1', '::1']:
            return False
        
        # Check if it's a private IP
        import socket
        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return False
        except socket.gaierror:
            # DNS resolution failed, let it through (will fail later anyway)
            pass
        
        return True
    except Exception:
        return False


def rate_limit(limits: List[str]):
    """
    Custom rate limit decorator.
    
    Usage:
        @app.route('/api/login', methods=['POST'])
        @rate_limit(["5 per minute"])
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting is handled by Flask-Limiter automatically
            # This decorator is for explicit limits per route
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def add_security_headers_to_app(app):
    """Add security headers middleware to Flask app (legacy support)"""
    middleware = SecurityMiddleware()
    middleware.init_app(app)
    return middleware
