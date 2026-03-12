#!/usr/bin/env python3
"""
CogniWatch - Analysis API Endpoints
Provides heatmap, trends, and analysis endpoints for detected agents

Endpoints:
- GET /api/analysis/heatmap - Framework distribution heatmap
- GET /api/analysis/trends - Detection trends over time
- GET /api/analysis/summary - Summary statistics
- GET /api/analysis/frameworks - List of detected frameworks
- GET /api/analysis/telemetry - Telemetry data
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class AnalysisAPI:
    """Analysis API endpoints for CogniWatch data"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
    
    def get_heatmap(self, timeframe: str = '24h') -> Dict[str, Any]:
        """
        Get framework distribution heatmap.
        
        Shows which frameworks are detected where, with confidence scores.
        
        Args:
            timeframe: Time window ('1h', '24h', '7d', '30d')
            
        Returns:
            Heatmap data with framework distribution by host/port
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parse timeframe
        time_filter = self._parse_timeframe(timeframe)
        
        # Query detection results
        query = """
        SELECT 
            host, 
            port, 
            top_framework, 
            confidence, 
            confidence_level,
            detection_quality,
            timestamp
        FROM detection_results
        WHERE timestamp >= ?
        ORDER BY confidence DESC
        """
        
        cursor.execute(query, (time_filter,))
        rows = cursor.fetchall()
        conn.close()
        
        # Build heatmap structure
        heatmap = {
            'timeframe': timeframe,
            'generated_at': datetime.utcnow().isoformat(),
            'total_detections': len(rows),
            'hosts': {},
            'frameworks': defaultdict(int),
            'confidence_distribution': {
                'very_high': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'very_low': 0
            }
        }
        
        for row in rows:
            host = row['host']
            port = row['port']
            framework = row['top_framework'] or 'unknown'
            confidence = row['confidence'] or 0.0
            level = row['confidence_level'] or 'unknown'
            
            # Count frameworks
            heatmap['frameworks'][framework] += 1
            
            # Count confidence levels
            if level in heatmap['confidence_distribution']:
                heatmap['confidence_distribution'][level] += 1
            
            # Add to host map
            if host not in heatmap['hosts']:
                heatmap['hosts'][host] = {
                    'ports': {},
                    'frameworks': set()
                }
            
            heatmap['hosts'][host]['ports'][str(port)] = {
                'framework': framework,
                'confidence': confidence,
                'quality': row['detection_quality'],
                'last_seen': row['timestamp']
            }
            heatmap['hosts'][host]['frameworks'].add(framework)
        
        # Convert sets to lists for JSON serialization
        for host in heatmap['hosts']:
            heatmap['hosts'][host]['frameworks'] = list(heatmap['hosts'][host]['frameworks'])
        
        # Convert defaultdict to dict
        heatmap['frameworks'] = dict(heatmap['frameworks'])
        
        return heatmap
    
    def get_trends(self, timeframe: str = '7d', 
                   metric: str = 'detections') -> Dict[str, Any]:
        """
        Get detection trends over time.
        
        Args:
            timeframe: Time window ('1h', '24h', '7d', '30d')
            metric: Metric to trend ('detections', 'frameworks', 'confidence')
            
        Returns:
            Trend data with time-series points
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        time_filter = self._parse_timeframe(timeframe)
        
        # Determine grouping interval based on timeframe
        interval = self._get_interval(timeframe)
        
        if metric == 'detections':
            query = f"""
            SELECT 
                strftime('{interval}', timestamp) as time_bucket,
                COUNT(*) as detection_count,
                COUNT(DISTINCT host) as unique_hosts,
                COUNT(DISTINCT top_framework) as unique_frameworks
            FROM detection_results
            WHERE timestamp >= ?
            GROUP BY time_bucket
            ORDER BY time_bucket
            """
            
            cursor.execute(query, (time_filter,))
            rows = cursor.fetchall()
            
            trends = {
                'metric': 'detections',
                'timeframe': timeframe,
                'interval': interval,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points': [
                    {
                        'timestamp': row['time_bucket'],
                        'detection_count': row['detection_count'],
                        'unique_hosts': row['unique_hosts'],
                        'unique_frameworks': row['unique_frameworks']
                    }
                    for row in rows
                ]
            }
        
        elif metric == 'frameworks':
            query = f"""
            SELECT 
                strftime('{interval}', timestamp) as time_bucket,
                top_framework,
                COUNT(*) as count
            FROM detection_results
            WHERE timestamp >= ? AND top_framework IS NOT NULL
            GROUP BY time_bucket, top_framework
            ORDER BY time_bucket, count DESC
            """
            
            cursor.execute(query, (time_filter,))
            rows = cursor.fetchall()
            
            # Group by time bucket
            by_time = defaultdict(list)
            for row in rows:
                by_time[row['time_bucket']].append({
                    'framework': row['top_framework'],
                    'count': row['count']
                })
            
            trends = {
                'metric': 'frameworks',
                'timeframe': timeframe,
                'interval': interval,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points': [
                    {
                        'timestamp': bucket,
                        'frameworks': frameworks
                    }
                    for bucket, frameworks in by_time.items()
                ]
            }
        
        elif metric == 'confidence':
            query = f"""
            SELECT 
                strftime('{interval}', timestamp) as time_bucket,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as sample_count
            FROM detection_results
            WHERE timestamp >= ? AND confidence IS NOT NULL
            GROUP BY time_bucket
            ORDER BY time_bucket
            """
            
            cursor.execute(query, (time_filter,))
            rows = cursor.fetchall()
            
            trends = {
                'metric': 'confidence',
                'timeframe': timeframe,
                'interval': interval,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points': [
                    {
                        'timestamp': row['time_bucket'],
                        'avg_confidence': row['avg_confidence'],
                        'min_confidence': row['min_confidence'],
                        'max_confidence': row['max_confidence'],
                        'sample_count': row['sample_count']
                    }
                    for row in rows
                ]
            }
        
        else:
            trends = {'error': f'Unknown metric: {metric}'}
        
        conn.close()
        return trends
    
    def get_summary(self, timeframe: str = '24h') -> Dict[str, Any]:
        """
        Get summary statistics.
        
        Args:
            timeframe: Time window
            
        Returns:
            Summary statistics
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        time_filter = self._parse_timeframe(timeframe)
        
        # Overall statistics
        cursor.execute("""
        SELECT 
            COUNT(*) as total_detections,
            COUNT(DISTINCT host) as unique_hosts,
            COUNT(DISTINCT top_framework) as unique_frameworks,
            AVG(confidence) as avg_confidence,
            MAX(confidence) as max_confidence,
            AVG(detection_time_ms) as avg_detection_time
        FROM detection_results
        WHERE timestamp >= ?
        """, (time_filter,))
        
        stats = cursor.fetchone()
        
        # Framework breakdown
        cursor.execute("""
        SELECT 
            top_framework,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM detection_results
        WHERE timestamp >= ? AND top_framework IS NOT NULL
        GROUP BY top_framework
        ORDER BY count DESC
        """, (time_filter,))
        
        frameworks = [
            {
                'framework': row['top_framework'],
                'count': row['count'],
                'avg_confidence': row['avg_confidence']
            }
            for row in cursor.fetchall()
        ]
        
        # Detection quality breakdown
        cursor.execute("""
        SELECT 
            detection_quality,
            COUNT(*) as count
        FROM detection_results
        WHERE timestamp >= ?
        GROUP BY detection_quality
        """, (time_filter,))
        
        quality = [
            {
                'quality': row['detection_quality'],
                'count': row['count']
            }
            for row in cursor.fetchall()
        ]
        
        # Latest detections
        cursor.execute("""
        SELECT 
            host,
            port,
            top_framework,
            confidence,
            timestamp
        FROM detection_results
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 10
        """, (time_filter,))
        
        latest = [
            {
                'host': row['host'],
                'port': row['port'],
                'framework': row['top_framework'],
                'confidence': row['confidence'],
                'timestamp': row['timestamp']
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'timeframe': timeframe,
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': {
                'total_detections': stats['total_detections'] or 0,
                'unique_hosts': stats['unique_hosts'] or 0,
                'unique_frameworks': stats['unique_frameworks'] or 0,
                'avg_confidence': stats['avg_confidence'] or 0.0,
                'max_confidence': stats['max_confidence'] or 0.0,
                'avg_detection_time_ms': stats['avg_detection_time'] or 0.0
            },
            'frameworks': frameworks,
            'detection_quality': quality,
            'latest_detections': latest
        }
    
    def get_telemetry_summary(self, host: str, port: int) -> Dict[str, Any]:
        """
        Get telemetry summary for a specific host/port.
        
        Args:
            host: Target host
            port: Target port
            
        Returns:
            Telemetry summary
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest telemetry
        cursor.execute("""
        SELECT * FROM telemetry
        WHERE host = ? AND port = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """, (host, port))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {'error': 'No telemetry data found'}
        
        # Get telemetry history for trends
        cursor.execute("""
        SELECT 
            timestamp,
            avg_response_time_ms,
            success_rate,
            active_sessions,
            health_status
        FROM telemetry
        WHERE host = ? AND port = ?
        ORDER BY timestamp DESC
        LIMIT 100
        """, (host, port))
        
        history = [
            {
                'timestamp': r['timestamp'],
                'avg_response_time_ms': r['avg_response_time_ms'],
                'success_rate': r['success_rate'],
                'active_sessions': r['active_sessions'],
                'health_status': r['health_status']
            }
            for r in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'host': host,
            'port': port,
            'latest': dict(row),
            'history': history
        }
    
    def _parse_timeframe(self, timeframe: str) -> datetime:
        """Parse timeframe string to datetime"""
        now = datetime.utcnow()
        
        if timeframe == '1h':
            return (now - timedelta(hours=1)).isoformat()
        elif timeframe == '24h':
            return (now - timedelta(days=1)).isoformat()
        elif timeframe == '7d':
            return (now - timedelta(weeks=1)).isoformat()
        elif timeframe == '30d':
            return (now - timedelta(days=30)).isoformat()
        else:
            return (now - timedelta(days=1)).isoformat()
    
    def _get_interval(self, timeframe: str) -> str:
        """Get SQL strftime interval based on timeframe"""
        if timeframe == '1h':
            return '%Y-%m-%d %H:%M'  # Group by minute
        elif timeframe == '24h':
            return '%Y-%m-%d %H:00'  # Group by hour
        elif timeframe == '7d':
            return '%Y-%m-%d'  # Group by day
        elif timeframe == '30d':
            return '%Y-%m-%d'  # Group by day
        else:
            return '%Y-%m-%d %H:00'


def main():
    """Test analysis API"""
    print("\n📊 CogniWatch Analysis API Test\n")
    
    api = AnalysisAPI()
    
    # Test heatmap
    print("Testing /api/analysis/heatmap...")
    heatmap = api.get_heatmap('24h')
    print(f"  Total detections: {heatmap['total_detections']}")
    print(f"  Frameworks: {list(heatmap['frameworks'].keys())}")
    print(f"  Confidence distribution: {heatmap['confidence_distribution']}")
    
    # Test trends
    print("\nTesting /api/analysis/trends...")
    trends = api.get_trends('7d', 'detections')
    print(f"  Metric: {trends['metric']}")
    print(f"  Data points: {len(trends['data_points'])}")
    
    # Test summary
    print("\nTesting /api/analysis/summary...")
    summary = api.get_summary('24h')
    print(f"  Total detections: {summary['statistics']['total_detections']}")
    print(f"  Average confidence: {summary['statistics']['avg_confidence']:.2f}")
    print(f"  Frameworks detected: {len(summary['frameworks'])}")
    
    print("\n✅ Analysis API test complete\n")


if __name__ == "__main__":
    main()
