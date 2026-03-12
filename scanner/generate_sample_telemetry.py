"""
VULCAN Telemetry Sample Data Generator
For testing and demonstration purposes
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'cogniwatch.db'


def generate_sample_telemetry():
    """Generate realistic sample telemetry data for testing"""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Sample data templates
    frameworks = ['openclaw', 'langchain', 'autogen', 'crewai', 'llamaindex']
    models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet', 'llama-2-70b', 'mistral-large']
    tools_pool = ['web_search', 'read', 'write', 'exec', 'email', 'calendar', 'database', 'code_runner']
    auth_methods = ['none', 'api_key', 'jwt', 'oauth', 'basic']
    
    # Get existing agents or create sample ones
    cursor.execute('SELECT id FROM agents LIMIT 5')
    existing_agents = [row['id'] for row in cursor.fetchall()]
    
    if not existing_agents:
        # Create sample agents
        sample_agents = [
            ('openclaw-local-1', 'OpenClaw Local 1', 'gpt-4'),
            ('openclaw-local-2', 'OpenClaw Local 2', 'claude-3'),
            ('langchain-dev', 'LangChain Dev Agent', 'gpt-3.5-turbo'),
            ('autogen-team', 'AutoGen Team Lead', 'gpt-4'),
            ('crewai-worker', 'CrewAI Worker', 'llama-2'),
        ]
        
        for agent_id, name, model in sample_agents:
            cursor.execute('''
                INSERT OR IGNORE INTO agents (id, name, model, status, first_seen, last_seen)
                VALUES (?, ?, ?, 'active', datetime('now'), datetime('now'))
            ''', (agent_id, name, model))
        
        existing_agents = [a[0] for a in sample_agents]
    
    print(f"📊 Generating telemetry for {len(existing_agents)} agents...")
    now = datetime.now()
    
    for agent_id in existing_agents:
        print(f"  → {agent_id}")
        
        # 1. Agent Capabilities
        framework = random.choice(frameworks)
        model = random.choice(models)
        num_tools = random.randint(3, 7)
        tools = random.sample(tools_pool, num_tools)
        
        cursor.execute('''
            INSERT INTO agent_capabilities (
                agent_id, framework, framework_version, model_provider, model_name,
                context_window, available_tools, api_versions, feature_flags,
                capabilities_hash, streaming_support, streaming_protocol,
                multimodal_input, multimodal_output, function_calling,
                agent_orchestration, memory_persistence, discovered_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (
            agent_id,
            framework,
            f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
            'openai' if 'gpt' in model else 'anthropic' if 'claude' in model else 'meta',
            model,
            random.choice([4096, 8192, 16384, 32768, 128000]),
            json.dumps(tools),
            json.dumps(['v1', 'v2']),
            json.dumps({'debug_mode': random.choice([True, False]), 'unsafe_tools': False}),
            f"{random.randint(1000,9999):x}",
            random.choice([True, True, True, False]),  # 75% have streaming
            'sse' if random.random() > 0.5 else 'websocket',
            json.dumps(random.sample(['image', 'audio'], random.randint(0, 2))),
            json.dumps(['text'] + (['image'] if random.random() > 0.7 else [])),
            random.choice([True, True, True, False]),
            random.choice([True, False, False]),
            random.choice([True, False]),
        ))
        
        # 2. Performance Metrics (multiple time points)
        for hours_ago in range(0, 24, 6):
            timestamp = (now - timedelta(hours=hours_ago)).isoformat()
            base_rt = random.uniform(200, 500)
            
            cursor.execute('''
                INSERT INTO performance_metrics (
                    agent_id, response_time_p50, response_time_p95, response_time_p99,
                    throughput_rps, concurrent_sessions, token_throughput, error_rate,
                    availability_pct, measured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_id,
                base_rt,
                base_rt * random.uniform(1.5, 2.5),
                base_rt * random.uniform(2.5, 4.0),
                random.uniform(10, 50),
                random.randint(5, 50),
                random.uniform(500, 2000),
                random.uniform(0.001, 0.05),
                random.uniform(95, 99.9),
                timestamp
            ))
        
        # 3. Security Assessments
        auth_method = random.choice(auth_methods)
        sec_score = random.randint(40, 100)
        
        cursor.execute('''
            INSERT INTO security_assessments (
                agent_id, auth_method, rate_limiting_enabled, rate_limit_threshold,
                cors_policy, admin_endpoints_exposed, default_credentials,
                https_enforced, known_vulnerabilities, security_score, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            agent_id,
            auth_method,
            random.choice([True, True, False]),
            random.choice([60, 100, 120, 300]),
            random.choice(['permissive', 'restrictive', 'misconfigured']),
            random.choice([True, False, False, False]),  # 25% exposed
            random.choice([True, False, False, False, False]),  # 20% default creds
            random.choice([True, True, True, False]),
            json.dumps([
                {'cve': 'CVE-2024-1234', 'severity': 'high', 'description': 'Example vulnerability'}
            ] if random.random() > 0.7 else []),
            sec_score,
        ))
        
        # 4. Topology Data
        cursor.execute('''
            INSERT INTO topology_data (
                agent_id, behind_proxy, proxy_type, load_balanced, cdn_detected,
                hosting_provider, container_detected, orchestrator, asn,
                geo_location, network_distance, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            agent_id,
            random.choice([True, True, False]),
            random.choice(['nginx', 'apache', 'traefik', None]),
            random.choice([True, False]),
            random.choice([True, False, False]),
            random.choice(['AWS', 'GCP', 'Azure', 'DigitalOcean', 'Local']),
            random.choice([True, True, True, False]),
            random.choice(['k8s', 'docker', 'swarm', None]),
            f"AS{random.randint(1000, 60000)}",
            random.choice(['US-East', 'US-West', 'EU-West', 'EU-Central', 'Local Network']),
            random.randint(1, 15),
        ))
        
        # 5. Behavioral Patterns
        peak_hours = random.sample(range(8, 20), random.randint(4, 8))
        endpoint_usage = {tool: random.randint(10, 100) for tool in random.sample(tools_pool, min(5, len(tools)))}
        
        cursor.execute('''
            INSERT INTO behavioral_patterns (
                agent_id, uptime_pattern, peak_activity_hours, session_duration_p50,
                session_duration_p95, endpoint_usage, version_history, update_frequency,
                activity_trend, anomaly_score, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            agent_id,
            json.dumps({str(h): random.choice([1, 0, 1, 1, 1]) for h in range(24)}),
            json.dumps(peak_hours),
            random.uniform(5, 30),
            random.uniform(30, 120),
            json.dumps(endpoint_usage),
            json.dumps([
                {'version': '1.0', 'date': (now - timedelta(days=30)).isoformat()},
                {'version': '1.1', 'date': (now - timedelta(days=15)).isoformat()},
                {'version': '1.2', 'date': now.isoformat()}
            ]),
            random.uniform(7, 30),
            random.choice(['increasing', 'stable', 'decreasing']),
            random.uniform(0.1, 0.9),
        ))
    
    conn.commit()
    
    # Summary statistics
    cursor.execute('SELECT COUNT(*) FROM agent_capabilities')
    caps_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM performance_metrics')
    perf_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM security_assessments')
    sec_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM topology_data')
    topo_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM behavioral_patterns')
    behav_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n✅ Sample telemetry data generated!")
    print(f"   • Agent capabilities: {caps_count} records")
    print(f"   • Performance metrics: {perf_count} records")
    print(f"   • Security assessments: {sec_count} records")
    print(f"   • Topology data: {topo_count} records")
    print(f"   • Behavioral patterns: {behav_count} records")
    print(f"\n📊 Database: {DB_PATH}")
    print("\n🌐 Test the API endpoints:")
    print("   curl http://localhost:9000/api/telemetry/heatmap")
    print("   curl http://localhost:9000/api/telemetry/trends")
    print("   curl http://localhost:9000/api/telemetry/security-distribution")
    print("   curl http://localhost:9000/api/telemetry/framework-comparison")
    print("   curl http://localhost:9000/api/telemetry/anomalies")


if __name__ == '__main__':
    generate_sample_telemetry()
