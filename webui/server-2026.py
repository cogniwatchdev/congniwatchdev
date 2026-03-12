"""
CogniWatch 2026 - Next-Gen Dashboard Server
Production-hardened Flask application on PORT 9001
Independent from legacy server (port 9000)

Features:
- Modern iOS-style dashboard with navy/pink/cyan theme
- Real-time agent discovery
- Activity feed from database
- Mobile-responsive design
"""

from flask import Flask, render_template, jsonify, request, g, make_response, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import logging
import sqlite3
from pathlib import Path
import threading
import os

# Configuration
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR.parent / 'config' / 'cogniwatch.json'
DATA_DIR = BASE_DIR.parent / 'data'

def load_config():
    """Load configuration with environment variable override"""
    config = {}
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
    
    # Environment overrides
    config['openclaw_gateway'] = config.get('openclaw_gateway', {})
    config['openclaw_gateway']['url'] = os.environ.get(
        'OPENCLAW_GATEWAY_URL',
        config['openclaw_gateway'].get('url', 'ws://127.0.0.1:18789')
    )
    config['openclaw_gateway']['token'] = os.environ.get(
        'OPENCLAW_GATEWAY_TOKEN',
        config['openclaw_gateway'].get('token', '')
    )
    
    config['webui'] = config.get('webui', {})
    config['webui']['host'] = os.environ.get('COGNIWATCH_HOST', '0.0.0.0')
    config['webui']['port'] = int(os.environ.get('COGNIWATCH_PORT', 9001))  # PORT 9001!
    config['webui']['debug'] = os.environ.get('COGNIWATCH_DEBUG', 'false').lower() == 'true'
    
    return config

# Initialize Flask app
app = Flask(__name__, 
            template_folder=BASE_DIR / 'templates',
            static_folder=BASE_DIR / 'static')

config = load_config()

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('COGNIWATCH_SECRET_KEY', os.urandom(32).hex())
app.config['TOKEN_EXPIRY_HOURS'] = int(os.environ.get('COGNIWATCH_TOKEN_EXPIRY', 24))

