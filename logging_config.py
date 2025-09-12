import logging
from logging.handlers import RotatingFileHandler
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

def setup_security_logger(name="security_audit", log_level=logging.INFO):
    """
    Configure a dedicated logger for security audit events.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    log_file = os.path.join(LOG_DIR, "security-audit.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger

# Monitoring configuration
class ServiceMonitor:
    """
    Monitor service health and performance metrics
    """
    def __init__(self, service_name):
        self.service_name = service_name
        self.logger = setup_logger(f"monitor.{service_name}")
        self.security_logger = setup_security_logger()
        self.metrics = {
            'request_count': 0,
            'error_count': 0,
            'last_error': None,
            'last_success': None,
            'auth_success_count': 0,
            'auth_failure_count': 0,
            'permission_denied_count': 0,
            'suspicious_activity_count': 0,
            'total_response_time': 0,
            'response_count': 0
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

    def record_response_time(self, response_time):
        """Record response time for an operation"""
        self.metrics['total_response_time'] += response_time
        self.metrics['response_count'] += 1

    def record_auth_success(self, username, ip_address):
        """Record a successful authentication attempt"""
        self.metrics['auth_success_count'] += 1
        self.security_logger.info(f"AUTH_SUCCESS: User '{username}' from IP '{ip_address}' authenticated successfully.")

    def record_auth_failure(self, username, ip_address):
        """Record a failed authentication attempt"""
        self.metrics['auth_failure_count'] += 1
        self.security_logger.warning(f"AUTH_FAILURE: User '{username}' from IP '{ip_address}' failed to authenticate.")

    def record_permission_denied(self, user, action, resource, ip_address):
        """Record a permission denied event"""
        self.metrics['permission_denied_count'] += 1
        self.security_logger.warning(f"PERMISSION_DENIED: User '{user}' from IP '{ip_address}' attempted to perform '{action}' on '{resource}' without permission.")

    def record_suspicious_activity(self, activity_details, user=None, ip_address=None):
        """Record suspicious activity"""
        self.metrics['suspicious_activity_count'] += 1
        log_message = f"SUSPICIOUS_ACTIVITY: {activity_details}"
        if user: log_message += f" (User: {user})"
        if ip_address: log_message += f" (IP: {ip_address})"
        self.security_logger.critical(log_message)
    
    def get_metrics(self):
        """Return current metrics"""
        return {
            **self.metrics,
            'success_rate': (
                1 - (self.metrics['error_count'] / self.metrics['request_count'])
            ) if self.metrics['request_count'] > 0 else 1.0,
            'average_response_time': (
                self.metrics['total_response_time'] / self.metrics['response_count']
            ) if self.metrics['response_count'] > 0 else 0.0
        }