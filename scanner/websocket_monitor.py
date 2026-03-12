#!/usr/bin/env python3
"""
CogniWatch - WebSocket Anomaly Detection Module
Detects ClawJacked attack pattern: WebSocket connection spikes from localhost

Detection Logic:
- Monitor gateway ports (18789, 18790, 18794, 18795)
- Track WebSocket connection rate per source IP
- Baseline: 1-5 concurrent connections is normal
- Alert threshold: >50 connections/min from single IP
- Store connection events in database for trend analysis
"""

import socket
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway ports to monitor
GATEWAY_PORTS = [18789, 18790, 18794, 18795]

# Detection thresholds
CONNECTION_THRESHOLD = 50  # connections per minute
BASELINE_MAX = 5  # normal concurrent connections
TIME_WINDOW_SECONDS = 60

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'


class WebSocketMonitor:
    """Monitor WebSocket connections for anomaly detection"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.connection_history: Dict[str, List[datetime]] = {}  # IP -> timestamps
        
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_table(self):
        """Ensure websocket_connections table exists"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
    
    def check_websocket_port(self, host: str, port: int) -> bool:
        """Check if WebSocket port is open (simple TCP check)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"WebSocket port check failed for {host}:{port}: {e}")
            return False
    
    def simulate_connection_event(self, source_ip: str, gateway_port: int):
        """
        Record a WebSocket connection event
        In production, this would hook into gateway logs or use netstat/ss
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get current connection count for this IP in the time window
        cutoff_time = datetime.now() - timedelta(seconds=TIME_WINDOW_SECONDS)
        
        cursor.execute('''
        SELECT COUNT(*) as count FROM websocket_connections
        WHERE source_ip = ? AND gateway_port = ? AND timestamp > ?
        ''', (source_ip, gateway_port, cutoff_time.isoformat()))
        
        row = cursor.fetchone()
        current_count = row['count'] if row else 0
        
        # Record new connection
        cursor.execute('''
        INSERT INTO websocket_connections (gateway_port, source_ip, connection_count)
        VALUES (?, ?, ?)
        ''', (gateway_port, source_ip, current_count + 1))
        
        conn.commit()
        conn.close()
        
        # Update in-memory history
        key = f"{source_ip}:{gateway_port}"
        if key not in self.connection_history:
            self.connection_history[key] = []
        self.connection_history[key].append(datetime.now())
        
        logger.debug(f"Recorded WebSocket connection from {source_ip} to port {gateway_port} (count: {current_count + 1})")
    
    def detect_anomaly(self, source_ip: str, gateway_port: int) -> Tuple[bool, int, float]:
        """
        Check if connection rate from IP exceeds threshold
        
        Returns:
            (is_anomaly, connection_count, confidence_score)
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get connection count in time window
        cutoff_time = datetime.now() - timedelta(seconds=TIME_WINDOW_SECONDS)
        
        cursor.execute('''
        SELECT COUNT(*) as count FROM websocket_connections
        WHERE source_ip = ? AND gateway_port = ? AND timestamp > ?
        ''', (source_ip, gateway_port, cutoff_time.isoformat()))
        
        row = cursor.fetchone()
        connection_count = row['count'] if row else 0
        
        conn.close()
        
        # Calculate confidence score based on severity
        if connection_count >= CONNECTION_THRESHOLD:
            # Critical: way above threshold
            confidence = min(0.95, 0.8 + (connection_count - CONNECTION_THRESHOLD) / 200)
            return True, connection_count, confidence
        elif connection_count > BASELINE_MAX * 2:
            # Warning: elevated but not critical
            confidence = 0.5 + (connection_count - BASELINE_MAX * 2) / 100
            return False, connection_count, confidence
        
        return False, connection_count, 0.0
    
    def scan_gateway(self, host: str, port: int) -> Dict:
        """
        Scan a gateway port for WebSocket anomalies
        
        Returns detection result dict
        """
        result = {
            "detection_type": "websocket_anomaly",
            "host": host,
            "port": port,
            "is_open": False,
            "anomaly_detected": False,
            "connection_count": 0,
            "confidence": 0.0,
            "severity": "NONE",
            "evidence": [],
            "recommendation": ""
        }
        
        # Check if port is open
        if not self.check_websocket_port(host, port):
            result["evidence"].append(f"Port {port} is closed")
            return result
        
        result["is_open"] = True
        result["evidence"].append(f"WebSocket port {port} is open")
        
        # For localhost connections, simulate checking connection rate
        # In production, this would analyze real connection data
        if host in ["127.0.0.1", "localhost", "::1"]:
            # Check for anomaly (simulated for now)
            is_anomaly, count, confidence = self.detect_anomaly(host, port)
            
            result["connection_count"] = count
            result["anomaly_detected"] = is_anomaly
            result["confidence"] = confidence
            
            if is_anomaly:
                result["severity"] = "HIGH"
                result["evidence"].append(f"Detected {count} connections/min from {host} (threshold: {CONNECTION_THRESHOLD})")
                result["recommendation"] = "Investigate potential ClawJacked WebSocket flooding attack. Consider rate limiting."
            else:
                result["severity"] = "LOW"
                result["evidence"].append(f"Normal connection rate: {count} connections/min")
        else:
            # Remote host - just record baseline
            is_anomaly, count, confidence = self.detect_anomaly(host, port)
            result["connection_count"] = count
            result["severity"] = "INFO"
            result["evidence"].append(f"Remote host connection baseline: {count} connections")
        
        return result
    
    def scan_all_gateways(self, hosts: List[str] = None) -> List[Dict]:
        """
        Scan multiple gateway hosts for WebSocket anomalies
        
        Args:
            hosts: List of host IPs to scan (default: localhost)
        
        Returns:
            List of detection results
        """
        if hosts is None:
            hosts = ["127.0.0.1"]
        
        results = []
        
        for host in hosts:
            for port in GATEWAY_PORTS:
                result = self.scan_gateway(host, port)
                results.append(result)
                
                if result["anomaly_detected"]:
                    logger.warning(f"🚨 WebSocket anomaly detected: {host}:{port} - {result['connection_count']} connections")
        
        return results
    
    def get_trend_analysis(self, source_ip: str = None, hours: int = 24) -> Dict:
        """
        Analyze WebSocket connection trends
        
        Returns trend statistics for the specified time period
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if source_ip:
            cursor.execute('''
            SELECT 
                gateway_port,
                COUNT(*) as total_connections,
                MAX(connection_count) as peak_connections,
                AVG(connection_count) as avg_connections,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM websocket_connections
            WHERE source_ip = ? AND timestamp > ?
            GROUP BY gateway_port
            ''', (source_ip, cutoff_time.isoformat()))
        else:
            cursor.execute('''
            SELECT 
                source_ip,
                gateway_port,
                COUNT(*) as total_connections,
                MAX(connection_count) as peak_connections,
                AVG(connection_count) as avg_connections,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM websocket_connections
            WHERE timestamp > ?
            GROUP BY source_ip, gateway_port
            ''', (cutoff_time.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        trends = []
        for row in rows:
            row_dict = dict(row)
            trend = {
                "source_ip": row_dict.get('source_ip', 'N/A'),
                "gateway_port": row_dict['gateway_port'],
                "total_connections": row_dict['total_connections'],
                "peak_connections": row_dict['peak_connections'],
                "avg_connections": row_dict['avg_connections'] or 0,
                "first_seen": row_dict['first_seen'],
                "last_seen": row_dict['last_seen']
            }
            trends.append(trend)
        
        return {
            "time_period_hours": hours,
            "total_records": len(trends),
            "trends": trends
        }


def main():
    """Test WebSocket monitor"""
    print("\n👁️ CogniWatch WebSocket Anomaly Detector\n")
    print("Testing WebSocket connection monitoring...\n")
    
    monitor = WebSocketMonitor()
    
    # Simulate some connection events for testing
    print("📝 Simulating connection events...")
    for _ in range(55):  # Simulate 55 connections (above threshold)
        monitor.simulate_connection_event("127.0.0.1", 18789)
    
    # Scan gateways
    print("\n🔍 Scanning gateways for WebSocket anomalies...")
    results = monitor.scan_all_gateways(["127.0.0.1"])
    
    # Report findings
    anomalies = [r for r in results if r["anomaly_detected"]]
    
    if anomalies:
        print(f"\n🚨 DETECTED {len(anomalies)} WEBSOCKET ANOMALIES:\n")
        
        for result in anomalies:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ 📊 Connections: {result['connection_count']}/min")
            print(f"│ 🎯 Confidence: {result['confidence']:.0%}")
            print(f"│ ⚠️  Severity: {result['severity']}")
            print(f"│ 💡 Recommendation: {result['recommendation']}")
            print(f"└─────────────────────────────────────────────\n")
    else:
        print("\n✅ No WebSocket anomalies detected")
    
    # Show trend analysis
    print("\n📈 Trend Analysis (last 24 hours):")
    trends_data = monitor.get_trend_analysis(hours=24)
    print(f"   Total records: {trends_data['total_records']}")
    
    for trend in trends_data['trends'][:5]:  # Show first 5
        src = trend.get('source_ip', 'N/A')
        print(f"   - {src}:{trend['gateway_port']} - Peak: {trend['peak_connections']} connections")


if __name__ == "__main__":
    main()
