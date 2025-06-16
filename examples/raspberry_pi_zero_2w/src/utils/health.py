"""
System health monitoring and diagnostics
"""

import psutil
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from ..core.exceptions import HardwareError

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    temperature_celsius: Optional[float]
    uptime_seconds: float
    load_average: Tuple[float, float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int

@dataclass
class ProcessMetrics:
    """Process-specific metrics"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    num_threads: int
    num_fds: int
    status: str

class SystemHealth:
    """System health status and thresholds"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'temperature_warning': 70.0,
            'temperature_critical': 80.0
        }
        
        self.status = "healthy"
        self.alerts = []
        self.last_check = None
    
    def check_health(self, metrics: SystemMetrics) -> str:
        """Check system health based on metrics"""
        self.alerts.clear()
        self.last_check = time.time()
        
        # Check CPU
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            self.alerts.append(f"CRITICAL: CPU usage {metrics.cpu_percent:.1f}%")
            self.status = "critical"
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            self.alerts.append(f"WARNING: CPU usage {metrics.cpu_percent:.1f}%")
            if self.status == "healthy":
                self.status = "warning"
        
        # Check Memory
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            self.alerts.append(f"CRITICAL: Memory usage {metrics.memory_percent:.1f}%")
            self.status = "critical"
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            self.alerts.append(f"WARNING: Memory usage {metrics.memory_percent:.1f}%")
            if self.status == "healthy":
                self.status = "warning"
        
        # Check Disk
        if metrics.disk_usage_percent >= self.thresholds['disk_critical']:
            self.alerts.append(f"CRITICAL: Disk usage {metrics.disk_usage_percent:.1f}%")
            self.status = "critical"
        elif metrics.disk_usage_percent >= self.thresholds['disk_warning']:
            self.alerts.append(f"WARNING: Disk usage {metrics.disk_usage_percent:.1f}%")
            if self.status == "healthy":
                self.status = "warning"
        
        # Check Temperature
        if metrics.temperature_celsius:
            if metrics.temperature_celsius >= self.thresholds['temperature_critical']:
                self.alerts.append(f"CRITICAL: Temperature {metrics.temperature_celsius:.1f}°C")
                self.status = "critical"
            elif metrics.temperature_celsius >= self.thresholds['temperature_warning']:
                self.alerts.append(f"WARNING: Temperature {metrics.temperature_celsius:.1f}°C")
                if self.status == "healthy":
                    self.status = "warning"
        
        # If no alerts, system is healthy
        if not self.alerts:
            self.status = "healthy"
        
        return self.status

class HealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self, monitoring_interval: float = 30.0):
        """Initialize health monitor"""
        self.monitoring_interval = monitoring_interval
        self.health = SystemHealth()
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 100
        self.monitoring_enabled = False
        self.boot_time = psutil.boot_time()
        
        logger.info("Health monitor initialized")
    
    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi specific)"""
        try:
            # Try Raspberry Pi thermal zone
            thermal_file = Path('/sys/class/thermal/thermal_zone0/temp')
            if thermal_file.exists():
                with open(thermal_file, 'r') as f:
                    temp_millicelsius = int(f.read().strip())
                    return temp_millicelsius / 1000.0
            
            # Try vcgencmd (if available)
            import subprocess
            result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                if 'temp=' in temp_str:
                    temp_value = temp_str.split('=')[1].replace("'C", "")
                    return float(temp_value)
            
        except Exception as e:
            logger.debug(f"Could not read CPU temperature: {e}")
        
        return None
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Temperature
            temperature = self.get_cpu_temperature()
            
            # Uptime
            uptime_seconds = time.time() - self.boot_time
            
            # Load average
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # getloadavg not available on all platforms
                load_avg = (0.0, 0.0, 0.0)
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                temperature_celsius=temperature,
                uptime_seconds=uptime_seconds,
                load_average=load_avg
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise HardwareError(f"System metrics collection failed: {e}")
    
    def get_network_metrics(self) -> NetworkMetrics:
        """Get network interface metrics"""
        try:
            net_io = psutil.net_io_counters()
            
            return NetworkMetrics(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                errors_in=net_io.errin,
                errors_out=net_io.errout,
                drops_in=net_io.dropin,
                drops_out=net_io.dropout
            )
            
        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
            return NetworkMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    def get_process_metrics(self, pid: Optional[int] = None) -> ProcessMetrics:
        """Get metrics for current or specified process"""
        try:
            if pid is None:
                process = psutil.Process()
            else:
                process = psutil.Process(pid)
            
            # Get process info
            with process.oneshot():
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                num_threads = process.num_threads()
                
                try:
                    num_fds = process.num_fds()
                except (AttributeError, psutil.AccessDenied):
                    num_fds = 0
                
                return ProcessMetrics(
                    pid=process.pid,
                    name=process.name(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_rss_mb=memory_info.rss / (1024 * 1024),
                    num_threads=num_threads,
                    num_fds=num_fds,
                    status=process.status()
                )
                
        except Exception as e:
            logger.error(f"Failed to collect process metrics: {e}")
            raise HardwareError(f"Process metrics collection failed: {e}")
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            # Collect metrics
            system_metrics = self.get_system_metrics()
            network_metrics = self.get_network_metrics()
            process_metrics = self.get_process_metrics()
            
            # Check health status
            health_status = self.health.check_health(system_metrics)
            
            # Store metrics history
            self.metrics_history.append(system_metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            # Compile health report
            health_report = {
                'status': health_status,
                'timestamp': time.time(),
                'alerts': self.health.alerts.copy(),
                'system': system_metrics.to_dict(),
                'network': asdict(network_metrics),
                'process': asdict(process_metrics),
                'thresholds': self.health.thresholds.copy()
            }
            
            # Log health status
            if health_status == "critical":
                logger.error(f"System health CRITICAL: {', '.join(self.health.alerts)}")
            elif health_status == "warning":
                logger.warning(f"System health WARNING: {', '.join(self.health.alerts)}")
            else:
                logger.debug("System health OK")
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'timestamp': time.time(),
                'error': str(e),
                'alerts': [f"Health check failed: {e}"]
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary with trends"""
        if not self.metrics_history:
            return {'status': 'no_data', 'message': 'No metrics available'}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 readings
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_temp = None
        
        temps = [m.temperature_celsius for m in recent_metrics if m.temperature_celsius]
        if temps:
            avg_temp = sum(temps) / len(temps)
        
        # Calculate trends (simple slope)
        def calculate_trend(values):
            if len(values) < 2:
                return 0
            return (values[-1] - values[0]) / len(values)
        
        cpu_trend = calculate_trend([m.cpu_percent for m in recent_metrics])
        memory_trend = calculate_trend([m.memory_percent for m in recent_metrics])
        
        return {
            'status': self.health.status,
            'last_check': self.health.last_check,
            'metrics_count': len(self.metrics_history),
            'averages': {
                'cpu_percent': round(avg_cpu, 1),
                'memory_percent': round(avg_memory, 1),
                'temperature_celsius': round(avg_temp, 1) if avg_temp else None
            },
            'trends': {
                'cpu_trend': round(cpu_trend, 2),
                'memory_trend': round(memory_trend, 2)
            },
            'current_alerts': self.health.alerts.copy()
        }
    
    def save_metrics_to_file(self, filename: str):
        """Save metrics history to JSON file"""
        try:
            data = {
                'timestamp': time.time(),
                'metrics_count': len(self.metrics_history),
                'metrics': [m.to_dict() for m in self.metrics_history]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.metrics_history)} metrics to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save metrics to file: {e}")
    
    def load_metrics_from_file(self, filename: str):
        """Load metrics history from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.metrics_history = []
            for metric_data in data.get('metrics', []):
                metrics = SystemMetrics(**metric_data)
                self.metrics_history.append(metrics)
            
            logger.info(f"Loaded {len(self.metrics_history)} metrics from {filename}")
            
        except Exception as e:
            logger.error(f"Failed to load metrics from file: {e}")

def format_bytes(bytes_value: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"

if __name__ == "__main__":
    """Test health monitoring"""
    print("🏥 Testing Health Monitor")
    
    try:
        monitor = HealthMonitor()
        
        # Get system metrics
        metrics = monitor.get_system_metrics()
        print(f"CPU: {metrics.cpu_percent:.1f}%")
        print(f"Memory: {metrics.memory_percent:.1f}%")
        print(f"Disk: {metrics.disk_usage_percent:.1f}%")
        print(f"Temperature: {metrics.temperature_celsius}°C")
        
        # Perform health check
        health_report = monitor.check_system_health()
        print(f"Health Status: {health_report['status']}")
        
        if health_report['alerts']:
            print("Alerts:")
            for alert in health_report['alerts']:
                print(f"  - {alert}")
        
        # Get summary
        summary = monitor.get_health_summary()
        print(f"Health Summary: {summary}")
        
        print("✅ Health monitor test passed")
        
    except Exception as e:
        print(f"❌ Health monitor test failed: {e}")
        import traceback
        traceback.print_exc()
