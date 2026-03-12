#!/usr/bin/env python3
"""
CogniWatch Cloud Scanner
Scan public internet for AI agent frameworks
Private data collection - NOT FOR PUBLIC EXPOSURE
"""

import asyncio
import aiohttp
import websocket
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
import ipaddress
import random
from dataclasses import dataclass, asdict
import asyncpg  # PostgreSQL async driver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentDiscovery:
    """Discovered AI agent instance"""
    ip: str
    port: int
    framework: str
    version: Optional[str]
    model: Optional[str]
    detected_at: str
    banner: Optional[str]
    confidence: float
    country: Optional[str] = None
    asn: Optional[str] = None
    is_exposed: bool = True  # Publicly accessible


class CloudScanner:
    """
    Cloud-based AI agent scanner
    Scans public IPv4 space for agent frameworks
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.database_url = config['database']['url']
        self.scan_rate = config.get('scan_rate', 100)  # IPs per second
        self.ports = config.get('ports', [18789, 18790, 18791])  # OpenClaw defaults
        self.user_agent = config.get('user_agent', 'CogniWatch-Scanner/1.0')
        self.respect_robots = config.get('respect_robots', True)
        
        self.db_pool = None
        self.session = None
        self.scan_count = 0
        self.found_count = 0
        
    async def connect_db(self):
        """Connect to PostgreSQL"""
        self.db_pool = await asyncpg.create_pool(self.database_url)
        logger.info(f"✅ Connected to PostgreSQL")
        
        # Create tables if not exist
        await self.init_db()
    
    async def init_db(self):
        """Initialize database schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id SERIAL PRIMARY KEY,
                    ip VARCHAR(45) NOT NULL,
                    port INTEGER NOT NULL,
                    framework VARCHAR(50) NOT NULL,
                    version VARCHAR(50),
                    model VARCHAR(100),
                    detected_at TIMESTAMP NOT NULL,
                    banner TEXT,
                    confidence FLOAT NOT NULL,
                    country VARCHAR(2),
                    asn VARCHAR(100),
                    is_exposed BOOLEAN DEFAULT TRUE,
                    UNIQUE(ip, port, framework)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id SERIAL PRIMARY KEY,
                    scan_range VARCHAR(50) NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    ips_scanned INTEGER DEFAULT 0,
                    agents_found INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'running'
                )
            """)
            
            logger.info("✅ Database schema initialized")
    
    async def scan_ip(self, ip: str, port: int, semaphore: asyncio.Semaphore) -> Optional[AgentDiscovery]:
        """Scan single IP:port for agent frameworks"""
        async with semaphore:
            try:
                # Check if port is open
                is_open = await self.check_port(ip, port)
                
                if not is_open:
                    return None
                
                # Port is open - try to fingerprint
                discovery = await self.fingerprint_agent(ip, port)
                
                if discovery:
                    self.found_count += 1
                    logger.info(f"🎯 FOUND: {discovery.framework} @ {ip}:{port} ({discovery.confidence:.0%})")
                    
                    # Save to database
                    await self.save_discovery(discovery)
                
                self.scan_count += 1
                
                # Progress logging
                if self.scan_count % 1000 == 0:
                    logger.info(f"📈 Scanned {self.scan_count} IPs, found {self.found_count} agents")
                
                return discovery
                
            except Exception as e:
                logger.debug(f"Error scanning {ip}:{port}: {e}")
                return None
    
    async def check_port(self, ip: str, port: int, timeout: float = 2.0) -> bool:
        """Check if TCP port is open"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def fingerprint_agent(self, ip: str, port: int) -> Optional[AgentDiscovery]:
        """Fingerprint agent framework via HTTP/WebSocket"""
        
        # Try HTTP first
        try:
            async with self.session.get(
                f"http://{ip}:{port}/",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                html = await response.text()
                
                # Check for OpenClaw signatures
                if 'openclaw' in html.lower() or 'OpenClaw' in html:
                    version = self.extract_version(html)
                    return AgentDiscovery(
                        ip=ip,
                        port=port,
                        framework="openclaw",
                        version=version,
                        model=None,
                        detected_at=datetime.now().isoformat(),
                        banner=html[:1000],
                        confidence=0.85 if 'openclaw-app' in html else 0.65
                    )
                
                # Add more framework detection here
                
        except Exception:
            pass
        
        # Try WebSocket (OpenClaw uses WebSocket)
        try:
            ws = await asyncio.wait_for(
                websocket.connect(f"ws://{ip}:{port}/", close_timeout=2),
                timeout=5
            )
            
            # Send status request
            await ws.send(json.dumps({"action": "status"}))
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            
            try:
                data = json.loads(response)
                
                # Check for OpenClaw response patterns
                if 'sessions' in data or 'gateway' in data or 'status' in data:
                    await ws.close()
                    return AgentDiscovery(
                        ip=ip,
                        port=port,
                        framework="openclaw",
                        version=None,
                        model=data.get('model'),
                        detected_at=datetime.now().isoformat(),
                        banner=response[:1000],
                        confidence=0.95  # WebSocket confirmation = high confidence
                    )
            except:
                pass
            
            await ws.close()
            
        except Exception:
            pass
        
        return None
    
    def extract_version(self, html: str) -> Optional[str]:
        """Extract version from HTML"""
        # Look for version patterns in HTML
        import re
        match = re.search(r'v?(\d+\.\d+\.\d+)', html)
        if match:
            return match.group(1)
        return None
    
    async def save_discovery(self, discovery: AgentDiscovery):
        """Save discovery to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agents (ip, port, framework, version, model, detected_at, banner, confidence, is_exposed)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (ip, port, framework) DO UPDATE SET
                    detected_at = EXCLUDED.detected_at,
                    version = EXCLUDED.version,
                    model = EXCLUDED.model,
                    confidence = EXCLUDED.confidence,
                    banner = EXCLUDED.banner
            """,
                discovery.ip,
                discovery.port,
                discovery.framework,
                discovery.version,
                discovery.model,
                discovery.detected_at,
                discovery.banner,
                discovery.confidence,
                discovery.is_exposed
            )
    
    async def scan_range(self, network: str):
        """Scan entire IP range"""
        logger.info(f"🚀 Starting scan of {network}")
        
        # Parse network
        if '/' in network:
            ips = list(ipaddress.IPv4Network(network, strict=False))
        else:
            ips = [ipaddress.IPv4Address(network)]
        
        # Create scan record
        async with self.db_pool.acquire() as conn:
            scan_id = await conn.fetchval("""
                INSERT INTO scans (scan_range, started_at, status)
                VALUES ($1, $2, 'running')
                RETURNING id
            """, network, datetime.now())
        
        # Scan with rate limiting
        semaphore = asyncio.Semaphore(self.scan_rate)
        
        tasks = []
        for ip in ips:
            for port in self.ports:
                task = asyncio.create_task(self.scan_ip(str(ip), port, semaphore))
                tasks.append(task)
                
                # Small delay to avoid overwhelming
                if len(tasks) % 100 == 0:
                    await asyncio.sleep(0.1)
        
        # Wait for all scans to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update scan record
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE scans
                SET completed_at = $1, ips_scanned = $2, agents_found = $3, status = 'completed'
                WHERE id = $4
            """, datetime.now(), len(ips) * len(self.ports), self.found_count, scan_id)
        
        logger.info(f"✅ Scan complete: {network} - Found {self.found_count} agents")
    
    async def run(self):
        """Main scanner loop"""
        logger.info("👁️ CogniWatch Cloud Scanner starting...")
        logger.info(f"📡 Scan rate: {self.scan_rate} IPs/sec")
        logger.info(f"🎯 Target ports: {self.ports}")
        logger.info(f"💾 Database: {self.database_url}")
        
        # Initialize
        await self.connect_db()
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Scan targets (start with high-probability ranges)
            scan_targets = self.config.get('scan_targets', [
                # Common VPS provider ranges (where OpenClaw users deploy)
                # Start small for testing
                "digitalocean",  # We'll expand this
                "linode",
                "aws-ec2"
            ])
            
            # For MVP, just scan some common ranges
            # In production, we'd scan full IPv4 space
            
            test_ranges = [
                # Example: Scan some DigitalOcean NYC ranges (where Jannie might be)
                # These are EXAMPLES - replace with real scanning strategy
                "159.65.0.0/16",  # DigitalOcean NYC
                "167.99.0.0/16",  # DigitalOcean NYC
                "104.248.0.0/16", # DigitalOcean SFO
            ]
            
            for network in test_ranges:
                try:
                    await self.scan_range(network)
                except KeyboardInterrupt:
                    logger.info("⚠️ Scan interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"❌ Error scanning {network}: {e}")
                    continue
        
        logger.info("✅ All scans complete!")


async def main():
    """Run cloud scanner"""
    
    # Configuration
    config = {
        "database": {
            "url": "postgresql://cogniwatch:PASSWORD@localhost:5432/cogniwatch"
        },
        "scan_rate": 100,  # IPs per second
        "ports": [18789, 18790, 18791],  # OpenClaw defaults
        "user_agent": "CogniWatch-Scanner/1.0 (Research)",
        "respect_robots": True,
        "scan_targets": ["test-ranges"]
    }
    
    scanner = CloudScanner(config)
    await scanner.run()


if __name__ == "__main__":
    asyncio.run(main())
