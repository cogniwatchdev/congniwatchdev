"""
CogniWatch Database Schema
SQLite database for agent monitoring data

Includes tables for:
- Agents and sessions
- Activities (time-series)
- Alerts
- Daily costs
- Detection results (multi-layer)
- Telemetry data
- Analysis metrics
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'

def init_db():
    """Initialize database with schema"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Agents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        model TEXT,
        persona TEXT,
        status TEXT DEFAULT 'unknown',
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP,
        gateway_url TEXT,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        label TEXT,
        kind TEXT,
        created_at TIMESTAMP,
        last_activity TIMESTAMP,
        message_count INTEGER DEFAULT 0,
        token_usage_in INTEGER DEFAULT 0,
        token_usage_out INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Activities table (time-series agent actions)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        session_id TEXT,
        activity_type TEXT NOT NULL,
        tool_name TEXT,
        details JSON,
        token_count INTEGER,
        cost_usd REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    # Create index for fast timestamp queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_activities_timestamp 
    ON activities(timestamp DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_activities_agent 
    ON activities(agent_id, timestamp DESC)
    ''')
    
    # Alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        session_id TEXT,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        details JSON,
        resolved BOOLEAN DEFAULT FALSE,
        resolved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    # Cost tracking table (daily aggregates)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        agent_id TEXT,
        token_in INTEGER DEFAULT 0,
        token_out INTEGER DEFAULT 0,
        api_calls INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        UNIQUE(date, agent_id),
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Create index for date queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_daily_costs_date 
    ON daily_costs(date DESC)
    ''')
    
    # ===== VULCAN TELEMETRY TABLES =====
    
    # Agent capabilities table (Identity & Capability Telemetry)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_capabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        framework TEXT,
        framework_version TEXT,
        model_provider TEXT,
        model_name TEXT,
        context_window INTEGER,
        available_tools JSON,
        api_versions JSON,
        feature_flags JSON,
        persona TEXT,
        capabilities_hash TEXT,
        streaming_support BOOLEAN,
        streaming_protocol TEXT,
        multimodal_input JSON,
        multimodal_output JSON,
        function_calling BOOLEAN,
        agent_orchestration BOOLEAN,
        memory_persistence BOOLEAN,
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        UNIQUE(agent_id, updated_at)
    )
    ''')
    
    # Performance metrics table (Performance Telemetry)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        response_time_p50 REAL,
        response_time_p95 REAL,
        response_time_p99 REAL,
        throughput_rps REAL,
        concurrent_sessions INTEGER,
        token_throughput REAL,
        error_rate REAL,
        availability_pct REAL,
        measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Create indexes for performance metrics
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent 
    ON performance_metrics(agent_id, measured_at DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_performance_metrics_time 
    ON performance_metrics(measured_at DESC)
    ''')
    
    # Security assessments table (Security Posture Telemetry)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        auth_method TEXT,
        rate_limiting_enabled BOOLEAN,
        rate_limit_threshold INTEGER,
        cors_policy TEXT,
        admin_endpoints_exposed BOOLEAN,
        default_credentials BOOLEAN,
        https_enforced BOOLEAN,
        known_vulnerabilities JSON,
        security_score INTEGER,
        assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Create index for security assessments
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_security_assessments_agent 
    ON security_assessments(agent_id, assessed_at DESC)
    ''')
    
    # Topology data table (Network Topology Telemetry)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topology_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        behind_proxy BOOLEAN,
        proxy_type TEXT,
        load_balanced BOOLEAN,
        cdn_detected BOOLEAN,
        hosting_provider TEXT,
        container_detected BOOLEAN,
        orchestrator TEXT,
        asn TEXT,
        geo_location TEXT,
        network_distance INTEGER,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Create indexes for topology data
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_topology_data_agent 
    ON topology_data(agent_id)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_topology_data_hosting 
    ON topology_data(hosting_provider)
    ''')
    
    # Behavioral patterns table (Behavioral Telemetry)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS behavioral_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        uptime_pattern JSON,
        peak_activity_hours JSON,
        session_duration_p50 REAL,
        session_duration_p95 REAL,
        endpoint_usage JSON,
        version_history JSON,
        update_frequency REAL,
        activity_trend TEXT,
        anomaly_score REAL,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    # Create index for behavioral patterns
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_behavioral_patterns_agent 
    ON behavioral_patterns(agent_id)
    ''')
    
    # ===== VULCAN PHASE 3: Detection & Analysis Tables =====
    
    # Detection results table (multi-layer detection)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detection_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host TEXT NOT NULL,
        port INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        detection_time_ms REAL,
        top_framework TEXT,
        confidence REAL,
        confidence_level TEXT,
        detection_quality TEXT,
        layer_results JSON,
        framework_scores JSON,
        all_signals JSON,
        evidence JSON,
        recommendation TEXT,
        UNIQUE(host, port, timestamp)
    )
    ''')
    
    # Create indexes for detection queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_detection_host_port 
    ON detection_results(host, port)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_detection_timestamp 
    ON detection_results(timestamp DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_detection_framework 
    ON detection_results(top_framework)
    ''')
    
    # Analysis metrics table (for heatmap and trends API endpoints)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_type TEXT NOT NULL,  -- heatmap, trend, summary
        metric_name TEXT NOT NULL,
        timeframe TEXT,  -- hour, day, week, month
        metric_value REAL,
        metadata JSON,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for analysis queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_analysis_type_name 
    ON analysis_metrics(metric_type, metric_name)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
    ON analysis_metrics(timestamp DESC)
    ''')
    
    # ===== CLAWJACKED DETECTION TABLES (CIPHER) =====
    
    # WebSocket connections monitoring table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS websocket_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gateway_port INTEGER NOT NULL,
        source_ip TEXT NOT NULL,
        connection_count INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for fast IP-based queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_ws_connections_ip_time 
    ON websocket_connections(source_ip, timestamp DESC)
    ''')
    
    # Authentication attempts monitoring table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auth_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gateway_port INTEGER NOT NULL,
        source_ip TEXT NOT NULL,
        success BOOLEAN NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for IP and success tracking
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_auth_attempts_ip_time 
    ON auth_attempts(source_ip, timestamp DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_auth_attempts_success 
    ON auth_attempts(success, timestamp DESC)
    ''')
    
    # Device registrations auditing table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gateway_port INTEGER NOT NULL,
        device_name TEXT NOT NULL,
        device_id TEXT NOT NULL,
        source_ip TEXT NOT NULL,
        auto_approved BOOLEAN NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for device lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_device_registrations_id 
    ON device_registrations(device_id, timestamp DESC)
    ''')
    
    # Create index for auto-approve tracking
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_device_registrations_approved 
    ON device_registrations(auto_approved, timestamp DESC)
    ''')
    
    # ===== SECURITY DASHBOARD TABLES =====
    
    # Security alerts table (ClawJacked detection feed)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gateway_id TEXT NOT NULL,
        gateway_name TEXT NOT NULL,
        gateway_host TEXT NOT NULL,
        gateway_port INTEGER NOT NULL,
        detection_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        source_ip TEXT NOT NULL,
        details TEXT NOT NULL,
        status TEXT DEFAULT 'new',
        acknowledged_at TIMESTAMP,
        resolved_at TIMESTAMP,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for fast alert queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_security_alerts_time 
    ON security_alerts(timestamp DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_security_alerts_gateway 
    ON security_alerts(gateway_id, timestamp DESC)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_security_alerts_severity 
    ON security_alerts(severity, timestamp DESC)
    ''')
    
    # Gateways table (for security posture tracking)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gateways (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        host TEXT NOT NULL,
        port INTEGER NOT NULL,
        version TEXT,
        auth_method TEXT DEFAULT 'token',
        rate_limit_enabled BOOLEAN DEFAULT TRUE,
        device_approval_mode TEXT DEFAULT 'manual',
        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert default gateways if not exists
    cursor.execute('''
    INSERT OR IGNORE INTO gateways (id, name, host, port, auth_method, rate_limit_enabled, device_approval_mode)
    VALUES 
        ('neo-18789', 'Neo', '127.0.0.1', 18789, 'token', 1, 'manual'),
        ('atlas-18790', 'Atlas', '192.168.0.245', 18790, 'token', 1, 'manual'),
        ('cipher-18794', 'Cipher', '192.168.0.246', 18794, 'token', 1, 'manual'),
        ('vulcan-18795', 'Vulcan', '192.168.0.247', 18795, 'token', 1, 'manual')
    ''')
    
    # Users table for authentication
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'viewer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized at {DB_PATH}")
    print(f"   + VULCAN telemetry tables added")
    print(f"   + Detection results table added")
    print(f"   + Analysis metrics table added")
    print(f"   + CLAWJACKED detection tables added (websocket, auth, devices)")
    print(f"   + Users table added for authentication")

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
