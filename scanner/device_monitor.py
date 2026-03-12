#!/usr/bin/env python3
"""
CogniWatch - Device Registration Auditing Module
Detects ClawJacked attack pattern: Auto-approved device pairings

Detection Logic:
- Poll gateway /api/sessions or device registration endpoint
- Track new device registrations with timestamps
- Flag auto-approved registrations (should require manual review)
- Flag localhost-sourced registrations as HIGH RISK
- Alert on: new device + localhost source + auto-approve
"""

import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway ports to monitor
GATEWAY_PORTS = [18789, 18790, 18794, 18795]

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'


class DeviceMonitor:
    """Monitor device registrations for security auditing"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.known_devices: Dict[str, Dict] = {}  # device_id -> device info
        
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_table(self):
        """Ensure device_registrations table exists"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
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
        
        # Create index for fast device lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_registrations_id 
        ON device_registrations(device_id, timestamp DESC)
        ''')
        
        # Create index for auto-approve tracking
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_registrations_approved 
        ON device_registrations(auto_approved, timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_device_id(self, device_info: Dict) -> str:
        """Generate unique device ID from device information"""
        # Use device name + user agent + other identifiers
        identifier = f"{device_info.get('name', 'unknown')}:{device_info.get('user_agent', 'unknown')}:{device_info.get('timestamp', 'now')}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def record_device_registration(self, device_name: str, device_id: str, 
                                   gateway_port: int, source_ip: str, 
                                   auto_approved: bool):
        """Record a device registration event"""
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO device_registrations (device_name, device_id, gateway_port, source_ip, auto_approved)
        VALUES (?, ?, ?, ?, ?)
        ''', (device_name, device_id, gateway_port, source_ip, auto_approved))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded device registration: {device_name} ({device_id}) on port {gateway_port} - auto_approved={auto_approved}")
    
    def query_gateway_sessions(self, host: str, port: int) -> Optional[List[Dict]]:
        """
        Query gateway /api/sessions endpoint for device info
        
        Returns session/device data if available
        """
        try:
            url = f"http://{host}:{port}/api/sessions"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    # OpenClaw format: {"sessions": [...]} or {"sessionKey": ...}
                    sessions = data.get('sessions', [])
                    if sessions:
                        return sessions
                    # If single session object
                    if 'sessionKey' in data:
                        return [data]
                elif isinstance(data, list):
                    return data
                    
        except Exception as e:
            logger.debug(f"Failed to query sessions from {host}:{port}: {e}")
        
        return None
    
    def detect_suspicious_registration(self, source_ip: str, auto_approved: bool, 
                                       is_localhost: bool) -> Tuple[bool, float, str]:
        """
        Evaluate if a device registration is suspicious
        
        Returns:
            (is_suspicious, confidence_score, reason)
        """
        risk_score = 0
        reasons = []
        
        # Check 1: Localhost source (HIGH RISK)
        if is_localhost:
            risk_score += 50
            reasons.append("localhost-sourced registration")
        
        # Check 2: Auto-approved (should require manual review)
        if auto_approved:
            risk_score += 40
            reasons.append("auto-approved without manual review")
        
        # Check 3: Combination is CRITICAL
        if is_localhost and auto_approved:
            risk_score += 20  # Bonus risk for combination
            reasons.append("CRITICAL: localhost + auto-approve pattern")
        
        # Determine if suspicious
        is_suspicious = risk_score >= 60
        
        # Calculate confidence
        if risk_score >= 90:
            confidence = 0.95
        elif risk_score >= 70:
            confidence = 0.85
        elif risk_score >= 60:
            confidence = 0.70
        else:
            confidence = 0.3 + (risk_score / 200)
        
        reason = "; ".join(reasons) if reasons else "Low risk registration"
        
        return is_suspicious, confidence, reason
    
    def scan_gateway(self, host: str, port: int) -> Dict:
        """
        Scan a gateway port for suspicious device registrations
        
        Returns detection result dict
        """
        result = {
            "detection_type": "device_registration_audit",
            "host": host,
            "port": port,
            "sessions_accessible": False,
            "total_devices": 0,
            "suspicious_registrations": [],
            "auto_approved_count": 0,
            "localhost_registrations": 0,
            "severity": "NONE",
            "confidence": 0.0,
            "evidence": [],
            "recommendation": ""
        }
        
        # Query gateway sessions
        sessions = self.query_gateway_sessions(host, port)
        
        if sessions is None:
            result["evidence"].append(f"Could not access /api/sessions on {host}:{port}")
            result["severity"] = "INFO"
            result["recommendation"] = "Ensure gateway is running and accessible"
            return result
        
        result["sessions_accessible"] = True
        result["total_devices"] = len(sessions) if sessions else 0
        result["evidence"].append(f"Retrieved {result['total_devices']} sessions from gateway")
        
        # Analyze each session/device
        is_localhost = host in ["127.0.0.1", "localhost", "::1"]
        
        for session in (sessions or []):
            # Extract device info (adapt to different formats)
            device_name = session.get('device_name', session.get('name', 'Unknown Device'))
            device_id = session.get('device_id', session.get('sessionKey', 'unknown'))
            
            # Check if auto-approved
            auto_approved = session.get('auto_approved', True)  # Default to True if unknown
            
            # Record registration
            self.record_device_registration(
                device_name=device_name,
                device_id=device_id,
                gateway_port=port,
                source_ip=host,
                auto_approved=auto_approved
            )
            
            # Count risk factors
            if auto_approved:
                result["auto_approved_count"] += 1
            if is_localhost:
                result["localhost_registrations"] += 1
            
            # Check if suspicious
            is_suspicious, confidence, reason = self.detect_suspicious_registration(
                source_ip=host,
                auto_approved=auto_approved,
                is_localhost=is_localhost
            )
            
            if is_suspicious:
                result["suspicious_registrations"].append({
                    "device_name": device_name,
                    "device_id": device_id,
                    "auto_approved": auto_approved,
                    "source_ip": host,
                    "confidence": confidence,
                    "reason": reason
                })
        
        # Determine overall severity
        if result["suspicious_registrations"]:
            num_suspicious = len(result["suspicious_registrations"])
            
            if is_localhost and result["auto_approved_count"] > 0:
                result["severity"] = "CRITICAL"
                result["confidence"] = 0.95
                result["evidence"].append(f"Detected {num_suspicious} suspicious device registrations")
                result["evidence"].append("PATTERN: localhost + auto-approve = ClawJacked attack vector")
                result["recommendation"] = "IMMEDIATE: Review all auto-approved devices. Disable auto-approval. Manual review required for all new devices."
            else:
                result["severity"] = "HIGH"
                result["confidence"] = 0.85
                result["evidence"].append(f"Found {num_suspicious} potentially suspicious registrations")
                result["recommendation"] = "Review device registrations. Implement manual approval workflow."
        elif result["auto_approved_count"] > 0:
            result["severity"] = "WARNING"
            result["confidence"] = 0.6
            result["evidence"].append(f"{result['auto_approved_count']} auto-approved devices (review recommended)")
            result["recommendation"] = "Consider implementing manual approval for new device registrations"
        else:
            result["severity"] = "LOW"
            result["evidence"].append("Device registrations appear normal")
            result["recommendation"] = "Continue monitoring"
        
        return result
    
    def scan_all_gateways(self, hosts: List[str] = None) -> List[Dict]:
        """
        Scan multiple gateway hosts for suspicious device registrations
        
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
                
                if result["suspicious_registrations"]:
                    logger.warning(f"🚨 Suspicious device registrations: {host}:{port} - {len(result['suspicious_registrations'])} flagged")
        
        return results
    
    def get_registration_report(self, hours: int = 24) -> Dict:
        """
        Get report of device registrations
        
        Returns statistics and suspicious registrations
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get registration statistics
        cursor.execute('''
        SELECT 
            gateway_port,
            COUNT(*) as total_registrations,
            SUM(CASE WHEN auto_approved = TRUE THEN 1 ELSE 0 END) as auto_approved_count,
            SUM(CASE WHEN source_ip IN ('127.0.0.1', 'localhost') THEN 1 ELSE 0 END) as localhost_count,
            COUNT(DISTINCT device_id) as unique_devices
        FROM device_registrations
        WHERE timestamp > ?
        GROUP BY gateway_port
        ''', (cutoff_time.isoformat(),))
        
        port_stats = []
        for row in cursor.fetchall():
            stat = {
                "gateway_port": row['gateway_port'],
                "total_registrations": row['total_registrations'],
                "auto_approved_count": row['auto_approved_count'] or 0,
                "localhost_count": row['localhost_count'] or 0,
                "unique_devices": row['unique_devices'] or 0
            }
            port_stats.append(stat)
        
        # Get suspicious registrations (auto-approved from localhost)
        cursor.execute('''
        SELECT 
            device_name,
            device_id,
            gateway_port,
            source_ip,
            auto_approved,
            timestamp
        FROM device_registrations
        WHERE auto_approved = TRUE 
          AND source_ip IN ('127.0.0.1', 'localhost')
          AND timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 20
        ''', (cutoff_time.isoformat(),))
        
        suspicious = []
        for row in cursor.fetchall():
            suspicious.append({
                "device_name": row['device_name'],
                "device_id": row['device_id'],
                "gateway_port": row['gateway_port'],
                "source_ip": row['source_ip'],
                "auto_approved": row['auto_approved'],
                "timestamp": row['timestamp']
            })
        
        conn.close()
        
        total_registrations = sum(s['total_registrations'] for s in port_stats)
        total_auto_approved = sum(s['auto_approved_count'] for s in port_stats)
        
        return {
            "time_period_hours": hours,
            "total_registrations": total_registrations,
            "total_auto_approved": total_auto_approved,
            "unique_gateways": len(port_stats),
            "port_statistics": port_stats,
            "suspicious_registrations": suspicious,
            "risk_level": "CRITICAL" if suspicious else "LOW"
        }


