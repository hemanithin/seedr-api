from fastapi import HTTPException, Query
from utils.seedr_client import client_manager

# Dependency
def get_seedr_client(user_id: str = Query('default', description="User identifier")):
    """
    FastAPI dependency to get or initialize the Seedr client.
    """
    client = client_manager.get_client(user_id)
    if not client:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    return client
