from datetime import datetime

def to_dict(obj):
    """
    Recursively convert an object to a dictionary.
    Handles dataclasses, objects with __dict__, lists, datetime, and bytes.
    """
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    if hasattr(obj, '__dict__'):
        return {key: to_dict(value) for key, value in vars(obj).items()}
    return obj
