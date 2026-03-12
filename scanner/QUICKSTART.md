# 🔍 CogniWatch VULCAN - Quick Start Guide

Get started with advanced multi-layer agent detection in 5 minutes.

---

## Installation

All modules are already in place. Just ensure dependencies are installed:

```bash
cd /home/neo/cogniwatch
source venv/bin/activate  # If using virtualenv
pip install requests beautifulsoup4 websocket-client  # Verify dependencies
```

---

## Quick Test (Single Target)

Test the Neo gateway with full multi-layer detection:

```python
from scanner.integrated_detector import IntegratedDetector

# Initialize detector
detector = IntegratedDetector(timeout=3.0)

# Run comprehensive detection
result = detector.detect("192.168.0.245", 18789)

# Print results
print(f"\n🎯 Framework: {result.top_framework or 'Unknown'}")
print(f"📊 Confidence: {result.confidence:.1%}")
print(f"📈 Quality: {result.detection_quality}")
print(f"💡 Recommendation: {result.recommendation}")
```

---

## Test Individual Layers

### HTTP Fingerprinting
```python
from http_fingerprinter import HTTPFingerprinter

fp = HTTPFingerprinter(timeout=3.0)
result = fp.fingerprint("http://192.168.0.245:18789")

print(f"Server: {result.server_header}")
print(f"Title: {result.title}")
print(f"Frameworks: {result.framework_indicators}")
```

### API Behavioral Analysis
```python
from api_analyzer import APIAnalyzer

analyzer = APIAnalyzer(timeout=3.0)
result = analyzer.analyze("http://192.168.0.245:18789")

print(f"Endpoints responding: {result.endpoints_responding}")
print(f"Detected framework: {result.detected_framework}")
print(f"AI fields found: {result.framework_indicators}")
```

### WebSocket Detection
```python
from websocket_detector import WebSocketDetector

detector = WebSocketDetector(timeout=3.0)
result = detector.detect("ws://192.168.0.245:18789/")

print(f"Connected: {result.connection_success}")
print(f"Protocol: {result.protocol_type}")
print(f"Framework: {result.detected_framework}")
```

### Telemetry Collection
```python
from telemetry_collector import TelemetryCollector

collector = TelemetryCollector(timeout=3.0)
result = collector.collect("192.168.0.245", 18789)

print(f"Framework: {result.metadata.framework if result.metadata else None}")
print(f"Version: {result.metadata.version if result.metadata else None}")
print(f"Health: {result.activity.health_status if result.activity else None}")
print(f"Security: {result.security.exposure_level if result.security else None}")
```

---

## Run Full Test Suite

```bash
cd /home/neo/cogniwatch/scanner
python3 test_advanced_detection.py
```

Results saved to: `/tmp/vulcan_test_results_TIMESTAMP.json`

---

## Database Integration

### Initialize Schema
```bash
cd /home/neo/cogniwatch/database
python3 schema.py
```

Adds:
- `detection_results` table
- `analysis_metrics` table

### Query Recent Detections
```python
import sqlite3
from pathlib import Path

db_path = Path("/home/neo/cogniwatch/data/cogniwatch.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT host, port, top_framework, confidence, timestamp
    FROM detection_results
    ORDER BY timestamp DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row['host']}:{row['port']} - {row['top_framework']} ({row['confidence']:.0%})")
```

---

## Analysis API

### Framework Heatmap
```python
from webui.api_analysis import AnalysisAPI

api = AnalysisAPI()
heatmap = api.get_heatmap('24h')

print(f"Total detections: {heatmap['total_detections']}")
print(f"Frameworks: {list(heatmap['frameworks'].keys())}")
```

### Detection Trends
```python
trends = api.get_trends('7d', 'detections')
for point in trends['data_points'][-5:]:
    print(f"{point['timestamp']}: {point['detection_count']} detections")
```

### Summary Statistics
```python
summary = api.get_summary('24h')
print(f"Unique hosts: {summary['statistics']['unique_hosts']}")
print(f"Avg confidence: {summary['statistics']['avg_confidence']:.2f}")
```

---

## Custom Detection Profiles

### High-Speed Scan (skip heavy layers)
```python
detector = IntegratedDetector(
    timeout=2.0,
    enable_layers=['http', 'api']  # Skip WebSocket, TLS, Telemetry
)
```

### Deep Analysis (all layers + longer timeout)
```python
detector = IntegratedDetector(
    timeout=10.0,
    enable_layers=['http', 'api', 'websocket', 'tls', 'telemetry']
)
```

### Framework-Specific Scan
```python
from api_analyzer import APIAnalyzer

analyzer = APIAnalyzer(timeout=3.0)
result = analyzer.probe_specific_framework("http://192.168.0.245:18789", "openclaw")
```

---

## Confidence Scoring

### Adjust Layer Weights
```python
from confidence_engine import ConfidenceEngine, DetectionLayer

engine = ConfidenceEngine()
engine.adjust_layer_weights({
    DetectionLayer.API_BEHAVIORAL: 2.0,  # Higher weight for API
    DetectionLayer.HTTP_FINGERPRINT: 1.0  # Lower weight for HTTP
})
```

### Set Custom Thresholds
```python
engine.set_threshold('very_high', 0.90)  # Require 90% for "very high"
engine.set_threshold('high', 0.75)       # Require 75% for "high"
```

---

## Export Results

### JSON Export
```python
result_dict = result.to_dict()
import json
with open('detection_result.json', 'w') as f:
    json.dump(result_dict, f, indent=2)
```

### CSV Export (for multiple detections)
```python
import csv

detections = [...]  # List of IntegratedDetectionResult

with open('detections.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['host', 'port', 'framework', 'confidence', 'quality'])
    for det in detections:
        writer.writerow([
            det.host, det.port,
            det.top_framework,
            f"{det.confidence:.2f}",
            det.detection_quality
        ])
```

---

## Troubleshooting

### Module Import Errors
```bash
# Ensure you're in the right directory
cd /home/neo/cogniwatch/scanner

# Add to Python path if needed
export PYTHONPATH=/home/neo/cogniwatch/scanner:$PYTHONPATH
```

### Connection Timeouts
```python
# Increase timeout
detector = IntegratedDetector(timeout=10.0)

# Check firewall rules
sudo ufw status | grep 18789
```

### Missing Dependencies
```bash
pip install requests beautifulsoup4 websocket-client
```

---

## Next Steps

1. **Run test suite:** `python3 test_advanced_detection.py`
2. **Check results:** Review `/tmp/vulcan_test_results_*.json`
3. **Integrate with WebUI:** Add analysis endpoints to dashboard
4. **Schedule scans:** Set up cron jobs for periodic detection
5. **Visualize data:** Build heatmap and trend charts

---

**📚 Full Documentation:** See `VULCAN_IMPLEMENTATION.md`  
**💡 Examples:** Run individual module scripts with `python3 <module>.py`  
**🔧 API Reference:** Each module has docstrings and inline documentation  

---

*Built with ❤️ by VULCAN - Making CogniWatch the "Shodan for AI Agents"*
