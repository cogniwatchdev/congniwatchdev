"""
CogniWatch - OpenClaw Gateway Integration
Query OpenClaw Gateway API for agent data
"""

import requests
import websocket
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenClawGateway:
    """Client for OpenClaw Gateway API"""
    
    def __init__(self, url: str, token: str):
        self.url = url.replace('ws://', 'http://').replace('wss://', 'https://')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def get_status(self) -> Dict:
        """Get gateway status"""
        try:
            # Note: OpenClaw Gateway may not have a /status endpoint yet
            # This is a placeholder for when it's available
            response = self.session.get(f"{self.url}/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"Status endpoint not available: {e}")
            return {"status": "unknown", "message": str(e)}
    
    def get_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        try:
            # Try sessions endpoint (if available in OpenClaw)
            response = self.session.get(f"{self.url}/api/sessions", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"Sessions endpoint not available: {e}")
        
        # Fallback: Return empty list (will be populated by other means)
        return []
    
    def get_session_history(self, session_key: str, limit: int = 50) -> List[Dict]:
        """Get session message history"""
        try:
            response = self.session.get(
                f"{self.url}/api/sessions/history",
                params={'sessionKey': session_key, 'limit': limit},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('messages', [])
        except Exception as e:
            logger.debug(f"History endpoint error: {e}")
        
        return []
    
    def get_model_info(self) -> Dict:
        """Get current model information"""
        # This would need to be implemented in OpenClaw
        # For now, return placeholder
        return {
            "model": "unknown",
            "provider": "unknown"
        }
    
    def test_connection(self) -> bool:
        """Test if gateway is reachable"""
        try:
            response = self.session.get(f"{self.url}/", timeout=3)
            return response.status_code < 500  # Any response except server error
        except:
            return False

class AgentTracker:
    """Track agent state and activity"""
    
    def __init__(self, gateway: OpenClawGateway):
        self.gateway = gateway
        self.agents = {}  # Track known agents
        self.last_poll = {}  # Last poll time per agent
    
    def discover_agents(self, config: Dict) -> List[Dict]:
        """Discover agents via network scanning + Gateway query"""
        agents = []
        
        logger.info("🔍 Starting agent discovery...")
        
        # Method 1: Network scan (primary)
        try:
            from scanner.network_scanner import NetworkScanner
            
            network = config.get('scanner', {}).get('network', '192.168.0.0/24')
            timeout = config.get('scanner', {}).get('timeout', 1.0)
            
            logger.info(f"📡 Scanning network: {network}")
            
            scanner = NetworkScanner(network=network, timeout=timeout)
            discovered = scanner.scan_network()
            
            if discovered and len(discovered) > 0:
                logger.info(f"✨ Network scan found {len(discovered)} agents!")
                
                for agent in discovered:
                    # Convert scanner format to tracker format
                    agents.append({
                        "id": f"{agent['framework']}-{agent['host'].replace('.', '-')}-{agent['port']}",
                        "name": f"{agent['framework'].title()} @ {agent['host']}",
                        "framework": agent['framework'],
                        "host": agent['host'],
                        "port": agent['port'],
                        "model": agent.get('api_info', {}).get('model', 'unknown'),
                        "persona": f"Auto-discovered {agent['framework']} agent",
                        "gateway_url": f"ws://{agent['host']}:{agent['port']}",
                        "discovered_at": agent['detected_at'],
                        "discovery_method": "network_scan",
                        "status": agent['status']
                    })
                    
        except Exception as e:
            logger.warning(f"Network scan failed: {e}")
            logger.info("📋 Falling back to Gateway query...")
        
        # Method 2: Query OpenClaw Gateway (if network scan found nothing)
        if len(agents) == 0:
            try:
                sessions = self.gateway.get_sessions()
                
                if sessions and len(sessions) > 0:
                    logger.info(f"✨ Gateway query found {len(sessions)} sessions!")
                    
                    for session in sessions:
                        label = session.get('label', 'unknown')
                        model = session.get('model', 'unknown')
                        session_key = session.get('sessionKey', '')
                        
                        agent_name = label.split(':')[-1] if ':' in label else label
                        agent_name = agent_name.replace('-', ' ').title()
                        
                        agents.append({
                            "id": session_key,
                            "name": agent_name,
                            "model": model,
                            "persona": f"Auto-discovered via OpenClaw Gateway",
                            "gateway_url": config['openclaw_gateway']['url'],
                            "discovery_method": "gateway_query",
                            "discovered_at": datetime.now().isoformat()
                        })
                        
            except Exception as e:
                logger.warning(f"Gateway query failed: {e}")
                logger.info("📋 Falling back to configured agents...")
        
        # Method 3: Config fallback (if auto-discovery found nothing)
        if len(agents) == 0:
            logger.info("📋 Using configured agents as fallback")
            
            if 'agents' in config and isinstance(config['agents'], list):
                for agent_config in config['agents']:
                    agents.append({
                        "id": agent_config.get('id', f"agent-{len(agents)+1}"),
                        "name": agent_config.get('name', 'Unknown Agent'),
                        "model": agent_config.get('model', 'unknown'),
                        "persona": agent_config.get('persona', 'Custom agent'),
                        "gateway_url": agent_config.get('gateway_url', config['openclaw_gateway']['url']),
                        "discovery_method": "config",
                        "discovered_at": datetime.now().isoformat()
                    })
            else:
                logger.warning("⚠️ No agents discovered and no config fallback")
        
        logger.info(f"✅ Discovery complete: {len(agents)} agents found")
        return agents
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent"""
        # For Phase A, we'll use a simple active/idle/offline model
        # In production, this would query the actual agent state
        
        return {
            "id": agent_id,
            "status": "active",  # active, idle, offline
            "last_seen": datetime.now().isoformat(),
            "uptime_hours": 24.5,  # Would calculate from first_seen
            "current_goal": None,
            "confidence": None
        }
    
    def track_activity(self, agent_id: str, activity_type: str, details: Dict) -> Dict:
        """Record agent activity"""
        activity = {
            "agent_id": agent_id,
            "activity_type": activity_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # In production, this would save to database
        logger.info(f"Activity: {agent_id} - {activity_type}")
        
        return activity
    
    def calculate_costs(self, token_in: int, token_out: int, model: str) -> Dict:
        """Calculate cost from token usage"""
        # Approximate pricing ( adjust based on actual model pricing)
        pricing = {
            "qwen3.5:cloud": {"in": 0.000001, "out": 0.000003},
            "qwen3-coder:480b-cloud": {"in": 0.000002, "out": 0.000006},
            "default": {"in": 0.000001, "out": 0.000003}
        }
        
        rates = pricing.get(model, pricing["default"])
        
        cost_in = token_in * rates["in"]
        cost_out = token_out * rates["out"]
        total_cost = cost_in + cost_out
        
        return {
            "token_in": token_in,
            "token_out": token_out,
            "cost_in_usd": round(cost_in, 4),
            "cost_out_usd": round(cost_out, 4),
            "total_cost_usd": round(total_cost, 4)
        }

# Example usage
if __name__ == '__main__':
    # Test connection
    gateway = OpenClawGateway("ws://127.0.0.1:18789", "your-token-here")
    
    if gateway.test_connection():
        print("✅ Gateway connected")
        
        tracker = AgentTracker(gateway)
        agents = tracker.discover_agents({})
        
        print(f"📊 Found {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['model']})")
    else:
        print("❌ Gateway not reachable")
