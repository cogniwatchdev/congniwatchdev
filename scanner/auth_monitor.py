#!/usr/bin/env python3
"""
CogniWatch - Authentication Brute-Force Detection Module
Detects ClawJacked attack pattern: Repeated failed password attempts

Detection Logic:
- Parse gateway authentication logs (if accessible) OR
- Monitor for failed auth patterns via gateway /api/sessions endpoint
- Track failed attempts per source IP
- Alert threshold: >10 failures in 60 seconds (even from localhost)
- Support auto-block optional integration (ufw rules)
"""

import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway ports to monitor
GATEWAY_PORTS = [18789, 18790, 18794, 18795]

# Detection thresholds
FAILED_AUTH_THRESHOLD = 10  # failures per minute
TIME_WINDOW_SECONDS = 60

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'


class AuthMonitor:
    """Monitor authentication attempts for brute-force detection"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.failed_attempts: Dict[str, List[datetime]] = {}  # IP -> timestamps
        
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_table(self):
        """Ensure auth_attempts table exists"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gateway_port INTEGER NOT NULL,
            source_ip TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create index for fast IP-based queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_auth_attempts_ip_time 
        ON auth_attempts(source_ip, timestamp DESC)
        ''')
        
        # Create index for failure tracking
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_auth_attempts_success 
        ON auth_attempts(success, timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def record_auth_attempt(self, source_ip: str, gateway_port: int, success: bool):
        """Record an authentication attempt"""
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO auth_attempts (gateway_port, source_ip, success)
        VALUES (?, ?, ?)
        ''', (gateway_port, source_ip, success))
        
        conn.commit()
        conn.close()
        
        # Update in-memory tracking for failed attempts
        if not success:
            key = f"{source_ip}:{gateway_port}"
            if key not in self.failed_attempts:
                self.failed_attempts[key] = []
            self.failed_attempts[key].append(datetime.now())
        
        status = "✅ success" if success else "❌ failed"
        logger.debug(f"Recorded auth attempt from {source_ip} to port {gateway_port}: {status}")
    
    def detect_brute_force(self, source_ip: str, gateway_port: int) -> Tuple[bool, int, float]:
        """
        Check if failed auth attempts from IP exceed threshold
        
        Returns:
            (is_brute_force, failure_count, confidence_score)
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get failed attempt count in time window
        cutoff_time = datetime.now() - timedelta(seconds=TIME_WINDOW_SECONDS)
        
        cursor.execute('''
        SELECT COUNT(*) as count FROM auth_attempts
        WHERE source_ip = ? AND gateway_port = ? AND success = FALSE AND timestamp > ?
        ''', (source_ip, gateway_port, cutoff_time.isoformat()))
        
        row = cursor.fetchone()
        failure_count = row['count'] if row else 0
        
        conn.close()
        
        # Calculate confidence score based on severity
        if failure_count >= FAILED_AUTH_THRESHOLD:
            # Critical: brute-force detected
            confidence = min(0.98, 0.95 + (failure_count - FAILED_AUTH_THRESHOLD) / 100)
            return True, failure_count, confidence
        elif failure_count > 5:
            # Warning: elevated but not critical
            confidence = 0.6 + (failure_count - 5) / 20
            return False, failure_count, confidence
        
        return False, failure_count, 0.0
    
    def probe_auth_endpoint(self, host: str, port: int) -> Dict:
        """
        Probe gateway auth endpoint to check for failed auth patterns
        Note: This is a passive check - doesn't attempt to brute-force
        """
        result = {
            "endpoint_accessible": False,
            "auth_required": False,
            "error_type": None,
            "response_time_ms": 0
        }
        
        try:
            start_time = datetime.now()
            
            # Try to access sessions endpoint (should require auth)
            url = f"http://{host}:{port}/api/sessions"
            response = requests.get(url, timeout=5)
            
            result["response_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            result["endpoint_accessible"] = True
            
            # Check response status
            if response.status_code == 401 or response.status_code == 403:
                result["auth_required"] = True
                logger.debug(f"Auth endpoint at {host}:{port} requires authentication")
            elif response.status_code == 200:
                logger.warning(f"⚠️  Auth endpoint at {host}:{port} is publicly accessible!")
                result["auth_required"] = False
            else:
                result["error_type"] = f"HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            result["error_type"] = "Connection refused"
        except requests.exceptions.Timeout:
            result["error_type"] = "Timeout"
        except Exception as e:
            result["error_type"] = str(e)
        
        return result
    
    def scan_gateway(self, host: str, port: int) -> Dict:
        """
        Scan a gateway port for auth brute-force patterns
        
        Returns detection result dict
        """
        result = {
            "detection_type": "auth_brute_force",
            "host": host,
            "port": port,
            "endpoint_check": {},
            "brute_force_detected": False,
            "failure_count": 0,
            "confidence": 0.0,
            "severity": "NONE",
            "evidence": [],
            "recommendation": "",
            "auto_block_available": False
        }
        
        # Probe auth endpoint
        endpoint_info = self.probe_auth_endpoint(host, port)
        result["endpoint_check"] = endpoint_info
        
        # Check for brute-force pattern in database
        is_brute_force, failure_count, confidence = self.detect_brute_force(host, port)
        
        result["brute_force_detected"] = is_brute_force
        result["failure_count"] = failure_count
        result["confidence"] = confidence
        
        if is_brute_force:
            result["severity"] = "CRITICAL"
            result["evidence"].append(f"Detected {failure_count} failed auth attempts in {TIME_WINDOW_SECONDS}s from {host}")
            result["recommendation"] = f"IMMEDIATE ACTION: Block {host} using firewall. Enable rate limiting."
            
            # Check if auto-block is available
            result["auto_block_available"] = self._check_ufw_available()
        elif failure_count > 5:
            result["severity"] = "WARNING"
            result["evidence"].append(f"Elevated failed auth attempts: {failure_count} in {TIME_WINDOW_SECONDS}s")
            result["recommendation"] = "Monitor closely. Consider implementing stricter rate limits."
        else:
            result["severity"] = "LOW"
            result["evidence"].append(f"Normal auth activity: {failure_count} failures")
        
        # Add endpoint security info
        if endpoint_info.get("auth_required"):
            result["evidence"].append("Auth endpoint properly protected")
        elif endpoint_info.get("endpoint_accessible"):
            result["evidence"].append("⚠️ WARNING: Auth endpoint publicly accessible")
            result["severity"] = "HIGH" if result["severity"] == "NONE" else result["severity"]
        
        return result
    
    def _check_ufw_available(self) -> bool:
        """Check if UFW firewall is available for auto-blocking"""
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def auto_block_ip(self, source_ip: str, reason: str = "Brute-force detected") -> bool:
        """
        Attempt to automatically block an IP using UFW
        
        Returns True if successful, False otherwise
        """
        if not self._check_ufw_available():
            logger.warning(f"UFW not available for auto-blocking {source_ip}")
            return False
        
        try:
            # Add UFW deny rule
            subprocess.run(
                ['ufw', 'deny', 'from', source_ip, 'comment', reason],
                capture_output=True,
                timeout=10
            )
            
            logger.info(f"✅ Auto-blocked {source_ip} via UFW: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to auto-block {source_ip}: {e}")
            return False
    
    def scan_all_gateways(self, hosts: List[str] = None) -> List[Dict]:
        """
        Scan multiple gateway hosts for auth brute-force patterns
        
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
                
                if result["brute_force_detected"]:
                    logger.critical(f"🚨 BRUTE-FORCE detected: {host}:{port} - {result['failure_count']} failures")
        
        return results
    
    def get_failure_report(self, hours: int = 24) -> Dict:
        """
        Get report of authentication failures
        
        Returns statistics and top offending IPs
        """
        self._init_table()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get failure statistics by IP
        cursor.execute('''
        SELECT 
            source_ip,
            gateway_port,
            COUNT(*) as failure_count,
            MIN(timestamp) as first_attempt,
            MAX(timestamp) as last_attempt
        FROM auth_attempts
        WHERE success = FALSE AND timestamp > ?
        GROUP BY source_ip, gateway_port
        ORDER BY failure_count DESC
        LIMIT 20
        ''', (cutoff_time.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        top_offenders = []
        for row in rows:
            offender = {
                "source_ip": row['source_ip'],
                "gateway_port": row['gateway_port'],
                "failure_count": row['failure_count'],
                "first_attempt": row['first_attempt'],
                "last_attempt": row['last_attempt']
            }
            top_offenders.append(offender)
        
        total_failures = sum(o['failure_count'] for o in top_offenders)
        
        return {
            "time_period_hours": hours,
            "total_failures": total_failures,
            "unique_sources": len(top_offenders),
            "top_offenders": top_offenders
        }


def main():
    """Test Auth monitor"""
    print("\n👁️ CogniWatch Authentication Brute-Force Detector\n")
    print("Testing authentication monitoring...\n")
    
    monitor = AuthMonitor()
    
    # Simulate some failed auth attempts for testing
    print("📝 Simulating failed authentication attempts...")
    for _ in range(15):  # Simulate 15 failed attempts (above threshold)
        monitor.record_auth_attempt("127.0.0.1", 18789, success=False)
    
    # Add some successful attempts for comparison
    for _ in range(3):
        monitor.record_auth_attempt("127.0.0.1", 18789, success=True)
    
    # Scan gateways
    print("\n🔍 Scanning gateways for auth brute-force patterns...")
    results = monitor.scan_all_gateways(["127.0.0.1"])
    
    # Report findings
    brute_force = [r for r in results if r["brute_force_detected"]]
    warnings = [r for r in results if r["severity"] in ["WARNING", "HIGH"] and not r["brute_force_detected"]]
    
    if brute_force:
        print(f"\n🚨 DETECTED {len(brute_force)} BRUTE-FORCE ATTACKS:\n")
        
        for result in brute_force:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ ❌ Failed attempts: {result['failure_count']}")
            print(f"│ 🎯 Confidence: {result['confidence']:.0%}")
            print(f"│ 🔴 Severity: {result['severity']}")
            print(f"│ 🛡️  Auto-block available: {'✅ Yes' if result['auto_block_available'] else '❌ No'}")
            print(f"│ 💡 Recommendation: {result['recommendation']}")
            print(f"└─────────────────────────────────────────────\n")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(s):\n")
        
        for result in warnings:
            print(f"┌─────────────────────────────────────────────")
            print(f"│ 🚪 Gateway: {result['host']}:{result['port']}")
            print(f"│ {result['evidence'][0] if result['evidence'] else 'No details'}")
            print(f"└─────────────────────────────────────────────\n")
    
    if not brute_force and not warnings:
        print("\n✅ No authentication anomalies detected")
    
    # Show failure report
    print("\n📈 Failure Report (last 24 hours):")
    report = monitor.get_failure_report(hours=24)
    print(f"   Total failures: {report['total_failures']}")
    print(f"   Unique sources: {report['unique_sources']}")
    
    if report['top_offenders']:
        print("\n   Top offending IPs:")
        for offender in report['top_offenders'][:5]:
            print(f"   - {offender['source_ip']}: {offender['failure_count']} failures")


if __name__ == "__main__":
    main()
