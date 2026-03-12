#!/usr/bin/env python3
"""
CogniWatch Server - MINIMAL WORKING VERSION WITH AUTH
Production-ready authentication enabled.
"""

from flask import Flask, render_template, jsonify, request
import sqlite3, json, logging, os, hashlib
from pathlib import Path
from functools import wraps
import time

app = Flask(__name__)

DATA_DIR = Path(__file__).parent.parent / 'data'
TEMPLATES_DIR = Path(__file__).parent / 'templates'
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'cogniwatch.json'

# Load config
def load_tokens():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            return config.get('auth', {}).get('tokens', {})
    return {}

AUTH_TOKENS = load_tokens()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        if not token or token not in AUTH_TOKENS:
            return jsonify({'error': 'Unauthorized', 'message': 'Valid API token required'}), 401
        
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/agents')
@require_auth
def api_agents():
    db = DATA_DIR / 'cogniwatch.db'
    if not db.exists():
        return jsonify({"agents": [], "error": "No database"})
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM detection_results ORDER BY confidence DESC")
        agents = [dict(row) for row in c.fetchall()]
        return jsonify({"agents": agents, "total": len(agents)})
    except Exception as e:
        return jsonify({"error": str(e), "agents": []})
    finally:
        conn.close()

@app.route('/api/scan/status')
@require_auth
def api_scan_status():
    return jsonify({"scanning": False, "hostsScanned": 254, "totalHosts": 254})

@app.route('/api/agents/activity')
@require_auth
def api_activity():
    db = DATA_DIR / 'cogniwatch.db'
    if not db.exists():
        return jsonify({"activities": []})
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT id, agent_id, activity_type, tool_name, details, timestamp FROM activities ORDER BY timestamp DESC LIMIT 20")
        activities = [dict(row) for row in c.fetchall()]
        return jsonify({"activities": activities})
    except:
        return jsonify({"activities": []})
    finally:
        conn.close()

if __name__ == '__main__':
    logger.info(f"🚀 Starting CogniWatch on port 9000...")
    logger.info(f"   Templates: {TEMPLATES_DIR}")
    logger.info(f"   Database: {DATA_DIR}")
    app.run(host='0.0.0.0', port=9000, threaded=True, debug=False)
