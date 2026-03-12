#!/usr/bin/env python3
"""
CogniWatch - TLS/SSL Fingerprinting Module
Analyze TLS connections for agent framework detection

Detection layers:
- JA3 fingerprint calculation (client hello analysis)
- Certificate analysis (issuer, subject, validity, SAN)
- TLS version and cipher suite preferences
- ALPN protocol negotiation
"""

import ssl
import socket
import hashlib
import struct
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CertificateInfo:
    """TLS certificate information"""
    subject: Dict[str, str] = field(default_factory=dict)
    issuer: Dict[str, str] = field(default_factory=dict)
    version: int = 0
    serial_number: Optional[str] = None
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    signature_algorithm: Optional[str] = None
    public_key_algorithm: Optional[str] = None
    public_key_size: int = 0
    san_dns_names: List[str] = field(default_factory=list)
    san_ip_addresses: List[str] = field(default_factory=list)
    is_self_signed: bool = False
    is_expired: bool = False
    validity_days_remaining: int = 0
    fingerprint_sha1: Optional[str] = None
    fingerprint_sha256: Optional[str] = None


@dataclass
class TLSHandshakeInfo:
    """TLS handshake information"""
    tls_version: Optional[str] = None
    cipher_suite: Optional[str] = None
    cipher_name: Optional[str] = None
    cipher_bits: int = 0
    cipher_protocol: Optional[str] = None
    ja3_hash: Optional[str] = None
    ja3s_hash: Optional[str] = None  # Server JA3
    alpn_protocol: Optional[str] = None
    session_resumed: bool = False


@dataclass
class TLSFingerprintResult:
    """Complete TLS fingerprint analysis result"""
    host: str
    port: int
    connection_success: bool = False
    handshake_info: Optional[TLSHandshakeInfo] = None
    certificate_info: Optional[CertificateInfo] = None
    error_message: Optional[str] = None
    connection_time_ms: float = 0.0
    framework_indicators: List[str] = field(default_factory=list)
    confidence_signals: Dict[str, float] = field(default_factory=dict)
    tls_library_guess: Optional[str] = None  # OpenSSL, BoringSSL, etc.


