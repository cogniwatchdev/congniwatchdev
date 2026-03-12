#!/usr/bin/env python3
"""
CogniWatch Scanner Daemon
Continuous network scanning with configurable intervals
"""

import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.network_scanner import NetworkScanner
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
NETWORK = os.environ.get('SCANNER_NETWORK', '192.168.0.0/24')
INTERVAL_HOURS = int(os.environ.get('SCANNER_INTERVAL_HOURS', '24'))

def main():
    logger.info(f"Starting CogniWatch Scanner")
    logger.info(f"Network: {NETWORK}, Interval: {INTERVAL_HOURS}h")
    
    scanner = NetworkScanner(network=NETWORK, timeout=2.0)
    
    while True:
        try:
            logger.info(f"Starting scan at {datetime.now().isoformat()}")
            scanner.scan_network(parallel=100)
            logger.info(f"Scan complete. Sleeping for {INTERVAL_HOURS} hours...")
            time.sleep(INTERVAL_HOURS * 3600)
        except KeyboardInterrupt:
            logger.info('Scanner stopped by user')
            break
        except Exception as e:
            logger.error(f'Scan error: {e}')
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == '__main__':
    main()
