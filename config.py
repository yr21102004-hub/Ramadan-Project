import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Base Configuration Class.
    Follows Clean Code principles by separating concern of configuration from application logic.
    Enhanced with OSI Layer Security Protection
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'simple_secret_key')
    
    # Session Security (Layer 5-7)
    SESSION_COOKIE_SECURE = False # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # CSRF Protection (Layer 7)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Rate Limiting (Layer 5-7 - DDoS Protection)
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Database
    DATABASE_PATH = 'ramadan_company.db'
    BACKUP_DIR = 'backups'
    
    # File Uploads Security (Layer 7)
    UPLOAD_FOLDER = os.path.join('static', 'user_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Content Security Policy (Layer 7 - XSS Protection)
    CONTENT_SECURITY_POLICY = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", 
                      "https://cdn.jsdelivr.net", 
                      "https://unpkg.com",
                      "https://cdnjs.cloudflare.com"],
        'style-src': ["'self'", "'unsafe-inline'", 
                     "https://fonts.googleapis.com",
                     "https://cdn.jsdelivr.net",
                     "https://unpkg.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "data:"],
        'img-src': ["'self'", "data:", "https:", "blob:"],
        'connect-src': ["'self'", "ws:", "wss:"],
    }
    
    # Security Headers (Layer 6-7)
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(self), microphone=()',
    }
    
    # Input Validation (Layer 7)
    MAX_STRING_LENGTH = 10000
    MAX_ARRAY_LENGTH = 1000
    
    # IP Blocking Settings
    ENABLE_IP_BLOCKING = True
    BLOCK_DURATION = 3600  # 1 hour in seconds
    MAX_REQUESTS_PER_MINUTE = 100
    MAX_RAPID_REQUESTS = 10  # Max requests in 5 seconds

