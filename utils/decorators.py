from functools import wraps
from flask import request
from utils import client_manager

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.args.get('user_id', 'default')
        client = client_manager.get_client(user_id)
        if not client:
            return {'error': 'Not authenticated. Please login first.'}, 401
        return f(client, *args, **kwargs)
    return decorated_function
