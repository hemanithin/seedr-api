from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from seedrcc import Seedr
from seedrcc.exceptions import SeedrError
from utils.seedr_client import client_manager
from utils.dependencies import get_seedr_client

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Pydantic Models
class PasswordLoginRequest(BaseModel):
    username: str
    password: str

class DeviceCodeLoginRequest(BaseModel):
    device_code: str
    user_id: str = "default"

class RefreshTokenLoginRequest(BaseModel):
    refresh_token: str
    user_id: str = "default"

def to_dict(obj: Any) -> Dict[str, Any]:
    """Helper to convert objects to dict"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj) # Fallback

@router.post("/device-code", summary="Get device code for authentication")
def get_device_code():
    try:
        device_code_data = Seedr.get_device_code()
        return to_dict(device_code_data)
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/login/password", summary="Login with username and password")
def login_password(request: PasswordLoginRequest):
    try:
        client = client_manager.create_client_from_password(request.username, request.password)
        
        token_info = {
            "message": "Login successful",
            "user_id": request.username
        }
        
        if hasattr(client, "token") and client.token:
            token_info["token"] = to_dict(client.token)
        
        return token_info
        
    except SeedrError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/login/device-code", summary="Login with device code")
def login_device_code(request: DeviceCodeLoginRequest):
    try:
        client = client_manager.create_client_from_device_code(request.device_code, request.user_id)
        
        token_info = {
            "message": "Login successful",
            "user_id": request.user_id
        }
        
        if hasattr(client, "token") and client.token:
            token_info["token"] = to_dict(client.token)
        
        return token_info
        
    except SeedrError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/login/refresh-token", summary="Login with refresh token")
def login_refresh_token(request: RefreshTokenLoginRequest):
    try:
        client = client_manager.create_client_from_refresh_token(request.refresh_token, request.user_id)
        
        token_info = {
            "message": "Login successful",
            "user_id": request.user_id
        }
        
        if hasattr(client, "token") and client.token:
            token_info["token"] = to_dict(client.token)
        
        return token_info
        
    except SeedrError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/refresh", summary="Refresh access token")
def refresh_token(
    user_id: str = Query("default", description="User identifier"),
    client: Seedr = Depends(get_seedr_client)
):
    try:
        client.refresh_token()
        
        token_info = {
            "message": "Token refreshed successfully",
            "user_id": user_id
        }
        
        if hasattr(client, "token") and client.token:
            token_info["token"] = to_dict(client.token)
        
        return token_info
        
    except SeedrError as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/logout", summary="Logout and remove stored session")
def logout(user_id: str = Query("default", description="User identifier")):
    try:
        client_manager.remove_client(user_id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
