from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form, Response, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from seedrcc import Seedr
from seedrcc.exceptions import SeedrError
import requests
import subprocess
import os
import time
import logging
from config import settings
from utils.dependencies import get_seedr_client

router = APIRouter(
    prefix="/torrents",
    tags=["Torrents"]
)
logger = logging.getLogger(__name__)

# Pydantic Models
class AddTorrentRequest(BaseModel):
    magnet_link: str
    wishlist_id: Optional[str] = None
    folder_id: str = "-1"

class SmartAddTorrentRequest(BaseModel):
    magnet_link: str
    folder_id: str = "-1"
    skip_space_check: bool = False

class AddAndDownloadRequest(BaseModel):
    magnet_link: str
    folder_id: str = "-1"
    skip_space_check: bool = False
    wait_for_completion: bool = True
    max_wait_seconds: int = 300
    poll_interval: int = 5
    play_in_vlc: bool = False

class TorrentMetadataRequest(BaseModel):
    query: str

def to_dict(obj: Any) -> Dict[str, Any]:
    """Helper to convert objects to dict"""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)

# Helper functions
def _get_torrent_size(magnet_link: str) -> int:
    """Get torrent size from TorrentMeta API"""
    try:
        torrentmeta_url = 'https://torrentmeta.fly.dev'
        headers = {'Content-Type': 'application/json'}
        payload = {'query': magnet_link}
        
        response = requests.post(
            torrentmeta_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('data', {})
            if 'files' in metadata and isinstance(metadata['files'], list):
                return sum(file.get('size', 0) for file in metadata['files'])
        return 0
    except Exception as e:
        logger.error(f"Error fetching torrent size: {str(e)}")
        return 0

def _get_available_space(client: Seedr):
    """Get available space in bytes from Seedr account"""
    try:
        memory_bandwidth = client.get_memory_bandwidth()
        space_used = getattr(memory_bandwidth, 'space_used', 0)
        space_max = getattr(memory_bandwidth, 'space_max', 0)
        available_space = space_max - space_used
        return available_space, space_used, space_max
    except Exception as e:
        logger.error(f"Error fetching available space: {str(e)}")
        return 0, 0, 0

def _format_size(size_bytes: float) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

@router.post("/add", summary="Add torrent via magnet link")
def add_torrent(
    request: AddTorrentRequest,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        # Call add_torrent and get the raw result
        result = client.add_torrent(
            magnet_link=request.magnet_link,
            wishlist_id=request.wishlist_id,
            folder_id=request.folder_id
        )
        
        # If result has a response attribute (httpx Response object)
        if hasattr(result, 'status_code') and hasattr(result, 'text'):
            seedr_response = {
                "status_code": result.status_code,
                "raw_response": result.text
            }
            return {
                "success": True,
                "message": "Torrent added successfully",
                "seedr_response": seedr_response
            }
        else:
            # Fallback to dict conversion
            return {
                "success": True,
                "message": "Torrent added successfully",
                "result": to_dict(result)
            }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/smartAdd", summary="Smart add torrent with space validation")
def smart_add_torrent(
    request: SmartAddTorrentRequest,
    response: Response,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        # Perform space check unless explicitly skipped
        if not request.skip_space_check:
            torrent_size = _get_torrent_size(request.magnet_link)
            available_space, space_used, space_max = _get_available_space(client)
            
            if torrent_size > 0 and available_space > 0:
                if torrent_size > available_space:
                    space_needed = torrent_size - available_space
                    response.status_code = 507
                    return {
                        "success": False,
                        "error": "Insufficient storage space",
                        "message": "Cannot add torrent - not enough space available",
                        "space_check": {
                            "torrent_size": torrent_size,
                            "torrent_size_formatted": _format_size(torrent_size),
                            "available_space": available_space,
                            "available_space_formatted": _format_size(available_space),
                            "space_used": space_used,
                            "space_used_formatted": _format_size(space_used),
                            "space_max": space_max,
                            "space_max_formatted": _format_size(space_max),
                            "space_needed": space_needed,
                            "space_needed_formatted": _format_size(space_needed),
                            "sufficient": False
                        }
                    }
        
        # Add torrent
        result = client.add_torrent(
            magnet_link=request.magnet_link,
            folder_id=request.folder_id
        )
        
        # Handle raw response or dict conversion
        if hasattr(result, 'status_code') and hasattr(result, 'text'):
            result_data = {
                "status_code": result.status_code,
                "raw_response": result.text
            }
        else:
            result_data = to_dict(result)
        
        response_data = {
            "success": True,
            "message": "Torrent added successfully",
            "result": result_data
        }
        
        if not request.skip_space_check:
            torrent_size = _get_torrent_size(request.magnet_link) if "torrent_size" not in locals() else torrent_size
            available_space, space_used, space_max = _get_available_space(client) if "available_space" not in locals() else (available_space, space_used, space_max)
            
            response_data["space_check"] = {
                "torrent_size": torrent_size,
                "torrent_size_formatted": _format_size(torrent_size) if torrent_size > 0 else "Unknown",
                "available_space": available_space,
                "available_space_formatted": _format_size(available_space),
                "space_used": space_used,
                "space_used_formatted": _format_size(space_used),
                "space_max": space_max,
                "space_max_formatted": _format_size(space_max),
                "sufficient": True
            }
            
        return response_data

    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/addAndDownload", summary="Add torrent and wait for download URLs")
def add_and_download(
    request: AddAndDownloadRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        # Space Check Logic (Reuse helper or duplicate logic for clarity in one flow)
        if not request.skip_space_check:
            torrent_size = _get_torrent_size(request.magnet_link)
            available_space, space_used, space_max = _get_available_space(client)
            if torrent_size > 0 and available_space > 0 and torrent_size > available_space:
                response.status_code = 507
                return {
                    "success": False,
                    "error": "Insufficient storage space",
                    "space_check": {
                        "torrent_size": torrent_size,
                        "available_space": available_space,
                        "sufficient": False
                    }
                }

        # Add Torrent
        add_result = client.add_torrent(magnet_link=request.magnet_link, folder_id=request.folder_id)
        
        # Handle raw response or dict conversion
        if hasattr(add_result, 'status_code') and hasattr(add_result, 'text'):
            torrent_info = {
                "status_code": add_result.status_code,
                "raw_response": add_result.text
            }
        else:
            torrent_info = to_dict(add_result)
        
        response_data = {
            "success": True,
            "message": "Torrent added successfully",
            "torrent_info": torrent_info,
            "files": []
        }

        if not request.wait_for_completion:
            response.status_code = 202
            response_data["message"] = "Torrent added. Set wait_for_completion=true to get download URLs."
            response_data["status"] = "added"
            return response_data

        # Polling Logic
        start_time = time.time()
        max_wait = min(request.max_wait_seconds, 600)
        torrent_title = getattr(add_result, 'title', '')
        torrent_hash = getattr(add_result, 'torrent_hash', '')
        
        while (time.time() - start_time) < max_wait:
            try:
                folder_id_to_check = request.folder_id if request.folder_id != '-1' else '0'
                contents = client.list_contents(folder_id_to_check)
                
                is_downloading = False
                
                # Check torrents list for progress
                if hasattr(contents, 'torrents') and contents.torrents:
                    for torrent in contents.torrents:
                        if (hasattr(torrent, 'hash') and torrent.hash == torrent_hash) or \
                           (hasattr(torrent, 'title') and torrent.title == torrent_title):
                            progress = getattr(torrent, 'progress', 0)
                            try:
                                curr_prog = int(float(progress)) if isinstance(progress, str) else int(progress)
                            except:
                                curr_prog = 0
                            
                            if curr_prog < 100:
                                is_downloading = True
                            break
                
                if not is_downloading:
                    # Check for completed folder
                    matching_folder = None
                    normalized_title = torrent_title.replace('&', '_').replace(':', ' ').replace('?', '')
                    
                    if hasattr(contents, 'folders') and contents.folders:
                        for folder in contents.folders:
                            folder_name = getattr(folder, 'name', '')
                            if folder_name == torrent_title or \
                               folder_name == normalized_title or \
                               folder_name.replace('&', '_') == torrent_title.replace('&', '_'):
                                matching_folder = folder
                                break
                    
                    if matching_folder:
                        # Fetch files
                        folder_contents = client.list_contents(str(matching_folder.id))
                        if hasattr(folder_contents, 'files') and folder_contents.files:
                            for file in folder_contents.files:
                                try:
                                    file_info = client.fetch_file(str(file.folder_file_id))
                                    response_data['files'].append({
                                        'file_id': file.folder_file_id,
                                        'name': file.name,
                                        'size': file.size,
                                        'download_url': file_info.url
                                    })
                                except Exception:
                                    pass
                            
                            response_data['folder_id'] = matching_folder.id
                            response_data['status'] = 'completed'
                            
                            # VLC Playback
                            if request.play_in_vlc and settings.VLC_PATH and os.path.exists(settings.VLC_PATH):
                                valid_files = [f for f in response_data['files'] if 'download_url' in f]
                                if valid_files:
                                    enqueue = len(valid_files) > 1
                                    for file in valid_files:
                                        cmd = [settings.VLC_PATH]
                                        if enqueue:
                                            cmd.extend(["--one-instance", "--playlist-enqueue"])
                                        cmd.append(file['download_url'])
                                        subprocess.Popen(cmd)
                                    response_data['vlc_playback'] = {'started': True}

                            return response_data
            
                time.sleep(request.poll_interval)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(request.poll_interval)

        # Timeout
        response.status_code = 202
        response_data["status"] = "timeout"
        response_data["message"] = f"Timeout after {max_wait} seconds."
        return response_data

    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/add/file", summary="Add torrent via file upload")
def add_torrent_file(
    file: UploadFile = File(...),
    folder_id: str = Form("-1"),
    wishlist_id: Optional[str] = Form(None),
    client: Seedr = Depends(get_seedr_client)
):
    try:
        file_content = file.file.read()
        result = client.add_torrent(
            torrent_file=file_content,
            wishlist_id=wishlist_id,
            folder_id=folder_id
        )
        
        # Handle raw response or dict conversion
        if hasattr(result, 'status_code') and hasattr(result, 'text'):
            result_data = {
                "status_code": result.status_code,
                "raw_response": result.text
            }
        else:
            result_data = to_dict(result)
        
        return {
            "success": True,
            "message": "Torrent added successfully",
            "result": result_data
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.delete("/{torrent_id}", summary="Delete a torrent")
def delete_torrent(
    torrent_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.delete_torrent(torrent_id)
        return {
            "success": True,
            "message": "Torrent deleted successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.delete("/wishlist/{wishlist_id}", summary="Delete a wishlist item")
def delete_wishlist(
    wishlist_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.delete_wishlist(wishlist_id)
        return {
            "success": True,
            "message": "Wishlist item deleted successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/list", summary="List all active torrents")
async def list_torrents(client: Seedr = Depends(get_seedr_client)):
    try:
        contents = client.list_contents()
        torrents_list = []
        if hasattr(contents, 'torrents') and contents.torrents:
            torrents_list = [to_dict(t) for t in contents.torrents]
        
        return {
            "success": True,
            "torrents": torrents_list,
            "total": len(torrents_list)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/metadata", summary="Get torrent metadata")
async def get_metadata(request: TorrentMetadataRequest):
    try:
        torrentmeta_url = 'https://torrentmeta.fly.dev'
        headers = {'Content-Type': 'application/json'}
        payload = {'query': request.query}
        
        response = requests.post(
            torrentmeta_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "metadata": response.json()}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch torrent metadata")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
