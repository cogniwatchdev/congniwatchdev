"""
CogniWatch - Authentication Middleware
Production-ready authentication with JWT tokens, API keys, and role-based access control.
"""

import jwt
import secrets
import hashlib
import bcrypt
import time
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g, current_app
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'

# Role definitions
ROLES = {
    'admin': {
        'level': 100,
        'permissions': ['read', 'write', 'delete', 'admin', 'scan', 'config']
    },
    'viewer': {
        'level': 10,
        'permissions': ['read']
    },
    'scanner': {
        'level': 20,
        'permissions': ['read', 'scan']
    }
}

class AuthManager:
    """
    Authentication manager for CogniWatch.
    Handles JWT tokens, API keys, and session management.
    """
    
    def __init__(self, secret_key: str, token_expiry_hours: int = 24):
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours
        self.api_keys: Dict[str, Dict[str, Any]] = {}  # api_key -> {user_id, role, created_at}
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> {user_id, role, created_at, expires_at}
        self._load_config()
    
    def _load_config(self):
        """Load API keys and user config from secure storage"""
        config_path = Path(__file__).parent.parent / 'config' / 'auth.json'
        if config_path.exists():
            try:
                # In production, this would be encrypted
                with open(config_path) as f:
                    config = json.load(f)
                    self.api_keys = config.get('api_keys', {})
            except Exception as e:
                logger.warning(f"Failed to load auth config: {e}")
    
    def _save_config(self):
        """Save API keys and user config"""
        config_path = Path(__file__).parent.parent / 'config' / 'auth.json'
        try:
            config = {'api_keys': self.api_keys}
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            # Set restrictive permissions
            import os
            os.chmod(config_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to save auth config: {e}")
    
    def create_token(self, user_id: str, role: str = 'viewer') -> str:
        """Create a JWT token for a user"""
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}")
        
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.now(timezone.utc),
            'type': 'access'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        logger.info(f"Created token for user {user_id} with role {role}")
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token and return payload if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != 'access':
                return None
            
            # Check if session still valid
            session_id = payload.get('session_id')
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if datetime.fromisoformat(session['expires_at']) < datetime.now(timezone.utc):
                    # Session expired
                    del self.sessions[session_id]
                    return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def create_api_key(self, user_id: str, role: str = 'viewer', name: str = '') -> str:
        """Create a new API key for programmatic access"""
        api_key = f"cw_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            'user_id': user_id,
            'role': role,
            'name': name or 'Unnamed',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_used': None
        }
        self._save_config()
        
        logger.info(f"Created API key for user {user_id} ({name})")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return user info if valid"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            key_info = self.api_keys[key_hash]
            key_info['last_used'] = datetime.now(timezone.utc).isoformat()
            self._save_config()
            
            return {
                'user_id': key_info['user_id'],
                'role': key_info['role'],
                'auth_type': 'api_key'
            }
        
        return None
    
    def create_session(self, user_id: str, role: str = 'viewer') -> str:
        """Create a new session for web UI"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'role': role,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours)).isoformat()
        }
        
        # Cleanup old sessions
        self._cleanup_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session info if valid"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if datetime.fromisoformat(session['expires_at']) > datetime.now(timezone.utc):
                return session
            else:
                del self.sessions[session_id]
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session (logout)"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def _cleanup_sessions(self):
        """Remove expired sessions"""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, sess in self.sessions.items()
            if datetime.fromisoformat(sess['expires_at']) < now
        ]
        for sid in expired:
            del self.sessions[sid]
    
    def has_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission"""
        if role not in ROLES:
            return False
        return permission in ROLES[role]['permissions']
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False
    
    def validate_user_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate username/password against database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET last_login = datetime('now') WHERE id = ?",
                    (user['id'],)
                )
                conn.commit()
                conn.close()
                
                return {
                    'user_id': str(user['id']),
                    'username': user['username'],
                    'role': user['role']
                }
            
            return None
        except Exception as e:
            logger.error(f"User validation error: {e}")
            return None
    
    def create_user(self, username: str, password: str, role: str = 'viewer') -> Optional[int]:
        """Create a new user in the database"""
        try:
            password_hash = self.hash_password(password)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created user {username} with role {role}")
            return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"User {username} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user info by username"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, role, created_at, last_login FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                }
            return None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None


# Global auth manager (initialized by Flask app)
auth_manager: Optional[AuthManager] = None


def init_auth(app):
    """Initialize authentication with Flask app"""
    global auth_manager
    
    # Get secret key from environment or generate secure random
    secret_key = app.config.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning("Generated random SECRET_KEY (not persistent across restarts)")
    
    auth_manager = AuthManager(
        secret_key=secret_key,
        token_expiry_hours=app.config.get('TOKEN_EXPIRY_HOURS', 24)
    )
    
    logger.info("Authentication initialized")
    return auth_manager


def require_auth(*permissions):
    """
    Decorator to require authentication on Flask routes.
    
    Usage:
        @app.route('/api/agents')
        @require_auth('read')
        def api_agents():
            ...
    
    Multiple permissions:
        @require_auth('read', 'write')  # User needs at least one
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for authentication
            auth_header = request.headers.get('Authorization')
            session_cookie = request.cookies.get('session_id')
            api_key = request.headers.get('X-API-Key')
            
            user_info = None
            
            # Try JWT token (Authorization: Bearer <token>)
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = auth_manager.validate_token(token)
                if payload:
                    user_info = {
                        'user_id': payload['user_id'],
                        'role': payload['role'],
                        'auth_type': 'jwt'
                    }
            
            # Try API key
            elif api_key:
                user_info = auth_manager.validate_api_key(api_key)
            
            # Try session cookie
            elif session_cookie:
                session = auth_manager.get_session(session_cookie)
                if session:
                    user_info = {
                        'user_id': session['user_id'],
                        'role': session['role'],
                        'auth_type': 'session'
                    }
            
            # No valid authentication
            if not user_info:
                return jsonify({'error': 'Authentication required', 'message': 'Provide a valid Bearer token, API key, or session cookie'}), 401
            
            # Check permissions
            if permissions:
                has_access = any(
                    auth_manager.has_permission(user_info['role'], perm)
                    for perm in permissions
                )
                if not has_access:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'Required: {" or ".join(permissions)}'
                    }), 403
            
            # Store user info in Flask's g object for access in route
            g.user = user_info
            g.role = user_info['role']
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'role') or g.role != 'admin':
            return jsonify({
                'error': 'Admin access required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user info from request context"""
    if hasattr(g, 'user'):
        return g.user
    return None


def get_current_role() -> Optional[str]:
    """Get current user's role"""
    if hasattr(g, 'role'):
        return g.role
    return None
