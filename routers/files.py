from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from seedrcc import Seedr
from seedrcc.exceptions import SeedrError
from utils.dependencies import get_seedr_client
import logging

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)
logger = logging.getLogger(__name__)

# Pydantic Models
class CreateFolderRequest(BaseModel):
    name: str

class RenameRequest(BaseModel):
    new_name: str

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

@router.get("/list", summary="List folder contents")
def list_contents(
    folder_id: str = Query("0", description="Folder ID to list (default: '0' for root)"),
    client: Seedr = Depends(get_seedr_client)
):
    try:
        contents = client.list_contents(folder_id)
        return to_dict(contents)
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/list-all", summary="Recursively list all files and folders")
def list_all_contents(client: Seedr = Depends(get_seedr_client)):
    try:
        all_folders = []
        all_files = []
        folders_to_process = ['0']  # Start with root
        
        while folders_to_process:
            current_folder_id = folders_to_process.pop(0)
            contents = client.list_contents(current_folder_id)
            
            # Add current folder items
            if hasattr(contents, 'folders') and contents.folders:
                for folder in contents.folders:
                    all_folders.append(folder)
                    folders_to_process.append(str(folder.id))
            
            if hasattr(contents, 'files') and contents.files:
                for file in contents.files:
                    all_files.append(file)
        
        return {
            "folders": to_dict(all_folders),
            "files": to_dict(all_files),
            "total_folders": len(all_folders),
            "total_files": len(all_files)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/folder", summary="Create a new folder")
def create_folder(
    request: CreateFolderRequest,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.add_folder(request.name)
        return {
            "success": True,
            "message": "Folder created successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.put("/file/{file_id}/rename", summary="Rename a file")
def rename_file(
    file_id: str,
    request: RenameRequest,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.rename_file(file_id, rename_to=request.new_name)
        return {
            "success": True,
            "message": "File renamed successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.put("/folder/{folder_id}/rename", summary="Rename a folder")
def rename_folder(
    folder_id: str,
    request: RenameRequest,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.rename_folder(folder_id, rename_to=request.new_name)
        return {
            "success": True,
            "message": "Folder renamed successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.delete("/file/{file_id}", summary="Delete a file")
def delete_file(
    file_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.delete_file(file_id)
        return {
            "success": True,
            "message": "File deleted successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.delete("/folder/{folder_id}", summary="Delete a folder")
def delete_folder(
    folder_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        result = client.delete_folder(folder_id)
        return {
            "success": True,
            "message": "Folder deleted successfully",
            "result": to_dict(result)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/search", summary="Search files by query")
def search_files(
    query: str = Query(..., description="Search query"),
    client: Seedr = Depends(get_seedr_client)
):
    try:
        results = client.search_files(query)
        return {"results": to_dict(results)}
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/fetch/{file_id}", summary="Get file download URL")
def fetch_file(
    file_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        file_info = client.fetch_file(file_id)
        return to_dict(file_info)
    except SeedrError as e:
        error_msg = str(e)
        if "Invalid JSON" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Seedr API returned an invalid response. This usually happens if the file ID is incorrect, it belongs to a folder, or download limits are reached.",
                    "suggestion": "If you are trying to download a folder, please use the Archive/Download Folder feature."
                }
            )
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/archive/{folder_id}", summary="Create archive from folder")
def create_archive(
    folder_id: str,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        # Get folder contents and return download links for all files
        folder_contents = client.list_contents(folder_id)
        
        files_with_links = []
        
        # Iterate through all files in the folder
        if hasattr(folder_contents, 'files') and folder_contents.files:
            for file in folder_contents.files:
                try:
                    # Get download URL for each file
                    file_info = client.fetch_file(str(file.folder_file_id))
                    files_with_links.append({
                        'file_id': file.folder_file_id,
                        'name': file.name,
                        'size': file.size,
                        'download_url': file_info.url
                    })
                except Exception as e:
                    files_with_links.append({
                        'file_id': file.folder_file_id,
                        'name': file.name,
                        'size': file.size,
                        'error': f'Could not get download link: {str(e)}'
                    })
        
        return {
            "success": True,
            "message": f"Found {len(files_with_links)} files in folder",
            "folder_id": folder_id,
            "files": files_with_links,
            "total_files": len(files_with_links)
        }
    except SeedrError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/archive/{archive_id}/status", summary="Check status of a folder archive")
async def archive_status(
    archive_id: str,
    response: Response,
    client: Seedr = Depends(get_seedr_client)
):
    try:
        # We use fetch_file to check if the archive is ready
        file_info = client.fetch_file(archive_id)
        
        return {
            "status": "ready",
            "message": "Archive link generated.",
            "download_url": file_info.url,
            "name": file_info.name,
            "file_id": archive_id
        }
    except SeedrError as e:
        error_str = str(e)
        if "Invalid JSON" in error_str or "Not Found" in error_str:
            response.status_code = 202
            return {
                "status": "in_progress",
                "message": "Archive is still being created or registered by Seedr. Please wait a moment and check again.",
                "archive_id": archive_id
            }
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