def main():
    """Test Device monitor"""
    print("\n👁️ CogniWatch Device Registration Auditor\n")
    print("Testing device registration auditing...\n")
    
    monitor = DeviceMonitor()
    
    # Simulate some device registrations for testing
    print("📝 Simulating device registrations...")
    
    # Normal registration
    monitor.record_device_registration(
        device_name="Chrome Browser",
        device_id="device_abc123",
        gateway_port=18789,
        source_ip="192.168.1.50",
        auto_approved=False
    )
    
    # Suspicious registrations (localhost + auto-approve)
    for i in range(3):
        monitor.record_device_registration(
            device_name=f"Attacker Device {i}",
            device_id=f"attacker_{hashlib.sha256(str(i).encode()).hexdigest()[:8]}",
            gateway_port=18789,
            source_ip="127.0.0.1",
            auto_approved=True
        )
    
    # Scan gateways
    print("\n🔍 Scanning gateways for suspicious device registrations...")
    results = monitor.scan_all_gateways(["127.0.0.1"])
    
    # Report findings
    critical = [r for r in results if r["severity"] == "CRITICAL"]
    high = [r for r in results if r["severity"] == "HIGH"]
    warnings = [r for r in results if r["severity"] == "WARNING"]
    
    if critical:
        print(f"\n🚨 CRITICAL: {len(critical)} gateway(s) with suspicious device registrations:\n")
        
        for result in critical:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ 📱 Total devices: {result['total_devices']}")
            print(f"│ ⚠️  Suspicious: {len(result['suspicious_registrations'])}")
            print(f"│ ✅ Auto-approved: {result['auto_approved_count']}")
            print(f"│ 🎯 Confidence: {result['confidence']:.0%}")
            print(f"│ 🔴 Severity: {result['severity']}")
            
            if result['suspicious_registrations']:
                print(f"│")
                print(f"│ Suspicious devices:")
                for dev in result['suspicious_registrations'][:3]:
                    print(f"│   - {dev['device_name']} ({dev['reason']})")
            
            print(f"│")
            print(f"│ 💡 Recommendation: {result['recommendation']}")
            print(f"└─────────────────────────────────────────────\n")
    
    if high:
        print(f"\n⚠️  HIGH RISK: {len(high)} gateway(s):\n")
        for result in high:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ {result['evidence'][0] if result['evidence'] else 'No details'}")
            print(f"└─────────────────────────────────────────────\n")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(s):\n")
        for result in warnings:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ {result['evidence'][0] if result['evidence'] else 'No details'}")
            print(f"└─────────────────────────────────────────────\n")
    
    if not critical and not high and not warnings:
        print("\n✅ No suspicious device registrations detected")
    
    # Show registration report
    print("\n📈 Registration Report (last 24 hours):")
    report = monitor.get_registration_report(hours=24)
    print(f"   Total registrations: {report['total_registrations']}")
    print(f"   Auto-approved: {report['total_auto_approved']}")
    print(f"   Risk level: {report['risk_level']}")
    
    if report['suspicious_registrations']:
        print("\n   Recent suspicious registrations:")
        for reg in report['suspicious_registrations'][:5]:
            print(f"   - {reg['device_name']} on port {reg['gateway_port']} (auto-approved: {reg['auto_approved']})")


if __name__ == "__main__":
    main()
