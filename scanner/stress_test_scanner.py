#!/usr/bin/env python3
"""
CogniWatch Scanner Stress Testing Suite
=========================================

Mission: Stress test the scanner to ensure responsible scanning works under load.

Test Scenarios:
1. Rate Limiting Validation
2. Performance Benchmarks  
3. Resource Usage Monitoring
4. Error Handling
5. Concurrent Scans

Safety: Test on LOCAL network only (localhost or 192.168.1.0/24)
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Add scanner directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from network_scanner import NetworkScanner, FRAMEWORK_FINGERPRINTS
except ImportError:
    print("ERROR: Cannot import network_scanner. Make sure you're in the scanner directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stress_test")

# Try to import psutil for resource monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available - some resource metrics will be skipped")


@dataclass
class TestResult:
    """Container for test results"""
    test_name: str
    status: str  # PASS, FAIL, WARNING
    duration_sec: float
    metrics: Dict
    errors: List[str]
    recommendations: List[str]
    timestamp: str


@dataclass
class PerformanceMetrics:
    """Performance metrics captured during test"""
    start_time: float
    end_time: float
    duration_sec: float
    hosts_scanned: int
    agents_found: int
    hosts_per_second: float
    cpu_time_user: float
    cpu_time_system: float
    memory_mb_start: Optional[float]
    memory_mb_end: Optional[float]
    memory_delta_mb: Optional[float]


class ResourceMonitor:
    """Monitor system resources during tests"""
    
    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.samples = []
        self.running = False
        self.monitor_thread = None
        
    def start(self):
        """Start monitoring in background"""
        self.running = True
        self.samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            sample = self._capture_sample()
            self.samples.append(sample)
            time.sleep(self.sample_interval)
            
    def _capture_sample(self) -> Dict:
        """Capture a single resource sample"""
        sample = {
            'timestamp': time.time(),
            'cpu_percent': None,
            'memory_percent': None,
            'memory_mb': None,
            'network_sent_mb': None,
            'network_recv_mb': None,
            'open_files': None,
            'connections': None
        }
        
        if HAS_PSUTIL:
            try:
                process = psutil.Process(os.getpid())
                
                # CPU
                sample['cpu_percent'] = process.cpu_percent()
                
                # Memory
                mem_info = process.memory_info()
                sample['memory_mb'] = mem_info.rss / (1024 * 1024)
                sample['memory_percent'] = process.memory_percent()
                
                # Network I/O
                net_io = psutil.net_io_counters()
                sample['network_sent_mb'] = net_io.bytes_sent / (1024 * 1024)
                sample['network_recv_mb'] = net_io.bytes_recv / (1024 * 1024)
                
                # File handles
                sample['open_files'] = len(process.open_files())
                
                # Connections
                sample['connections'] = len(process.connections())
                
            except Exception as e:
                logger.debug(f"Error capturing resource sample: {e}")
                
        return sample
    
    def get_summary(self) -> Dict:
        """Get summary statistics from collected samples"""
        if not self.samples:
            return {}
            
        cpu_samples = [s['cpu_percent'] for s in self.samples if s['cpu_percent'] is not None]
        memory_samples = [s['memory_mb'] for s in self.samples if s['memory_mb'] is not None]
        
        summary = {
            'cpu_percent_avg': sum(cpu_samples) / len(cpu_samples) if cpu_samples else None,
            'cpu_percent_max': max(cpu_samples) if cpu_samples else None,
            'memory_mb_avg': sum(memory_samples) / len(memory_samples) if memory_samples else None,
            'memory_mb_max': max(memory_samples) if memory_samples else None,
            'sample_count': len(self.samples)
        }
        
        # Check for high CPU
        if summary['cpu_percent_max'] and summary['cpu_percent_max'] > 80:
            summary['cpu_warning'] = "CPU exceeded 80% - consider reducing worker count"
            
        return summary


class RateLimitValidator:
    """Validate that scanner respects rate limits"""
    
    def __init__(self, max_rate: float = 5.0, min_delay_ms: float = 200.0):
        self.max_rate = max_rate  # requests per second
        self.min_delay_ms = min_delay_ms  # minimum delay between requests
        self.request_timestamps = []
        self.lock = threading.Lock()
        
    def log_request(self):
        """Log a request timestamp"""
        with self.lock:
            self.request_timestamps.append(time.time())
            
    def validate(self) -> Tuple[bool, Dict]:
        """
        Validate rate limiting compliance
        
        Returns:
            Tuple of (is_compliant, metrics_dict)
        """
        if len(self.request_timestamps) < 2:
            return True, {'message': 'Insufficient samples'}
            
        timestamps = sorted(self.request_timestamps)
        deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        min_delay = min(deltas)
        avg_delay = sum(deltas) / len(deltas)
        max_rate_observed = 1.0 / min_delay if min_delay > 0 else float('inf')
        
        # Check compliance
        rate_compliant = max_rate_observed <= self.max_rate
        delay_compliant = min_delay >= (self.min_delay_ms / 1000.0)
        
        metrics = {
            'total_requests': len(timestamps),
            'min_delay_sec': min_delay,
            'avg_delay_sec': avg_delay,
            'max_rate_observed': max_rate_observed,
            'rate_limit_max': self.max_rate,
            'min_delay_required_ms': self.min_delay_ms,
            'rate_compliant': rate_compliant,
            'delay_compliant': delay_compliant
        }
        
        return rate_compliant and delay_compliant, metrics


class ScannerStressTester:
    """Main stress testing orchestrator"""
    
    def __init__(self, target_network: str = "127.0.0.1", output_dir: str = "/home/neo/cogniwatch"):
        self.target_network = target_network
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        
    def run_all_tests(self) -> Dict:
        """Run complete stress test suite"""
        logger.info("=" * 80)
        logger.info("COGNIWATCH SCANNER STRESS TEST SUITE")
        logger.info("=" * 80)
        logger.info(f"Target: {self.target_network}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("")
        
        start_time = time.time()
        
        # Test 1: Rate Limiting Validation
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: Rate Limiting Validation")
        logger.info("=" * 60)
        self._test_rate_limiting()
        
        # Test 2: Performance Benchmarks
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Performance Benchmarks")
        logger.info("=" * 60)
        self._test_performance_benchmarks()
        
        # Test 3: Resource Usage
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Resource Usage Monitoring")
        logger.info("=" * 60)
        self._test_resource_usage()
        
        # Test 4: Error Handling
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Error Handling")
        logger.info("=" * 60)
        self._test_error_handling()
        
        # Test 5: Concurrent Scans
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Concurrent Scans")
        logger.info("=" * 60)
        self._test_concurrent_scans()
        
        total_duration = time.time() - start_time
        
        # Generate report
        report = self._generate_report(total_duration)
        
        logger.info("\n" + "=" * 80)
        logger.info(f"STRESS TEST COMPLETE - Total duration: {total_duration:.1f}s")
        logger.info("=" * 80)
        
        return report
    
    def _test_rate_limiting(self):
        """Test 1: Rate Limiting Validation"""
        test_name = "Rate Limiting Validation"
        errors = []
        recommendations = []
        start_time = time.time()
        
        # Create scanner with rate limiting
        scanner = NetworkScanner(network=self.target_network, timeout=0.5)
        
        # Monkey-patch to track requests
        validator = RateLimitValidator(max_rate=5.0, min_delay_ms=200.0)
        original_scan_port = scanner.scan_port
        
        def tracked_scan_port(host, port):
            validator.log_request()
            return original_scan_port(host, port)
        
        scanner.scan_port = tracked_scan_port
        
        # Run scan with moderate parallelism
        logger.info("Running scan with rate limit monitoring...")
        try:
            agents = scanner.scan_network(parallel=10)  # Low parallelism for rate test
            duration = time.time() - start_time
            
            # Validate rate limiting
            is_compliant, metrics = validator.validate()
            
            status = "PASS" if is_compliant else "FAIL"
            
            if not is_compliant:
                errors.append(f"Rate limit exceeded: {metrics.get('max_rate_observed', 'N/A')} req/sec")
                recommendations.append("Reduce max_workers or add request throttling")
                
            result = TestResult(
                test_name=test_name,
                status=status,
                duration_sec=duration,
                metrics=metrics,
                errors=errors,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
            
            logger.info(f"Status: {status}")
            logger.info(f"Total requests: {metrics.get('total_requests', 0)}")
            logger.info(f"Max observed rate: {metrics.get('max_rate_observed', 'N/A')} req/sec")
            logger.info(f"Min delay: {metrics.get('min_delay_sec', 'N/A')*1000:.1f}ms")
            
        except Exception as e:
            logger.error(f"Rate limiting test failed: {e}")
            errors.append(str(e))
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_sec=time.time() - start_time,
                metrics={},
                errors=errors,
                recommendations=["Fix exception handling in scanner"],
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    def _test_performance_benchmarks(self):
        """Test 2: Performance Benchmarks"""
        test_name = "Performance Benchmarks"
        errors = []
        recommendations = []
        start_time = time.time()
        
        benchmarks = {
            'quick_scan': {'ports': 'common', 'target_sec': 180, 'actual_sec': None},
            'standard_scan': {'ports': 'agent_ports', 'target_sec': 300, 'actual_sec': None},
            'deep_scan': {'ports': 'full_range', 'target_sec': 900, 'actual_sec': None}
        }
        
        # Quick scan - localhost only, common ports
        logger.info("\n📊 Quick Scan Test (localhost, common ports)")
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=1.0)
            perf_start = time.perf_counter()
            cpu_start = os.times()
            
            agents = scanner.scan_network(parallel=50)
            
            perf_end = time.perf_counter()
            cpu_end = os.times()
            
            duration = perf_end - perf_start
            benchmarks['quick_scan']['actual_sec'] = duration
            
            status = "PASS" if duration < 180 else "WARNING"
            if duration >= 180:
                recommendations.append("Quick scan exceeded 3min target - consider optimizing")
                
            logger.info(f"Duration: {duration:.1f}s (target: <180s) - {status}")
            logger.info(f"Agents found: {len(agents)}")
            
        except Exception as e:
            errors.append(f"Quick scan failed: {e}")
            logger.error(f"Quick scan error: {e}")
        
        # Test with different worker counts
        logger.info("\n📊 Testing different worker counts...")
        worker_results = []
        
        for workers in [10, 50, 100, 200]:
            try:
                scanner = NetworkScanner(network="127.0.0.1", timeout=0.5)
                perf_start = time.perf_counter()
                agents = scanner.scan_network(parallel=workers)
                duration = time.perf_counter() - perf_start
                
                worker_results.append({
                    'workers': workers,
                    'duration_sec': duration,
                    'agents_found': len(agents),
                    'hosts_per_sec': 1.0 / duration if duration > 0 else 0
                })
                
                logger.info(f"Workers={workers:3d}: {duration:6.2f}s, {len(agents)} agents")
                
            except Exception as e:
                logger.error(f"Worker count {workers} failed: {e}")
                worker_results.append({
                    'workers': workers,
                    'duration_sec': None,
                    'error': str(e)
                })
        
        # Determine optimal worker count
        if worker_results:
            valid_results = [r for r in worker_results if 'error' not in r]
            if valid_results:
                optimal = min(valid_results, key=lambda x: x['duration_sec'])
                recommendations.append(f"Optimal worker count: {optimal['workers']} ({optimal['duration_sec']:.1f}s)")
        
        duration = time.time() - start_time
        result = TestResult(
            test_name=test_name,
            status="PASS" if not errors else "FAIL",
            duration_sec=duration,
            metrics={
                'benchmarks': benchmarks,
                'worker_comparison': worker_results
            },
            errors=errors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
    
    def _test_resource_usage(self):
        """Test 3: Resource Usage Monitoring"""
        test_name = "Resource Usage Monitoring"
        errors = []
        recommendations = []
        start_time = time.time()
        
        # Start resource monitoring
        monitor = ResourceMonitor(sample_interval=0.5)
        monitor.start()
        
        logger.info("Running scan with resource monitoring...")
        
        try:
            # Get initial memory
            memory_start = None
            if HAS_PSUTIL:
                process = psutil.Process(os.getpid())
                memory_start = process.memory_info().rss / (1024 * 1024)
                logger.info(f"Initial memory: {memory_start:.1f} MB")
            
            # Run scan
            scanner = NetworkScanner(network="127.0.0.1", timeout=1.0)
            agents = scanner.scan_network(parallel=100)
            
            # Get final memory
            memory_end = None
            if HAS_PSUTIL:
                process = psutil.Process(os.getpid())
                memory_end = process.memory_info().rss / (1024 * 1024)
                logger.info(f"Final memory: {memory_end:.1f} MB")
            
            # Stop monitoring
            monitor.stop()
            resource_summary = monitor.get_summary()
            
            duration = time.time() - start_time
            
            # Check for resource issues
            if resource_summary.get('cpu_percent_max', 0) > 80:
                errors.append(f"High CPU usage: {resource_summary['cpu_percent_max']:.1f}%")
                recommendations.append("Reduce parallelism or scan rate")
                
            if memory_end and memory_start and (memory_end - memory_start) > 500:
                errors.append(f"High memory growth: {memory_end - memory_start:.1f} MB")
                recommendations.append("Check for memory leaks in scanner")
            
            status = "PASS" if not errors else "WARNING"
            
            metrics = {
                'resource_summary': resource_summary,
                'memory_start_mb': memory_start,
                'memory_end_mb': memory_end,
                'memory_delta_mb': (memory_end - memory_start) if memory_start and memory_end else None,
                'agents_found': len(agents)
            }
            
            logger.info(f"CPU avg: {resource_summary.get('cpu_percent_avg', 'N/A')}%")
            logger.info(f"CPU max: {resource_summary.get('cpu_percent_max', 'N/A')}%")
            logger.info(f"Memory delta: {metrics['memory_delta_mb']} MB")
            
            result = TestResult(
                test_name=test_name,
                status=status,
                duration_sec=duration,
                metrics=metrics,
                errors=errors,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
            
        except Exception as e:
            monitor.stop()
            errors.append(f"Resource test failed: {e}")
            logger.error(f"Resource test error: {e}")
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_sec=time.time() - start_time,
                metrics={},
                errors=errors,
                recommendations=["Improve error handling"],
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    def _test_error_handling(self):
        """Test 4: Error Handling"""
        test_name = "Error Handling"
        errors = []
        recommendations = []
        error_metrics = {
            'timeout_test': {'tested': False, 'handled': False},
            'unreachable_host': {'tested': False, 'handled': False},
            'invalid_port': {'tested': False, 'handled': False},
            'database_error': {'tested': False, 'handled': False}
        }
        start_time = time.time()
        
        logger.info("Testing error handling scenarios...")
        
        # Test 1: Timeout behavior
        logger.info("\n  Testing timeout handling...")
        try:
            scanner = NetworkScanner(network="192.0.2.1", timeout=0.1)  # Non-routable IP
            start = time.time()
            agents = scanner.scan_network(parallel=5)
            duration = time.time() - start
            
            error_metrics['timeout_test']['tested'] = True
            error_metrics['timeout_test']['handled'] = True
            error_metrics['timeout_test']['duration_sec'] = duration
            logger.info(f"  Timeout test: {duration:.2f}s - Handled gracefully")
            
        except Exception as e:
            error_metrics['timeout_test']['tested'] = True
            error_metrics['timeout_test']['handled'] = False
            error_metrics['timeout_test']['error'] = str(e)
            errors.append(f"Timeout handling failed: {e}")
            logger.error(f"  Timeout test failed: {e}")
        
        # Test 2: Invalid port range
        logger.info("\n  Testing invalid port handling...")
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=0.5)
            # Try to scan with crazy port numbers
            result = scanner.scan_port("127.0.0.1", 99999)
            
            error_metrics['invalid_port']['tested'] = True
            error_metrics['invalid_port']['handled'] = True
            logger.info(f"  Invalid port test: Handled (result={result})")
            
        except Exception as e:
            error_metrics['invalid_port']['tested'] = True
            error_metrics['invalid_port']['handled'] = False
            error_metrics['invalid_port']['error'] = str(e)
            errors.append(f"Invalid port handling failed: {e}")
            logger.error(f"  Invalid port test failed: {e}")
        
        # Test 3: High concurrency stress
        logger.info("\n  Testing high concurrency...")
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=0.2)
            agents = scanner.scan_network(parallel=500)  # Very high parallelism
            
            error_metrics['high_concurrency']['tested'] = True
            error_metrics['high_concurrency']['handled'] = True
            logger.info(f"  High concurrency test: Handled 500 workers")
            
        except Exception as e:
            error_metrics['high_concurrency']['tested'] = True
            error_metrics['high_concurrency']['handled'] = False
            error_metrics['high_concurrency']['error'] = str(e)
            logger.warning(f"  High concurrency test failed: {e}")
        
        # Assess overall error handling
        handled_count = sum(1 for m in error_metrics.values() if m.get('handled', False))
        tested_count = sum(1 for m in error_metrics.values() if m.get('tested', False))
        
        status = "PASS" if handled_count == tested_count and tested_count > 0 else "WARNING"
        
        if handled_count < tested_count:
            recommendations.append("Improve error handling for failed scenarios")
        
        duration = time.time() - start_time
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_sec=duration,
            metrics={'error_scenarios': error_metrics},
            errors=errors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
    
    def _test_concurrent_scans(self):
        """Test 5: Concurrent Scans"""
        test_name = "Concurrent Scans"
        errors = []
        recommendations = []
        start_time = time.time()
        
        logger.info("Testing concurrent scan execution...")
        
        scan_results = []
        lock = threading.Lock()
        
        def run_scan(scan_id: int):
            try:
                scanner = NetworkScanner(network="127.0.0.1", timeout=0.5)
                start = time.time()
                agents = scanner.scan_network(parallel=50)
                duration = time.time() - start
                
                with lock:
                    scan_results.append({
                        'scan_id': scan_id,
                        'duration_sec': duration,
                        'agents_found': len(agents),
                        'status': 'SUCCESS',
                        'timestamp': datetime.now().isoformat()
                    })
                
                logger.info(f"  Scan {scan_id} completed: {duration:.2f}s, {len(agents)} agents")
                
            except Exception as e:
                with lock:
                    scan_results.append({
                        'scan_id': scan_id,
                        'status': 'FAILED',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                logger.error(f"  Scan {scan_id} failed: {e}")
        
        # Run 2 concurrent scans
        logger.info("\n  Running 2 concurrent scans...")
        threads = []
        for i in range(2):
            t = threading.Thread(target=run_scan, args=(i+1,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=300)
        
        # Check for race conditions or issues
        successful_scans = [r for r in scan_results if r['status'] == 'SUCCESS']
        failed_scans = [r for r in scan_results if r['status'] == 'FAILED']
        
        if failed_scans:
            errors.append(f"{len(failed_scans)} scan(s) failed")
            for failure in failed_scans:
                errors.append(f"  Scan {failure['scan_id']}: {failure.get('error', 'Unknown error')}")
        
        # Check for result interleaving (basic check)
        if len(successful_scans) == 2:
            durations = [s['duration_sec'] for s in successful_scans]
            if max(durations) - min(durations) > 10:
                recommendations.append(
                    f"Large duration variance ({max(durations):.1f}s vs {min(durations):.1f}s) - "
                    "possible resource contention"
                )
        
        status = "PASS" if not errors else "FAIL"
        
        duration = time.time() - start_time
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_sec=duration,
            metrics={
                'concurrent_scans': scan_results,
                'successful_count': len(successful_scans),
                'failed_count': len(failed_scans)
            },
            errors=errors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
    
    def _generate_report(self, total_duration: float) -> Dict:
        """Generate comprehensive stress test report"""
        report_path = self.output_dir / "STRESS_TEST_REPORT.md"
        
        # Compile results
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        
        # Build report
        report_lines = [
            "# CogniWatch Scanner Stress Test Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Target Network:** {self.target_network}",
            f"**Total Duration:** {total_duration:.1f}s",
            "",
            "## Executive Summary",
            "",
            f"✅ **Passed:** {passed}",
            f"❌ **Failed:** {failed}",
            f"⚠️ **Warnings:** {warnings}",
            "",
            "## Test Results",
            ""
        ]
        
        # Add detailed results
        for result in self.results:
            report_lines.extend([
                f"### {result.test_name}",
                "",
                f"**Status:** {result.status}",
                f"**Duration:** {result.duration_sec:.2f}s",
                ""
            ])
            
            if result.metrics:
                report_lines.append("**Metrics:**")
                report_lines.append("```json")
                report_lines.append(json.dumps(result.metrics, indent=2, default=str))
                report_lines.append("```")
                report_lines.append("")
            
            if result.errors:
                report_lines.append("**Errors:**")
                for error in result.errors:
                    report_lines.append(f"- ❌ {error}")
                report_lines.append("")
            
            if result.recommendations:
                report_lines.append("**Recommendations:**")
                for rec in result.recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        # Add performance benchmarks table
        report_lines.extend([
            "## Performance Benchmarks Summary",
            "",
            "| Test Type | Target | Actual | Status |",
            "|-----------|--------|--------|--------|"
        ])
        
        for result in self.results:
            if result.test_name == "Performance Benchmarks":
                workers = result.metrics.get('worker_comparison', [])
                for w in workers:
                    if 'error' not in w:
                        status = "✅" if w['duration_sec'] < 180 else "⚠️"
                        report_lines.append(
                            f"| {w['workers']} workers | - | {w['duration_sec']:.2f}s | {status} |"
                        )
        
        report_lines.append("")
        
        # Add recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        
        if all_recommendations:
            report_lines.extend([
                "## Tuning Recommendations",
                "",
            ])
            for i, rec in enumerate(set(all_recommendations), 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        # Write report
        report_content = "\n".join(report_lines)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"\n📄 Report saved to: {report_path}")
        
        # Return report dict
        return {
            'summary': {
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'total_duration_sec': total_duration
            },
            'results': [asdict(r) for r in self.results],
            'report_path': str(report_path)
        }


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("COGNIWATCH SCANNER STRESS TESTING SUITE")
    print("=" * 80)
    print("\n⚠️  SAFETY: Testing on LOCALHOST only")
    print("=" * 80 + "\n")
    
    # Create stress tester
    tester = ScannerStressTester(
        target_network="127.0.0.1",
        output_dir="/home/neo/cogniwatch"
    )
    
    # Run all tests
    report = tester.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {report['summary']['passed']}")
    print(f"Tests Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Total Duration: {report['summary']['total_duration_sec']:.1f}s")
    print(f"\n📄 Full report: {report['report_path']}")
    print("=" * 80 + "\n")
    
    return 0 if report['summary']['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
