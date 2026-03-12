#!/usr/bin/env python3
"""
CogniWatch Web UI Server
Main Flask application for the CogniWatch AI Agent Detection Network
"""

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

from webui.auth import init_auth
from webui.config import load_config
from webui.database.schema import init_db
from webui.middleware import SecurityMiddleware

# Load configuration
config = load_config()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('COGNIWATCH_SECRET_KEY', os.urandom(32).hex())

# =============================================================================
# CORS CONFIGURATION - Custom middleware handles actual headers
# =============================================================================

app.config['ALLOWED_CORS_ORIGINS'] = [
    'https://cogniwatch.dev',
    'https://www.cogniwatch.dev',
    os.environ.get('COGNIWATCH_HOST', 'http://127.0.0.1') + f":{config['webui']['port']}",
]
app.config['ALLOWED_IPS'] = os.environ.get('COGNIWATCH_ALLOWED_IPS', '').split(',') if os.environ.get('COGNIWATCH_ALLOWED_IPS') else []

# Initialize authentication
init_auth(app)

# Initialize security middleware (handles CORS, rate limiting, headers)
security = SecurityMiddleware()
security.init_app(app)

# Flask-CORS is disabled - custom middleware handles CORS with proper domain matching
# CORS(app, 
#      origins=app.config['ALLOWED_CORS_ORIGINS'],
#      supports_credentials=True,
#      allow_headers=['Content-Type', 'Authorization', 'X-API-Key'],
#      methods=['GET', 'POST', 'OPTIONS'])

# =============================================================================
# Database Helpers
# =============================================================================

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(config['database']['path'])
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================================
# Context Processors
# =============================================================================

@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    return {
        'app_version': config['app']['version'],
        'app_name': config['app']['name'],
        'scan_interval': config['scanner']['interval_minutes'],
    }

# =============================================================================
# Main Dashboard Routes (PUBLIC - No Authentication Required)
# =============================================================================

@app.route('/')
def index():
    """Root redirect to dashboard"""
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    """Main KPI dashboard - Tabler UI (PUBLIC)"""
    return render_template('dashboard-2026.html')

@app.route('/scan')
def scan():
    """Scan interface - Tabler UI"""
    return render_template('scan.html')

@app.route('/agents')
def agents():
    """Agent list view"""
    return render_template('agents.html')

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/security')
def security_page():
    """Security overview"""
    return render_template('security.html')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/about')
def about_page():
    """About page"""
    return render_template('about.html')

@app.route('/help')
def help_page():
    """Help center"""
    return render_template('help.html')

# =============================================================================
# API Endpoints (PUBLIC - No Authentication Required)
# =============================================================================

@app.route('/api/agents')
def api_agents():
    """
    API: Get all agents from detection_results table
    Returns agents discovered by the scanner with confidence scores
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest detections per host:port
        cursor.execute('''
            SELECT DISTINCT host, port, top_framework, confidence, confidence_level, 
                   detection_quality, layer_results, evidence, timestamp
            FROM detection_results
            WHERE (host, port, timestamp) IN (
                SELECT host, port, MAX(timestamp)
                FROM detection_results
                GROUP BY host, port
            )
            ORDER BY confidence DESC, timestamp DESC
        ''')
        
        agents = []
        for row in cursor.fetchall():
            agent_data = {
                'id': f"{row['top_framework']}-{row['host'].replace('.', '-')}-{row['port']}",
                'host': row['host'],
                'port': row['port'],
                'framework': row['top_framework'],
                'confidence': row['confidence'],
                'confidence_badge': get_confidence_badge(row['confidence']),
                'detection_quality': row['detection_quality'],
                'evidence': json.loads(row['evidence']) if row['evidence'] else {},
                'last_seen': row['timestamp'],
            }
            agents.append(agent_data)
        
        conn.close()
        
        # Return with metadata
        return jsonify({
            'agents': agents,
            'total': len(agents),
            'last_scan': get_last_scan_time(),
            'scan_status': 'idle'
        })
        
    except Exception as e:
        app.logger.error(f"API agents error: {e}")
        return jsonify({'error': str(e), 'agents': [], 'total': 0}), 500

@app.route('/api/scan/status')
def api_scan_status():
    """Get current scan status"""
    try:
        return jsonify({
            'status': 'idle',
            'progress': 0,
            'total_hosts': 254,
            'scanned': 0,
            'last_completed': get_last_scan_time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/alerts')
def api_security_alerts():
    """Get security alerts"""
    try:
        # Return mock alerts for now
        return jsonify({
            'alerts': [],
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': config['app']['version']})

# =============================================================================
# Helper Functions
# =============================================================================

def get_confidence_badge(confidence: float) -> str:
    """Get badge label for confidence score"""
    if confidence >= 0.95:
        return 'Confirmed'
    elif confidence >= 0.80:
        return 'High'
    elif confidence >= 0.60:
        return 'Medium'
    elif confidence >= 0.40:
        return 'Low'
    else:
        return 'Speculative'

def get_last_scan_time() -> str:
    """Get timestamp of last completed scan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(timestamp) FROM detection_results')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 'Never'
    except:
        return 'Never'

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start Flask server
    host = os.environ.get('COGNIWATCH_HOST', '0.0.0.0')
    port = int(os.environ.get('COGNIWATCH_PORT', config['webui']['port']))
    debug = os.environ.get('COGNIWATCH_DEBUG', 'false').lower() == 'true'
    
    print(f"🦈 CogniWatch Web UI starting on {host}:{port}")
    print(f"   Debug: {debug}")
    print(f"   Database: {config['database']['path']}")
    
    app.run(host=host, port=port, debug=debug)
