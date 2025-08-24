import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Log directory setup
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Common logging configuration
def setup_logger(name, log_level=logging.INFO):
    """
    Configure a logger with file rotation and console output
    
    Args:
        name (str): Logger name (usually __name__)
        log_level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Format for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB per file, max 5 files)
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Monitoring configuration
class ServiceMonitor:
    """
    Monitor service health and performance metrics
    """
    def __init__(self, service_name):
        self.service_name = service_name
        self.logger = setup_logger(f"monitor.{service_name}")
        self.metrics = {
            'request_count': 0,
            'error_count': 0,
            'last_error': None,
            'last_success': None
        }
    
    def record_request(self):
        """Record a new request"""
        self.metrics['request_count'] += 1
    
    def record_error(self, error):
        """Record an error"""
        self.metrics['error_count'] += 1
        self.metrics['last_error'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(error)
        }
        self.logger.error(f"Service error: {error}")
    
    def record_success(self):
        """Record a successful operation"""
        self.metrics['last_success'] = datetime.utcnow().isoformat()
    
    def get_metrics(self):
        """Return current metrics"""
        return {
            **self.metrics,
            'success_rate': (
                1 - (self.metrics['error_count'] / self.metrics['request_count'])
            ) if self.metrics['request_count'] > 0 else 1.0
        }