from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from seedrcc import Seedr
from seedrcc.exceptions import SeedrError
from utils.dependencies import get_seedr_client

router = APIRouter(
    prefix="/account",
    tags=["Account"]
)

# Pydantic Models
class ChangeNameRequest(BaseModel):
    name: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

def to_dict(obj: Any) -> Dict[str, Any]:
    """Helper to convert objects to dict"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)

@router.get("/settings", summary="Get account settings")
def get_settings(client: Seedr = Depends(get_seedr_client)):
    try:
        settings = client.get_settings()
        return to_dict(settings)
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/memory-bandwidth", summary="Get memory and bandwidth usage")
def get_memory_bandwidth(client: Seedr = Depends(get_seedr_client)):
    try:
        memory_bandwidth = client.get_memory_bandwidth()
        return to_dict(memory_bandwidth)
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/devices", summary="Get list of authorized devices")
def get_devices(client: Seedr = Depends(get_seedr_client)):
    try:
        devices = client.get_devices()
        return {"devices": to_dict(devices)}
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/list_wishlist", summary="Get user's wishlist")
def list_wishlist(client: Seedr = Depends(get_seedr_client)):
    try:
        settings = client.get_settings()
        settings_dict = to_dict(settings)
        
        # Extract wishlist from account data
        wishlist = []
        if isinstance(settings_dict, dict):
            account = settings_dict.get('account', {})
            if isinstance(account, dict):
                wishlist = account.get('wishlist', [])
        
        return {
            "result": True,
            "code": 200,
            "wishlist": wishlist
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.put("/name", summary="Change account name")
def change_name(request: ChangeNameRequest, client: Seedr = Depends(get_seedr_client)):
    try:
        result = client.change_name(request.name, request.password)
        return {
            "success": True,
            "message": "Name changed successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.put("/password", summary="Change account password")
def change_password(request: ChangePasswordRequest, client: Seedr = Depends(get_seedr_client)):
    try:
        result = client.change_password(request.old_password, request.new_password)
        return {
            "success": True,
            "message": "Password changed successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