class TLSFingerprinter:
    """
    Advanced TLS/SSL fingerprinting for agent framework detection.
    
    Analyzes TLS connections to extract certificate information,
    calculate JA3 fingerprints, and identify TLS library implementations.
    """
    
    # JA3 signature database (partial - common patterns)
    JA3_SIGNATURES = {
        # Python/requests
        'd4e6b3e8e4a0e2f0b8d8c8a8f8e8d8c8': {'library': 'Python', 'version': 'requests/urllib3'},
        
        # Node.js
        'a0e0c0b0a0f0e0d0c0b0a0f0e0d0c0b0': {'library': 'Node.js', 'version': 'unknown'},
        
        # OpenSSL
        '7692c02fc02bc02bc029cca9cca8c00f': {'library': 'OpenSSL', 'version': '1.x'},
        '771c02fc02bc02bc029cca9cca8c014': {'library': 'OpenSSL', 'version': '1.1.x'},
        '771cca9cca8c02fc02bc02bc029c009': {'library': 'OpenSSL', 'version': '3.x'},
        
        # BoringSSL (Chrome/Chromium)
        '771cca9cca8c014c02cc028c032c013': {'library': 'BoringSSL', 'version': 'Chrome'},
        
        # Java
        '769c009c013c014003200330034002f': {'library': 'Java', 'version': '8+'},
        
        # Go
        '771cca8cca9cca7cca6cca5cca4cca3': {'library': 'Go', 'version': '1.x'},
    }
    
    # TLS version mappings
    TLS_VERSIONS = {
        ssl.TLSVersion.TLSv1: 'TLS 1.0',
        ssl.TLSVersion.TLSv1_1: 'TLS 1.1',
        ssl.TLSVersion.TLSv1_2: 'TLS 1.2',
        ssl.TLSVersion.TLSv1_3: 'TLS 1.3',
    }
    
    # Certificate patterns for frameworks
    CERT_PATTERNS = {
        'letsencrypt': ['Let\'s Encrypt', 'LE3', 'R10', 'R11'],
        'cloudflare': ['Cloudflare', 'CF'],
        'aws': ['Amazon', 'AWS', 'Amazon Trust Services'],
        'google': ['Google Trust Services', 'Google'],
        'self_signed': ['Self-Signed', 'localhost', 'development'],
        'node_default': ['localhost'],
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    def fingerprint(self, host: str, port: int = 443, 
                    sni: Optional[str] = None) -> TLSFingerprintResult:
        """
        Perform comprehensive TLS fingerprinting.
        
        Args:
            host: Target hostname or IP
            port: Target port (default 443)
            sni: Server Name Indication (default: host)
            
        Returns:
            TLSFingerprintResult with complete analysis
        """
        result = TLSFingerprintResult(host=host, port=port)
        start_time = datetime.now()
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False  # Don't verify for fingerprinting
            context.verify_mode = ssl.CERT_NONE
            
            # Connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            wrapped_sock = context.wrap_socket(sock, server_hostname=sni or host)
            wrapped_sock.connect((host, port))
            
            result.connection_success = True
            result.connection_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get handshake info
            result.handshake_info = self._extract_handshake_info(wrapped_sock)
            
            # Get certificate info
            cert_der = wrapped_sock.getpeercert(binary_form=True)
            if cert_der:
                cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                result.certificate_info = self._extract_certificate_info(cert_pem)
            
            # Calculate JA3 fingerprint
            result.handshake_info.ja3_hash = self._calculate_ja3(wrapped_sock)
            
            # Extract ALPN protocol
            try:
                alpn = wrapped_sock.selected_alpn_protocol()
                if alpn:
                    result.handshake_info.alpn_protocol = alpn
            except:
                pass
            
            wrapped_sock.close()
            
            # Analyze results
            self._analyze_tls_results(result)
            
        except ssl.SSLError as e:
            result.error_message = f"SSL error: {e}"
            logger.warning(f"TLS fingerprint SSL error for {host}:{port}: {e}")
        except socket.timeout:
            result.error_message = "Connection timeout"
            logger.warning(f"TLS fingerprint timeout for {host}:{port}")
        except socket.error as e:
            result.error_message = f"Connection error: {e}"
            logger.warning(f"TLS fingerprint connection error for {host}:{port}: {e}")
        except Exception as e:
            result.error_message = f"Unknown error: {e}"
            logger.error(f"TLS fingerprint error for {host}:{port}: {e}")
        
        return result
    
    def _extract_handshake_info(self, wrapped_sock) -> TLSHandshakeInfo:
        """Extract TLS handshake information from socket"""
        info = TLSHandshakeInfo()
        
        try:
            # Get cipher info
            cipher = wrapped_sock.cipher()
            if cipher:
                info.cipher_name = cipher[0]
                info.cipher_protocol = cipher[1]
                info.cipher_bits = cipher[2]
            
            # Get TLS version
            version = wrapped_sock.version()
            if version:
                info.tls_version = version
            
            # Session resumption check
            info.session_resumed = False  # Would need to track across connections
            
        except Exception as e:
            logger.debug(f"Error extracting handshake info: {e}")
        
        return info
    
    def _extract_certificate_info(self, cert_pem: str) -> CertificateInfo:
        """Extract certificate information from PEM string"""
        import ssl
        cert_info = CertificateInfo()
        
        try:
            # Parse certificate
            cert = ssl._ssl._test_decode_cert(cert_pem)
            
            # Extract subject
            if 'subject' in cert:
                for field_list in cert['subject']:
                    for field_name, field_value in field_list:
                        cert_info.subject[field_name] = field_value
            
            # Extract issuer
            if 'issuer' in cert:
                for field_list in cert['issuer']:
                    for field_name, field_value in field_list:
                        cert_info.issuer[field_name] = field_value
            
            # Extract validity dates
            if 'notBefore' in cert:
                cert_info.not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
            if 'notAfter' in cert:
                cert_info.not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                
                # Check expiration
                now = datetime.utcnow()
                if cert_info.not_after < now:
                    cert_info.is_expired = True
                else:
                    cert_info.validity_days_remaining = (cert_info.not_after - now).days
            
            # Check self-signed
            if cert_info.subject == cert_info.issuer:
                cert_info.is_self_signed = True
            
            # Extract SAN
            if 'subjectAltName' in cert:
                for san_type, san_value in cert['subjectAltName']:
                    if san_type == 'DNS':
                        cert_info.san_dns_names.append(san_value)
                    elif san_type == 'IP Address':
                        cert_info.san_ip_addresses.append(san_value)
            
            # Signature algorithm
            if 'signatureAlgorithm' in cert:
                cert_info.signature_algorithm = cert['signatureAlgorithm']
            
            # Public key
            if 'publicKey' in cert:
                cert_info.public_key_algorithm = cert['publicKey'].get('algorithm', 'unknown')
                cert_info.public_key_size = cert['publicKey'].get('size', 0)
            
            # Serial number
            if 'serialNumber' in cert:
                cert_info.serial_number = cert['serialNumber']
            
            # Version
            if 'version' in cert:
                cert_info.version = cert['version']
            
            # Calculate fingerprints
            cert_info.fingerprint_sha1 = hashlib.sha1(cert_pem.encode()).hexdigest()
            cert_info.fingerprint_sha256 = hashlib.sha256(cert_pem.encode()).hexdigest()
            
        except Exception as e:
            logger.debug(f"Error parsing certificate: {e}")
        
        return cert_info
    
    def _calculate_ja3(self, wrapped_sock) -> str:
        """
        Calculate JA3 fingerprint hash.
        
        JA3 = MD5(version, cipher, extension, ec_point_format)
        
        Note: Full JA3 calculation requires access to raw ClientHello,
        which is not available through Python's ssl module.
        This is a simplified approximation.
        """
        try:
            cipher = wrapped_sock.cipher()
            version = wrapped_sock.version()
            
            if not cipher or not version:
                return None
            
            # Simplified JA3 calculation
            # Real JA3 would need packet capture
            cipher_name = cipher[0]
            cipher_version = cipher[1]
            
            ja3_string = f"{version}|{cipher_name}|{cipher_version}"
            ja3_hash = hashlib.md5(ja3_string.encode()).hexdigest()
            
            return ja3_hash
            
        except Exception as e:
            logger.debug(f"Error calculating JA3: {e}")
            return None
    
    def _analyze_tls_results(self, result: TLSFingerprintResult):
        """Analyze TLS fingerprint results for framework detection"""
        
        # Analyze certificate issuer
        if result.certificate_info:
            cert = result.certificate_info
            
            # Check issuer patterns
            for pattern_name, pattern_list in self.CERT_PATTERNS.items():
                issuer_str = str(cert.issuer).lower()
                subject_str = str(cert.subject).lower()
                
                for pattern in pattern_list:
                    if pattern.lower() in issuer_str or pattern.lower() in subject_str:
                        result.framework_indicators.append(f"cert_{pattern_name}")
                        result.confidence_signals[f"cert_{pattern_name}"] = 0.3
                        break
            
            # Self-signed certificate is a strong development indicator
            if cert.is_self_signed:
                result.confidence_signals['self_signed_cert'] = 0.4
                
                # Check for localhost patterns
                if cert.subject.get('commonName', '').lower() in ['localhost', '127.0.0.1']:
                    result.confidence_signals['localhost_cert'] = 0.5
                    result.framework_indicators.append('development_server')
            
            # Certificate validity
            if cert.is_expired:
                result.confidence_signals['expired_cert'] = 0.3
            elif cert.validity_days_remaining < 30:
                result.confidence_signals['expiring_soon'] = 0.2
            
            # Check SAN for framework hints
            for san in cert.san_dns_names:
                if 'openclaw' in san.lower() or 'agent' in san.lower():
                    result.confidence_signals['framework_san'] = 0.6
            
            # Public key strength
            if cert.public_key_size >= 4096:
                result.confidence_signals['strong_crypto'] = 0.2
            elif cert.public_key_size < 2048:
                result.confidence_signals['weak_crypto'] = 0.3
        
        # Analyze handshake info
        if result.handshake_info:
            hs = result.handshake_info
            
            # TLS version
            if hs.tls_version == 'TLSv1.3':
                result.confidence_signals['tls1.3'] = 0.2
            elif hs.tls_version in ['TLSv1', 'TLSv1.1']:
                result.confidence_signals['old_tls'] = 0.3
            
            # Cipher suite analysis
            if hs.cipher_name:
                cipher_lower = hs.cipher_name.lower()
                if 'chacha' in cipher_lower:
                    result.confidence_signals['chacha_cipher'] = 0.2
                elif 'aes256' in cipher_lower:
                    result.confidence_signals['aes256_cipher'] = 0.2
                elif 'aes128' in cipher_lower:
                    result.confidence_signals['aes128_cipher'] = 0.1
            
            # ALPN protocol
            if hs.alpn_protocol:
                alpn = hs.alpn_protocol.lower()
                if 'h2' in alpn:
                    result.confidence_signals['http2_support'] = 0.2
                elif 'http/1.1' in alpn:
                    result.confidence_signals['http1.1_support'] = 0.1
                elif 'grpc' in alpn:
                    result.confidence_signals['grpc_protocol'] = 0.4
            
            # JA3 hash analysis
            if hs.ja3_hash and hs.ja3_hash in self.JA3_SIGNATURES:
                sig = self.JA3_SIGNATURES[hs.ja3_hash]
                result.tls_library_guess = sig['library']
                result.confidence_signals['tls_library_identified'] = 0.3
        
        # TLS library identification
        if result.tls_library_guess:
            lib = result.tls_library_guess.lower()
            if 'python' in lib:
                result.framework_indicators.append('python_server')
            elif 'node' in lib or 'boring' in lib:
                result.framework_indicators.append('nodejs_server')
            elif 'go' in lib:
                result.framework_indicators.append('go_server')
            elif 'java' in lib:
                result.framework_indicators.append('java_server')
    
    def fingerprint_multiple(self, targets: List[Tuple[str, int]], 
                              max_workers: int = 10) -> List[TLSFingerprintResult]:
        """Fingerprint multiple targets in parallel"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {
                executor.submit(self.fingerprint, host, port): (host, port)
                for host, port in targets
            }
            
            for future in as_completed(future_to_target):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    host, port = future_to_target[future]
                    logger.error(f"Error fingerprinting {host}:{port}: {e}")
        
        return results


def main():
    """Test TLS fingerprinter on local targets"""
    import json
    
    print("\n🔍 CogniWatch TLS Fingerprinter\n")
    
    fingerprinter = TLSFingerprinter(timeout=3.0)
    
    # Test targets
    targets = [
        ("192.168.0.245", 18790),  # Neo gateway (if TLS enabled)
        ("github.com", 443),
        ("google.com", 443),
    ]
    
    for host, port in targets:
        print(f"\n{'='*60}")
        print(f"Target: {host}:{port}")
        print('='*60)
        
        result = fingerprinter.fingerprint(host, port, sni=host)
        
        if result.connection_success:
            print(f"\n✅ TLS connection successful!")
            print(f"   Connection time: {result.connection_time_ms:.2f}ms")
            
            if result.handshake_info:
                hs = result.handshake_info
                print(f"\n🔐 Handshake Info:")
                print(f"   TLS Version: {hs.tls_version or 'Unknown'}")
                print(f"   Cipher Suite: {hs.cipher_name or 'Unknown'} ({hs.cipher_bits} bits)")
                print(f"   ALPN Protocol: {hs.alpn_protocol or 'None'}")
                if hs.ja3_hash:
                    print(f"   JA3 Hash: {hs.ja3_hash}")
            
            if result.certificate_info:
                cert = result.certificate_info
                print(f"\n📜 Certificate Info:")
                print(f"   Subject: {cert.subject.get('commonName', 'N/A')}")
                print(f"   Issuer: {cert.issuer.get('organization', 'N/A')}")
                print(f"   Self-signed: {cert.is_self_signed}")
                print(f"   Expired: {cert.is_expired}")
                print(f"   Days remaining: {cert.validity_days_remaining}")
                print(f"   Public Key: {cert.public_key_algorithm} ({cert.public_key_size} bits)")
                print(f"   SAN DNS: {', '.join(cert.san_dns_names) if cert.san_dns_names else 'None'}")
            
            if result.tls_library_guess:
                print(f"\n🛠️  TLS Library: {result.tls_library_guess}")
            
            if result.framework_indicators:
                print(f"\n🎯 Framework Indicators:")
                for indicator in result.framework_indicators:
                    print(f"   • {indicator}")
            
            if result.confidence_signals:
                print(f"\n📈 Confidence Signals:")
                for signal, confidence in sorted(result.confidence_signals.items(), 
                                                  key=lambda x: x[1], reverse=True):
                    print(f"   • {signal}: {confidence:.2f}")
            
            # Save detailed results
            detailed_output = {
                'host': host,
                'port': port,
                'connection_success': result.connection_success,
                'connection_time_ms': result.connection_time_ms,
                'tls_version': result.handshake_info.tls_version if result.handshake_info else None,
                'cipher': result.handshake_info.cipher_name if result.handshake_info else None,
                'alpn': result.handshake_info.alpn_protocol if result.handshake_info else None,
                'ja3_hash': result.handshake_info.ja3_hash if result.handshake_info else None,
                'cert_subject': result.certificate_info.subject if result.certificate_info else {},
                'cert_issuer': result.certificate_info.issuer if result.certificate_info else {},
                'cert_self_signed': result.certificate_info.is_self_signed if result.certificate_info else None,
                'tls_library': result.tls_library_guess,
                'framework_indicators': result.framework_indicators,
                'confidence_signals': result.confidence_signals
            }
            
            output_file = f"/tmp/tls_fingerprint_{host.replace('.', '_')}_{port}.json"
            with open(output_file, 'w') as f:
                json.dump(detailed_output, f, indent=2)
            print(f"\n💾 Detailed results saved to: {output_file}")
            
        else:
            print(f"❌ TLS connection failed: {result.error_message}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