# CORS setup - allow local network access
CORS(app, 
     origins=['http://127.0.0.1:9001', 'http://localhost:9001', 'http://0.0.0.0:9001'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'])

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache for scan results
scan_cache = {
    "agents": [],
    "last_scan": None,
    "scan_status": "idle",
    "hosts_scanned": 0,
    "total_hosts": 254,
    "scan_rate": 0.0
}
cache_lock = threading.Lock()

# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    """Get database connection"""
    db_path = DATA_DIR / 'cogniwatch.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================================
# ROUTES - PUBLIC PAGES
# =============================================================================

@app.route('/')
def dashboard():
    """Serve the 2026 dashboard"""
    return render_template('dashboard-2026.html')

@app.route('/legal/terms')
def legal_terms():
    """Serve Terms of Service"""
    return render_template('legal/terms.html')

@app.route('/legal/privacy')
def legal_privacy():
    """Serve Privacy Policy"""
    return render_template('legal/privacy.html')

@app.route('/legal/disclaimer')
def legal_disclaimer():
    """Serve Disclaimer"""
    return render_template('legal/disclaimer.html')

@app.route('/legal/security')
def legal_security():
    """Serve Security Policy"""
    return render_template('legal/security.html')

@app.route('/legal/acceptable-use')
def legal_acceptable_use():
    """Serve Acceptable Use Policy"""
    return render_template('legal/acceptable-use.html')

@app.route('/legal/trademarks')
def legal_trademarks():
    """Serve Trademark Policy"""
    return render_template('legal/trademarks.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(BASE_DIR / 'static', filename)

# =============================================================================
# ROUTES - API ENDPOINTS
# =============================================================================

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "cogniwatch-2026",
        "port": 9001,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/agents')
def api_agents():
    """Get all discovered agents"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get agents with detection results
        c.execute("""
            SELECT DISTINCT 
                a.id, a.name, a.model, a.status, a.gateway_url,
                d.top_framework as framework, d.confidence, d.confidence_level,
                d.host, d.port, d.evidence
            FROM agents a
            LEFT JOIN detection_results d ON a.id = d.host || '-' || d.port
            ORDER BY d.confidence DESC
        """)
        
        agents = []
        for row in c.fetchall():
            # Map confidence_level to badge
            badge_map = {
                'confirmed': 'confirmed',
                'likely': 'likely', 
                'possible': 'possible'
            }
            
            agents.append({
                "id": row["id"] or f"agent-{row['host']}-{row['port']}",
                "name": row["name"] or f"Agent @ {row['host']}:{row['port']}",
                "framework": row["framework"] or "Unknown",
                "model": row["model"] or "unknown",
                "host": row["host"] or "127.0.0.1",
                "port": row["port"] or 8000,
                "status": row["status"] or "online",
                "confidence": row["confidence"] or 0.5,
                "confidence_badge": badge_map.get(row["confidence_level"], "possible"),
                "gateway_url": row["gateway_url"] or f"ws://{row['host']}:{row['port']}"
            })
        
        conn.close()
        
        # If no agents from DB, use cache
        if not agents and scan_cache["agents"]:
            agents = scan_cache["agents"]
        
        return jsonify({
            "agents": agents,
            "count": len(agents),
            "last_scan": scan_cache["last_scan"]
        })
        
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        return jsonify({"error": str(e), "agents": []}), 500

@app.route('/api/agents/activity')
def api_agents_activity():
    """Get recent agent activity feed - REAL DATA FROM DATABASE"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get recent activities with proper column mapping
        c.execute("""
            SELECT 
                id,
                agent_id,
                activity_type,
                tool_name,
                details,
                token_count,
                cost_usd,
                timestamp
            FROM activities
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        
        activities = []
        for row in c.fetchall():
            activities.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "activity_type": row["activity_type"],
                "tool_name": row["tool_name"],
                "details": row["details"],
                "token_count": row["token_count"],
                "cost_usd": float(row["cost_usd"]) if row["cost_usd"] else 0.0,
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        
        logger.info(f"✅ Activity feed: {len(activities)} activities returned")
        return jsonify({
            "activities": activities,
            "count": len(activities)
        })
        
    except Exception as e:
        logger.error(f"Activity feed error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "activities": [],
            "count": 0
        }), 500

@app.route('/api/scan/status')
def api_scan_status():
    """Get current scan status"""
    return jsonify({
        "status": scan_cache["scan_status"],
        "hosts_scanned": scan_cache["hosts_scanned"],
        "total_hosts": scan_cache["total_hosts"],
        "agents_found": len(scan_cache["agents"]),
        "scan_rate": scan_cache["scan_rate"],
        "last_scan": scan_cache["last_scan"]
    })

@app.route('/api/security/alerts')
def api_security_alerts():
    """Get security alerts"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, agent_id, alert_type, severity, message, created_at
            FROM alerts
            WHERE resolved = 0
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        alerts = []
        for row in c.fetchall():
            alerts.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "type": row["alert_type"],
                "severity": row["severity"],
                "message": row["message"],
                "timestamp": row["created_at"]
            })
        
        conn.close()
        return jsonify({"alerts": alerts, "count": len(alerts)})
        
    except Exception as e:
        logger.error(f"Security alerts error: {e}")
        return jsonify({"error": str(e), "alerts": []}), 500

# =============================================================================
# AUTHENTICATION (Simplified for 2026 UI)
# =============================================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Simple token-based authentication"""
    data = request.get_json()
    provided_token = data.get('token', '')
    expected_token = os.environ.get('COGNIWATCH_ADMIN_TOKEN', 
                                    config['openclaw_gateway'].get('token', ''))
    
    if expected_token and provided_token == expected_token:
        return jsonify({
            "success": True,
            "token": "cogniwatch-2026-session-token",
            "expires_in": 86400
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    port = config['webui']['port']
    host = config['webui']['host']
    debug = config['webui']['debug']
    
    logger.info(f"🚀 Starting CogniWatch 2026 Dashboard")
    logger.info(f"   📍 Host: {host}")
    logger.info(f"   🔌 Port: {port}")
    logger.info(f"   🐛 Debug: {debug}")
    logger.info(f"   📁 Templates: {BASE_DIR / 'templates'}")
    logger.info(f"   📁 Static: {BASE_DIR / 'static'}")
    
    # Verify template exists
    template_path = BASE_DIR / 'templates' / 'dashboard-2026.html'
    if template_path.exists():
        logger.info(f"   ✅ Dashboard template found")
    else:
        logger.error(f"   ❌ Dashboard template NOT found at {template_path}")
    
    app.run(host=host, port=port, debug=debug, threaded=True)
