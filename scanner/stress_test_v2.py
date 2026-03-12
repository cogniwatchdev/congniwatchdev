#!/usr/bin/env python3
"""
CogniWatch Scanner Stress Testing Suite - FIXED VERSION
=========================================================

Mission: Stress test the scanner to ensure responsible scanning works under load.
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
    print("ERROR: Cannot import network_scanner.")
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
    status: str
    duration_sec: float
    metrics: Dict
    errors: List[str]
    recommendations: List[str]
    timestamp: str


class ResourceMonitor:
    """Monitor system resources during tests"""
    
    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.samples = []
        self.running = False
        self.monitor_thread = None
        
    def start(self):
        self.running = True
        self.samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
    def _monitor_loop(self):
        while self.running:
            sample = self._capture_sample()
            self.samples.append(sample)
            time.sleep(self.sample_interval)
            
    def _capture_sample(self) -> Dict:
        sample = {
            'timestamp': time.time(),
            'cpu_percent': None,
            'memory_mb': None,
        }
        
        if HAS_PSUTIL:
            try:
                process = psutil.Process(os.getpid())
                sample['cpu_percent'] = process.cpu_percent()
                mem_info = process.memory_info()
                sample['memory_mb'] = mem_info.rss / (1024 * 1024)
            except Exception as e:
                logger.debug(f"Error capturing resource sample: {e}")
                
        return sample
    
    def get_summary(self) -> Dict:
        if not self.samples:
            return {}
            
        cpu_samples = [s['cpu_percent'] for s in self.samples if s['cpu_percent'] is not None]
        memory_samples = [s['memory_mb'] for s in self.samples if s['memory_mb'] is not None]
        
        return {
            'cpu_percent_avg': sum(cpu_samples) / len(cpu_samples) if cpu_samples else None,
            'cpu_percent_max': max(cpu_samples) if cpu_samples else None,
            'memory_mb_avg': sum(memory_samples) / len(memory_samples) if memory_samples else None,
            'memory_mb_max': max(memory_samples) if memory_samples else None,
            'sample_count': len(self.samples)
        }


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
        
        start_time = time.time()
        
        # Test 1: Quick Performance Test
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: Quick Performance Benchmark")
        logger.info("=" * 60)
        self._test_quick_performance()
        
        # Test 2: Worker Count Comparison
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Worker Count Optimization")
        logger.info("=" * 60)
        self._test_worker_counts()
        
        # Test 3: Resource Usage
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Resource Usage")
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
        report = self._generate_report(total_duration)
        
        logger.info("\n" + "=" * 80)
        logger.info(f"STRESS TEST COMPLETE - Total: {total_duration:.1f}s")
        logger.info("=" * 80)
        
        return report
    
    def _test_quick_performance(self):
        """Test 1: Quick Performance"""
        test_name = "Quick Performance Benchmark"
        errors = []
        recommendations = []
        start_time = time.time()
        
        logger.info("Running quick scan (localhost, 50 workers)...")
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=1.0)
            perf_start = time.perf_counter()
            
            agents = scanner.scan_network(parallel=50)
            
            duration = time.perf_counter() - perf_start
            status = "PASS" if duration < 180 else "WARNING"
            
            if duration >= 180:
                recommendations.append("Quick scan exceeded 3min target")
                
            result = TestResult(
                test_name=test_name,
                status=status,
                duration_sec=duration,
                metrics={
                    'agents_found': len(agents),
                    'hosts_per_sec': 1.0 / duration if duration > 0 else 0,
                    'target_sec': 180
                },
                errors=errors,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
            
            logger.info(f"Duration: {duration:.2f}s - {status}")
            logger.info(f"Agents found: {len(agents)}")
            
        except Exception as e:
            errors.append(str(e))
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_sec=time.time() - start_time,
                metrics={},
                errors=errors,
                recommendations=["Fix scanner exception"],
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    def _test_worker_counts(self):
        """Test 2: Different worker counts"""
        test_name = "Worker Count Optimization"
        errors = []
        recommendations = []
        start_time = time.time()
        
        worker_results = []
        
        for workers in [10, 50, 100, 200]:
            try:
                scanner = NetworkScanner(network="127.0.0.1", timeout=0.5)
                perf_start = time.perf_counter()
                agents = scanner.scan_network(parallel=workers)
                duration = time.perf_counter() - perf_start
                
                worker_results.append({
                    'workers': workers,
                    'duration_sec': round(duration, 3),
                    'agents_found': len(agents)
                })
                
                logger.info(f"Workers={workers:3d}: {duration:6.3f}s, {len(agents)} agents")
                
            except Exception as e:
                errors.append(f"Worker count {workers} failed: {e}")
                worker_results.append({
                    'workers': workers,
                    'error': str(e)
                })
        
        # Find optimal
        valid_results = [r for r in worker_results if 'error' not in r]
        if valid_results:
            optimal = min(valid_results, key=lambda x: x['duration_sec'])
            recommendations.append(f"Optimal workers: {optimal['workers']} ({optimal['duration_sec']:.3f}s)")
        
        result = TestResult(
            test_name=test_name,
            status="PASS" if not errors else "WARNING",
            duration_sec=time.time() - start_time,
            metrics={'worker_comparison': worker_results},
            errors=errors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
    
    def _test_resource_usage(self):
        """Test 3: Resource Usage"""
        test_name = "Resource Usage Monitoring"
        errors = []
        recommendations = []
        start_time = time.time()
        
        monitor = ResourceMonitor(sample_interval=0.5)
        monitor.start()
        
        memory_start = None
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            memory_start = process.memory_info().rss / (1024 * 1024)
            logger.info(f"Initial memory: {memory_start:.1f} MB")
        
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=1.0)
            agents = scanner.scan_network(parallel=100)
            
            memory_end = None
            if HAS_PSUTIL:
                process = psutil.Process(os.getpid())
                memory_end = process.memory_info().rss / (1024 * 1024)
                logger.info(f"Final memory: {memory_end:.1f} MB")
            
            monitor.stop()
            resource_summary = monitor.get_summary()
            
            duration = time.time() - start_time
            
            # Check for issues
            cpu_max = resource_summary.get('cpu_percent_max', 0)
            if cpu_max and cpu_max > 80:
                errors.append(f"High CPU: {cpu_max:.1f}%")
                recommendations.append("Reduce parallelism")
                
            memory_delta = (memory_end - memory_start) if memory_start and memory_end else None
            if memory_delta and memory_delta > 500:
                errors.append(f"High memory growth: {memory_delta:.1f} MB")
                recommendations.append("Check for memory leaks")
            
            status = "PASS" if not errors else "WARNING"
            
            result = TestResult(
                test_name=test_name,
                status=status,
                duration_sec=duration,
                metrics={
                    'resource_summary': resource_summary,
                    'memory_start_mb': memory_start,
                    'memory_end_mb': memory_end,
                    'memory_delta_mb': memory_delta,
                    'agents_found': len(agents)
                },
                errors=errors,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
            
            logger.info(f"CPU max: {cpu_max}%")
            logger.info(f"Memory delta: {memory_delta} MB")
            
        except Exception as e:
            monitor.stop()
            errors.append(f"Resource test failed: {e}")
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_sec=time.time() - start_time,
                metrics={},
                errors=errors,
                recommendations=["Fix resource monitoring"],
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    def _test_error_handling(self):
        """Test 4: Error Handling"""
        test_name = "Error Handling"
        errors = []
        recommendations = []
        error_metrics = {}
        start_time = time.time()
        
        logger.info("Testing error handling...")
        
        # Test 1: Timeout
        logger.info("  Testing timeout handling...")
        error_metrics['timeout_test'] = {'tested': False, 'handled': False}
        try:
            scanner = NetworkScanner(network="192.0.2.1", timeout=0.1)
            start = time.time()
            agents = scanner.scan_network(parallel=5)
            duration = time.time() - start
            
            error_metrics['timeout_test'] = {'tested': True, 'handled': True, 'duration_sec': duration}
            logger.info(f"  Timeout test: {duration:.2f}s - Handled")
            
        except Exception as e:
            error_metrics['timeout_test'] = {'tested': True, 'handled': False, 'error': str(e)}
            errors.append(f"Timeout handling failed: {e}")
        
        # Test 2: Invalid port
        logger.info("  Testing invalid port...")
        error_metrics['invalid_port'] = {'tested': False, 'handled': False}
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=0.5)
            result = scanner.scan_port("127.0.0.1", 99999)
            
            error_metrics['invalid_port'] = {'tested': True, 'handled': True, 'result': result}
            logger.info(f"  Invalid port: Handled (result={result})")
            
        except Exception as e:
            error_metrics['invalid_port'] = {'tested': True, 'handled': False, 'error': str(e)}
            errors.append(f"Invalid port failed: {e}")
        
        # Test 3: High concurrency
        logger.info("  Testing high concurrency...")
        error_metrics['high_concurrency'] = {'tested': False, 'handled': False}
        try:
            scanner = NetworkScanner(network="127.0.0.1", timeout=0.2)
            agents = scanner.scan_network(parallel=500)
            
            error_metrics['high_concurrency'] = {'tested': True, 'handled': True, 'workers': 500}
            logger.info(f"  High concurrency: Handled 500 workers")
            
        except Exception as e:
            error_metrics['high_concurrency'] = {'tested': True, 'handled': False, 'error': str(e)}
            logger.warning(f"  High concurrency failed: {e}")
        
        handled = sum(1 for m in error_metrics.values() if m.get('handled'))
        tested = sum(1 for m in error_metrics.values() if m.get('tested'))
        
        status = "PASS" if handled == tested and tested > 0 else "WARNING"
        if handled < tested:
            recommendations.append("Improve error handling")
        
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_sec=time.time() - start_time,
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
        
        logger.info("Running 2 concurrent scans...")
        
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
                        'duration_sec': round(duration, 3),
                        'agents_found': len(agents),
                        'status': 'SUCCESS'
                    })
                
                logger.info(f"  Scan {scan_id}: {duration:.2f}s, {len(agents)} agents")
                
            except Exception as e:
                with lock:
                    scan_results.append({
                        'scan_id': scan_id,
                        'status': 'FAILED',
                        'error': str(e)
                    })
                logger.error(f"  Scan {scan_id} failed: {e}")
        
        threads = []
        for i in range(2):
            t = threading.Thread(target=run_scan, args=(i+1,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=300)
        
        successful = [r for r in scan_results if r.get('status') == 'SUCCESS']
        failed = [r for r in scan_results if r.get('status') == 'FAILED']
        
        if failed:
            errors.append(f"{len(failed)} scan(s) failed")
        
        status = "PASS" if not errors else "FAIL"
        
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_sec=time.time() - start_time,
            metrics={
                'concurrent_scans': scan_results,
                'successful_count': len(successful),
                'failed_count': len(failed)
            },
            errors=errors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
    
    def _generate_report(self, total_duration: float) -> Dict:
        """Generate report"""
        report_path = self.output_dir / "STRESS_TEST_REPORT.md"
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        
        report_lines = [
            "# CogniWatch Scanner Stress Test Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Target:** {self.target_network}",
            f"**Duration:** {total_duration:.1f}s",
            "",
            "## Summary",
            "",
            f"✅ Passed: {passed}",
            f"❌ Failed: {failed}",
            f"⚠️ Warnings: {warnings}",
            "",
            "## Test Results",
            ""
        ]
        
        for result in self.results:
            report_lines.extend([
                f"### {result.test_name}",
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
                for err in result.errors:
                    report_lines.append(f"❌ {err}")
                report_lines.append("")
            
            if result.recommendations:
                for rec in result.recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")
            
            report_lines.append("---")
        
        # Performance table
        report_lines.extend([
            "",
            "## Performance Benchmarks",
            "",
            "| Workers | Duration | Agents |",
            "|---------|----------|--------|"
        ])
        
        for result in self.results:
            if result.test_name == "Worker Count Optimization":
                for w in result.metrics.get('worker_comparison', []):
                    if 'error' not in w:
                        report_lines.append(
                            f"| {w['workers']} | {w['duration_sec']:.3f}s | {w['agents_found']} |"
                        )
        
        report_lines.append("")
        
        content = "\n".join(report_lines)
        with open(report_path, 'w') as f:
            f.write(content)
        
        logger.info(f"\n📄 Report: {report_path}")
        
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
    print("\n" + "=" * 80)
    print("COGNIWATCH SCANNER STRESS TEST")
    print("=" * 80)
    print("\n⚠️  LOCALHOST ONLY\n")
    
    tester = ScannerStressTester(
        target_network="127.0.0.1",
        output_dir="/home/neo/cogniwatch"
    )
    
    report = tester.run_all_tests()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Duration: {report['summary']['total_duration_sec']:.1f}s")
    print(f"\n📄 Report: {report['report_path']}")
    
    return 0 if report['summary']['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
