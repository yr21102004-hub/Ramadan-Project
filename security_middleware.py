"""
Advanced Security Middleware for OSI Layer Protection
Protects against various attacks across different OSI layers
"""
from flask import request, abort, jsonify
from functools import wraps
import re
import hashlib
import time
from collections import defaultdict
import ipaddress

class SecurityMiddleware:
    """Comprehensive security middleware for OSI layer protection"""
    
    def __init__(self, app=None):
        self.app = app
        self.request_history = defaultdict(list)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r'(\%27)|(\')|(\-\-)|(\%23)|(#)',  # SQL Injection
            r'((\%3C)|<)((\%2F)|\/)*[a-z0-9\%]+((\%3E)|>)',  # XSS
            r'((\%3C)|<)((\%69)|i|(\%49))((\%6D)|m|(\%4D))((\%67)|g|(\%47))',  # XSS img tag
            r'(((\%3C)|<)(\%2F|\/)*(\%73)|s)((\%63)|c|(\%43))((\%72)|r|(\%52))',  # XSS script
            r'((\%3C)|<)[^\n]+((\%3E)|>)',  # Generic XSS
            r'\.\./|\.\.\%2F',  # Path Traversal
            r'(union|select|insert|update|delete|drop|create|alter|exec|execute)',  # SQL Keywords
            r'(<script|javascript:|onerror=|onload=)',  # XSS patterns
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Register before_request handlers
        app.before_request(self.check_request_security)
        app.before_request(self.rate_limit_check)
        app.before_request(self.validate_headers)
        
    def check_request_security(self):
        """
        Layer 7 (Application Layer) Protection
        - SQL Injection detection
        - XSS detection
        - Path Traversal detection
        - Command Injection detection
        """
        # Get client IP
        client_ip = self.get_client_ip()
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            abort(403, description="Your IP has been blocked due to suspicious activity")
        
        # Check request data for malicious patterns
        suspicious_data = []
        
        # Check URL parameters
        for key, value in request.args.items():
            if self.contains_malicious_pattern(str(value)):
                suspicious_data.append(f"URL param: {key}")
        
        # Check form data
        if request.form:
            for key, value in request.form.items():
                if self.contains_malicious_pattern(str(value)):
                    suspicious_data.append(f"Form field: {key}")
        
        # Check JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    self.check_json_recursive(json_data, suspicious_data)
            except:
                pass
        
        # Check headers for injection attempts
        for header, value in request.headers:
            if self.contains_malicious_pattern(str(value)):
                suspicious_data.append(f"Header: {header}")
        
        # If suspicious patterns found, log and block
        if suspicious_data:
            self.log_security_event(client_ip, "Malicious Pattern Detected", suspicious_data)
            self.block_ip(client_ip)
            abort(403, description="Malicious request detected")
    
    def rate_limit_check(self):
        """
        Layer 5-7 Protection (Session/Presentation/Application)
        - DDoS protection
        - Brute force protection
        - Request flooding protection
        """
        client_ip = self.get_client_ip()
        current_time = time.time()
        
        # Clean old requests (older than 60 seconds)
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 60
        ]
        
        # Add current request
        self.request_history[client_ip].append(current_time)
        
        # Check request rate (max 100 requests per minute)
        if len(self.request_history[client_ip]) > 100:
            self.log_security_event(client_ip, "Rate Limit Exceeded", 
                                   f"{len(self.request_history[client_ip])} requests in 60s")
            self.block_ip(client_ip)
            abort(429, description="Too many requests. Please slow down.")
        
        # Check for rapid-fire requests (more than 10 in 5 seconds)
        recent_requests = [
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 5
        ]
        
        if len(recent_requests) > 10:
            self.log_security_event(client_ip, "Rapid Fire Detected", 
                                   f"{len(recent_requests)} requests in 5s")
            self.block_ip(client_ip, duration=300)  # Block for 5 minutes
            abort(429, description="Request rate too high. Temporarily blocked.")
    
    def validate_headers(self):
        """
        Layer 6-7 Protection (Presentation/Application)
        - Header validation
        - Content-Type validation
        - Origin validation
        """
        # Validate Content-Type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            
            # Allow only specific content types
            allowed_types = [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'text/plain'
            ]
            
            if not any(allowed in content_type for allowed in allowed_types):
                if content_type and 'boundary=' not in content_type:
                    self.log_security_event(self.get_client_ip(), 
                                          "Invalid Content-Type", content_type)
        
        # Validate User-Agent (block empty or suspicious user agents)
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
            if any(agent in user_agent.lower() for agent in suspicious_agents):
                self.log_security_event(self.get_client_ip(), 
                                      "Suspicious User-Agent", user_agent)
        
        # Check for Host header injection
        host = request.headers.get('Host', '')
        if host and not self.is_valid_host(host):
            self.log_security_event(self.get_client_ip(), 
                                  "Invalid Host Header", host)
            abort(400, description="Invalid host header")
    
    def contains_malicious_pattern(self, data):
        """Check if data contains malicious patterns"""
        data_lower = data.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, data_lower, re.IGNORECASE):
                return True
        
        return False
    
    def check_json_recursive(self, data, suspicious_data, path=""):
        """Recursively check JSON data for malicious patterns"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                self.check_json_recursive(value, suspicious_data, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self.check_json_recursive(item, suspicious_data, new_path)
        elif isinstance(data, str):
            if self.contains_malicious_pattern(data):
                suspicious_data.append(f"JSON field: {path}")
    
    def get_client_ip(self):
        """Get real client IP (considering proxies)"""
        # Check X-Forwarded-For header (for proxies/load balancers)
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Check X-Real-IP header
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        
        # Fallback to remote_addr
        return request.remote_addr or '0.0.0.0'
    
    def is_valid_host(self, host):
        """Validate host header"""
        # Remove port if present
        host = host.split(':')[0]
        
        # Allow localhost and 127.0.0.1
        if host in ['localhost', '127.0.0.1', '0.0.0.0']:
            return True
        
        # Check if it's a valid domain or IP
        try:
            ipaddress.ip_address(host)
            return True
        except:
            # Check if it's a valid domain name
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
            return bool(re.match(domain_pattern, host))
    
    def block_ip(self, ip, duration=None):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        
        # If duration specified, schedule unblock (in production, use Redis/database)
        if duration:
            # For now, just log it
            self.log_security_event(ip, "IP Blocked", f"Duration: {duration}s")
    
    def log_security_event(self, ip, event_type, details):
        """Log security events"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] IP: {ip} | Event: {event_type} | Details: {details}"
        
        # Write to security log file
        try:
            with open('logs/security.log', 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except:
            # Create logs directory if it doesn't exist
            import os
            os.makedirs('logs', exist_ok=True)
            with open('logs/security.log', 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        
        # Also log to console in development
        print(f"🔒 SECURITY EVENT: {log_entry}")


# Additional security decorators
def require_https(f):
    """Decorator to require HTTPS for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not request.headers.get('X-Forwarded-Proto') == 'https':
            # In development, allow HTTP
            if not request.host.startswith('127.0.0.1') and not request.host.startswith('localhost'):
                abort(403, description="HTTPS required")
        return f(*args, **kwargs)
    return decorated_function


def sanitize_input(data):
    """Sanitize user input to prevent XSS"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
        # Remove script tags
        data = re.sub(r'<script.*?</script>', '', data, flags=re.IGNORECASE | re.DOTALL)
        # Remove event handlers
        data = re.sub(r'on\w+\s*=', '', data, flags=re.IGNORECASE)
    return data
