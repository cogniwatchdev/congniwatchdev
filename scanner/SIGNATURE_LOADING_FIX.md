# Signature Loading Fix - Implementation Report

**Problem**: Cipher scanner reported "0 signatures loaded" even though `framework_signatures.json` (20KB) existed.

**Root Causes Identified**:
1. `advanced_detector.py` was passing the file path instead of directory to `SignatureLoader`
2. `SignatureLoader` only supported legacy individual JSON files, not the consolidated `framework_signatures.json`
3. `ConfidenceConfig` was missing required `base_confidence` and `max_confidence` fields

**Files Modified**:

### 1. `/home/neo/cogniwatch/scanner/advanced_detector.py`
- **Line ~431**: Changed from loading `framework_signatures.json` as a path to using the consolidated file directly
- Now passes the correct file path to `SignatureLoader`

### 2. `/home/neo/cogniwatch/scanner/signature_loader.py`
- **Added `ConfidenceConfig.base_confidence`** (default: 0.05) - starting confidence before signals
- **Added `ConfidenceConfig.max_confidence`** (default: 0.98) - maximum achievable confidence
- **Updated `SignatureLoader.__init__`**: Now accepts file or directory path
- **Added `_load_consolidated()`**: New method to load from consolidated JSON format
- **Added `_convert_to_signature()`**: Converts consolidated format to legacy `FrameworkSignature` objects
- **Updated `_load_signature_legacy()`**: Handles legacy individual JSON files with `api_endpoints` as dict
- **Updated `get_confidence_config()`**: Handles both dict and object formats

### 3. `/home/neo/cogniwatch/docker-compose.yml`
- **Added volume mount**: `./scanner:/cogniwatch/scanner:ro` to scanner service
- Ensures signatures are available in container for VPS deployment

**Test Results**:
```
✅ Loaded 6 frameworks from consolidated signature file
✅ Port index created with 7 entries
✅ API endpoints in correct format (list of dicts)
✅ All key frameworks detected: crewai, autogen studio, langgraph, agent-zero, picoclaw, zeroclaw
```

**Frameworks Loaded** (6 total):
1. CrewAI
2. AutoGen Studio
3. LangGraph
4. Agent-Zero
5. PicoClaw
6. ZeroClaw

**Backward Compatibility**: 
The `SignatureLoader` maintains support for legacy individual signature files in the `signatures/` directory. It will automatically use the consolidated file if present, falling back to loading individual files otherwise.

**Verification Commands**:
```bash
# Test signature loading
cd /home/neo/cogniwatch
python3 scanner/test_signature_loading.py

# Run detector
python3 scanner/advanced_detector.py
```

**Status**: ✅ COMPLETE - Scanner now reports "Total signatures loaded: 6" instead of 0.
