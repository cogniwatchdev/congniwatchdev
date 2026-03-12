"""
CogniWatch Telemetry API
VULCAN - AI Agent Telemetry Collection and Analysis

Provides endpoints for telemetry heatmap, trends, security distribution,
framework comparison, and anomaly detection.
"""

from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from database.schema import get_db_connection

logger = logging.getLogger(__name__)

# Create blueprint
telemetry_api = Blueprint('telemetry_api', __name__, url_prefix='/api/telemetry')


@telemetry_api.route('/heatmap')
def telemetry_heatmap():
    """
    GET /api/telemetry/heatmap
    
    Global distribution of agent capabilities.
    Shows frameworks, models, capabilities, and security posture across all agents.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Framework distribution
        cursor.execute('''
            SELECT ac.framework, COUNT(*) as count
            FROM agent_capabilities ac
            WHERE ac.framework IS NOT NULL
            GROUP BY ac.framework
            ORDER BY count DESC
        ''')
        frameworks = {row['framework']: row['count'] for row in cursor.fetchall()}
        
        # Model distribution
        cursor.execute('''
            SELECT ac.model_name, COUNT(*) as count
            FROM agent_capabilities ac
            WHERE ac.model_name IS NOT NULL
            GROUP BY ac.model_name
            ORDER BY count DESC
        ''')
        models = {row['model_name']: row['count'] for row in cursor.fetchall()}
        
        # Capabilities distribution (aggregate tools from JSON)
        cursor.execute('SELECT available_tools FROM agent_capabilities')
        tool_counts = {}
        for row in cursor.fetchall():
            if row['available_tools']:
                try:
                    tools = json.loads(row['available_tools'])
                    for tool in tools:
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Security posture distribution
        cursor.execute('''
            SELECT sa.auth_method, COUNT(*) as count
            FROM security_assessments sa
            WHERE sa.auth_method IS NOT NULL
            GROUP BY sa.auth_method
            ORDER BY count DESC
        ''')
        security_posture = {row['auth_method']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            "frameworks": frameworks,
            "models": models,
            "capabilities": tool_counts,
            "security_posture": security_posture,
            "total_agents": sum(frameworks.values()) if frameworks else 0,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Heatmap query failed: {e}")
        conn.close()
        return jsonify({"error": str(e)}), 500


@telemetry_api.route('/trends')
def telemetry_trends():
    """
    GET /api/telemetry/trends
    
    Temporal patterns: uptime, activity cycles, version changes.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Uptime over 24h (hourly breakdown)
        cursor.execute('''
            SELECT strftime('%H', measured_at) as hour, 
                   COUNT(DISTINCT agent_id) as online_agents
            FROM performance_metrics
            WHERE measured_at >= datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour
        ''')
        uptime_24h = [
            {"hour": int(row['hour']), "online_agents": row['online_agents']}
            for row in cursor.fetchall()
        ]
        
        # Activity patterns from behavioral data
        cursor.execute('SELECT peak_activity_hours FROM behavioral_patterns')
        all_peak_hours = []
        for row in cursor.fetchall():
            if row['peak_activity_hours']:
                try:
                    hours = json.loads(row['peak_activity_hours'])
                    all_peak_hours.extend(hours)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Calculate hour-of-day distribution
        hour_distribution = {}
        for hour in all_peak_hours:
            hour_str = str(hour)
            hour_distribution[hour_str] = hour_distribution.get(hour_str, 0) + 1
        
        # Normalize to 0-1 scale
        max_count = max(hour_distribution.values()) if hour_distribution else 1
        hour_of_day = {k: round(v / max_count, 2) for k, v in hour_distribution.items()}
        
        # New agents in last 7 days
        cursor.execute('''
            SELECT COUNT(*) as new_agents
            FROM agents
            WHERE first_seen >= datetime('now', '-7 days')
        ''')
        new_agents_7d = cursor.fetchone()['new_agents']
        
        # Version updates in last 7 days (framework_version changes)
        cursor.execute('''
            SELECT COUNT(DISTINCT agent_id) as version_updates
            FROM agent_capabilities
            WHERE updated_at >= datetime('now', '-7 days')
            AND framework_version IS NOT NULL
        ''')
        version_updates_7d = cursor.fetchone()['version_updates']
        
        conn.close()
        
        return jsonify({
            "uptime_24h": uptime_24h,
            "activity_peaks": {
                "hour_of_day": hour_of_day
            },
            "new_agents_7d": new_agents_7d,
            "version_updates_7d": version_updates_7d,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Trends query failed: {e}")
        conn.close()
        return jsonify({"error": str(e)}), 500


@telemetry_api.route('/security-distribution')
def security_distribution():
    """
    GET /api/telemetry/security-distribution
    
    Security posture across all agents.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Auth method distribution
        cursor.execute('''
            SELECT sa.auth_method, COUNT(*) as count
            FROM security_assessments sa
            WHERE sa.auth_method IS NOT NULL
            GROUP BY sa.auth_method
            ORDER BY count DESC
        ''')
        auth_rows = cursor.fetchall()
        total_auth = sum(row['count'] for row in auth_rows)
        
        auth_distribution = {}
        for row in auth_rows:
            auth_distribution[row['auth_method']] = {
                "count": row['count'],
                "percentage": round((row['count'] / total_auth * 100), 1) if total_auth > 0 else 0
            }
        
        # Vulnerability summary (parse from JSON)
        cursor.execute('SELECT known_vulnerabilities FROM security_assessments')
        vuln_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for row in cursor.fetchall():
            if row['known_vulnerabilities']:
                try:
                    vulns = json.loads(row['known_vulnerabilities'])
                    for vuln in vulns:
                        severity = vuln.get('severity', 'medium').lower()
                        if severity in vuln_summary:
                            vuln_summary[severity] += 1
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Exposed endpoints count
        cursor.execute('''
            SELECT COUNT(*) as exposed_count
            FROM security_assessments
            WHERE admin_endpoints_exposed = 1
        ''')
        exposed_admin = cursor.fetchone()['exposed_count']
        
        cursor.execute('''
            SELECT COUNT(*) as config_exposed
            FROM security_assessments
            WHERE default_credentials = 1
        ''')
        exposed_config = cursor.fetchone()['config_exposed']
        
        # Average security score
        cursor.execute('''
            SELECT AVG(security_score) as avg_score
            FROM security_assessments
            WHERE security_score IS NOT NULL
        ''')
        avg_security_score = cursor.fetchone()['avg_score']
        
        conn.close()
        
        return jsonify({
            "auth_distribution": auth_distribution,
            "vulnerability_summary": vuln_summary,
            "exposed_endpoints": {
                "admin_panels": exposed_admin,
                "config_files": exposed_config,
                "debug_endpoints": exposed_admin  # Approximate
            },
            "avg_security_score": round(avg_security_score, 1) if avg_security_score else 0,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Security distribution query failed: {e}")
        conn.close()
        return jsonify({"error": str(e)}), 500


@telemetry_api.route('/framework-comparison')
def framework_comparison():
    """
    GET /api/telemetry/framework-comparison
    
    Performance metrics grouped by AI framework and model.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Framework performance aggregates
        cursor.execute('''
            SELECT 
                ac.framework,
                COUNT(DISTINCT ac.agent_id) as count,
                AVG(pm.response_time_p50) as response_time_p50,
                AVG(pm.response_time_p99) as response_time_p99,
                AVG(pm.error_rate) as error_rate,
                AVG(pm.availability_pct) as availability
            FROM agent_capabilities ac
            JOIN performance_metrics pm ON ac.agent_id = pm.agent_id
            WHERE ac.framework IS NOT NULL
            GROUP BY ac.framework
            ORDER BY count DESC
        ''')
        frameworks = [
            {
                "name": row['framework'] or 'unknown',
                "count": row['count'],
                "response_time_p50": round(row['response_time_p50'], 0) if row['response_time_p50'] else 0,
                "response_time_p99": round(row['response_time_p99'], 0) if row['response_time_p99'] else 0,
                "error_rate": round(row['error_rate'], 3) if row['error_rate'] else 0,
                "availability": round(row['availability'], 1) if row['availability'] else 0
            }
            for row in cursor.fetchall()
        ]
        
        # Model performance aggregates
        cursor.execute('''
            SELECT 
                ac.model_name,
                COUNT(DISTINCT ac.agent_id) as count,
                AVG(pm.response_time_p50) as response_time_p50,
                AVG(pm.error_rate) as error_rate
            FROM agent_capabilities ac
            JOIN performance_metrics pm ON ac.agent_id = pm.agent_id
            WHERE ac.model_name IS NOT NULL
            GROUP BY ac.model_name
            ORDER BY count DESC
            LIMIT 10
        ''')
        models = [
            {
                "model": row['model_name'] or 'unknown',
                "avg_response_time": round(row['response_time_p50'], 0) if row['response_time_p50'] else 0,
                "error_rate": round(row['error_rate'], 3) if row['error_rate'] else 0,
                "agent_count": row['count']
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            "frameworks": frameworks,
            "model_comparison": models,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Framework comparison query failed: {e}")
        conn.close()
        return jsonify({"error": str(e)}), 500


@telemetry_api.route('/anomalies')
def telemetry_anomalies():
    """
    GET /api/telemetry/anomalies
    
    Detected unusual patterns and potential security issues.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        anomalies = []
        
        # Detect capability changes (compare latest two capability records)
        cursor.execute('''
            SELECT ac1.agent_id, ac1.available_tools as current_tools,
                   ac2.available_tools as previous_tools,
                   ac1.updated_at, ac2.updated_at as prev_updated
            FROM agent_capabilities ac1
            JOIN agent_capabilities ac2 ON ac1.agent_id = ac2.agent_id
            WHERE ac1.updated_at > datetime('now', '-24 hours')
            AND ac2.updated_at < datetime('now', '-24 hours')
            AND ac1.available_tools != ac2.available_tools
            ORDER BY ac1.updated_at DESC
            LIMIT 10
        ''')
        
        for row in cursor.fetchall():
            try:
                current = json.loads(row['current_tools']) if row['current_tools'] else []
                previous = json.loads(row['previous_tools']) if row['previous_tools'] else []
                new_tools = set(current) - set(previous)
                
                if new_tools:
                    anomalies.append({
                        "agent_id": row['agent_id'],
                        "type": "capability_change",
                        "severity": "critical" if "exec" in new_tools or "write" in new_tools else "high",
                        "description": f"New tool(s) enabled: {', '.join(new_tools)}",
                        "detected_at": row['updated_at'],
                        "previous_tools": previous,
                        "current_tools": current
                    })
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Detect security regressions
        cursor.execute('''
            SELECT sa1.agent_id, sa1.auth_method as current_auth,
                   sa2.auth_method as prev_auth, sa1.assessed_at
            FROM security_assessments sa1
            JOIN security_assessments sa2 ON sa1.agent_id = sa2.agent_id
            WHERE sa1.assessed_at > datetime('now', '-24 hours')
            AND sa2.assessed_at < datetime('now', '-24 hours')
            AND (sa1.auth_method != sa2.auth_method OR sa1.security_score < sa2.security_score)
            ORDER BY sa1.assessed_at DESC
            LIMIT 10
        ''')
        
        for row in cursor.fetchall():
            if row['current_auth'] == 'none' and row['prev_auth'] is not None and row['prev_auth'] != 'none':
                anomalies.append({
                    "agent_id": row['agent_id'],
                    "type": "security_regression",
                    "severity": "critical",
                    "description": "Authentication disabled (was previously enabled)",
                    "detected_at": row['assessed_at'],
                    "previous_auth": row['prev_auth'],
                    "current_auth": row['current_auth']
                })
        
        # Detect activity spikes (high anomaly scores)
        cursor.execute('''
            SELECT agent_id, anomaly_score, computed_at
            FROM behavioral_patterns
            WHERE anomaly_score > 0.7
            ORDER BY anomaly_score DESC
            LIMIT 10
        ''')
        
        for row in cursor.fetchall():
            anomalies.append({
                "agent_id": row['agent_id'],
                "type": "activity_spike",
                "severity": "high" if row['anomaly_score'] > 0.9 else "medium",
                "description": f"Unusual activity pattern detected (score: {row['anomaly_score']:.2f})",
                "detected_at": row['computed_at'],
                "anomaly_score": row['anomaly_score']
            })
        
        conn.close()
        
        # Categorize by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'medium')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return jsonify({
            "anomalies": anomalies,
            "total_anomalies": len(anomalies),
            "by_severity": by_severity,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        conn.close()
        return jsonify({"error": str(e)}), 500
