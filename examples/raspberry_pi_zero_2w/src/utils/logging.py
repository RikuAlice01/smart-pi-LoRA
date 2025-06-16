"""
Enhanced logging configuration with structured logging and performance monitoring
"""

import logging
import logging.handlers
import sys
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    def filter(self, record):
        """Add performance metrics to record"""
        record.uptime = time.time() - self.start_time
        return True

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_log_size: int = 10,
    backup_count: int = 5,
    console_logging: bool = True,
    file_logging: bool = True,
    structured_logging: bool = False,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path
        max_log_size: Maximum log file size in MB
        backup_count: Number of backup log files to keep
        console_logging: Enable console logging
        file_logging: Enable file logging
        structured_logging: Use structured JSON logging
        log_format: Custom log format string
    
    Returns:
        Configured root logger
    """
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    if structured_logging:
        formatter = StructuredFormatter()
    else:
        if log_format is None:
            log_format = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '[%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
            )
        formatter = logging.Formatter(log_format)
    
    # Add performance filter
    perf_filter = PerformanceFilter()
    
    # Console handler
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(perf_filter)
        
        # Use different level for console if needed
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_logging and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_log_size * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        file_handler.setFormatter(formatter)
        file_handler.addFilter(perf_filter)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    
    # Add system info to first log
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Console logging: {console_logging}")
    logger.info(f"File logging: {file_logging} ({'enabled' if log_file else 'no file specified'})")
    logger.info(f"Structured logging: {structured_logging}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger with consistent configuration"""
    return logging.getLogger(name)

class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)

class TimingLogger:
    """Context manager for timing operations"""
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        duration = end_time - self.start_time
        
        if exc_type is None:
            self.logger.log(self.level, f"Completed {self.operation} in {duration:.3f}s")
        else:
            self.logger.error(f"Failed {self.operation} after {duration:.3f}s: {exc_val}")

def log_function_calls(logger: logging.Logger, level: int = logging.DEBUG):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.log(level, f"Calling {func_name}")
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.log(level, f"Completed {func_name} in {duration:.3f}s")
                return result
            except Exception as e:
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.error(f"Failed {func_name} after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

if __name__ == "__main__":
    """Test logging configuration"""
    print("📝 Testing Logging Configuration")
    
    # Test basic logging
    setup_logging(
        log_level="DEBUG",
        log_file="test_log.log",
        console_logging=True,
        file_logging=True,
        structured_logging=False
    )
    
    logger = get_logger(__name__)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test context logging
    with LogContext(logger, device_id="TEST_001", operation="test"):
        logger.info("Message with context")
    
    # Test timing
    with TimingLogger(logger, "test operation"):
        time.sleep(0.1)
    
    # Test structured logging
    print("\nTesting structured logging:")
    setup_logging(
        log_level="INFO",
        console_logging=True,
        file_logging=False,
        structured_logging=True
    )
    
    logger2 = get_logger("structured_test")
    logger2.info("Structured log message", extra={"device_id": "TEST_002", "sensor": "temperature"})
    
    print("✅ Logging tests completed")
