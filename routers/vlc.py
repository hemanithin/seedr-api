from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
from config import settings

router = APIRouter(
    prefix="/vlc",
    tags=["VLC Player"]
)

class PlayRequest(BaseModel):
    url: str
    enqueue: bool = False

@router.post("/play", summary="Play a download URL in VLC media player")
async def play_in_vlc(request: PlayRequest):
    try:
        # Check if VLC exists
        if not os.path.exists(settings.VLC_PATH):
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "VLC not found",
                    "message": f"VLC media player not found at: {settings.VLC_PATH}",
                    "suggestion": "Please install VLC or update VLC_PATH in config"
                }
            )

        # Build VLC command
        if request.enqueue:
            vlc_command = [settings.VLC_PATH, "--one-instance", "--playlist-enqueue", request.url]
        else:
            vlc_command = [settings.VLC_PATH, request.url]

        # Launch VLC
        subprocess.Popen(vlc_command)

        return {
            "success": True,
            "message": "VLC opened successfully",
            "url": request.url,
            "mode": "enqueued" if request.enqueue else "playing"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/config", summary="Get current VLC configuration")
def get_vlc_config():
    return {
        "vlc_path": settings.VLC_PATH,
        "vlc_exists": os.path.exists(settings.VLC_PATH),
        "platform": os.name
    }
