from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(roles):
    """
    Decorator to ensure user has one of the required roles.
    roles: list of strings, e.g. ['admin', 'manager']
    """
    if not isinstance(roles, list):
        roles = [roles]
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Check user role
            if current_user.role not in roles:
                flash('عذراً، لا تملك الصلاحية للوصول لهذه الصفحة.', 'danger')
                return redirect(url_for('admin.admin_dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
